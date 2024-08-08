import streamlit as st
import os
import time
import pandas as pd
from wikihow_sequence_reconstruction.scripts.preprocess import preprocess_text, process_document

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
        
        uploaded_file = st.file_uploader("Upload a document (CSV or PDF)", type=['csv', 'pdf'])

        if uploaded_file:
            preprocessed_data = process_document(uploaded_file)
            if preprocessed_data:
                # Save the preprocessed data
                if not os.path.exists('data/documents'):
                    os.makedirs('data/documents')
                
                if uploaded_file.name.endswith('.csv'):
                    preprocessed_csv = pd.DataFrame(preprocessed_data)
                    preprocessed_csv.to_csv('data/documents/preprocessed_sequences.csv', index=False)
                    st.success(f"Preprocessed data for {preprocessed_data['title']} saved to data/documents/preprocessed_sequences.csv")
                else:
                    with open(f'data/documents/preprocessed_sequences_{uploaded_file.name.split(".")[0]}.txt', 'w') as f:
                        f.write('\n'.join(preprocessed_data['steps']))
                    st.success(f"Preprocessed data for {preprocessed_data['title']} saved to data/documents/preprocessed_sequences_{uploaded_file.name.split('.')[0]}.txt")

    with col2:
        st.markdown('<p class="medium-font">Sequence Reconstruction</p>', unsafe_allow_html=True)
        
        query = st.text_area("Enter your query for sequence reconstruction:", height=100)

        if st.button("Reconstruct Sequence", key="reconstruct"):
            if query:
                with st.spinner("Reconstructing sequence..."):
                    # TODO: Replace with your actual sequence reconstruction logic
                    st.success("Sequence reconstructed successfully!")
                    
                    st.markdown('<div class="result-box">', unsafe_allow_html=True)
                    st.markdown('<p class="small-font">Reconstructed Sequence:</p>', unsafe_allow_html=True)
                    st.write("Placeholder for reconstructed sequence")
                    
                    # TODO: Display the reconstructed sequence steps
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