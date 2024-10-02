import os
from dotenv import load_dotenv
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain.schema import Document
from langgraph.graph import END, START

import operator
from typing_extensions import TypedDict
from typing import List, Annotated

load_dotenv()

llm = ChatOllama(model='llama3.1', temperature=0)
llm_json_mode = ChatOllama(model='llama3.1', temperature=0, format='json')

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

retriever = vectorstore.as_retriever(k=5)

# Define a custom prompt template
router_instructions = """
You are an expert at routing a user question to a sequence generator or web search.

The vector store contains the following {context} related to the user query.

If the information in the vector store seems sufficient to answer the question route towards sequence generator to answer the question using vector store.

Else if the information seems insufficient or irrelevant to answer the question use the web search to find more information.

Return JSON with single key, datasource, that is 'websearch' or 'sequence generator' depending on the question.

Question: {question}
Answer:"""

seq_generator_instructions = """
You are an expert at reconstructing sequences for a user question.

Answer the user question based on the {context}

Only give the answer nothing else.

Your answer should be in steps such as step1: /n step2: /n step3: ....

Include explanation of every step and if any reaction is involved.

Question: {question}
Answer:"""

# def router(user_query):
#
#     docs = retriever.invoke(user_query)
#     context = " ".join([doc.page_content for doc in docs])
#
#     print("---context---")
#     print(context)
#     print("------------------------------")
#     prompt_template = PromptTemplate(
#         input_variables=["context", "question"],
#         template=router_instructions,
#     )
#
#     prompt = prompt_template.format(context=context, question=user_query)
#
#     router_response = llm_json_mode.invoke(prompt)
#
#     try:
#         response_json = json.loads(router_response.content)
#         return response_json
#     except json.JSONDecodeError:
#         return {"error": "Failed to decode JSON response from LLM"}
#     except AttributeError:
#         return {"error": "LLM response does not have 'content' attribute"}
#
#
# def generator(user_query):
#     docs = retriever.invoke(user_query)
#     context = " ".join([doc.page_content for doc in docs])
#     seq_generator_prompt = seq_generator_instructions.format(context=context, question=user_query)
#     generation = llm.invoke([HumanMessage(content=seq_generator_prompt)])
#     return generation.content

# # Test the router function with a sample query
# if __name__ == "__main__":
#     test_query = "What are the steps for synthesis of nitrogen?"
#
#     # Call the router function with the test query
#     result = generator(test_query)
#
#     print(result)
#     # # Print the result
#     # print("Routing Decision:")
#     # print(json.dumps(result, indent=4))


# # Test the router function with a sample query
# if __name__ == "__main__":
#     test_query = "What are the steps for synthesis of nitrogen?"
#
#     # Call the router function with the test query
#     result = router(test_query)
#
#     print(result)
#     # Print the result
#     print("Routing Decision:")
#     print(json.dumps(result, indent=4))

web_search_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
    api_key=os.environ.get("TAVILY_API_KEY"),
    # include_domains=[...],
    # exclude_domains=[...],
    # name="...",            # overwrite default tool name
    # description="...",     # overwrite default tool description
    # args_schema=...,       # overwrite default args_schema: BaseModel
)


class GraphState(TypedDict):
    """
    Graph state is a dictionary that contains information we want to propagate to, and modify in, each graph node.
    """

    question: str  # User question
    generation: str  # LLM generation
    web_search: str  # Binary decision to run web search
    documents: List[str]  # List of retrieved documents


# -----------Nodes------------
def retrieve(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Write retrieved documents to documents key in state
    documents = retriever.invoke(question)
    return {"documents": documents}


def generate(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]

    # RAG generation
    docs_txt = " ".join([doc.page_content for doc in documents])
    seq_generator_prompt = seq_generator_instructions.format(context=docs_txt, question=question)
    generation = llm.invoke([HumanMessage(content=seq_generator_prompt)])
    return {"generation": generation}


def web_search(state):
    """
    Web search based on the question

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Appended web results to documents
    """

    print("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents", [])

    # Web search
    docs = web_search_tool.invoke({"query": question})
    web_results = "\n".join([d["content"] for d in docs])
    web_results = Document(page_content=web_results)
    documents.append(web_results)
    return {"documents": documents}


# -----------Edges------------


def route_question(state):
    """
    Route question to web search or sequence generator

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    print("---ROUTE QUESTION---")
    question = state["question"]
    documents = state["documents"]
    context = " ".join([doc.page_content for doc in documents])
    router_instructions_formated = router_instructions.format(question=question, context=context)
    route = llm_json_mode.invoke(
        [SystemMessage(content=router_instructions_formated)]
        + [HumanMessage(content=state["question"])]
    )
    source = json.loads(route.content)["datasource"]
    if source == "websearch":
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return "websearch"
    elif source == "sequence generator":
        print("---ROUTE QUESTION TO RAG---")
        return "sequence generator"


from langgraph.graph import StateGraph
from IPython.display import Image, display

workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("websearch", web_search)  # web search
workflow.add_node("retrieve", retrieve)  # retrieve
workflow.add_node("generate", generate)  # generate

workflow.add_edge(START, "retrieve")
workflow.add_conditional_edges(
    "retrieve",

    route_question,
    {"websearch": "websearch", "sequence generator": "generate"},
)
workflow.add_edge("websearch", "generate")
workflow.add_edge("generate", END)

graph = workflow.compile()
display(Image(graph.get_graph().draw_mermaid_png()))

inputs = {"question": "steps for synthesis of nitrogen?"}
for event in graph.stream(inputs, stream_mode="values"):
    print(event)
