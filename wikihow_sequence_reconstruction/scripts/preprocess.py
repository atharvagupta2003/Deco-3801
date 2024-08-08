import pandas as pd
import os
import re
from nltk.tokenize import sent_tokenize

# Load the dataset
all_data = pd.read_csv('../data/wikihowAll.csv')

# Handle missing values in the 'text' column
all_data['text'] = all_data['text'].fillna('')

# Function to extract and preprocess steps
def extract_steps(text):
    # Split text into sentences
    sentences = sent_tokenize(text)
    # Preprocess each sentence
    steps = [re.sub(r'[^A-Za-z\s]', '', sentence).lower().strip() for sentence in sentences]
    return steps

# Apply the extraction to the dataset
all_data['steps'] = all_data['text'].apply(extract_steps)

# Save preprocessed sequences
if not os.path.exists('../preprocessed_data'):
    os.makedirs('../preprocessed_data')

all_data[['title', 'steps']].to_csv('../preprocessed_data/preprocessed_sequences_wikihowAll.csv', index=False)
