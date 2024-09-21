import arxiv
import fitz  # PyMuPDF
import requests
import os

# Function to search ArXiv
def search_arxiv(query, max_results=5):
    print(f"Searching ArXiv for: {query}")
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    results = []
    for result in search.results():
        results.append({
            'title': result.title,
            'summary': result.summary,
            'url': result.entry_id,
            'pdf_url': result.pdf_url,
            'published': result.published,
        })
    return results

# Function to download PDF
def download_pdf(pdf_url, title, save_folder):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        file_name = f"{title}.pdf".replace('/', '-')
        file_path = os.path.join(save_folder, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    else:
        print(f"Failed to download {title}.")
        return None

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

# If you want to test this module independently
def main():
    query = input("Enter your search query: ")
    results = search_arxiv(query)

    if results:
        for i, paper in enumerate(results):
            print(f"{i + 1}) {paper['title']}")
            print(f"   Summary: {paper['summary']}")
            print(f"   Published: {paper['published']}")
            print(f"   URL: {paper['url']}\n")

            # Optional: Download and extract text
            # Uncomment the following lines if you wish to download PDFs
            """
            save_folder = 'data_arxiv'
            os.makedirs(save_folder, exist_ok=True)
            pdf_file = download_pdf(paper['pdf_url'], paper['title'], save_folder)
            if pdf_file:
                text = extract_text_from_pdf(pdf_file)
                text_file = pdf_file.replace('.pdf', '.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"   Text extracted and saved to: {text_file}\n")
            """
    else:
        print("Papers not found.")

if __name__ == '__main__':
    main()
