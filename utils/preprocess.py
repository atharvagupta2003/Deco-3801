import pandas as pd
import os
import re
from nltk.tokenize import sent_tokenize
import pdfplumber


def preprocess_text(text):
    """
    Function to extract and preprocess steps from the text.
    """
    # Handle missing values
    if pd.isna(text):
        text = ''

    # Split text into sentences
    sentences = sent_tokenize(text)

    # Preprocess each sentence
    steps = [re.sub(r'[^A-Za-z0-9\s]', '', sentence).lower().strip() for sentence in sentences]

    return steps


def process_document(file):
    """
    Function to process the uploaded document and preprocess the text.
    """
    # Check the file type
    if file.name.endswith('.csv'):
        data = pd.read_csv(file)
        # Handle missing values in 'text' column
        data['text'] = data['text'].fillna('')
        preprocessed_data = data.apply(lambda row: {'title': row['title'], 'steps': preprocess_text(row['text'])},
                                       axis=1)
        return preprocessed_data.to_dict()
    elif file.name.endswith('.pdf'):
        with pdfplumber.open(file) as pdf:
            text = '\n'.join([page.extract_text() for page in pdf.pages])
            steps = preprocess_text(text)
            return {'title': file.name, 'steps': steps}
    else:
        return None


def save_preprocessed_data(preprocessed_data, output_path):
    """
    Function to save the preprocessed data to a CSV file.
    """
    if isinstance(preprocessed_data, dict):
        # Convert dictionary to DataFrame
        df = pd.DataFrame.from_records([preprocessed_data])
    else:
        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(preprocessed_data)

    # Save DataFrame to CSV
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))

    df.to_csv(output_path, index=False)

# Example usage
# Assuming you have a file object 'file'
# preprocessed_data = process_document(file)
# save_preprocessed_data(preprocessed_data, '../preprocessed_data/preprocessed_sequences.csv')