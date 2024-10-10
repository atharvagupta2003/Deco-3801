import os
from dotenv import load_dotenv
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import Document
from langgraph.graph import END, START
from ingest import retriever
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

prompt = PromptTemplate(
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


retrieval_grader = prompt | llm_json_mode | JsonOutputParser()

web_search_tool = TavilySearchResults(
    max_results=10,
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
    print(documents)
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


workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("websearch", web_search)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.add_node("grade_documents", grade_documents)

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
    {"useful": END,
        "not useful": "retrieve"},
)
workflow.add_edge("generate", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
display(Image(graph.get_graph().draw_mermaid_png()))
config = {"configurable": {"thread_id": "1"}}
# inputs = {"question": "major wars involved in world war 1"}
# for event in graph.stream(inputs, stream_mode="values", config=config):
#     print(event)