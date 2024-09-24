from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from ingest import preprocess_and_ingest
from retriever import ask_question
from preprocessor import process_document
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            logging.info(f"File {filename} uploaded successfully")

            # Process the document
            processed_data = process_document(file_path)

            # Ingest the processed data
            num_documents = preprocess_and_ingest(processed_data)

            logging.info(f"Ingested {num_documents} documents from {filename}")

            return jsonify(
                {'message': f'File uploaded and ingested successfully. {num_documents} documents processed.'}), 200
        return jsonify({'error': 'File type not allowed'}), 400
    except Exception as e:
        logging.error(f"Error in upload_file: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        logging.info(f"Received question: {question}")

        answer = ask_question(question)
        logging.info(f"Answer generated for question: {question}")
        return jsonify({'answer': answer['result']}), 200
    except Exception as e:
        logging.error(f"Error in ask: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5050)