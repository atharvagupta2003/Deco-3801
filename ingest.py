import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain_text_splitters import CharacterTextSplitter
import pandas as pd

load_dotenv()

def preprocess_and_ingest(file_path):
    """
    Preprocesses the given file and ingests the processed text into Pinecone.
    """
    # Load and preprocess the file
    if file_path.endswith('.csv'):
        data = pd.read_csv(file_path)
        documents = [row['text'] for _, row in data.iterrows()]
    elif file_path.endswith('.txt'):
        with open(file_path, 'r') as file:
            documents = file.readlines()
    else:
        raise ValueError("Unsupported file format")

    # Combine documents into a single text block
    text = "\n".join(documents)

    # Split the text into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0.1)
    split_text = text_splitter.split_documents([text])

    # Initialize embeddings and vector store
    model_name = "multilingual-e5-large"
    embeddings = PineconeEmbeddings(
        model=model_name,
        pinecone_api_key=os.environ.get("PINECONE_API_KEY")
    )

    index_name = os.getenv("INDEX_NAME")

    # Ingest into Pinecone
    PineconeVectorStore.from_documents(split_text, embeddings, index=index_name)

    return len(split_text)