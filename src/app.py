import streamlit as st 
from PIL import Image 

# Load and resize the image
image = Image.open("/Users/varunsingh/Desktop/Project/Deco-3801/src/file copy.jpg")
resized_image = image.resize((400, 200))

def about():
    description = """
    ### Sequence Reconstruction using Foundation Models and RAG

    This project aims to develop a pipeline for the reconstruction of sequential information, such as chemical synthesis steps or timeline events, using Foundation Models (FMs) and Retrieval Augmented Generation (RAG). The pipeline enables users to easily understand how sequential information flows from one piece to another, identify gaps, and automate the otherwise tedious manual reconstruction process. Users can interact with the pipeline through a user-friendly interface, upload relevant documents, enter queries, and search for related papers in PubMed and arXiv.

    **Key Features:**
    - Upload documents and enter queries to reconstruct sequences.
    - Integration with PubMed and arXiv for relevant research paper searches.
    - Designed to provide a general solution for various domains including chemical synthesis and timeline reconstruction.

    This project is developed in collaboration with NVIDIA, leveraging advanced AI models to ground the reconstructed sequences in factual information.
    """
    return description

def reconstruct_sequence():
    # Placeholder function for sequence reconstruction
    # In a real application, this would contain the actual reconstruction logic
    sequence = "ATCG" * 10  # Example sequence
    return sequence

def main():
    
    description = """
    ### Sequence Reconstruction using Foundation Models and RAG

    This project aims to develop a pipeline for the reconstruction of sequential information, such as chemical synthesis steps or timeline events, using Foundation Models (FMs) and Retrieval Augmented Generation (RAG). The pipeline enables users to easily understand how sequential information flows from one piece to another, identify gaps, and automate the otherwise tedious manual reconstruction process. Users can interact with the pipeline through a user-friendly interface, upload relevant documents, enter queries, and search for related papers in PubMed and arXiv.

    **Key Features:**
    - Upload documents and enter queries to reconstruct sequences.
    - Integration with PubMed and arXiv for relevant research paper searches.
    - Designed to provide a general solution for various domains including chemical synthesis and timeline reconstruction.

    This project is developed in collaboration with NVIDIA, leveraging advanced AI models to ground the reconstructed sequences in factual information.
    """
    
    st.set_page_config(page_title="Sequence Reconstruction Pipeline", layout="wide")

    # Custom CSS to create a top navigation bar
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
    }
    .navbar {
        display: flex;
        justify-content: space-around;
        padding: 10px;
        background-color: #f0f2f6;
        margin-bottom: 20px;
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
        st.title("Enhance your research with our Sequence Reconstruction Pipeline")
        st.write("Easily manage documents, perform advanced searches, and visualize reconstructed sequences.")

        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(image, width=400, use_column_width=True)
        
        with col2:
            st.subheader("Upload Documents")
            st.write("Add your documents to start the sequence reconstruction process.")
            st.file_uploader("Choose files", accept_multiple_files=True)

        # Search bar
        st.text_input("Enter your sequence reconstruction query")

        # Reconstruct Sequence button
        if st.button("Reconstruct Sequence"):
            sequence = reconstruct_sequence()
            
            # Display the reconstructed sequence
            st.subheader("Reconstructed Sequence")
            st.text_area("", value=sequence, height=100, key="reconstructed_sequence")

            # Display the visualization
            st.subheader("Visualization")
            st.write("This is a placeholder for the sequence visualization.")
            # In a real application, you would generate and display the visualization here
            # For example:
            # st.plotly_chart(generate_sequence_plot(sequence))

    elif page == "About":
        st.title("About")
        st.write(description)
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
