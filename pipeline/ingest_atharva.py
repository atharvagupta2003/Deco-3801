from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import os

embeddings = NVIDIAEmbeddings(
    model="nv-embedqa-e5-v5",
    api_key=os.environ.get("nvidia_api_key"),
    truncate="NONE",
)
# Test with a small text sample
try:
    test_embedding = embeddings.embed_query("Sample text")
    print("Test successful!")
except Exception as e:
    print(f"Embedding failed: {e}")
