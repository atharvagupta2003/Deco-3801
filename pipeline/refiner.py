from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import HuggingFaceHub
import os

# Initialize Hugging Face LLM
llm = HuggingFaceHub(
    repo_id="google/flan-t5-large",
    model_kwargs={"temperature": 0.1, "max_length": 512},
    huggingfacehub_api_token=os.environ.get("HUGGINGFACEHUB_API_TOKEN")
)

# Define the prompt template
refinement_template = """
Given the user's question:

"{question}"

Generate a list of the most relevant and specific keywords or phrases that can be used to search for academic papers related to this question.

Keywords:
"""

refinement_prompt = PromptTemplate(
    template=refinement_template,
    input_variables=["question"]
)

# Create the LLMChain
refinement_chain = LLMChain(
    llm=llm,
    prompt=refinement_prompt
)

def get_refined_search_terms(question):
    refined_terms = refinement_chain.run(question)
    return refined_terms.strip()
