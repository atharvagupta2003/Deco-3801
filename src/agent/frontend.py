import requests
import streamlit as st
import os
import uuid

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

# Initialize session state variables
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None
if "query" not in st.session_state:
    st.session_state.query = ""
if "vector_db_choice" not in st.session_state:
    st.session_state.vector_db_choice = "Wiki"
if "need_user_input" not in st.session_state:
    st.session_state.need_user_input = False
if "options" not in st.session_state:
    st.session_state.options = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_choice_made" not in st.session_state:
    st.session_state.user_choice_made = False
if "user_choice" not in st.session_state:
    st.session_state.user_choice = None

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
    if os.path.exists(css_file):
        load_css(css_file)
    else:
        st.write("CSS file not found.")

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
    tabs = st.tabs(["Home", "Visualization"])

    with tabs[0]:
        st.markdown('<h3 class="nvidia-green">Upload Documents and Enter Query</h3>', unsafe_allow_html=True)

        # File uploader
        uploaded_files = st.file_uploader(" ", type=['txt', 'csv', 'pdf'], accept_multiple_files=True, label_visibility="collapsed")

        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files  # Store uploaded files in session state

            # Display file details
            for file in uploaded_files:
                st.write(f"File: {file.name}, Size: {file.size} bytes")

            if st.button("Process Files"):
                try:
                    files = [('file', (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    with st.spinner("Processing files..."):
                        response = requests.post('http://localhost:5050/upload', files=files)

                    if response.status_code == 200:
                        st.success("Files uploaded and processed successfully!")
                    else:
                        error_message = response.json().get('error', 'Unknown error') if response.content else 'No response from server'
                        st.error(f"Error uploading files. Status code: {response.status_code}. Message: {error_message}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the server: {str(e)}")

        # Dropdown for vector database selection
        vector_db_choice = st.selectbox(
            "Select the vector database for the query:",
            ("Wiki", "ArXiv", "Custom"),
            key="vector_db_selector"
        )
        st.session_state.vector_db_choice = vector_db_choice  # Store vector database choice in session state

        # Query input for document Q&A
        query = st.text_input("Enter your query for sequence reconstruction:")

        # Reconstruct Sequence button
        if st.button("Reconstruct Sequence", disabled=st.session_state.need_user_input):
            if query:
                st.session_state.query = query
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.answer = ""  # Reset previous answer
                st.session_state.need_user_input = False
                st.session_state.user_choice_made = False
                st.session_state.user_choice = None

                # Send initial request to backend
                try:
                    with st.spinner("Processing..."):
                        response = requests.post('http://localhost:5050/ask', json={
                            'question': query,
                            'vector_db_choice': st.session_state.vector_db_choice,
                            'session_id': st.session_state.session_id
                        })

                    response_data = response.json()
                    if response.status_code == 200:
                        if response_data.get('need_user_input'):
                            st.session_state.options = response_data['options']
                            st.session_state.need_user_input = True
                            st.session_state.session_id = response_data['session_id']
                        elif 'answer' in response_data:
                            st.session_state.answer = response_data['answer']
                            st.success("Answer generated!")
                        elif 'error' in response_data:
                            st.error(f"Error: {response_data['error']}")
                        else:
                            st.error("Unexpected response from server.")
                    else:
                        error_message = response_data.get('error', 'Unknown error')
                        st.error(f"Error: {error_message}")
                except Exception as e:
                    st.error(f"Error connecting to the server: {str(e)}")
            else:
                st.warning("Please enter a question before proceeding.")

        # If user input is needed
        if st.session_state.need_user_input:
            st.write("Please select a search tool:")
            selected_option = st.radio("Search Tools", st.session_state.options, key="user_choice_radio")

            if st.button("Submit Choice"):
                if selected_option:
                    st.session_state.user_choice = selected_option
                    st.session_state.user_choice_made = True

                    try:
                        with st.spinner("Processing your choice..."):
                            response = requests.post('http://localhost:5050/ask', json={
                                'question': st.session_state.query,
                                'vector_db_choice': st.session_state.vector_db_choice,
                                'user_choice': st.session_state.user_choice,
                                'session_id': st.session_state.session_id
                            })

                        response_data = response.json()
                        if response.status_code == 200:
                            if 'answer' in response_data:
                                st.session_state.answer = response_data['answer']
                                st.session_state.need_user_input = False
                                st.success("Answer generated!")
                            elif response_data.get('need_user_input'):
                                # If more input is needed, update options
                                st.session_state.options = response_data['options']
                                st.session_state.need_user_input = True
                                st.session_state.user_choice_made = False
                                st.warning("Please select an option.")
                            elif 'error' in response_data:
                                st.error(f"Error: {response_data['error']}")
                            else:
                                st.error("Unexpected response from server.")
                        else:
                            error_message = response_data.get('error', 'Unknown error')
                            st.error(f"Error: {error_message}")
                    except Exception as e:
                        st.error(f"Error connecting to the server: {str(e)}")
                else:
                    st.warning("Please select an option before submitting.")

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

if __name__ == "__main__":
    main()
