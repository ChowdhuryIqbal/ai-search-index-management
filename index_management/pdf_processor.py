import logging
import tempfile
# from fitz import open as fitz_open
from index_management.utils import chunk_text
from langchain.document_loaders import PyPDFLoader
import os
import fitz  # PyMuPDF
import time
import base64
import requests

def extract_tables_from_pdf(blob_client, form_recognizer_client):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        blob_data = blob_client.download_blob()
        blob_data.readinto(temp_file)
        temp_file.flush()
        temp_file_name = temp_file.name

    with open(temp_file_name, "rb") as f:
        poller = form_recognizer_client.begin_analyze_document("prebuilt-layout", document=f)
    result = poller.result()

    os.remove(temp_file_name)

    tables = []
    for table in result.tables:
        table_data = []
        for cell in table.cells:
            table_data.append({
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                "content": cell.content
            })
        tables.append(table_data)

    return tables

def extract_images_from_pdf(pdf_document):
    images = []
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        for image_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{image_ext}") as temp_file:
                temp_file.write(image_bytes)
                image_path = temp_file.name
            images.append((page_number, image_path))
    return images

def analyze_image_with_gpt4v(image_path, gpt4v_endpoint, headers):
    encoded_image = base64.b64encode(open(image_path, 'rb').read()).decode('ascii')
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You can analyze images. You are an expert in understanding diagrams and workflows based on legends found in an image."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "Analyze this image and describe its contents, including any legends, diagrams, or workflows you can identify."
                    }
                ]
            }
        ],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 800
    }

    try:
        response = requests.post(gpt4v_endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to make the request. Error: {e}")
        return None

def has_tables(blob_client, form_recognizer_client):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        blob_data = blob_client.download_blob()
        blob_data.readinto(temp_file)
        temp_file.flush()
        temp_file_name = temp_file.name

    with open(temp_file_name, "rb") as f:
        poller = form_recognizer_client.begin_analyze_document("prebuilt-layout", document=f)
    result = poller.result()

    os.remove(temp_file_name)

    return len(result.tables) > 0

def process_new_files(container_client, form_recognizer_client, oai_client, gpt4v_endpoint, headers, new_files, user_id):
    documents = []
    id = 1
    for blob_name in new_files:
        blob_client = container_client.get_blob_client(blob_name)

        # Read and process the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            blob_data = blob_client.download_blob()
            blob_data.readinto(temp_file)
            temp_file_name = temp_file.name

        try:
            pdf_document = fitz.open(temp_file_name)

            # Extract and process tables
            if has_tables(blob_client, form_recognizer_client):
                logging.info(f"Tables found in {blob_name}. Extracting tables...")
                tables = extract_tables_from_pdf(blob_client, form_recognizer_client)
                for table_id, table in enumerate(tables):
                    table_content = "\n".join([cell["content"] for cell in table])
                    table_chunks = chunk_text(table_content)
                    for j, chunk in enumerate(table_chunks):
                        response = oai_client.embeddings.create(model="text-embedding-ada-002", input=chunk)
                        vector = response.dict()['data'][0]['embedding']
                        logging.info(f"Generated Embedding for table chunk {j}: {vector}")

                        document = {
                            "id": f"{id}_table_{table_id}_{j}",
                            "filepath": blob_name,
                            "content": chunk,
                            "metadata": blob_name,
                            "contentVector": vector,
                            "@search.action": "upload"
                        }
                        documents.append(document)
                    id += 1

            # Extract and process images
            images = extract_images_from_pdf(pdf_document)
            for page_number, image_path in images:
                logging.info(f"Analyzing image on page {page_number} with GPT-4 Vision...")
                gpt4v_analysis = analyze_image_with_gpt4v(image_path, gpt4v_endpoint, headers)
                if gpt4v_analysis:
                    gpt4v_response = gpt4v_analysis["choices"][0]["message"]["content"]
                    image_chunks = chunk_text(gpt4v_response)
                    for k, chunk in enumerate(image_chunks):
                        response = oai_client.embeddings.create(model="text-embedding-ada-002", input=chunk)
                        vector = response.dict()['data'][0]['embedding']
                        logging.info(f"Generated Embedding for image chunk {k}: {vector}")

                        document = {
                            "id": f"{id}_image_{page_number}_{k}",
                            "filepath": blob_name,
                            "content": chunk,
                            "metadata": blob_name,
                            "contentVector": vector,
                            "@search.action": "upload"
                        }
                        documents.append(document)
                        id += 1
                    os.remove(image_path)

            # Process remaining content
            logging.info(f"Processing remaining content of {blob_name}...")
            loader = PyPDFLoader(temp_file_name)
            pages = loader.load()
                
            if pages is not None:
                content = "\n".join([page.page_content for page in pages])
                chunks = chunk_text(content)
                for i, chunk in enumerate(chunks):
                    response = oai_client.embeddings.create(model="text-embedding-ada-002", input=chunk)
                    vector = response.dict()['data'][0]['embedding']
                    logging.info(f"Generated Embedding for chunk {i}: {vector}")

                    document = {
                        "id": f"{id}_{i}",
                        "filepath": blob_name,
                        "content": chunk,
                        "metadata": blob_name,
                        "contentVector": vector,
                            "@search.action": "upload"
                    }
                    documents.append(document)
                id += 1

            pdf_document.close()
        finally:
            time.sleep(0.1)  # Small delay before attempting to delete
            try:
                os.remove(temp_file_name)
            except PermissionError:
                logging.warning(f"Unable to delete temporary file: {temp_file_name}")

    return documents
