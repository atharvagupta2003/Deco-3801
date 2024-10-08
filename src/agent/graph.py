import os
from dotenv import load_dotenv
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA  
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain.schema import Document
from langgraph.graph import END, START
from langgraph.graph import StateGraph
from src.agent.ingest import retriever
import operator
from typing_extensions import TypedDict
from typing import List, Annotated

load_dotenv()

llm = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0)
llm_json_mode = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0, format='json')

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

always give the source with the answer

Your answer should be in steps such as step1: /n step2: /n step3: ....

Give only the answer nothing else

Include explanation of every step and if any reaction is involved.

Question: {question}
Answer:"""

# ans_grader_instructions = """
# You are a grader assessing whether an answer is useful to resolve a question. /n
# Here is the answer:
# /n ------- /n
# {generation}
# /n ------- /n
# Here is the question: {question}
#
# Return JSON with single key, score, that is 'yes' or 'no' depending on the question and the answer generated.
#
# Return the result as a JSON object like this:
# {score: "yes"} or {score: "no"}
# """
from langchain_core.output_parsers import JsonOutputParser

prompt = PromptTemplate(
    template="""You are a grader assessing whether an answer is useful to resolve a question. \n 
    Here is the answer:
    \n ------- \n
    {generation} 
    \n ------- \n
    Here is the question: {question}
    Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. \n
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.""",
    input_variables=["generation", "question"],
)

answer_grader = prompt | llm_json_mode | JsonOutputParser()

web_search_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
    api_key=os.environ.get("TAVILY_API_KEY"),
)


class GraphState(TypedDict):
    """
    Graph state is a dictionary that contains information we want to propagate to, and modify in, each graph node.
    """

    question: str
    generation: str
    web_search: str
    documents: List[str]


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


def grade_generation(state):
    """
    Determines whether the generation answers the question or not.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    print("---GRADE GENERATION vs QUESTION---")
    question = state["question"]
    generation = state["generation"]
    score = answer_grader.invoke({'question': question, 'generation': generation})
    grade = score["score"]
    if grade == "yes":
        print("---DECISION: GENERATION ADDRESSES QUESTION---")
        return "useful"
    else:
        print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
        return "not useful"


def setup_workflow():
    workflow = StateGraph(GraphState)

    workflow.add_node("websearch", web_search)
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("generate", generate)

    workflow.add_edge(START, "retrieve")
    workflow.add_conditional_edges("retrieve", route_question, {"websearch": "websearch", "sequence generator": "generate"})
    workflow.add_edge("websearch", "generate")
    workflow.add_conditional_edges("generate", grade_generation, {"useful": END, "not useful": "retrieve"})
    workflow.add_edge("generate", END)

    return workflow


def ask_question(question: str):
    workflow = setup_workflow()
    inputs = {"question": question}
    events = []

    for event in workflow.compile().stream(inputs, stream_mode="values"):
        events.append(event)
    return events


def main():
    question = "steps for synthesis of carbon monoxide?"
    result = ask_question(question)
    print(result)


if __name__ == "__main__":
    main()