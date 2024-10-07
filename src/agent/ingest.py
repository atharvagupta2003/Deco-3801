import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma
import tiktoken

load_dotenv()

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

# Initialize embeddings
embeddings = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.environ.get("nvidia_api_key"),
        truncate="NONE",
)

# Create and persist the vector store
vectorstore = Chroma.from_documents(
        documents=doc_splits,
        embedding=embeddings,
        collection_name="rag-chroma",
)
print("Embeddings successfully stored in Chroma vector database.")

retriever = vectorstore.as_retriever(k=5)
