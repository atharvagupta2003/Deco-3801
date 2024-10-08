from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from pipeline.old_ingest import ingest_documents
from src.agent.graph import ask_question
import logging
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200


@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No file part'}), 400

        files = request.files.getlist('files[]')

        if not files or files[0].filename == '':
            return jsonify({'error': 'No selected files'}), 400

        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_upload')
        os.makedirs(upload_folder, exist_ok=True)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
            else:
                return jsonify({'error': f'File type not allowed: {file.filename}'}), 400

        logging.info(f"Files uploaded successfully to {upload_folder}")

        # Ingest the documents
        ingest_documents(upload_folder)

        # Clean up the temporary upload folder
        for filename in os.listdir(upload_folder):
            os.remove(os.path.join(upload_folder, filename))
        os.rmdir(upload_folder)

        return jsonify({'message': 'Files uploaded and ingested successfully.'}), 200
    except Exception as e:
        logging.error(f"Error in upload_files: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        logging.info(f"Received question: {question}")

        answer_list = ask_question(question)
        answer = answer_list[2]['generation'].pretty_repr()
        logging.info(f"Answer generated for question: {question}")
        return jsonify({'answer': answer}), 200
    except Exception as e:
        logging.error(f"Error in ask: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5050)