import requests
import streamlit as st
import os
import time


# Function to check server health
def check_server_health():
    try:
        response = requests.get('http://localhost:5050/health')
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Progress Bar for File Uploads
def file_upload_progress(files):
    progress_bar = st.progress(0)
    total_files = len(files)

    for i, file in enumerate(files):
        time.sleep(1)  # Simulate upload time
        st.write(f"Processing {file.name} ...")
        progress_bar.progress((i + 1) / total_files)


# Initialize session state variables
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None
if "query" not in st.session_state:
    st.session_state.query = ""


def main():
    # Set Streamlit page configuration
    st.set_page_config(
        page_title="Sequence Reconstruction",
        page_icon="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Load the external CSS file
    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
    load_css(css_file)


    # NVIDIA logo
    st.markdown('<img src="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg" class="nvidia-logo">',
                unsafe_allow_html=True)

    # Title
    st.markdown("<div class='stHeader'><h1>Sequence Reconstruction</h1></div>", unsafe_allow_html=True)

    # Check server health
    if not check_server_health():
        st.error("Error: Unable to connect to the server. Please ensure the Flask backend is running.")
        st.stop()

    # Navigation tabs without icons
    tabs = st.tabs(["Home", "Visualization", "Gap Identification"])

    with tabs[0]:
        st.markdown('<h3 class="nvidia-green">Upload Documents and Enter Query</h2>', unsafe_allow_html=True)


        uploaded_files = st.file_uploader(" ", type=['txt', 'csv', 'pdf'], accept_multiple_files=True, label_visibility="collapsed")

        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files  # Store uploaded files in session state

            # Display file details
            for file in uploaded_files:
                st.write(f"File: {file.name}, Size: {file.size} bytes")

            if st.button("Process Files"):
                file_upload_progress(uploaded_files)  # Show progress bar for file uploads
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

        # Query input for document Q&A
        query = st.text_input("Enter your query for sequence reconstruction:")

        if st.button("Reconstruct Sequence"):
            if query:
                st.session_state.query = query  # Store query in session state
                try:
                    # Send the question to the Flask backend
                    with st.spinner("Generating answer..."):
                        response = requests.post('http://localhost:5050/ask', json={'question': query})

                    if response.status_code == 200:
                        st.session_state.answer = response.json()['answer']  # Store answer in session state
                        st.success("Answer generated!")
                    else:
                        error_message = response.json().get('error', 'Unknown error') if response.content else 'No response from server'
                        st.error(f"Error getting answer. Status code: {response.status_code}. Message: {error_message}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the server: {str(e)}")
            else:
                st.warning("Please enter a question before getting an answer.")

        # Display the answer if available
        if st.session_state.answer:
            st.markdown("<div class='answer-box'>", unsafe_allow_html=True)
            st.write("Answer:", st.session_state.answer)
            st.markdown("</div>", unsafe_allow_html=True)

            # Download button for generated results
            st.download_button(label="Download Answer",
                               data=st.session_state.answer,
                               file_name="answer.txt",
                               mime="text/plain")

            # User Feedback Mechanism
            st.write("Did this answer your question?")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("👍 Yes"):
                    st.success("Thank you for your feedback!")
            with col2:
                if st.button("👎 No"):
                    st.error("Sorry to hear that! We'll work on improving.")

    # Visualization Tab (can be extended with actual visualizations)
    with tabs[1]:
        st.header("Visualization")
        st.write("Visualization content goes here.")

    # Gap Identification Tab (can be extended with actual logic)
    with tabs[2]:
        st.header("Gap Identification")
        st.write("Gap Identification content goes here.")


if __name__ == "__main__":
    main()