import os
from dotenv import load_dotenv

# Adjusted imports
from pipeline.refiner import get_refined_search_terms
from web_scrapers.search_tool_arxiv import search_arxiv, process_arxiv_results
from web_scrapers.search_tool import search_pubmed, fetch_pubmed_details, process_pubmed_results

def load_dotenv_if_exists():
    """Load environment variables from .env file if it exists."""
    if os.path.exists('.env'):
        load_dotenv()
        print("Environment variables loaded from .env file.")
    else:
        print("No .env file found. Please ensure environment variables are set.")

def main():
    # Load environment variables
    load_dotenv_if_exists()

    print("Hello! Welcome to the Chemical Information Retrieval System")
    print("Type 'exit' to quit the program")

    while True:
        user_question = input("\nEnter your question: ")

        if user_question.lower() == 'exit':
            print("Thank you for using the Chemical Information Retrieval System. Goodbye!")
            break

        # Get refined search terms from the Refiner
        refined_search_terms = get_refined_search_terms(user_question)
        print(f"\nRefined Search Terms:\n{refined_search_terms}")

        # Combine user query and refined terms
        combined_query = f"{user_question} {refined_search_terms}"

        # Directory to save downloaded research papers
        save_folder = 'data/research_papers'
        os.makedirs(save_folder, exist_ok=True)

        # Search ArXiv
        arxiv_results = search_arxiv(combined_query)
        print("\nArXiv Results:")
        if arxiv_results:
            # Process and download ArXiv results
            process_arxiv_results(arxiv_results, save_folder)
        else:
            print("No relevant papers found on ArXiv.")

        # Search PubMed
        pubmed_ids = search_pubmed(combined_query)
        pubmed_details = fetch_pubmed_details(pubmed_ids)
        print("\nPubMed Results:")
        if 'PubmedArticle' in pubmed_details and pubmed_details['PubmedArticle']:
            # Process and save PubMed results
            process_pubmed_results(pubmed_details, save_folder)
        else:
            print("No relevant papers found on PubMed.")

        print("\nDownload process completed.")

if __name__ == "__main__":
    main()
