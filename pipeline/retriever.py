import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings
from langchain import hub
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_ollama.llms import OllamaLLM

load_dotenv()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
if __name__ == "__main__":
    print("retrieving")

    #check for the metrices to use
    #are cosine the best or will k means/nearest neighbour work well for our task
    embeddings = PineconeEmbeddings()
    model = OllamaLLM(model="llama3.1")

    # this is the query that user will input in frontend
    # wrap it inside a prompt template in future
    # can we pass the query through any other llm for refinement
    query = "what is a chemical synthesis?"
    chain = PromptTemplate.from_template(template=query) | model
    res = chain.invoke(input={})
    print(res)

    # maybe use any of the hwchase17 retriever prompt
    #experiment which one works better with FAISS
    retrieval_prompt = hub.pull("langchain_ai/retrieval-qa-chat")

    #Maybe use FAISS vecotr store
    vectors = PineconeVectorStore(
        index_name=os.environ['INDEX_NAME'], embedding=embeddings
    )

    docs_chain = create_stuff_documents_chain(model, retrieval_prompt)
    retrieval_chain = create_retrieval_chain(
        retriever=vectors.as_retriever(), combine_docs_chain=docs_chain
    )

    res = retrieval_chain.invoke(input={"input": query})

    #should we create a separate pipeline for res to pass them through another llm for refinement?
    print(res)

    #temporary retrieval prompt
    #can this be improved by one-shot or chain of thought prompting?
    #figure out a way for dynamic prompt reconstruction
    template = """
    Use the given following starting materials and reaction conditions in context, reconstruct the most efficient sequence of chemical reactions that leads to the desired product. Ensure that each step in the synthesis is chemically feasible and includes all necessary reagents, catalysts, and conditions. Provide a detailed description of each reaction step, including any intermediate compounds formed.

    **Starting Materials:**
    - [List of reactants]

    **Reaction Conditions:**
    - [List of reaction conditions]

    **Desired Product:**
    - [Chemical structure or name of the desired product]

    **Constraints:**
    - [Any specific constraints, e.g., reaction time, temperature, yield optimization]

    **Output Format:**
    - Step-by-step reaction sequence with detailed explanations.
    - Include intermediate compounds and conditions for each step.
    
    {context}
    
    Question: {question}"""

    retrieval_prompt = PromptTemplate.from_template(template)

    #how will we parse out the output?
    #We have to parse it out in steps
    chain = (
        {"context": vectors.as_retriever() | format_docs, "question": RunnablePassthrough}
         | retrieval_prompt
         | model
         # | Output_Parser()
    )

    result = chain.invoke(query)
    print(result)