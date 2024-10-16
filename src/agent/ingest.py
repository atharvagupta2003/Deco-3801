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

load_dotenv()

# Define the directory where PDFs will be downloaded
pdf_dir = 'data'

# Create the directory if it does not exist
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)
    print(f"Created directory: {pdf_dir}")


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


#Initialize NVIDIA embeddings for ArXiv
embeddings = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    api_key=os.environ.get("nvidia_api_key"),
    truncate="NONE",
)
custom_vectorstore = None

def create_custom_vectorstore(docs_list):
    global custom_vectorstore
    # Convert the docs_list to Document objects
    documents = [Document(page_content=doc["text"], metadata={"source": doc["title"]}) for doc in docs_list]

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=400, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(documents)
    print(f"Number of document chunks: {len(doc_splits)}")

    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        embedding=embeddings,
        collection_name="custom-chroma",
    )
    custom_vectorstore = vectorstore
    return vectorstore


def create_arxiv_vectorstore():
    """
    Download, extract text, and split documents from ArXiv URLs.
    """
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
        print(f"Downloaded: {pdf_filename}")

        # Step 3: Extract text from the downloaded PDF
        extracted_text = extract_text_from_pdf(pdf_filename)

        # Create a document dictionary and add it to the docs list
        docs.append({
            "title": f"ArXiv Paper {i + 1}",
            "text": extracted_text
        })

    # Step 4: Split the documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=50
    )
    doc_splits = []
    for doc in docs:
        doc_splits.extend(text_splitter.split_text(doc["text"]))

    print(f"Number of document chunks: {len(doc_splits)}")
    vectorstore = Chroma.from_texts(
      texts=doc_splits,
      embedding=embeddings,
      collection_name="arxiv-chroma",
    )
    return vectorstore

def create_wiki_vectorstore():
    urls = [
        "https://en.wikipedia.org/wiki/Carbon_monoxide",
        "https://en.wikipedia.org/wiki/Nylon_66",
        "https://en.wikipedia.org/wiki/Oxygen",
        "https://en.wikipedia.org/wiki/Nitrogen"
    ]

    # Load documents
    docs = [WebBaseLoader(url).load() for url in urls]
    docs_list = [item for sublist in docs for item in sublist]

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=400, chunk_overlap=50
    )
    doc_splits = text_splitter.split_documents(docs_list)
    print(f"Number of document chunks: {len(doc_splits)}")

    vectorstore = Chroma.from_documents(
        documents=doc_splits,
        embedding=embeddings,
        collection_name="wiki-chroma",
    )
    return vectorstore

def get_retriever(vector_db_choice):
    if vector_db_choice == 'Wiki':
        return create_wiki_vectorstore().as_retriever()
    elif vector_db_choice == 'ArXiv':
        return create_arxiv_vectorstore().as_retriever()
    elif vector_db_choice == 'Custom':
        if custom_vectorstore is not None:
            return custom_vectorstore.as_retriever()
        else:
            raise ValueError("Custom vectorstore is not initialized.")
    else:
        raise ValueError("Invalid vector database choice")
print("Embeddings successfully stored in Chroma vector database.")

# retriever_arxiv = create_arxiv_vectorstore().as_retriever(k=5)

# retriever_custom = create_custom_vectorstore(docs_list).as_retriever(k=5)