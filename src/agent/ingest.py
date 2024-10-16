# ingest.py

import requests
import fitz  # PyMuPDF for PDF processing
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the directory where PDFs will be downloaded
pdf_dir = 'data'

# Create the directory if it does not exist
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)
    print(f"Created directory: {pdf_dir}")

# Global variables to hold vectorstores
wiki_vectorstore = None
arxiv_vectorstore = None
custom_vectorstore = None  # Global variable for custom vectorstore

# Initialize NVIDIA embeddings
embeddings = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    api_key=os.environ.get("nvidia_api_key"),
    truncate="NONE",
)

def download_pdf(pdf_url, save_path):
    """
    Download the PDF from the given URL and save it to the specified path.
    """
    response = requests.get(pdf_url)
    with open(save_path, 'wb') as f:
        f.write(response.content)

def extract_text_from_pdf(pdf_path):
    """
    Extract text from the given PDF file using PyMuPDF (fitz).
    """
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)  # load each page
        text += page.get_text()  # extract text from each page
    return text

def create_custom_vectorstore(docs_list):
    global custom_vectorstore
    logging.info("Creating custom vectorstore...")
    # Convert the docs_list to Document objects
    documents = [Document(page_content=doc["text"], metadata={"source": doc["title"]}) for doc in docs_list]

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=400, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(documents)
    logging.info(f"Number of document chunks: {len(doc_splits)}")

    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        embedding=embeddings,
        collection_name="custom-chroma",
    )
    custom_vectorstore = vectorstore
    logging.info("Custom vectorstore created.")
    return vectorstore

def create_arxiv_vectorstore():
    global arxiv_vectorstore
    if arxiv_vectorstore is not None:
        return arxiv_vectorstore

    logging.info("Creating ArXiv vectorstore...")
    # List of ArXiv PDF URLs
    urls = [
        "https://arxiv.org/pdf/2306.07377v1.pdf",
        "https://arxiv.org/pdf/2306.10577v1.pdf",
    ]

    docs = []
    for i, pdf_url in enumerate(urls):
        # Step 1: Create a path for the PDF to be saved in the data folder
        pdf_filename = os.path.join(pdf_dir, f"arxiv_paper_{i + 1}.pdf")

        # Step 2: Download the PDF
        download_pdf(pdf_url, pdf_filename)
        logging.info(f"Downloaded: {pdf_filename}")

        # Step 3: Extract text from the downloaded PDF
        extracted_text = extract_text_from_pdf(pdf_filename)

        # Create a document dictionary and add it to the docs list
        docs.append({
            "title": f"ArXiv Paper {i + 1}",
            "text": extracted_text
        })

    # Split the documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=50
    )
    documents = []
    for doc in docs:
        splits = text_splitter.split_text(doc["text"])
        for i, chunk in enumerate(splits):
            documents.append(Document(page_content=chunk, metadata={"source": doc["title"]}))

    logging.info(f"Number of document chunks: {len(documents)}")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="arxiv-chroma",
    )
    arxiv_vectorstore = vectorstore
    logging.info("ArXiv vectorstore created.")
    return vectorstore

def create_wiki_vectorstore():
    global wiki_vectorstore
    if wiki_vectorstore is not None:
        return wiki_vectorstore

    logging.info("Creating Wiki vectorstore...")
    urls = [
        "https://en.wikipedia.org/wiki/Carbon_monoxide",
        "https://en.wikipedia.org/wiki/Nylon_66",
        "https://en.wikipedia.org/wiki/Oxygen",
        "https://en.wikipedia.org/wiki/Nitrogen"
    ]

    # Load documents
    docs = []
    for url in urls:
        loader = WebBaseLoader(url)
        loaded_docs = loader.load()
        for doc in loaded_docs:
            docs.append(doc)

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=400, chunk_overlap=50
    )
    documents = text_splitter.split_documents(docs)
    logging.info(f"Number of document chunks: {len(documents)}")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="wiki-chroma",
    )
    wiki_vectorstore = vectorstore
    logging.info("Wiki vectorstore created.")
    return vectorstore

def get_retriever(vector_db_choice):
    global custom_vectorstore, wiki_vectorstore, arxiv_vectorstore
    if vector_db_choice == 'Wiki':
        if wiki_vectorstore is None:
            create_wiki_vectorstore()
        retriever = wiki_vectorstore.as_retriever()
        return retriever
    elif vector_db_choice == 'ArXiv':
        if arxiv_vectorstore is None:
            create_arxiv_vectorstore()
        retriever = arxiv_vectorstore.as_retriever()
        return retriever
    elif vector_db_choice == 'Custom':
        if custom_vectorstore is not None:
            retriever = custom_vectorstore.as_retriever()
            return retriever
        else:
            raise ValueError("Custom vectorstore is not initialized. Please upload documents to create a custom vectorstore.")
    else:
        raise ValueError("Invalid vector database choice")

logging.info("Ingest module loaded successfully.")
