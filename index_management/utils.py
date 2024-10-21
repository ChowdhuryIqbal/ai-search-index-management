from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging
import tempfile

def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    text_splitter = RecursiveCharacterTextSplitter(
       chunk_size=chunk_size, 
       chunk_overlap=chunk_overlap,
       length_function=len,
       is_separator_regex=False
    )
    return text_splitter.split_text(text)

def read_blob_content(blob_client):
    """Read the contents of a blob."""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_name = temp_file.name
            logging.info(f'Temporary file created: {temp_file_name}')

            blob_data = blob_client.download_blob()
            blob_data.readinto(temp_file)
            temp_file.flush()

            try:
                with open(temp_file_name, 'r', encoding='utf-8') as file:
                    content = file.read()
            except UnicodeDecodeError:
                with open(temp_file_name, 'rb') as file:
                    content = file.read().decode('latin1')

        os.remove(temp_file_name)

        return content
    except Exception as e:
        logging.error(f"Error reading blob content: {e}")
        return None
