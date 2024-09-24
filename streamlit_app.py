import streamlit as st
import requests
import os
import json

# Set Streamlit page configuration
st.set_page_config(
    page_title="NVIDIA-style Document Q&A",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to set NVIDIA-style green and black theme
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
    }
    .stTextInput>div>div>input {
        color: #ffffff;
        background-color: #2a2a2a;
    }
    .stTextArea>div>div>textarea {
        color: #ffffff;
        background-color: #2a2a2a;
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
st.title("📚 Document Q&A System")

# Check server health
if not check_server_health():
    st.error("Error: Unable to connect to the server. Please ensure the Flask backend is running.")
    st.stop()

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'csv'])

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
        response = requests.post('http://localhost:5050/upload', files=files)

        if response.status_code == 200:
            st.success("File uploaded and processed successfully!")
        else:
            error_message = response.json().get('error',
                                                'Unknown error') if response.content else 'No response from server'
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
            response = requests.post('http://localhost:5050/ask', json={'question': question})

            if response.status_code == 200:
                answer = response.json()['answer']
                st.write("Answer:", answer)
            else:
                error_message = response.json().get('error',
                                                    'Unknown error') if response.content else 'No response from server'
                st.error(f"Error getting answer. Status code: {response.status_code}. Message: {error_message}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the server: {str(e)}")
    else:
        st.warning("Please enter a question.")

# Display information about the system
st.sidebar.title("About")
st.sidebar.info("This is a document Q&A system that uses NVIDIA AI for embeddings and retrieval.")
st.sidebar.info("Upload a document and ask questions to get AI-powered answers!")