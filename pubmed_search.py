from Bio import Entrez
import json

# Function to search PubMed
def search_pubmed(query, max_results=20):
    Entrez.email = 'atharvagupta2003@gmail.com'
    handle = Entrez.esearch(db='pubmed',
                            sort='relevance',
                            retmax=max_results,
                            retmode='xml',
                            term=query)
    results = Entrez.read(handle)
    return results['IdList']

# Function to fetch details of articles
def fetch_pubmed_details(id_list):
    ids = ','.join(id_list)
    Entrez.email = 'atharvagupta2003@gmail.com'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    return results

# Main function to execute search and retrieve articles
def main():
    query = input("Enter your search query: ")
    print("Searching PubMed for: ", query)

    # Search PubMed
    id_list = search_pubmed(query)
    if not id_list:
        print("No results found for your query.")
        return

    # Fetch details for the results
    papers = fetch_pubmed_details(id_list)

    # Print out the titles of the papers found
    print("\nRelevant papers found:")
    for i, paper in enumerate(papers['PubmedArticle']):
        title = paper['MedlineCitation']['Article']['ArticleTitle']
        print(f"{i + 1}) {title}")

    # Print detailed structure of the first paper
    if papers['PubmedArticle']:
        print("\nStructure of the first paper (JSON):")
        print(json.dumps(papers['PubmedArticle'][0], indent=2))

if __name__ == "__main__":
    main()
