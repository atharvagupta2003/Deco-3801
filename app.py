from flask import Flask, request, jsonify
from flask_cors import CORS
from ingest import preprocess_and_ingest
from retriever import retrieve_sequence
from preprocessor import process_document
from pubmed_search import search_pubmed, fetch_pubmed_details
from arxiv_search import search_arxiv, download_pdf, extract_text_from_pdf
import os

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

@app.route('/ingest', methods=['POST'])
def ingest():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file:
        filename = file.filename
        file_path = os.path.join('data', 'documents', filename)
        file.save(file_path)
        try:
            preprocessed_data = process_document(file)
            num_documents = preprocess_and_ingest(file_path)
            return jsonify({'status': 'success', 'message': f'Document ingested successfully. {num_documents} chunks created.'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/reconstruct', methods=['POST'])
def reconstruct():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'status': 'error', 'message': 'Query is required'}), 400
    try:
        result = retrieve_sequence(query)
        return jsonify({'status': 'success', 'sequence': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/search_pubmed', methods=['POST'])
def pubmed_search():
    data = request.json
    query = data.get('query')
    max_results = data.get('max_results', 20)
    if not query:
        return jsonify({'status': 'error', 'message': 'Query is required'}), 400
    try:
        id_list = search_pubmed(query, max_results)
        papers = fetch_pubmed_details(id_list)
        results = []
        for paper in papers['PubmedArticle']:
            article = paper['MedlineCitation']['Article']
            results.append({
                'title': article['ArticleTitle'],
                'abstract': article.get('Abstract', {}).get('AbstractText', [''])[0],
                'authors': ', '.join([author['LastName'] + ' ' + author['ForeName'] for author in article.get('AuthorList', [])]),
                'publication_date': paper['MedlineCitation']['DateCompleted']['Year']
            })
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/search_arxiv', methods=['POST'])
def arxiv_search():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'status': 'error', 'message': 'Query is required'}), 400
    try:
        results = search_arxiv(query)
        return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)