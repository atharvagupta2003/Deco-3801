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

from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import Document
from langgraph.graph import END, START
from ingest import get_retriever
import operator
from typing_extensions import TypedDict
from typing import List, Annotated
from langgraph.graph import StateGraph
from IPython.display import Image, display
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

llm = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0)
llm_json_mode = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0, format='json')

seq_generator_instructions = """
You are an expert at reconstructing sequences based on user questions.

Using the provided {context}, answer the user's question in a step-by-step format.

Structure your answer as follows:
Step 1:
Step 2:
Step 3:
...

**Important Instructions:**
- **If timeline reconstruction is involved, present each event in a separate step, sequenced based on the date of the event,
    with the date included and a brief explanation.**
- **Always include the source with your answer.**
- **Ensure that reactions are presented in their particular order, with explanations for each.**
- **Include an explanation for each step and any reactions involved.**

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
    Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
    your output should always be a json with no explanations""",

    input_variables=["generation", "question"],
)

# prompt = PromptTemplate(
#     template="""You are a grader assessing whether an answer is useful to resolve a question and follows the required format.
#
# Here is the answer:
# -------
# {generation}
# -------
# Here is the question: {question}
#
# The answer should always follow this specific format:
# - The answer should be presented in a step-by-step manner:
#   Step 1:
#   Step 2:
#   Step 3:
#   ...
#
# - If timeline reconstruction is involved, each event should be listed in a separate step, sequenced based on the date of the event, with the date included and a brief explanation.
#
# - The answer should always include the source with each step.
#
# - Reactions should be presented in their correct order, with explanations for each.
#
# Assess if the answer follows this format and whether it is useful to resolve the question.
#
# Give a binary score 'yes' or 'no' to indicate whether the answer is both useful and follows the format.
# Provide the binary score as a JSON with a single key 'score' and no preamble or explanation. Your output should always be a JSON with no explanations.""",
#
#     input_variables=["generation", "question"],
# )

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

grader_prompt = PromptTemplate(
    template="""You are a teacher grading a quiz. You will be given: 
1/ a QUESTION
2/ A FACT provided by the student

You are grading RELEVANCE RECALL:
A score of 1 means that ANY of the statements in the FACT are relevant to the QUESTION. 
A score of 0 means that NONE of the statements in the FACT are relevant to the QUESTION. 
1 is the highest (best) score. 0 is the lowest score you can give.

**Important Instructions:**
- **Do not provide any explanations or reasoning in your final answer.**
- **Do not include any preamble or additional text.**
- **Only output the binary score as a JSON with a single key 'score'.**

**Example 1:**

Question:
What is the capital city of France?

Fact:
Paris is known for its art, gastronomy, and culture.

Provide the binary score as a JSON with a single key 'score' and nothing else.

**Example Output:**
{{"score": 1}}

**Example 2:**

Question:
What is the boiling point of water?

Fact:
The Great Wall of China is visible from space.

Provide the binary score as a JSON with a single key 'score' and nothing else.

**Example Output:**
{{"score": 0}}

---

Now, please evaluate the following:

Question:
{question}

Fact:
{documents}

Provide the binary score as a JSON with a single key 'score' and nothing else.
""",
    input_variables=["question", "documents"],
)


retrieval_grader = grader_prompt | llm_json_mode | JsonOutputParser()

web_search_tool = TavilySearchResults(
    max_results=10,
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

## Callable for Tavily
def search_tavily(query):
    """
    Perform a search using Tavily API and return the response.
    """
    try:
        # Ensure the query is well-formed for Tavily
        response = web_search_tool.invoke({"query": query})

        # Debug the raw response
        print(f"Raw Tavily API response: {response}")

        # Check if the response is a list and contains results
        if response and isinstance(response, list) and len(response) > 0:
            # The response is a list of results with 'url', 'content', etc.
            combined_results = "\n".join([result.get('content', 'No content available') for result in response])
            if combined_results:
                return combined_results  # Return the combined content
            else:
                print("No relevant content found in Tavily results.")
                return None
        else:
            print("Tavily API returned an empty list or an unexpected format.")
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
    vector_db_choice = state.get('vector_db_choice', 'Wiki')  # Default to 'Wiki' if not specified
    retriever = get_retriever(vector_db_choice)
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
    print(documents)
    # RAG generation
    if not documents:
        message = state.get("message", "No external sources were useful. Generating the answer based on the LLM's information.")
        seq_generator_prompt = f"{message}\n\n{seq_generator_instructions}".format(context="", question=question)
    else:
        docs_txt = " ".join([doc.page_content for doc in documents])
        seq_generator_prompt = seq_generator_instructions.format(context=docs_txt, question=question)
    
    generation = llm.invoke([HumanMessage(content=seq_generator_prompt)])
    return {"generation": generation}


import json

# Helper function to get user-selected search tool
def get_user_search_tool():
    # Present the options to the user
    print("Select a search tool by entering the corresponding number:")
    print("1. Tavily")
    print("2. Arxiv")
    print("3. Wikipedia")
    print("If the selected tool doesn't return good results, the system will automatically try other tools.")

    # Get user's choice
    choice = input("Enter your choice (1/2/3): ")

    # Map user choice to the tool name
    if choice == "1":
        return "Tavily"
    elif choice == "2":
        return "Arxiv"
    elif choice == "3":
        return "Wikipedia"
    else:
        print("Invalid choice, defaulting to Tavily.")
        return "Tavily"

# Modified web_search function
def web_search(state):
    """
    Perform web search based on the user's selected tool. If no results, generate using LLM's own information.
    """
    print("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents", [])

    # Get user's search tool choice
    selected_tool = get_user_search_tool()

    # Perform search based on selected tool
    if selected_tool == "Tavily":
        tavily_response = search_tavily(question)
        if tavily_response:
            web_results_doc = Document(page_content=tavily_response)
            documents.append(web_results_doc)
            print("Tavily returned results.")
        else:
            print("Tavily failed to return results.")
            return {"documents": [], "message": "Tavily did not yield any useful results."}

    elif selected_tool == "Arxiv":
        arxiv_response = search_arxiv(question)
        if arxiv_response:
            arxiv_results = "\n".join([f"Title: {result['title']}\nSummary: {result['summary']}" for result in arxiv_response])
            arxiv_doc = Document(page_content=arxiv_results)
            documents.append(arxiv_doc)
            print("Arxiv returned results.")
        else:
            print("Arxiv failed to return results.")
            return {"documents": [], "message": "Arxiv did not yield any useful results."}

    elif selected_tool == "Wikipedia":
        wikipedia_response = search_wikipedia(question)
        if wikipedia_response:
            wiki_results = wikipedia_response if isinstance(wikipedia_response, str) else wikipedia_response.get('content', 'No content available')
            wiki_doc = Document(page_content=wiki_results)
            documents.append(wiki_doc)
            print("Wikipedia returned results.")
        else:
            print("Wikipedia failed to return results.")
            return {"documents": [], "message": "Wikipedia did not yield any useful results."}

    # If no documents were found, return an empty list
    if not documents:
        print(f"No results found from {selected_tool}, generating answer using LLM's knowledge.")
        return {"documents": [], "message": f"{selected_tool} did not yield any useful results, providing an answer based on LLM's own information."}
    
    return {"documents": documents, "message": None}



def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    question = state["question"]
    documents = state["documents"]
    filtered_docs = []
    search = "No"
    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "documents": d.page_content}
        )
        grade = score["score"]
        if grade == "yes" or grade == 1 or grade == "1":
            filtered_docs.append(d)
        else:
            search = "Yes"
            continue
    return {
        "documents": filtered_docs,
        "question": question,
        "search": search,
    }

# -----------Edges------------

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

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """
    search = state["search"]
    if search == "Yes":
        print("---Web search---")
        return "search"
    else:
        print("---generate---")
        return "generate"

# Create a placeholder for the workflow and graph
workflow = None
graph = None

def create_all_vectorstores():
    print("Creating Wiki vectorstore...")
    get_retriever("Wiki")
    print("Creating ArXiv vectorstore...")
    get_retriever("ArXiv")

    print("All vectorstores created.")
# Function to setup the workflow
def setup_workflow():
    global workflow
    global graph

    if workflow is None or graph is None:  # Only set up if not already initialized
        workflow = StateGraph(GraphState)

        # Adding the new nodes
        workflow.add_node("websearch", web_search)
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("generate", generate)
        workflow.add_node("grade_documents", grade_documents)

        # Adding the edges as per the new workflow
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            decide_to_generate,
            {
                "search": "websearch",
                "generate": "generate",
            },
        )
        workflow.add_edge("websearch", "generate")
        workflow.add_conditional_edges(
            "generate",
            grade_generation,
            {"useful": END, "not useful": "retrieve"},
        )
        workflow.add_edge("generate", END)

        # Adding memory and compiling the workflow
        memory = MemorySaver()
        graph = workflow.compile(checkpointer=memory)

    return workflow, graph


# Run this block only when graph.py is executed directly (not imported)
if __name__ == "__main__":
    create_all_vectorstores()
    workflow, graph = setup_workflow()  # Setup only when running directly
    user_question = input("Please enter your question (or press Enter to use the default): ")
    question_to_ask = user_question if user_question else "steps for synthesis of carbon monoxide?"
    vector_db_choice = input("Please enter the vector database (Wiki/ArXiv/Custom): ")
    vector_db_choice = vector_db_choice if vector_db_choice else "Wiki"

    inputs = {"question": question_to_ask, "vector_db_choice": vector_db_choice}

    # Updated configuration with additional keys
    config = {
        "configurable": {
            "thread_id": "1",
            "checkpoint_ns": "default_ns",
            "checkpoint_id": "checkpoint_1"
        }
    }

    # Streaming the events as per the new workflow
    for event in graph.stream(inputs, stream_mode="values", config=config):
        print(event)

else:
    create_all_vectorstores()
    # When imported, the workflow will only be setup when explicitly called, not during import.
    setup_workflow()  # Make sure the graph is set up if needed# Make sure the graph is set up if needed