from flask import Flask, request, jsonify
import os
import logging
from flask_cors import CORS
from werkzeug.utils import secure_filename
import ingest  # Assuming you have a method in ingest to create custom vectorstore
from graph import setup_workflow
from graph import workflow, graph, get_retriever

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
custom_vectorstore = None
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the uploaded file is in allowed extensions."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload documents and use them to create a custom vector database.
    """
    global custom_vectorstore

    logging.info("Received upload request")

    if 'file' not in request.files:
        logging.error("No file part in the request")
        return jsonify({'error': 'No file part in the request'}), 400

    files = request.files.getlist('file')  # Get multiple files if any

    if not files or files[0].filename == '':
        logging.error("No selected file")
        return jsonify({'error': 'No selected file'}), 400

    uploaded_docs = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            logging.info(f"File uploaded: {filename}")

            # Read file contents (for simplicity, only handling text-based files here)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_content = f.read()
                    uploaded_docs.append({
                        "title": filename,
                        "text": file_content
                    })
            except Exception as e:
                logging.error(f"Error reading file {filename}: {str(e)}")
                return jsonify({'error': f"Error reading file {filename}: {str(e)}"}), 500
        else:
            logging.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': f'Invalid file type: {file.filename}'}), 400

    if not uploaded_docs:
        logging.error("No valid documents were uploaded")
        return jsonify({'error': 'No valid documents were uploaded'}), 400

    # Create custom vector database with the uploaded documents
    try:
        ingest.create_custom_vectorstore(uploaded_docs)
        logging.info("Custom vector database created successfully.")
    except Exception as e:
        logging.error(f"Error creating vector database: {str(e)}")
        return jsonify({'error': f"Failed to create vector database: {str(e)}"}), 500
    return jsonify({'status': 'Files uploaded and custom vector database created'}), 200

def run_graph_workflow(question: str, vector_db_choice: str):
    """
    This function runs the graph workflow with the given question and returns the generated AI answer.
    """
    if graph is None:
        logging.error("Graph is not initialized.")
        return "Error: Graph not initialized."

    inputs = {
        "question": question,
        "vector_db_choice": vector_db_choice  # Pass the selected vector DB
    }

    config = {
        "configurable": {
            "thread_id": "1",  # Example thread_id, adjust as needed
            "checkpoint_ns": "default_ns",
            "checkpoint_id": "checkpoint_1"
        }
    }

    output = None
    try:
        # Run the graph to process the question with the selected vector DB
        for event in graph.stream(inputs, stream_mode="values", config=config):
            output = event  # Capture the output
            if 'generation' in output:
                generation = output['generation']
                return generation.content  # Return the actual content generated by the AI
            else:
                logging.warning(f"Unexpected event structure: {output}")

        if not output:
            logging.error("No output received from the graph.")
            return "Error: No output received from the AI."

    except Exception as e:
        logging.error(f"Error during graph processing: {str(e)}")
        return f"Error during AI processing: {str(e)}"

    logging.error("No 'generation' found in the graph output.")
    return "Error: No generation found in the AI response."

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        vector_db_choice = data.get('vector_db_choice', 'Wiki')  # Get the vector_db_choice from request
        logging.info(f"Received question: {question}")
        logging.info(f"Selected vector database: {vector_db_choice}")

        # Use the helper function to run the graph workflow and get the AI-generated answer
        answer = run_graph_workflow(question, vector_db_choice)  # Pass vector_db_choice here

        if answer:
            logging.info(f"Answer generated for question: {question}")
            return jsonify({'answer': answer}), 200
        else:
            return jsonify({'error': 'No answer generated by the AI.'}), 500
    except Exception as e:
        logging.error(f"Error in ask: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5050)