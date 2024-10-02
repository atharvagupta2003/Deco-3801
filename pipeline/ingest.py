import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader, CSVLoader, PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma
import tiktoken

load_dotenv()

def num_tokens(text: str, model: str = "cl100k_base") -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.get_encoding(model)
    return len(encoding.encode(text))

def truncate_text(text: str, max_tokens: int = 512) -> str:
    """Truncate text to a maximum number of tokens."""
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])

def ingest_documents(folder_path):
    # Load all text, CSV, and PDF files in the given folder
    documents = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith('.txt'):
            loader = TextLoader(file_path)
            documents.extend(loader.load())
        elif filename.endswith('.csv'):
            loader = CSVLoader(file_path)
            documents.extend(loader.load())
        elif filename.endswith('.pdf'):
            loader = PyPDFLoader(file_path)
            documents.extend(loader.load())

    # Split text into chunks
    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=300,
        chunk_overlap=50,
        length_function=lambda text: num_tokens(text, "cl100k_base"),
        is_separator_regex=False,
    )
    texts = text_splitter.split_documents(documents)
    print(f"Number of document chunks: {len(texts)}")

    # Truncate long texts
    truncated_texts = [truncate_text(doc.page_content) for doc in texts]

    # Add logging to check token counts
    for i, text in enumerate(truncated_texts):
        token_count = num_tokens(text)
        if token_count > 512:
            print(f"Warning: Chunk {i} has {token_count} tokens after truncation.")

    # Initialize embeddings
    embeddings = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.environ.get("nvidia_api_key"),
        truncate="NONE",
    )

    # Create and persist the vector store
    vectorstore = Chroma.from_texts(
        texts=truncated_texts,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    print("Embeddings successfully stored in Chroma vector database.")

if __name__ == "__main__":
    # This allows the script to be run standalone for testing
    test_folder = "/Users/aniketgupta/Desktop/Deco-3801/data"
    ingest_documents(test_folder)