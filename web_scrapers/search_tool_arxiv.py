import arxiv
import fitz  # PyMuPDF
import requests
import os

class ArxivSearchTool:
    def __init__(self, max_results=5, save_folder="downloads"):
        self.max_results = max_results
        self.save_folder = save_folder
        os.makedirs(save_folder, exist_ok=True)

    # Function to search ArXiv
    def search(self, query):
        print(f"Searching ArXiv for: {query}")
        search = arxiv.Search(
            query=query,
            max_results=self.max_results,
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
    def download_pdf(self, pdf_url, title):
        response = requests.get(pdf_url)
        if response.status_code == 200:
            file_name = f"{self.sanitize_filename(title)}.pdf"
            file_path = os.path.join(self.save_folder, file_name)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded PDF: {file_path}")
            return file_path
        else:
            print(f"Failed to download {title}. Status Code: {response.status_code}")
            return None

    # Function to sanitize file names
    @staticmethod
    def sanitize_filename(filename):
        # Replace or remove characters that are invalid in file names
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '-')
        return filename

    # Function to extract text from PDF
    @staticmethod
    def extract_text_from_pdf(file_path):
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    # Function to save extracted text
    @staticmethod
    def save_text(text, file_path):
        text_file = file_path.replace('.pdf', '.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Extracted text saved to: {text_file}")

    # Function to process ArXiv search results
    def process_results(self, results):
        for i, paper in enumerate(results):
            print(f"{i + 1}) {paper['title']}")
            print(f"   Summary: {paper['summary']}")
            print(f"   Published: {paper['published']}")
            print(f"   URL: {paper['url']}\n")

            # Download PDF
            pdf_file = self.download_pdf(paper['pdf_url'], paper['title'])
            if pdf_file:
                # Extract text from PDF
                text = self.extract_text_from_pdf(pdf_file)
                # Save extracted text
                self.save_text(text, pdf_file)
