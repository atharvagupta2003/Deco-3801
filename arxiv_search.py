import fitz  # PyMuPDF
import requests
import os
import arxiv

def search_arxiv(query):
    print(f"Searching ArXiv for: {query}")
    client = arxiv.Client()
    results = client.results(arxiv.Search(
        query=query,
        max_results=1,  # 1 result
        sort_by=arxiv.SortCriterion.Relevance,
    ))

    papers = []
    for result in results:
        papers.append({
            'title': result.title,
            'summary': result.summary,
            'url': result.entry_id,
            'pdf_url': result.pdf_url,
            'published': result.published,
        })
    return papers

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

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def main():
    query = input("Enter your search query: ")

    save_folder = 'data'
    os.makedirs(save_folder, exist_ok=True)

    results = search_arxiv(query)

    if results:
        for i, paper in enumerate(results):
            print(f"{i + 1}) {paper['title']}")
            print(f"   Summary: {paper['summary']}")
            print(f"   Published: {paper['published']}")
            print(f"   URL: {paper['url']}\n")

            # Download the PDF and save it in the data folder
            pdf_file = download_pdf(paper['pdf_url'], paper['title'], save_folder)
            if pdf_file:
                # Extract text
                text = extract_text_from_pdf(pdf_file)
                # Save the text in the data folder
                text_file = pdf_file.replace('.pdf', '.txt')
                text_file_path = os.path.join(save_folder, os.path.basename(text_file))
                with open(text_file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"   Text extracted and saved to: {text_file_path}\n")
    else:
        print("No relevant papers found.")

if __name__ == '__main__':
    main()
