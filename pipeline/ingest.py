import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma
from utils.preprocess import process_document


load_dotenv()


def preprocess_and_ingest(file_path):
    # Open the file and pass it to process_document
    with open(file_path, 'rb') as file:
        preprocessed_data = process_document(file)

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0.1)
    chunks = text_splitter.split_text(' '.join(preprocessed_data['steps']))

    embeddings = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.environ.get("nvidia_api_key"),
        truncate="NONE",
    )

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )



    return len(chunks)


if __name__ == "__main__":
    file_path = "/Users/aniketgupta/Desktop/Deco-3801/chemical.txt"
    num_chunks = preprocess_and_ingest(file_path)
    print(f"Number of chunks ingested: {num_chunks}")
    print("Embeddings successfully stored in Chroma vector database.")