import streamlit as st
import requests
import os
import json

# Set Streamlit page configuration
st.set_page_config(
    page_title="Sequence Reconstruction ",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to set NVIDIA-style green and black theme with improved aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #76b900;
        border-color: #76b900;
        border-radius: 5px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #5a8f00;
        border-color: #5a8f00;
    }
    .stTextInput>div>div>input {
        color: #ffffff;
        background-color: #2a2a2a;
        border-radius: 5px;
        border: 1px solid #3a3a3a;
    }
    .stTextArea>div>div>textarea {
        color: #ffffff;
        background-color: #2a2a2a;
        border-radius: 5px;
        border: 1px solid #3a3a3a;
    }
    .stHeader {
        background-color: #76b900;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .file-uploader {
        border: 2px dashed #76b900;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }
    .answer-box {
        background-color: #2a2a2a;
        border-radius: 10px;
        padding: 20px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Create temp directory if it doesn't exist
temp_dir = "temp"
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# Function to check server health
def check_server_health():
    try:
        response = requests.get('http://localhost:5050/health')
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Title
st.markdown("<div class='stHeader'><h1>📚 NVIDIA Sequence Reconstruction </h1></div>", unsafe_allow_html=True)

# Check server health
if not check_server_health():
    st.error("Error: Unable to connect to the server. Please ensure the Flask backend is running.")
    st.stop()

# File uploader
st.markdown("<div class='file-uploader'>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'csv'])
st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file is not None:
    # Display file details
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    # Save the file temporarily
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Send the file to the Flask backend
    try:
        files = {'file': open(temp_file_path, 'rb')}
        with st.spinner("Processing file..."):
            response = requests.post('http://localhost:5050/upload', files=files)

        if response.status_code == 200:
            st.success("File uploaded and processed successfully!")
        else:
            error_message = response.json().get('error', 'Unknown error') if response.content else 'No response from server'
            st.error(f"Error uploading file. Status code: {response.status_code}. Message: {error_message}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the server: {str(e)}")
    finally:
        # Remove the temporary file
        os.remove(temp_file_path)

# Question input
question = st.text_input("Ask a question about the uploaded document:")

if st.button("Get Answer"):
    if question:
        try:
            # Send the question to the Flask backend
            with st.spinner("Generating answer..."):
                response = requests.post('http://localhost:5050/ask', json={'question': question})

            if response.status_code == 200:
                answer = response.json()['answer']
                st.markdown("<div class='answer-box'>", unsafe_allow_html=True)
                st.write("Answer:", answer)
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                error_message = response.json().get('error', 'Unknown error') if response.content else 'No response from server'
                st.error(f"Error getting answer. Status code: {response.status_code}. Message: {error_message}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the server: {str(e)}")
    else:
        st.warning("Please enter a question.")

# Display information about the system
st.sidebar.title("About")
st.sidebar.info("This is a document Q&A system that uses NVIDIA AI for embeddings and retrieval.")
st.sidebar.info("Upload a document and ask questions to get AI-powered answers!")
st.sidebar.markdown("---")
st.sidebar.markdown("Made  by Noisy Indian Varun Singh ")