# web_scrapers/search_tool.py

from Bio import Entrez
import os

# Function to search PubMed
def search_pubmed(query, max_results=5):
    Entrez.email = 'your_email@example.com'  # Replace with your email
    handle = Entrez.esearch(db='pubmed',
                            sort='relevance',
                            retmax=max_results,
                            retmode='xml',
                            term=query)
    results = Entrez.read(handle)
    handle.close()
    return results['IdList']

# Function to fetch details of articles
def fetch_pubmed_details(id_list):
    if not id_list:
        return []
    ids = ','.join(id_list)
    Entrez.email = 'your_email@example.com'  # Replace with your email
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    handle.close()
    return results

# Function to sanitize file names
def sanitize_filename(filename):
    # Replace or remove characters that are invalid in file names
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '-')
    return filename

# Function to save abstract to a text file
def save_abstract(title, abstract, save_folder):
    if not abstract:
        print(f"No abstract available for: {title}")
        return
    # Sanitize title for file name
    file_name = f"{sanitize_filename(title)}.txt"
    file_path = os.path.join(save_folder, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"Title: {title}\n\nAbstract:\n{abstract}")
    print(f"Abstract saved to: {file_path}")

# Function to process PubMed search results
def process_pubmed_results(papers, save_folder):
    print("\nRelevant papers found and abstracts saved:")
    for i, paper in enumerate(papers['PubmedArticle']):
        title = paper['MedlineCitation']['Article']['ArticleTitle']
        abstract = ''
        try:
            abstract = paper['MedlineCitation']['Article']['Abstract']['AbstractText'][0]
        except KeyError:
            abstract = ''

        print(f"{i + 1}) {title}")
        save_abstract(title, abstract, save_folder)
