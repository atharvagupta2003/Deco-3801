# src/agent/ingest.py

import os
from langchain.vectorstores import Chroma  # Updated import path
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFMinerLoader, UnstructuredWordDocumentLoader
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Debug: Check if API key is loaded
nvidia_api_key = os.environ.get("nvidia_api_key")

# Initialize embeddings
embeddings = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    api_key=nvidia_api_key,
    truncate="NONE",
)

# Initialize vector stores with unique collection names and persist directories
wiki_vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="wiki-chroma",
    persist_directory="chroma_wiki"
)

arxiv_vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="arxiv-chroma",
    persist_directory="chroma_arxiv"
)

custom_vectorstore = Chroma(
    embedding_function=embeddings,
    collection_name="custom-chroma",
    persist_directory="chroma_custom"
)

def get_retriever(vector_db_choice):
    """
    Returns the retriever for the specified vector store.

    Args:
        vector_db_choice (str): Choice of vector store ('Wiki', 'ArXiv', 'Custom').

    Returns:
        Chroma: Retriever object for the selected vector store.

    Raises:
        ValueError: If an invalid vector_db_choice is provided.
    """
    if vector_db_choice == 'Wiki':
        logging.info("Retrieving from Wiki vectorstore.")
        return wiki_vectorstore.as_retriever()
    elif vector_db_choice == 'ArXiv':
        logging.info("Retrieving from ArXiv vectorstore.")
        return arxiv_vectorstore.as_retriever()
    elif vector_db_choice == 'Custom':
        logging.info("Retrieving from Custom vectorstore.")
        return custom_vectorstore.as_retriever()
    else:
        logging.error("Invalid vector database choice provided.")
        raise ValueError("Invalid vector database choice")

def create_custom_vectorstore(documents):
    """
    Adds documents to the custom vector store and persists them.

    Args:
        documents (List[Document]): List of Document objects.

    Returns:
        Chroma: The populated custom vector store.

    Raises:
        Exception: If there's an error during the addition or persistence of documents.
    """
    if not documents:
        logging.warning("No documents provided for the custom vector store.")
        return custom_vectorstore

    try:
        custom_vectorstore.add_documents(documents)
        custom_vectorstore.persist()
        logging.info("Custom vectorstore created and persisted successfully.")
        return custom_vectorstore
    except Exception as e:
        logging.error(f"Error creating custom vector store: {str(e)}")
        raise e

def create_custom_vectorstore_from_file(docs_list):
    """
    Processes uploaded documents, splits them into chunks, and adds them to the custom vector store.

    Args:
        docs_list (List[dict]): List of dictionaries with 'title' and 'text' keys.

    Returns:
        Chroma: The populated custom vector store.

    Raises:
        Exception: If there's an error during processing or vector store creation.
    """
    try:
        if not docs_list:
            logging.warning("No documents provided for the custom vector store.")
            return custom_vectorstore

        # Convert the docs_list to Document objects
        documents = [Document(page_content=doc["text"], metadata={"source": doc["title"]}) for doc in docs_list]

        # Split documents into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        doc_splits = text_splitter.split_documents(documents)
        logging.info(f"Number of document chunks: {len(doc_splits)}")

        # Add documents to custom vectorstore
        custom_vectorstore = create_custom_vectorstore(doc_splits)
        return custom_vectorstore
    except Exception as e:
        logging.error(f"Error processing documents: {str(e)}")
        raise e

logging.info("Ingest module loaded successfully.")
