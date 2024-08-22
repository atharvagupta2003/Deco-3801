import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

load_dotenv()

#which is the best way to integrate this with our preprocessor?

#document to vector storage
if __name__ == "__main__":
    loader = TextLoader("/Users/hp/Desktop/react-langchain/chemical")
    document = loader.load()

    #check for data cleaning.
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0.1)
    text = text_splitter.split_documents(document)
    print(f"Number of documents: {len(text)}")

    model_name = "multilingual-e5-large"
    embeddings = PineconeEmbeddings(
        model=model_name,
        pinecone_api_key=os.environ.get("PINECONE_API_KEY")
    )
    print("ingesting")
    PineconeVectorStore.from_documents(text, embeddings, index=os.getenv("INDEX_NAME"))