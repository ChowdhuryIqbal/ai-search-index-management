# Azure AI Search Index Manager

This Python project helps manage Azure AI Search Index by uploading, indexing, and deleting documents (specifically PDFs). The PDFs are stored in an Azure Blob Storage container and are processed for table extraction, image analysis, and embedding generation using Azure AI services (e.g., Form Recognizer, GPT-4 Vision, and OpenAI Embeddings).

## Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [Upload Documents](#upload-documents)
  - [Delete Documents](#delete-documents)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Logging](#logging)

## Requirements

- **Python:** Python 3.7 or later
- **Azure Services:**
  - Azure Blob Storage
  - Azure Cognitive Search
  - Azure Form Recognizer
  - Azure OpenAI API (GPT-4 Vision)

## Installation

1. Clone the Repository

    ```bash
    git clone https://github.com/ChowdhuryIqbal/ai-search-index-management.git
    cd index_management
    ```

2. Install Dependencies

    ```bash
    pip install -r requirements.txt
    ```

3. Set Up Environment Variables

   You need to create a `.env` file in the root directory of the project to provide Azure credentials and configuration values.

    ```bash
    touch .env
    ```

   Then, open the `.env` file and add the following keys:

    ```ini
    # Azure Blob Storage
    BlobConnectionString=<BLOB_CONNECTION_STRING>

    # Azure Cognitive Search
    SearchServiceName=<SEARCH_SERVICE_NAME>
    SearchAdminKey=<SEARCH_ADMIN_KEY>

    # Azure Form Recognizer
    FormRecognizerEndpoint=<FORM_RECOGNIZER_ENDPOINT>
    FormRecognizerKey=<FORM_RECOGNIZER_KEY>

    # Azure OpenAI GPT-4 Vision
    OPENAI_API_KEY_AUSEAST=<OPENAI_API_KEY_FOR_GPT4V>
    OPENAI_API_BASE_AUSEAST=<OPENAI_API_BASE>
    OPENAI_API_VERSION_AUSEAST=<OPENAI_API_VERSION>
    MODEL_AUSEAST=<OPENAI_MODEL_NAME>

    # Optional - Azure Queue (for queuing document names)
    QueueConnectionString=<QUEUE_CONNECTION_STRING>
    QueueName=<QUEUE_NAME>
    ```

## Usage

Running the code supports two main operations: uploading documents to the Azure AI Search Index and deleting documents from the index. You can run these operations through the command-line interface.

### 1. Upload Documents

To upload and index new PDF documents from a blob storage container to the Azure AI Search Index, run:

    ```bash
    python -m index_management.main upload <index_name> <container_name>
    ```

Where:

- `<index_name>` is the name of the Azure Cognitive Search index (for example, `sample_index`).
- `<container_name>` is the name of the Azure Blob Storage container holding the PDF files (for example, `sample-docs`).

Example:

    ```bash
    python -m index_management.main upload my_index my_container
    ```

### 2. Delete Documents

To delete specific documents from the Azure AI Search Index, based on the blob names, run:

    ```bash
    python -m index_management.main delete <index_name> <container_name> --blob_names <blob_name_1> <blob_name_2>
    ```

Where:

- `<index_name>` is the name of the Azure Cognitive Search index.
- `<container_name>` is the name of the blob storage container.
- `<blob_name_1>` and `<blob_name_2>` are the names of the specific blobs (PDF files) to be deleted from the index.

Example:

    ```bash
    python -m index_management.main delete my_index my_container --blob_names file1.pdf file2.pdf
    ```

## Environment Variables

The `.env` file should contain the following environment variables to enable the Azure services to function correctly.

    # Azure Blob Storage
    BlobConnectionString=<BLOB_CONNECTION_STRING>

    # Azure Cognitive Search
    SearchServiceName=<SEARCH_SERVICE_NAME>
    SearchAdminKey=<SEARCH_ADMIN_KEY>

    # Azure Form Recognizer
    FormRecognizerEndpoint=<FORM_RECOGNIZER_ENDPOINT>
    FormRecognizerKey=<FORM_RECOGNIZER_KEY>

    # Azure OpenAI GPT-4 Vision
    OPENAI_API_KEY_AUSEAST=<OPENAI_API_KEY_FOR_GPT4V>
    OPENAI_API_BASE_AUSEAST=<OPENAI_API_BASE>
    OPENAI_API_VERSION_AUSEAST=<OPENAI_API_VERSION>
    MODEL_AUSEAST=<OPENAI_MODEL_NAME>

    # Optional - Azure Queue (for queuing document names)
    QueueConnectionString=<QUEUE_CONNECTION_STRING>
    QueueName=<QUEUE_NAME>
    

## Project Structure

Here’s a breakdown of the file structure:

- `main.py`: Handles command-line arguments and calls other modules to perform operations.
- `blob_handler.py`: Manages interactions with Azure Blob Storage.
- `search_index.py`: Contains functions for creating, uploading, and deleting documents in the Azure Cognitive Search index.
- `pdf_processor.py`: Processes PDFs (table extraction, images, embeddings).
- `gpt4v_handler.py`: Handles GPT-4 Vision image analysis.
- `utils.py`: Contains utility functions for chunking text, reading blob contents, etc.

## Logging

The application uses Python’s built-in logging module. Logs are printed to the console to track the flow of the application, including successful indexing, errors, and upload progress.

You can adjust the logging level by modifying this line in the `main.py`:

    
    logging.basicConfig(level=logging.INFO)
    
Change `INFO` to `DEBUG` for more detailed logs or `ERROR` to show only errors.
