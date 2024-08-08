import streamlit as st
import os
import time

def save_uploaded_file(uploaded_file):
    try:
        with open(os.path.join("data/documents", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except:
        return False



#mock , need to be replaced with the original logic once we move down the project 
def mock_sequence_reconstruction(query):
    steps = [
        "Analyze input query",
        "Retrieve relevant documents",
        "Extract key information",
        "Identify sequence components",
        "Arrange components in logical order",
        "Fill in missing steps",
        "Generate final sequence"
    ]
    return ". ".join(steps)

def main():
    st.set_page_config(page_title="Sequence Reconstruction Pipeline", layout="wide")
    
    # Custom CSS
    st.markdown("""
    <style>
    .big-font {
        font-size: 50px !important;
        font-weight: bold;
        color: #1E88E5;
        margin-bottom: 30px;
    }
    .medium-font {
        font-size: 30px !important;
        font-weight: bold;
        color: #0D47A1;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .small-font {
        font-size: 18px !important;
        color: #1565C0;
        margin-bottom: 10px;
    }
    .result-box {
        background-color: #E3F2FD;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #90CAF9;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #1565C0;
    }
    .stTextArea>div>div>textarea {
        background-color: #F3F3F3;
        color: #333333;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="big-font">Sequence Reconstruction Pipeline</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<p class="medium-font">Document Management</p>', unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader("Upload documents", accept_multiple_files=True)

        if uploaded_files:
            for file in uploaded_files:
                if save_uploaded_file(file):
                    st.success(f"File {file.name} saved successfully")
                else:
                    st.error(f"Error saving file {file.name}")

        st.markdown('<p class="small-font">Existing Documents</p>', unsafe_allow_html=True)
        if not os.path.exists("data/documents"):
            os.makedirs("data/documents")
        documents = os.listdir("data/documents")
        if documents:
            for file in documents:
                st.write(f"📄 {file}")
        else:
            st.write("No documents uploaded yet.")

    with col2:
        st.markdown('<p class="medium-font">Sequence Reconstruction</p>', unsafe_allow_html=True)
        
        query = st.text_area("Enter your query for sequence reconstruction:", height=100)

        if st.button("Reconstruct Sequence", key="reconstruct"):
            if query:
                with st.spinner("Reconstructing sequence..."):
                    time.sleep(2)
                    result = mock_sequence_reconstruction(query)
                    
                    st.success("Sequence reconstructed successfully!")
                    
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown('<p class="small-font">Reconstructed Sequence:</p>', unsafe_allow_html=True)
                    st.write(result)
                    
                    steps = result.split('. ')
                    for i, step in enumerate(steps, 1):
                        st.markdown(f"**Step {i}:** {step}")
                        st.progress(i / len(steps))
                        time.sleep(0.5)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("Please enter a query.")

    st.sidebar.title("About")
    st.sidebar.info(
        "This application demonstrates a sequence reconstruction pipeline "
        "using Foundation Models and Retrieval Augmented Generation. "
        "Upload documents, enter a query, and see the reconstructed sequence."
    )
    
    st.markdown(
        """
    <div style='position: fixed; bottom: 0; left: 0; width: 100%; color: #1E88E5; text-align: center; padding: 10px;'>
    Created as part of the AI project for sequence reconstruction.
    </div>
    """,
    unsafe_allow_html=True
    )

if __name__ == "__main__": 
    main()