import requests
import streamlit as st
import os

def reconstruct_sequence(query, files):
    # Placeholder function for sequence reconstruction
    sequence = "ATCG" * 10  # Example sequence
    return sequence

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Sequence Reconstruction",
        page_icon="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg",
        layout="wide"
    )

    # Load the external CSS file
    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
    load_css(css_file)

    # NVIDIA logo
    st.markdown('<img src="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg" class="nvidia-logo">', unsafe_allow_html=True)

    # Title
    st.title("Sequence Reconstruction")

    # Navigation tabs without icons
    tabs = st.tabs(["Home", "Visualization", "Gap Identification"])
    
    with tabs[0]:
        st.markdown('<h2 class="nvidia-green">Upload Documents and Enter Query</h2>', unsafe_allow_html=True)

        # File uploader
        st.markdown('<div class="file-uploader">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader("Drag and drop files here", type=['txt', 'csv', 'pdf'], accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
        st.markdown('Limit 200MB per file', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if uploaded_files:
            # Display file details
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
        st.text_area("Enter your query for sequence reconstruction:", height=100, key="query_input")

        # Reconstruct Sequence button
        if st.button("Reconstruct Sequence"):
            query = st.session_state.query_input
            uploaded_files = st.session_state.file_uploader

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

    with tabs[1]:
        st.header("Visualization")
        st.write("Visualization content goes here.")

    with tabs[2]:
        st.header("Gap Identification")
        st.write("Gap Identification content goes here.")

if __name__ == "__main__":
    main()