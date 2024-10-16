# app.py

from flask import Flask, request, jsonify
import os
import logging
from flask_cors import CORS
from werkzeug.utils import secure_filename
from src.agent.ingest import create_custom_vectorstore
from src.agent.graph import setup_workflow, workflow, graph

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# In-memory storage for graph states
graph_states = {}

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

            # Read file contents
            try:
                if filename.lower().endswith('.pdf'):
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(file_path)
                    pdf_pages = loader.load_and_split()
                    for page in pdf_pages:
                        uploaded_docs.append({
                            "title": filename,
                            "text": page.page_content
                        })
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                        uploaded_docs.append({
                            "title": filename,
                            "text": file_content
                        })
                logging.info(f"Processed file: {filename}")
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
        create_custom_vectorstore(uploaded_docs)
        logging.info("Custom vector database created successfully.")
    except Exception as e:
        logging.error(f"Error creating vector database: {str(e)}")
        return jsonify({'error': f"Failed to create vector database: {str(e)}"}), 500
    return jsonify({'status': 'Files uploaded and custom vector database created'}), 200

def run_graph_workflow(question: str, vector_db_choice: str, session_id: str, user_choice: str = None):
    """
    Runs the graph workflow with the given question and returns the generated AI answer.
    """
    if graph is None:
        logging.error("Graph is not initialized.")
        return {'error': "Error: Graph not initialized."}

    # Retrieve or initialize the state for this session
    state = graph_states.get(session_id, {'question': question, 'vector_db_choice': vector_db_choice})

    # If user_choice is provided, include it in the state
    if user_choice:
        state['selected_tool'] = user_choice
        # Also, reset 'need_user_input' in case it was set previously
        state['need_user_input'] = False

    output = {}
    try:
        # Run the graph with the current state using stream
        events = graph.stream(state, stream_mode="values")
        for event in events:
            state.update(event)
            output.update(event)
            logging.info(f"Graph event: {event}")

            if 'error' in state:
                logging.error(f"Error in graph execution: {state['error']}")
                return {'error': state['error']}

            if state.get('need_user_input'):
                logging.info("Need user input. Options provided.")
                # Save the state before returning
                graph_states[session_id] = state
                return {'need_user_input': True, 'options': state['options'], 'session_id': session_id}

            if 'generation' in output:
                generation = output['generation']
                # Clean up the state after completion
                if session_id in graph_states:
                    del graph_states[session_id]
                logging.info("Generation completed successfully.")
                return {'answer': generation.content}

        if not output:
            logging.error("No output received from the graph.")
            return {'error': "Error: No output received from the AI."}

    except Exception as e:
        logging.error(f"Error during graph processing: {str(e)}")
        return {'error': f"Error during AI processing: {str(e)}"}

    logging.error("No 'generation' found in the graph output.")
    return {'error': "Error: No generation found in the AI response."}

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        vector_db_choice = data.get('vector_db_choice', 'Wiki')
        user_choice = data.get('user_choice', None)
        session_id = data.get('session_id', 'default')

        logging.info(f"Received question: {question}")
        logging.info(f"Selected vector database: {vector_db_choice}")
        logging.info(f"User choice: {user_choice}")
        logging.info(f"Session ID: {session_id}")

        # Use the helper function to run the graph workflow and get the AI-generated answer
        response_data = run_graph_workflow(question, vector_db_choice, session_id, user_choice)

        if 'answer' in response_data:
            return jsonify({'answer': response_data['answer']}), 200
        elif 'need_user_input' in response_data and response_data['need_user_input']:
            return jsonify({'need_user_input': True, 'options': response_data['options'], 'session_id': response_data['session_id']}), 200
        else:
            error = response_data.get('error', 'No answer generated by the AI.')
            return jsonify({'error': error}), 500

    except Exception as e:
        logging.error(f"Error in ask: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    setup_workflow()  # Ensure the graph is set up
    app.run(debug=True, host='0.0.0.0', port=5050)
