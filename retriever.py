import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma
from langchain_ollama.llms import OllamaLLM
from database import get_relevant_documents
load_dotenv()


def retrieve_sequence(query):
    relevant_docs = get_relevant_documents(query)
    # Implement your sequence reconstruction logic here
    reconstructed_sequence = " ".join(doc['content'] for doc in relevant_docs)
    return reconstructed_sequence
# Initialize embeddings
embeddings = NVIDIAEmbeddings(
    model="nvidia/nv-embedqa-e5-v5",
    api_key=os.environ.get("nvidia_api_key"),
    truncate="NONE",
)

# Load the persisted Chroma vector store
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# Initialize Ollama LLM
llm = OllamaLLM(
    model="llama3.1",  # Changed to llama2 as llama3.1 might not be available
    temperature=0.1
)

# Define a custom prompt template
template = """
Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {question}
Answer:"""

prompt = PromptTemplate(
    template=template,
    input_variables=["context", "question"]
)

# Create a retrieval chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(),
    chain_type_kwargs={"prompt": prompt}
)


# Function to perform retrieval and answer questions
def ask_question(question):
    try:
        response = qa_chain.invoke(question)
        return response
    except Exception as e:
        print(f"Error while asking question: {str(e)}")
        raise e


# Main interaction loop
if __name__ == "__main__":
    print("Welcome to the Chemical Information Retrieval System")
    print("Type 'exit' to quit the program")

    while True:
        user_question = input("\nEnter your question: ")

        if user_question.lower() == 'exit':
            print("Thank you for using the Chemical Information Retrieval System. Goodbye!")
            break

        answer = ask_question(user_question)
        print(f"\nAnswer: {answer['result']}")