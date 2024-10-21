from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.storage.queue import QueueClient
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
import argparse
import logging
import os
from dotenv import load_dotenv
from index_management.search_index import create_search_index_if_not_exists, delete_documents_from_index, list_existing_documents, upload_documents_to_index
from index_management.blob_handler import get_blob_container_client, queue_blob_names
from index_management.pdf_processor import process_new_files
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables from .env file
load_dotenv()
# Setup logging
logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description='Process some PDFs.')
    parser.add_argument('operation', type=str, help='Operation to perform (upload or delete)')
    parser.add_argument('user_id', type=str, help='User ID')
    parser.add_argument('container_name', type=str, help='Blob storage container name')
    parser.add_argument('--blob_names', type=str, nargs='*', help='List of blob names to delete for delete operation')
    args = parser.parse_args()


    operation = args.operation
    user_id = args.user_id
    container_name = args.container_name
    blob_names_to_delete = args.blob_names

    blob_connection_string = os.getenv('BlobConnectionString')
    search_service_name = os.getenv('SearchServiceName')
    search_admin_key = os.getenv('SearchAdminKey')
    form_recognizer_endpoint = os.getenv('FormRecognizerEndpoint')
    form_recognizer_key = os.getenv('FormRecognizerKey')
    gpt4v_key = os.getenv('OPENAI_API_KEY_AUSEAST')
    api_base = os.getenv('OPENAI_API_BASE_AUSEAST')
    api_version = os.getenv('OPENAI_API_VERSION_AUSEAST')
    model_auseast = os.getenv('MODEL_AUSEAST')

    gpt4v_endpoint = f"https://{api_base}.openai.azure.com/openai/deployments/{model_auseast}/chat/completions?api-version={api_version}"

    headers = {
        "Content-Type": "application/json",
        "api-key": gpt4v_key,
    }

    if not blob_connection_string:
        raise Exception("Blob connection string not found in environment variables.")
    if not search_service_name or not search_admin_key:
        raise Exception("Search service name or admin key not found in environment variables.")
    if not form_recognizer_endpoint or not form_recognizer_key:
        raise Exception("Form Recognizer endpoint or key not found in environment variables.")

    endpoint = f"https://{search_service_name}.search.windows.net"
    search_client = SearchClient(endpoint=endpoint, index_name=user_id, credential=AzureKeyCredential(search_admin_key))

    oai_client = AzureOpenAI(
        api_key=os.getenv('AzureOpenaiApiKey'),
        api_version="2024-02-01",
        azure_endpoint=os.getenv('AzureOpenaiEndpoint')
    )

    form_recognizer_client = DocumentAnalysisClient(endpoint=form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key))

    logging.info('Starting operation.')

    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    if not container_client.exists():
        raise Exception(f"Container '{container_name}' does not exist in the blob storage.")

    # Create the search index if it doesn't exist
    create_search_index_if_not_exists(service_name=search_service_name, index_name=user_id, 
                                      semantic_config_name="azureml-default", admin_key=search_admin_key,
                                      language=None, vector_config_name="default")

    # List all PDF files in the container
    blob_names = [blob.name for blob in container_client.list_blobs() if blob.name.lower().endswith('.pdf')]

    if operation == "upload":
        existing_files = list_existing_documents(search_client)
        new_files = [blob.name for blob in container_client.list_blobs() if blob.name.lower().endswith('.pdf') and blob.name not in existing_files]

        if not new_files:
            logging.info("No new files to index.")
            return

        documents = process_new_files(container_client, form_recognizer_client, oai_client, gpt4v_endpoint, headers, new_files, user_id)
        if documents:
            upload_documents_to_index(search_client, documents)
            queue_blob_names(new_files)
        else:
            logging.info("No new documents to upload.")

    elif operation == "delete":
        if not blob_names_to_delete:
            raise Exception("No blob names specified for deletion.")
        delete_documents_from_index(search_client, user_id, blob_names_to_delete)
    else:
        raise Exception(f"Operation {operation} is not supported.")

if __name__ == "__main__":
    main()
