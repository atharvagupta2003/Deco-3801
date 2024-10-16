# ingest.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma  # Updated import
from pydantic import BaseModel

def load_documents(directory):
    """
    Load all supported documents from the specified directory.

    Supported formats:
    - .txt
    - .pdf

    Args:
        directory (str): Path to the directory containing research papers.

    Returns:
        list: A list of loaded documents.
    """
    documents = []
    # Supported file extensions
    supported_extensions = ['.txt', '.pdf']
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return documents

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        _, ext = os.path.splitext(filename)
        
        if ext.lower() == '.txt':
            try:
                loader = TextLoader(filepath, encoding='utf-8')
                loaded_docs = loader.load()
                documents.extend(loaded_docs)
                print(f"Loaded TXT file: {filename}")
            except Exception as e:
                print(f"Error loading TXT file {filename}: {e}")
        elif ext.lower() == '.pdf':
            try:
                loader = PyPDFLoader(filepath)
                loaded_docs = loader.load()
                documents.extend(loaded_docs)
                print(f"Loaded PDF file: {filename}")
            except Exception as e:
                print(f"Error loading PDF file {filename}: {e}")
        else:
            print(f"Unsupported file format: {filename}")
    
    return documents

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Directory containing your research papers
    directory = "data/research_papers/"
    
    # Load all documents from the directory
    documents = load_documents(directory)
    print(f"\nTotal documents loaded: {len(documents)}")
    
    if not documents:
        print("No documents to process. Exiting.")
        return

    # Split documents into smaller chunks
    text_splitter = CharacterTextSplitter(chunk_size=250, chunk_overlap=50)  # Further reduced chunk_size and overlap
    texts = text_splitter.split_documents(documents)
    print(f"Total chunks created: {len(texts)}")
    
    # Initialize NVIDIA embeddings
    embeddings = NVIDIAEmbeddings(
        model="nv-embedqa-e5-v5",
        api_key=os.environ.get("nvidia_api_key"),
        truncate="NONE",
    )
    
    # Initialize Chroma vector store
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=embeddings
    )
    
    # Define batch size to ensure we don't exceed token limits
    batch_size = 3  # Reduced batch size to prevent exceeding token limits
    total_chunks = len(texts)
    
    print("\nStarting embedding and ingestion process...")
    
    for i in range(0, total_chunks, batch_size):
        batch = texts[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}: {len(batch)} chunks")
        try:
            vectorstore.add_documents(batch)
        except Exception as e:
            print(f"Error embedding batch {i//batch_size + 1}: {e}")
    
    # Persist the vector store to disk
    # According to the deprecation warning, manual persistence is no longer needed
    # So you can comment out or remove the persist() call
    # vectorstore.persist()
    print("Embeddings successfully stored in Chroma vector database.")

if __name__ == "__main__":
    main()
