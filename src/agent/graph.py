import os
from dotenv import load_dotenv
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA  
from langchain_chroma import Chroma
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from web_scrapers.search_tool_arxiv import ArxivSearchTool
from langchain_community.tools.tavily_search import TavilySearchResults
from web_scrapers.search_tool_arxiv import *

from langchain.schema import Document
from langgraph.graph import END, START
from langgraph.graph import StateGraph
from src.agent.ingest import retriever
import operator
from typing_extensions import TypedDict
from typing import List, Annotated
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

llm = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0, api_key=os.getenv('nvidia_api_key'))
llm_json_mode = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0, format='json', api_key=os.getenv('nvidia_api_key'))


router_instructions = """
You are an expert at routing a user question to a sequence generator or web search.

The vector store contains the following context related to the user query:
{context}

If the information in the vector store seems sufficient to answer the question, route towards 'sequence generator' to answer the question using vector store.

Else if the information seems insufficient or irrelevant to answer the question, use 'websearch' to find more information.

Provide the result as a JSON object with a single key 'datasource' and no preamble or explanation.

Return the result as a JSON object like this:
{{"datasource": "websearch"}} or {{"datasource": "sequence generator"}}.

Question: {question}
Answer:"""


seq_generator_instructions = """
You are an expert at reconstructing sequences for a user question.

Answer the user question based on the {context}

Only give the answer nothing else.

Always give the source with the answer.

Your answer should be in steps such as step1: /n step2: /n step3: .... 

Include an explanation of every step and if any reaction is involved.

Question: {question}
Answer:"""

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

prompt_template = """
You are an intelligent assistant tasked with selecting the best web search tools to retrieve information based on the user's query. 
Here are the available tools:
{tools_list}

Here is the user query: {question}

Based on the query, select one or more of the tools that would provide the most relevant information. 
Once the search is complete, use the information retrieved to generate a clear and concise answer to the query.
Respond with the names of the tools you would like to use as a JSON list with no explanation. 
For example, ['Tavily', 'Arxiv', 'Wikipedia'] or ['Wikipedia'] or ['Tavily', 'Arxiv'].
"""

# Create the prompt template
prompt = PromptTemplate(
    template=prompt_template,
    input_variables=["question", "tools_list"]
)

web_search_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True,
    include_raw_content=True,
    include_images=True,
    api_key=os.environ.get("TAVILY_API_KEY"),
)

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=5, max_characters=10000))

arxiv_tool = ArxivSearchTool(max_results=5, save_folder="downloads")

# List of available web scrapers
web_scrapers = [
    {"name": "Tavily", "description": "For general web content, images, and raw content."},
    {"name": "Arxiv", "description": "For academic papers and research articles."},
    {"name": "Wikipedia", "description": "For general knowledge and concise information from Wikipedia."}
]

# Format the tools list as a string for the prompt
tools_list = "\n".join([f"{i+1}. {scraper['name']}: {scraper['description']}" for i, scraper in enumerate(web_scrapers)])

# Callable for Tavily
def search_tavily(query):
    """
    Perform a search using Tavily API and return the response.
    """
    try:
        # Ensure the query is well-formed for Tavily
        response = web_search_tool.invoke({"query": query})
        
        # Debug the raw response
        print(f"Raw Tavily API response: {response}")
        
        # Parse the response if valid
        if response and isinstance(response, dict):
            return response
        else:
            print("Tavily API returned an unexpected response format.")
            return None
    
    except Exception as e:
        print(f"Error during Tavily API call: {e}")
        return None
    
# Callable for Arxiv
def search_arxiv(query):
    """
    Perform a search using Arxiv API and return the response.
    """
    print(f"Searching ArXiv for: {query}")
    try:
        response = arxiv_tool.search(query)
        print(f"Arxiv response: {response}")
        return response
    except Exception as e:
        print(f"Error during Arxiv API call: {e}")
        return None

# Callable for Wikipedia
def search_wikipedia(query):
    """
    Perform a search using Wikipedia API and return the response.
    """
    print(f"Searching Wikipedia for: {query}")
    try:
        response = wikipedia.invoke({"query": query})
        print(f"Wikipedia response: {response}")
        return response
    except Exception as e:
        print(f"Error during Wikipedia API call: {e}")
        return None

web_tools = [
    {
        "name": "Tavily",
        "description": "For general web content, images, and raw content.",
        "function": search_tavily
    },
    {
        "name": "Arxiv",
        "description": "For academic papers and research articles.",
        "function": search_arxiv
    },
    {
        "name": "Wikipedia",
        "description": "For general knowledge and concise information from Wikipedia.",
        "function": search_wikipedia
    }
]
llm_with_tools = prompt | llm.bind_tools([tool["function"] for tool in web_tools])

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


import json

def web_search(state):
    """
    Perform web search using selected tools and return the results.
    """
    print("---WEB SEARCH---")
    question = state["question"]
    
    documents = state.get("documents", [])
    
    # Perform Tavily search
    tavily_response = search_tavily(question)
    if tavily_response and 'results' in tavily_response:
        tavily_results = tavily_response.get('results', [])
        combined_results = "\n".join([result.get('content', 'No content available') for result in tavily_results])
        if combined_results:
            web_results_doc = Document(page_content=combined_results)
            documents.append(web_results_doc)
        else:
            print("No relevant content found in Tavily response.")
    
    # Perform Arxiv search
    arxiv_response = search_arxiv(question)
    if arxiv_response:
        arxiv_results = "\n".join([f"Title: {result['title']}\nSummary: {result['summary']}" for result in arxiv_response])
        if arxiv_results:
            arxiv_doc = Document(page_content=arxiv_results)
            documents.append(arxiv_doc)

    # Perform Wikipedia search
    wikipedia_response = search_wikipedia(question)
    if wikipedia_response:
        # Since wikipedia_response is likely a string, use it directly
        wiki_results = wikipedia_response if isinstance(wikipedia_response, str) else wikipedia_response.get('content', 'No content available')
        if wiki_results:
            wiki_doc = Document(page_content=wiki_results)
            documents.append(wiki_doc)
    
    if not documents:
        print("No results found from any search tool.")
        return {"documents": []}
    
    return {"documents": documents}


# -----------Edges------------
import json
import re

def route_question(state):
    """
    Route question to web search or sequence generator.
    """
    print("---ROUTE QUESTION---")
    question = state["question"]
    documents = state["documents"]
    context = " ".join([doc.page_content for doc in documents])

    router_instructions_formatted = router_instructions.format(question=question, context=context)
    
    try:
        # Invoke the LLM to route the question
        route = llm_json_mode.invoke(
            [SystemMessage(content=router_instructions_formatted)]
            + [HumanMessage(content=state["question"])]
        )

        # Extract the JSON part from the response
        json_match = re.search(r'{.*}', route.content, re.DOTALL)
        if json_match:
            json_content = json.loads(json_match.group(0))
        else:
            raise ValueError(f"Invalid JSON received: {route.content}")

        # Check the 'datasource' key in the JSON response
        source = json_content.get("datasource", None)
        if source == "websearch":
            print("---ROUTE QUESTION TO WEB SEARCH---")
            return "websearch"
        elif source == "sequence generator":
            print("---ROUTE QUESTION TO SEQUENCE GENERATOR---")
            return "sequence generator"
        else:
            raise ValueError(f"Invalid datasource in JSON: {route.content}")

    except ValueError as e:
        # Handle invalid or missing JSON issues
        print(f"Error decoding JSON from LLM response: {e}")
        return "error"
    
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return "error"




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
    question = "Give me evolution timeline steps for amphibians"
    response = search_tavily(question)
    print(f"Tavily response for test query: {response}")
    result = ask_question(question)
    print(result)


if __name__ == "__main__":
    main()
