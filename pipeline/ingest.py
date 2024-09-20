import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma

load_dotenv()

#document to vector storage
if __name__ == "__main__":
    loader = TextLoader("/Users/hp/Desktop/react-langchain/chemical")
    document = loader.load()

    #check for data cleaning.
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0.1)
    text = text_splitter.split_documents(document)
    print(f"Number of documents: {len(text)}")

    embeddings = NVIDIAEmbeddings(
        model="nvidia/nv-embedqa-e5-v5",
        api_key=os.environ.get("nvidia_api_key"),
        truncate="NONE",
    )

    vectorstore = Chroma.from_documents(
        documents=text,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )

    vectorstore.persist()

    print("Embeddings successfully stored in Chroma vector database.")
