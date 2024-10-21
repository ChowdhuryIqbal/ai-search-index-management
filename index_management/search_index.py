import logging
import os
import requests
from tqdm import tqdm

def create_search_index_if_not_exists(service_name, index_name, semantic_config_name, admin_key, language, vector_config_name):
    url = f"https://{service_name}.search.windows.net/indexes/{index_name}?api-version=2023-07-01-Preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key,
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logging.info(f"Search index {index_name} already exists.")
        return
    elif response.status_code == 404:
        logging.info(f"Search index {index_name} does not exist. Creating a new one.")
    else:
        raise Exception(f"Failed to check if search index exists. Error: {response.text}")

    body = {
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "searchable": True,
                "key": True,
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": True,
                "sortable": False,
                "facetable": False,
                "filterable": False,
                "analyzer": f"{language}.lucene" if language else None,
            },
            {
                "name": "title",
                "type": "Edm.String",
                "searchable": True,
                "sortable": False,
                "facetable": False,
                "filterable": False,
                "analyzer": f"{language}.lucene" if language else None,
            },
            {
                "name": "filepath",
                "type": "Edm.String",
                "searchable": True,
                "sortable": False,
                "facetable": False,
                "filterable": True,
            },
            {
                "name": "url",
                "type": "Edm.String",
                "searchable": True,
            },
            {
                "name": "metadata",
                "type": "Edm.String",
                "searchable": True,
            },
            {
                "name": "contentVector",
                "type": "Collection(Edm.Single)",
                "searchable": True,
                "retrievable": True,
                "dimensions": int(os.getenv("VECTOR_DIMENSION", 1536)),
                "vectorSearchConfiguration": vector_config_name
            },
        ],
        "suggesters": [],
        "scoringProfiles": [],
        "semantic": {
            "configurations": [
                {
                    "name": semantic_config_name,
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "prioritizedContentFields": [{"fieldName": "content"}],
                        "prioritizedKeywordsFields": [],
                    },
                }
            ]
        },
        "vectorSearch": {
            "algorithmConfigurations": [
                {
                    "name": vector_config_name,
                    "kind": "hnsw"
                }
            ]
        }
    }

    response = requests.put(url, json=body, headers=headers)
    if response.status_code == 201:
        logging.info(f"Created search index {index_name}")
    elif response.status_code == 204:
        logging.info(f"Updated existing search index {index_name}")
    else:
        raise Exception(f"Failed to create search index. Error: {response.text}")

def delete_documents_from_index(search_client, index_name, blob_names):
    search_parameters = {
        "select": "*",
    }
    
    results = search_client.search(search_text="*", **search_parameters)
    ids_to_delete = []

    for result in results:
        doc_id = result.get("id")
        file_path = result.get("filepath")
        
        if file_path in blob_names:
            ids_to_delete.append(doc_id)
    
    if not ids_to_delete:
        logging.info("No documents found for the provided blob names.")
        return
    
    delete_actions = [{"@search.action": "delete", "id": doc_id} for doc_id in ids_to_delete]
    search_client.delete_documents(documents=delete_actions)
    logging.info(f"Deleted documents with IDs: {ids_to_delete}")

def upload_documents_to_index(search_client, documents, upload_batch_size=50):
    for i in tqdm(range(0, len(documents), upload_batch_size), desc="Indexing Chunks..."):
        batch = documents[i:i + upload_batch_size]
        results = search_client.upload_documents(documents=batch)
        num_failures = 0
        errors = set()
        for result in results:
            if not result.succeeded:
                logging.error(f"Indexing Failed for {result.key} with ERROR: {result.error_message}")
                num_failures += 1
                errors.add(result.error_message)
        if num_failures > 0:
            raise Exception(f"INDEXING FAILED for {num_failures} documents. Please recreate the index."
                            f"To Debug: PLEASE CHECK chunk_size and upload_batch_size. \n Error Messages: {list(errors)}")

def list_existing_documents(search_client):
    search_parameters = {
        "select": "filepath",
    }
    
    results = search_client.search(search_text="*", **search_parameters)
    existing_files = set()

    for result in results:
        existing_files.add(result.get("filepath"))
    
    return existing_files
