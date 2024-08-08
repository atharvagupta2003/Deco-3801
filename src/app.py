import streamlit as st
import base64
import streamlit.components.v1 as components

value = 0
input_entered = 0
st.set_page_config(page_title="🦙💬 SeqSynth")

# Apply background image CSS
background_image = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background-color:#1c1c3c;
    background-size: 100vw 100vh;  
    background-position: center;  
    background-repeat: no-repeat;
}
</style>
"""
st.markdown(background_image, unsafe_allow_html=True)

# Initialize session state for prompts and uploaded files
if "prompts" not in st.session_state:
    st.session_state.prompts = [{
        "role": "assistant",
        "content": ("Welcome to SeqSynth, an intelligent sequence reconstruction tool designed to streamline the process of understanding complex sequential information. "
                    "Our application enables you to effortlessly generate sequences for activities such as chemical synthesis steps or timeline events. Simply upload your files and specify the process or activity, "
                    "and SeqSynth will provide a clear and coherent sequence, helping you identify gaps and understand the flow of information with ease.")
    }]

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# Display chat messages from history
for prompt in st.session_state.prompts:
    with st.chat_message(prompt["role"]):
        st.markdown(prompt["content"])

# Handle user input
if input := st.chat_input("For what process or activity are you requiring the sequential steps?"):
    st.chat_message("user").markdown(input)
    st.session_state.prompts.append({"role": "user", "content": input})


# Sidebar content
with st.sidebar:
    st.image("/Users/varunsingh/Desktop/First-Project/src/Logo.png", use_column_width=True)
    st.markdown(
        """
        <style>
        .custom-title {
            font-size: 30px;
            background: linear-gradient(to right, #1e90ff, #6a11cb, #2575fc, #00ced1, #32cd32);
            -webkit-background-clip: text;
            color: transparent;
            font-family: 'Arial', sans-serif;
            letter-spacing: -.03em;
            text-align: center;
            font-weight: bold;
        }
        </style>
        <div class="custom-title">
            <div class="line-one">Welcome to SeqSynth</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_files = st.file_uploader("Choose a file to upload", accept_multiple_files=True)

    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
    

    for i in st.session_state.prompts:
        if i["role"] == "user":
            input_entered = 1
    
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True) 
    if st.button("Submit", help="Please click on  this button to get the desired sequence"):
        if not st.session_state.uploaded_files:
            st.write("Please upload a file")
        elif input_entered == 0:
            st.write("Please enter the prompt")
        else:
            file_names = "  \n ".join([uploaded_file.name for uploaded_file in st.session_state.uploaded_files])
            value = 1
            st.write("Files uploaded successfully!")


if value:
    st.chat_message("assistant").markdown(file_names)

def clear_chat_history():
    st.session_state.prompts = [{"role": "assistant",  "content": ("Welcome to SeqSynth, an intelligent sequence reconstruction tool designed to streamline the process of understanding complex sequential information. "
                    "Our application enables you to effortlessly generate sequences for activities such as chemical synthesis steps or timeline events. Simply upload your files and specify the process or activity, "
                    "and SeqSynth will provide a clear and coherent sequence, helping you identify gaps and understand the flow of information with ease.")}]
    st.session_state.uploaded_files = []
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

