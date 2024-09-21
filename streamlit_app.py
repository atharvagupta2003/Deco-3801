import streamlit as st
import os
import pandas as pd
import requests

API_URL = 'http://localhost:5000'

def call_flask_api(endpoint, json_data=None, files=None):
    try:
        if files:
            response = requests.post(f"{API_URL}/{endpoint}", files=files)
        else:
            response = requests.post(f"{API_URL}/{endpoint}", json=json_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None

def main():
    st.set_page_config(page_title="Sequence Reconstruction Pipeline", layout="wide")
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

    tab1, tab2, tab3, tab4 = st.tabs(["Document Management", "Sequence Reconstruction", "PubMed Search", "arXiv Search"])

    with tab1:
        st.markdown('<p class="medium-font">Document Management</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload a document (CSV or PDF)", type=['csv', 'pdf'])
        
        if uploaded_file:
            if st.button("Ingest Document"):
                with st.spinner("Ingesting document..."):
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = call_flask_api('ingest', files=files)
                    if response and response.get('status') == 'success':
                        st.success(response.get('message'))
                    else:
                        st.error("Failed to ingest document.")

    with tab2:
        st.markdown('<p class="medium-font">Sequence Reconstruction</p>', unsafe_allow_html=True)
        query = st.text_area("Enter your query for sequence reconstruction:", height=100)

        if st.button("Reconstruct Sequence", key="reconstruct"):
            if query:
                with st.spinner("Reconstructing sequence..."):
                    response = call_flask_api('reconstruct', json_data={'query': query})
                    if response and response.get('status') == 'success':
                        st.success("Sequence reconstructed successfully!")
                        st.markdown('<div class="result-box">', unsafe_allow_html=True)
                        st.markdown('<p class="small-font">Reconstructed Sequence:</p>', unsafe_allow_html=True)
                        st.write(response.get('sequence', "No sequence found."))
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error("Failed to reconstruct sequence.")
            else:
                st.warning("Please enter a query.")

    with tab3:
        st.markdown('<p class="medium-font">PubMed Search</p>', unsafe_allow_html=True)
        pubmed_query = st.text_input("Enter your PubMed search query:")
        max_results = st.number_input("Maximum number of results:", min_value=1, max_value=100, value=20)

        if st.button("Search PubMed", key="pubmed_search"):
            if pubmed_query:
                with st.spinner("Searching PubMed..."):
                    response = call_flask_api('search_pubmed', json_data={'query': pubmed_query, 'max_results': max_results})
                    if response and response.get('status') == 'success':
                        st.success("PubMed search completed successfully!")
                        for paper in response.get('results', []):
                            st.markdown('<div class="result-box">', unsafe_allow_html=True)
                            st.markdown(f"<p class='small-font'>{paper['title']}</p>", unsafe_allow_html=True)
                            st.write(f"Authors: {paper['authors']}")
                            st.write(f"Published: {paper['publication_date']}")
                            st.write(f"Abstract: {paper['abstract']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error("Failed to search PubMed.")
            else:
                st.warning("Please enter a search query.")

    with tab4:
        st.markdown('<p class="medium-font">arXiv Search</p>', unsafe_allow_html=True)
        arxiv_query = st.text_input("Enter your arXiv search query:")

        if st.button("Search arXiv", key="arxiv_search"):
            if arxiv_query:
                with st.spinner("Searching arXiv..."):
                    response = call_flask_api('search_arxiv', json_data={'query': arxiv_query})
                    if response and response.get('status') == 'success':
                        st.success("arXiv search completed successfully!")
                        for paper in response.get('results', []):
                            st.markdown('<div class="result-box">', unsafe_allow_html=True)
                            st.markdown(f"<p class='small-font'>{paper['title']}</p>", unsafe_allow_html=True)
                            st.write(f"Summary: {paper['summary']}")
                            st.write(f"Published: {paper['published']}")
                            st.write(f"URL: {paper['url']}")
                            st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.error("Failed to search arXiv.")
            else:
                st.warning("Please enter a search query.")

    st.sidebar.title("About")
    st.sidebar.info(
        "This application demonstrates a sequence reconstruction pipeline "
        "using Foundation Models and Retrieval Augmented Generation. "
        "Upload documents, enter a query, and see the reconstructed sequence. "
        "You can also search PubMed and arXiv for relevant papers."
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