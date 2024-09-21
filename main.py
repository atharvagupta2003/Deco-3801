# main.py

import os
from dotenv import load_dotenv

# Adjusted imports
from pipeline.retriever import qa_chain
from pipeline.refiner import get_refined_search_terms
from web_scrapers.search_tool_arxiv import search_arxiv
from web_scrapers.search_tool import search_pubmed, fetch_pubmed_details

load_dotenv()

def ask_question(question):
    response = qa_chain.run(question)
    return response

if __name__ == "__main__":
    print("Hello! Welcome to the Chemical Information Retrieval System")
    print("Type 'exit' to quit the program")

    while True:
        user_question = input("\nEnter your question: ")

        if user_question.lower() == 'exit':
            print("Thank you for using the Chemical Information Retrieval System. Goodbye!")
            break

        # Get refined search terms from the LLM
        refined_search_terms = get_refined_search_terms(user_question)
        print(f"\nRefined Search Terms:\n{refined_search_terms}")

        # Combine user query and refined terms
        combined_query = f"{user_question} {refined_search_terms}"

        # Search ArXiv
        arxiv_results = search_arxiv(combined_query)
        print("\nArXiv Results:")
        if arxiv_results:
            for i, paper in enumerate(arxiv_results):
                print(f"{i + 1}) {paper['title']}")
                print(f"   Summary: {paper['summary']}")
                print(f"   URL: {paper['url']}\n")
        else:
            print("No relevant papers found on ArXiv.")

        # Search PubMed
        pubmed_ids = search_pubmed(combined_query)
        pubmed_details = fetch_pubmed_details(pubmed_ids)
        print("\nPubMed Results:")
        if 'PubmedArticle' in pubmed_details and pubmed_details['PubmedArticle']:
            for i, paper in enumerate(pubmed_details['PubmedArticle']):
                title = paper['MedlineCitation']['Article']['ArticleTitle']
                print(f"{i + 1}) {title}")
        else:
            print("No relevant papers found on PubMed.")
