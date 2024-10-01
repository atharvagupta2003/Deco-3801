import streamlit as st
import requests
import os
import json

def reconstruct_sequence(query, files):
    # Placeholder function for sequence reconstruction
    sequence = "ATCG" * 10  # Example sequence
    return sequence

def main():
    st.set_page_config(
        page_title="Sequence Reconstruction",
        page_icon="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
    <style>
    body {
        background-color: #1A1A1A; 
        color: #FFFFFF;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 20px;
        background-color: #1A1A1A;
    }
    .stApp {
        background-color: #000000;
        color: #ffffff;
        font-family: "NVIDIA", Arial, Helvetica, sans-serif;
    }
    .logo-nav-container {
        display: flex;
        align-items: center;
    }
    .nvidia-logo {
        height: 30px;
        margin-right: 20px;
    }
    .nav-links {
        display: flex;
    }
    .nav-links a {
        color: #FFFFFF;
        text-decoration: none;
        margin-left: 20px;
        font-weight: bold;
        transition: color 0.3s ease;
    }
    .nav-links a:hover {
        color: #76B900;
    }
    .green-line {
        border: none;
        height: 2px;
        background-color: #76B900;
        margin: 0;
    }
    .content {
        padding: 20px;
    }
    /* Compact file uploader styles */
    .stFileUploader {
        width: 100%;
    }
    .stFileUploader > div {
        padding: 0 !important;
    }
    .stFileUploader > div > small {
        display: none !important;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"] {
        min-height: unset !important;
        padding: 5px 10px !important;
        display: flex;
        align-items: center;
        justify-content: space-between;
        background-color: white;
        color: black;
        border-radius: 4px;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"] svg {
        display: none;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"]::before {
        content: "📄";
        margin-right: 10px;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"] span {
        flex-grow: 1;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"] span span {
        display: none;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"] span::after {
        content: "Limit 200MB per file";
        font-size: 0.8em;
        color: #666;
    }
    .stFileUploader [data-testid="stFileUploadDropzone"] button {
        padding: 2px 8px !important;
        font-size: 0.8em !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #76B900 !important;
        border-radius: 5px !important;
        padding: 10px !important;
    }
    .stTextArea > div > div > textarea::placeholder {
        color: #808080 !important;
    }
    .stButton > button {
        background-color: #76B900;
        color: #FFFFFF;
    }
    .query-input {
        margin-top: 20px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header with logo and navigation
    st.markdown("""
    <div class="header-container">
        <div class="logo-nav-container">
            <img src="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg" class="nvidia-logo">
            <div class="nav-links">
                <a href="?page=home">HOME</a>
                <a href="?page=visualization">VISUALIZATION</a>
                <a href="?page=gap-identification">GAP IDENTIFICATION</a>
            </div>
        </div>
    </div>
    <hr class="green-line">
    """, unsafe_allow_html=True)

    # Get the current page from query parameters
    current_page = st.query_params.get("page", "home")

    # Content container
    st.markdown('<div class="content">', unsafe_allow_html=True)

    if current_page == "home":
        st.markdown('<h2 style="color: #76B900;">Upload Documents and Enter Query</h2>', unsafe_allow_html=True)
        
        
        uploaded_files = st.file_uploader("Drag and drop files here",  type=['txt', 'csv', 'pdf'], accept_multiple_files=True, key="file_uploader")
        if uploaded_files:
            for file in uploaded_files:
                st.write(f"File: {file.name}, Size: {file.size} bytes")
            if st.button("Process Files"):
                try:
                    files = [('files[]', file) for file in uploaded_files]
                    with st.spinner("Processing files..."):
                        response = requests.post('http://localhost:5050/upload', files=files)

                    if response.status_code == 200:
                        st.success("Files uploaded and processed successfully!")
                    else:
                        error_message = response.json().get('error', 'Unknown error') if response.content else 'No response from server'
                        st.error(f"Error uploading files. Status code: {response.status_code}. Message: {error_message}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the server: {str(e)}")


        # Query input
        st.markdown('<div class="query-input">', unsafe_allow_html=True)
        query = st.text_area("", placeholder="Enter your prompt for sequence reconstruction", height=100, key="query_input")
        st.markdown('</div>', unsafe_allow_html=True)

        # Reconstruct Sequence button
        if st.button("Reconstruct Sequence"):
            if query and uploaded_files:
                try:
                    # Send the question to the Flask backend
                    with st.spinner("Generating answer..."):
                        response = requests.post('http://localhost:5050/ask', json={'question': query})

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
                st.warning("Please enter a query and upload files before reconstructing the sequence.")

    elif current_page == "visualization":
        st.header("Visualization")
        st.write("Visualization content goes here.")

    elif current_page == "gap-identification":
        st.header("Gap Identification")
        st.write("Gap Identification content goes here.")

    st.markdown('</div>', unsafe_allow_html=True)
    st.sidebar.title("About")
    st.sidebar.info("This is a document Q&A system that uses NVIDIA AI for embeddings and retrieval.")
    st.sidebar.info("Upload TXT, CSV, or PDF documents and ask questions to get AI-powered answers!")
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with by Noisy Indian Varun Singh ")

if __name__ == "__main__":
    main()