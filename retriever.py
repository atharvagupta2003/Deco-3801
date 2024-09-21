import os
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import OpenAI

load_dotenv()

def retrieve_sequence(query):
    # Initialize embeddings and vector store
    model_name = "multilingual-e5-large"
    embeddings = PineconeEmbeddings(
        model=model_name,
        pinecone_api_key=os.environ.get("PINECONE_API_KEY")
    )

    index_name = os.getenv("INDEX_NAME")
    vectorstore = PineconeVectorStore(index=index_name, embedding=embeddings)

    # Initialize OpenAI model
    llm = OpenAI(temperature=0)

    # Create RetrievalQA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

    # Run the query
    result = qa_chain.run(query)

    return result