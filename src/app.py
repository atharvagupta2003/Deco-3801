import streamlit as st

def reconstruct_sequence(query, files):
    # Placeholder function for sequence reconstruction
    sequence = "ATCG" * 10  # Example sequence
    return sequence

def main():
    st.set_page_config(
        page_title="Sequence Reconstruction Pipeline",
        page_icon="https://upload.wikimedia.org/wikipedia/sco/2/21/Nvidia_logo.svg",
        layout="wide"
    )

    # Custom CSS
    st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    .stButton > button {
        background-color: #76B900;
        color: #ffffff;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border-radius: 20px;
    }
    .stButton > button:hover {
        background-color: #5c9100;
    }
    .navbar {
        display: flex;
        justify-content: space-around;
        padding: 10px;
        background-color: #1a1a1a;
        margin-bottom: 20px;
    }
    h1, h2, h3 {
        color: #76B900;
    }
    .chat-input {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 1rem;
        background-color: #1a1a1a;
    }
    .main-content {
        margin-bottom: 120px;
    }
    .file-upload-btn {
        background-color: #333333;
        color: #ffffff;
        border: none;
        border-radius: 5px;
        padding: 10px 15px;
        cursor: pointer;
    }
    .send-btn {
        background-color: #76B900;
        color: #ffffff;
        border: none;
        border-radius: 20px;
        padding: 10px 20px;
        cursor: pointer;
        font-size: 16px;
    }
    .visualization-placeholder {
        background-color: #1a1a1a;
        border: 1px solid #333;
        height: 400px;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }
    .custom-input {
        width: 100%;
        padding: 10px 15px;
        border-radius: 20px;
        border: 1px solid #333;
        background-color: #1a1a1a;
        color: #ffffff;
    }
    .custom-input::placeholder {
        color: #76B900;
    }
    .delete-btn {
        color: #ff0000;
        cursor: pointer;
        margin-left: 10px;
    }
    .file-upload-text {
        color: #76B900;
        font-size: 14px;
        text-align: right;
        margin-top: 5px;
    }
    .file-upload-container {
        background-color: #333333;
        border-radius: 5px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Top navigation bar
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        home = st.button("Home")
    with col2:
        about = st.button("About")
    with col3:
        doc_management = st.button("Document Management")
    with col4:
        pubmed = st.button("PubMed Search")
    with col5:
        arxiv = st.button("arXiv Search")

    # Determine which page to show
    if home:
        page = "Home"
    elif about:
        page = "About"
    elif doc_management:
        page = "Document Management"
    elif pubmed:
        page = "PubMed Search"
    elif arxiv:
        page = "arXiv Search"
    else:
        page = "Home"  # Default page

    # Main content
    if page == "Home":
        st.title("Sequence Reconstruction Pipeline")
        
        # Initialize session state
        if 'conversation' not in st.session_state:
            st.session_state.conversation = []
        if 'sequence' not in st.session_state:
            st.session_state.sequence = None
        if 'clear_input' not in st.session_state:
            st.session_state.clear_input = False

        # Main content area (for visualization)
        main_content = st.container()

        # Always display the visualization placeholder
        with main_content:
            visualization_placeholder = st.empty()
            visualization_placeholder.markdown('<div class="visualization-placeholder">Visualization Placeholder</div>', unsafe_allow_html=True)

        # Display conversation history with delete buttons
        for i, item in enumerate(st.session_state.conversation):
            col1, col2 = st.columns([20, 1])
            with col1:
                st.write(item)
            with col2:
                if st.button("❌", key=f"delete_{i}"):
                    del st.session_state.conversation[i]
                    st.rerun()

        # Chat input area
        with st.container():
            st.markdown('<div class="chat-input">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                query = st.text_input("", placeholder="Enter sequence...", key="query_input")
            with col2:
                st.markdown('<div class="file-upload-container">', unsafe_allow_html=True)
                uploaded_files = st.file_uploader("", accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
                st.markdown('<p class="file-upload-text">Drag and drop files here (Limit 200MB per file)</p>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                send_button = st.button("Send", key="send_button")
            
            st.markdown('</div>', unsafe_allow_html=True)

        if send_button and query:
            # Add user query to conversation
            st.session_state.conversation.append(f"User: {query}")
            
            if uploaded_files:
                file_names = [file.name for file in uploaded_files]
                st.session_state.conversation.append(f"Files uploaded: {', '.join(file_names)}")

            # Reconstruct sequence
            st.session_state.sequence = reconstruct_sequence(query, uploaded_files)
            
            # Add system response to conversation
            st.session_state.conversation.append(f"System: Sequence reconstructed. Length: {len(st.session_state.sequence)}")

            # Update visualization placeholder with sequence info
            visualization_placeholder.markdown(f"""
            <div class="visualization-placeholder">
                <div>
                    <h3>Sequence Information</h3>
                    <p>Sequence: {st.session_state.sequence}</p>
                    <p>Query used: {query}</p>
                    <p>Number of files uploaded: {len(uploaded_files)}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Clear the input
            st.session_state.query_input = ""
            st.rerun()

    elif page == "About":
        st.title("About")
        st.write("About page content goes here.")
    elif page == "Document Management":
        st.title("Document Management")
        st.write("Document Management page content goes here.")
    elif page == "PubMed Search":
        st.title("PubMed Search")
        st.write("PubMed Search page content goes here.")
    elif page == "arXiv Search":
        st.title("arXiv Search")
        st.write("arXiv Search page content goes here.")

    # Footer
    st.markdown("---")
    st.write("Created as part of the AI project for sequence reconstruction.")

if __name__ == "__main__":
    main()
