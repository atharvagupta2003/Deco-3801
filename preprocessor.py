import pandas as pd
import os
import re
from nltk.tokenize import sent_tokenize
import pdfplumber
import PyPDF2
import csv
def process_document(file_path):
    if file_path.endswith('.pdf'):
        return process_pdf(file_path)
    elif file_path.endswith('.csv'):
        return process_csv(file_path)
    else:
        raise ValueError("Unsupported file type")

def process_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return [{'content': text}]

def process_csv(file_path):
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        return [row for row in reader]

# def preprocess_text(text):
#     sentences = sent_tokenize(text)
#     steps = [re.sub(r'[^A-Za-z0-9\s]', '', sentence).lower().strip() for sentence in sentences]
#     return steps
#
# def process_document(file):
#     if file.name.endswith('.csv'):
#         data = pd.read_csv(file)
#         data['text'] = data['text'].fillna('')
#         preprocessed_data = data.apply(lambda row: {'title': row['title'], 'steps': preprocess_text(row['text'])}, axis=1)
#         return preprocessed_data.to_dict(orient='records')
#     elif file.name.endswith('.pdf'):
#         with pdfplumber.open(file) as pdf:
#             text = '\n'.join([page.extract_text() for page in pdf.pages])
#             steps = preprocess_text(text)
#             return {'title': file.name, 'steps': steps}
#     else:
#         return None
#
# def save_preprocessed_data(preprocessed_data, output_path):
#     df = pd.DataFrame.from_records([preprocessed_data]) if isinstance(preprocessed_data, dict) else pd.DataFrame(preprocessed_data)
#     if not os.path.exists(os.path.dirname(output_path)):
#         os.makedirs(os.path.dirname(output_path))
#     df.to_csv(output_path, index=False)

