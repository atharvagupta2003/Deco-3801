# frontend.py

import requests
import streamlit as st
import os
import uuid
from visualisation import call_visualisation  # Ensure this module exists and is correctly implemented
import time

# Cached function to check server health every 60 seconds
@st.cache_data(ttl=60)
def check_server_health():
    try:
        response = requests.get('http://localhost:5050/health')
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.error(f"CSS file not found: {file_name}")

# Progress Bar for File Uploads
def file_upload_progress(files):
    progress_bar = st.progress(0)
    total_files = len(files)

    for i, file in enumerate(files):
        time.sleep(0.5)  # Simulate processing time
        progress_bar.progress((i + 1) / total_files)
    progress_bar.empty()  # Remove progress bar after completion

# Initialize session state variables
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None
if "query" not in st.session_state:
    st.session_state.query = ""
if "vector_db_choice" not in st.session_state:
    st.session_state.vector_db_choice = "Custom"
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
if "show_suggestions" not in st.session_state:
    st.session_state.show_suggestions = False  # Track whether suggestions are visible
if "selected_suggestion" not in st.session_state:
    st.session_state.selected_suggestion = ""

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

    # Header Section
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.image(
                "https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg",
                width=150,
            )
        with col2:
            st.markdown(
                "<h1 style='color: #76B900; text-align: center;'>Sequence Reconstruction</h1>",
                unsafe_allow_html=True
            )
        with col3:
            st.empty()

    # Check server health
    if not check_server_health():
        st.error("Error: Unable to connect to the server. Please ensure the Flask backend is running.")
        st.stop()

    tabs = st.tabs(["Home", "Visualization"])

    with tabs[0]:
        # Reduced font size for the header
        st.markdown(
            "<h2 style='font-size:20px;'>Upload Documents</h2>",
            unsafe_allow_html=True
        )

        # File uploader
        uploaded_files = st.file_uploader(
            "",
            type=['txt', 'csv', 'pdf', 'docx'],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files  # Store uploaded files in session state

            # Button to process files
            if st.button("Process Files"):
                try:
                    files = [('file', (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    with st.spinner("Processing files..."):
                        response = requests.post('http://localhost:5050/upload', files=files)

                    if response.status_code == 200:
                        st.success("Files uploaded and processed successfully!")
                        file_upload_progress(uploaded_files)  # Show progress bar
                    else:
                        error_message = response.json().get('error', 'Unknown error') if response.content else 'No response from server'
                        st.error(f"Error uploading files. Status code: {response.status_code}. Message: {error_message}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the server: {str(e)}")

        # Vector Database Selection and Query Input
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing

        # Increase font size for the selectbox label
        st.markdown(
            "<h2 style='font-size:20px;'>Select Vector Database for Query</h2>",
            unsafe_allow_html=True
        )
        vector_db_choice = st.selectbox(
            "",
            ("Wiki", "ArXiv", "Custom"),
            index=2,  # Default to "Custom"
            key="vector_db_selector",
            label_visibility="collapsed"
        )
        st.session_state.vector_db_choice = vector_db_choice  # Store vector database choice in session state

        st.markdown("<br><br>", unsafe_allow_html=True)
        # Toggle button for showing/hiding example queries
        if st.button("Suggestions"):
            st.session_state.show_suggestions = not st.session_state.show_suggestions

        # Conditionally display the suggestion dropdown
        if st.session_state.show_suggestions:
            suggestions = [
                "Provide the timeline for the events in World War 2.",
                "Sequence all of Napoleon's battles in order.",
                "Give all the steps for synthesis of Carbon Monoxide.",
                "What are the steps to create a neural network?"
            ]

            selected_suggestion = st.selectbox(
                "",  # No label
                options=["Select a suggestion..."] + suggestions,
                key="suggestion_selector",
                label_visibility="collapsed"
            )

            # Use the selected suggestion to populate the query input field
            if selected_suggestion != "Select a suggestion...":
                query = st.text_input("", value=selected_suggestion, key="query_input")
            else:
                query = st.text_input("", placeholder="Type your question here...", key="query_input")
        else:
            # Default input if no suggestion is shown
            query = st.text_input("", placeholder="Type your question here...", key="query_input")

        # Reconstruct Sequence button
        if st.button("Reconstruct Sequence"):
            if query.strip():
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
                st.warning("Please enter a valid question before proceeding.")

        # If user input is needed
        if st.session_state.need_user_input:
            st.markdown("<h2 style='font-size:20px;'>Additional Information Required</h2>", unsafe_allow_html=True)
            st.write("Please select a search tool:")
            # Remove space after the label
            selected_option = st.radio(
                "",
                st.session_state.options,
                key="user_choice_radio",
                label_visibility="collapsed"
            )

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
            st.subheader("Answer:")
            st.markdown(
                f"""
                <div class='answer-box'>
                    {st.session_state.answer}
                </div>
                """,
                unsafe_allow_html=True
            )

            # Download button for generated results
            st.download_button(
                label="Download Answer",
                data=st.session_state.answer,
                file_name="answer.txt",
                mime="text/plain"
            )

            # User Feedback Mechanism
            st.markdown("---")  # Separation
            st.subheader("Did this answer your question?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Yes"):
                    st.success("Thank you for your feedback!")
            with col2:
                if st.button("👎 No"):
                    st.error("Sorry to hear that! We'll work on improving.")

    with tabs[1]:
        st.header("Visualization")
        if st.session_state.answer:
            call_visualisation(st.session_state.answer)
        else:
            st.info("Please generate an answer to view its visualization.")

if __name__ == "__main__":
    main()
