import os
import pdfminer.high_level
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_ollama import OllamaEmbeddings
import chromadb

# Directory where your documents are stored
DOCUMENTS_DIR = "/home/ai-bench/Documents"

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="device_docs")

# Load embedding model
#embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
embedding_model = OllamaEmbeddings(model="deepseek-r1")
# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    return pdfminer.high_level.extract_text(pdf_path)

# Process all PDFs in the directory
for filename in os.listdir(DOCUMENTS_DIR):
    if filename.endswith(".pdf"):
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        text = extract_text_from_pdf(file_path)
        
        # Split text into smaller chunks (e.g., 500-character chunks)
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        
        # Add to ChromaDB
        collection.add(
            documents=chunks,
            metadatas=[{"source": filename}] * len(chunks),
            ids=[f"{filename}-{i}" for i in range(len(chunks))]
        )

print("Documents successfully indexed!")

