# src/agent/graph.py

import os
from dotenv import load_dotenv
import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_chroma import Chroma  # Updated import from langchain_chroma
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from web_scrapers.search_tool_arxiv import ArxivSearchTool
from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import Document
from langgraph.graph import END, START
from src.agent.ingest import get_retriever
from typing_extensions import TypedDict
from typing import List, Any
from langgraph.graph import StateGraph
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Initialize LLMs
llm = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0)
llm_json_mode = ChatNVIDIA(model='meta/llama-3.1-405b-instruct', temperature=0, format='json')

# from langchain_ollama import ChatOllama -- For Debugging Only
# llm = ChatOllama(model='llama3.1', temperature=0)
# llm_json_mode = ChatOllama(model='llama3.1', temperature=0, format='json')

# Define prompt templates
seq_generator_instructions = """
You are an expert at reconstructing sequences based on user questions.

Using the provided {context}, answer the user's question in a step-by-step format.

If the sequence is a timeline or a chemical sequence, start your answer with:
- "The following is a timeline sequence" or
- "The following is a chemical sequence"
If the sequence is neither of these, do not include this line.

Structure your answer as follows:
Step 1: Heading
Explanation
Step 2: Heading
Explanation
Step 3: Heading
Explanation
...

*Important Instructions:*
- *If timeline reconstruction is involved, present each event in a separate step, sequenced based on the date of the event, with the date included and a brief explanation.*
  - For timelines, use the format: Step 1: Date - Event
- *Always include the source with your answer.*
- *Ensure that reactions are presented in their particular order, with explanations for each.*
- *Include an explanation for each step and any reactions involved.*

Question: {question}
Answer:"""

grader_prompt_template = """
You are a grader assessing whether an answer is useful to resolve a question.

Here is the answer:
-------
{generation}
-------
Here is the question: {question}
Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question.

Provide the binary score as a JSON with a single key 'score' and no preamble or explanation.
Your output should always be a JSON with no explanations.
"""

prompt = PromptTemplate(
    template=grader_prompt_template,
    input_variables=["generation", "question"],
)

answer_grader = prompt | llm_json_mode | JsonOutputParser()

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

# Initialize web search tools
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

# Define callable functions for web searches
def search_tavily(query):
    """
    Perform a search using Tavily API and return the response.
    """
    try:
        # Ensure the query is well-formed for Tavily
        response = web_search_tool.invoke({"query": query})

        # Debug the raw response
        logging.info(f"Raw Tavily API response: {response}")

        # Check if the response is a list and contains results
        if response and isinstance(response, list) and len(response) > 0:
            # The response is a list of results with 'url', 'content', etc.
            combined_results = "\n".join([result.get('content', 'No content available') for result in response])
            if combined_results:
                return combined_results  # Return the combined content
            else:
                logging.info("No relevant content found in Tavily results.")
                return None
        else:
            logging.info("Tavily API returned an empty list or an unexpected format.")
            return None

    except Exception as e:
        logging.error(f"Error during Tavily API call: {e}")
        return None

def search_arxiv(query):
    """
    Perform a search using Arxiv API and return the response.
    """
    logging.info(f"Searching ArXiv for: {query}")
    try:
        response = arxiv_tool.search(query)
        logging.info(f"Arxiv response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error during Arxiv API call: {e}")
        return None

def search_wikipedia(query):
    """
    Perform a search using Wikipedia API and return the response.
    """
    logging.info(f"Searching Wikipedia for: {query}")
    try:
        response = wikipedia.invoke({"query": query})
        logging.info(f"Wikipedia response: {response}")
        return response
    except Exception as e:
        logging.error(f"Error during Wikipedia API call: {e}")
        return None

class GraphState(TypedDict):
    """
    Graph state is a dictionary that contains information we want to propagate to, and modify in, each graph node.
    """
    question: str
    generation: Any
    web_search: str
    documents: List[Any]
    need_user_input: bool
    options: List[str]
    selected_tool: str
    message: str
    search: str
    vector_db_choice: str
    error: str

# Initialize global variables
workflow = None
graph = None

# -----------Nodes------------
def retrieve(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        dict: New key added to state, documents, that contains retrieved documents
    """
    logging.info("---RETRIEVE---")
    question = state["question"]
    vector_db_choice = state.get('vector_db_choice', 'Wiki')  # Default to 'Wiki' if not specified
    try:
        retriever = get_retriever(vector_db_choice)
        documents = retriever.invoke(question)
        logging.info(f"Documents retrieved: {len(documents)}")
        return {"documents": documents}
    except Exception as e:
        logging.error(f"Error in retrieve node: {str(e)}")
        state['error'] = f"Error in retrieve node: {str(e)}"
        return state

def generate(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        dict: New key added to state, generation, that contains LLM generation
    """
    logging.info("---GENERATE---")
    question = state["question"]
    documents = state.get("documents", [])
    logging.info(f"Documents: {documents}")
    # RAG generation
    try:
        if not documents:
            message = state.get("message", "No external sources were useful. Generating the answer based on the LLM's information.")
            seq_generator_prompt = seq_generator_instructions.format(context="", question=question)
        else:
            docs_txt = " ".join([doc.page_content for doc in documents])
            seq_generator_prompt = seq_generator_instructions.format(context=docs_txt, question=question)

        generation = llm.invoke([HumanMessage(content=seq_generator_prompt)])
        logging.info(f"Generation type: {type(generation)}")
        logging.info(f"Generation content: {generation}")

        # Handle different possible return types from llm.invoke()
        if hasattr(generation, 'content'):
            generated_text = generation.content
        elif isinstance(generation, str):
            generated_text = generation
        else:
            raise ValueError("LLM returned content in an unexpected format.")

        if not generated_text:
            raise ValueError("LLM returned empty content.")

        logging.info(f"Generation: {generated_text}")
        return {"generation": generated_text}
    except Exception as e:
        logging.error(f"Error during generation: {str(e)}")
        state['error'] = f"Error during generation: {str(e)}"
        return state  # Return the state with the error included

def web_search(state):
    """
    Perform web search based on the user's selected tool. If no results, generate using LLM's own information.
    """
    logging.info("---WEB SEARCH---")
    question = state["question"]
    documents = state.get("documents", [])

    # Check if 'selected_tool' is in state
    if 'selected_tool' not in state or not state['selected_tool']:
        # Indicate that user input is needed
        state['need_user_input'] = True
        state['options'] = ['Tavily', 'Arxiv', 'Wikipedia']
        return state

    selected_tool = state['selected_tool']
    logging.info(f"Selected tool: {selected_tool}")

    # Reset 'need_user_input' flag
    state['need_user_input'] = False  # Ensure it's reset

    # Perform search based on selected tool
    if selected_tool == "Tavily":
        tavily_response = search_tavily(question)
        if tavily_response:
            web_results_doc = Document(page_content=tavily_response)
            documents.append(web_results_doc)
            logging.info("Tavily returned results.")
        else:
            logging.info("Tavily failed to return results.")
            state['documents'] = []
            state['message'] = "Tavily did not yield any useful results."

    elif selected_tool == "Arxiv":
        arxiv_response = search_arxiv(question)
        if arxiv_response:
            arxiv_results = "\n".join([f"Title: {result['title']}\nSummary: {result['summary']}" for result in arxiv_response])
            arxiv_doc = Document(page_content=arxiv_results)
            documents.append(arxiv_doc)
            logging.info("Arxiv returned results.")
        else:
            logging.info("Arxiv failed to return results.")
            state['documents'] = []
            state['message'] = "Arxiv did not yield any useful results."

    elif selected_tool == "Wikipedia":
        wikipedia_response = search_wikipedia(question)
        if wikipedia_response:
            wiki_results = wikipedia_response if isinstance(wikipedia_response, str) else wikipedia_response.get('content', 'No content available')
            wiki_doc = Document(page_content=wiki_results)
            documents.append(wiki_doc)
            logging.info("Wikipedia returned results.")
        else:
            logging.info("Wikipedia failed to return results.")
            state['documents'] = []
            state['message'] = "Wikipedia did not yield any useful results."

    else:
        logging.error(f"Invalid selected tool: {selected_tool}")
        state['error'] = f"Invalid selected tool: {selected_tool}"

    # Update the state with new documents
    state['documents'] = documents
    return state

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        dict: Updates documents key with only filtered relevant documents
    """
    logging.info("---GRADE DOCUMENTS---")
    question = state["question"]
    documents = state.get("documents", [])
    filtered_docs = []
    search = "No"

    if not documents:
        # No documents retrieved, need to search
        search = "Yes"
    else:
        for d in documents:
            try:
                score = retrieval_grader.invoke(
                    {"question": question, "documents": d.page_content}
                )
                grade = score.get("score", 0)
                if grade in ["yes", 1, "1"]:
                    filtered_docs.append(d)
                else:
                    continue
            except Exception as e:
                logging.error(f"Error during document grading: {str(e)}")
                continue
        if not filtered_docs:
            search = "Yes"

    state.update({
        "documents": filtered_docs,
        "search": search,
    })
    return state

# -----------Edges------------

def grade_generation(state):
    """
    Determines whether the generation answers the question or not.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    logging.info("---GRADE GENERATION vs QUESTION---")
    question = state["question"]
    generation = state.get("generation", "")
    try:
        score = answer_grader.invoke({'question': question, 'generation': generation})
        grade = score.get("score", 0)
        if grade == "yes":
            logging.info("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            logging.info("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            return "not useful"
    except Exception as e:
        logging.error(f"Error during generation grading: {str(e)}")
        state['error'] = f"Error during generation grading: {str(e)}"
        return "not useful"

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-perform web search.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    search = state.get("search", "No")
    if search == "Yes":
        logging.info("---DECISION: PERFORM WEB SEARCH---")
        return "websearch"
    else:
        logging.info("---DECISION: GENERATE ANSWER---")
        return "generate"

def create_all_vectorstores():
    logging.info("Initializing vectorstores...")
    get_retriever("Wiki")
    get_retriever("ArXiv")
    get_retriever("Custom")  # Ensure Custom is also initialized
    logging.info("All vectorstores initialized.")

# Function to setup the workflow
def setup_workflow():
    global workflow
    global graph

    if workflow is None or graph is None:  # Only set up if not already initialized
        workflow = StateGraph(GraphState)

        # Adding the nodes
        workflow.add_node("retrieve", retrieve)
        workflow.add_node("grade_documents", grade_documents)
        workflow.add_node("websearch", web_search)
        workflow.add_node("generate", generate)
        workflow.add_node("grade_generation", grade_generation)

        # Adding the edges
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "grade_documents")

        # Conditional edges based on grading documents
        workflow.add_conditional_edges(
            "grade_documents",
            decide_to_generate,
            {
                "websearch": "websearch",
                "generate": "generate",
            },
        )

        # Edge from websearch to generate
        workflow.add_edge("websearch", "generate")

        # Edge from generate to grade_generation
        workflow.add_edge("generate", "grade_generation")

        # Conditional edges based on grading generation
        workflow.add_conditional_edges(
            "grade_generation",
            lambda state: "END" if state.get("grade") == "useful" else "retrieve",
            {
                "useful": END,
                "not useful": "retrieve",
            },
        )

        # Compiling the workflow without a checkpointer
        graph = workflow.compile()

    return workflow, graph

# Initialize vector stores and setup workflow when module is imported
create_all_vectorstores()
setup_workflow()
logging.info("Graph module initialized successfully.")
