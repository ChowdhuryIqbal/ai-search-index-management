import logging
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient
import json
import os

def get_blob_container_client(connection_string, container_name):
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    
    if not container_client.exists():
        raise Exception(f"Container '{container_name}' does not exist in the blob storage.")
    return container_client

def queue_blob_names(blob_names):
    queue_connection_string = os.getenv('QueueConnectionString')
    queue_name = os.getenv('QueueName')

    if not queue_connection_string or not queue_name:
        raise Exception("Queue connection string or queue name not found in environment variables.")

    queue_client = QueueClient.from_connection_string(queue_connection_string, queue_name)

    for blob_name in blob_names:
        queue_client.send_message(json.dumps({"blob_name": blob_name}))
        logging.info(f"Queued blob name: {blob_name}")
