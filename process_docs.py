import os
import time
import zipfile
import pdfminer.high_level
import pytesseract
from PIL import Image
import pandas as pd
from pdfminer.pdfdocument import PDFNoValidXRef
from pdfminer.psparser import PSEOF
from langchain_ollama import OllamaEmbeddings
import chromadb
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Directory where documents are stored
DOCUMENTS_DIR = "/home/ai-bench/Documents"

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="device_docs")

# Load embedding model
embedding_model = OllamaEmbeddings(model="deepseek-r1")

# Allowed file types
SUPPORTED_FILE_TYPES = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".xlsx", ".xls", ".txt", ".zip"}

# Function to extract ZIP files (Prevents Infinite Recursion)
def extract_zip(zip_path, extract_to):
    extracted_folder = os.path.join(extract_to, os.path.basename(zip_path).replace(".zip", ""))
    
    # Check if already extracted to avoid infinite recursion
    if os.path.exists(extracted_folder):
        print(f"🔹 Skipping already extracted ZIP: {zip_path}")
        return extracted_folder

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder)
        print(f"✅ Extracted: {zip_path} to {extracted_folder}")
        return extracted_folder
    except Exception as e:
        print(f"⚠️ Error extracting ZIP file {zip_path}: {e}")
        return None

# OCR: Extract text from images
def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        print(f"⚠️ Error extracting text from image {image_path}: {e}")
        return ""

# Extract text from PDFs (handles corrupt PDFs)
def extract_text_from_pdf(pdf_path):
    try:
        return pdfminer.high_level.extract_text(pdf_path)
    except (PDFNoValidXRef, PSEOF):
        print(f"⚠️ Warning: Skipping corrupt PDF {pdf_path}")
        return ""
    except Exception as e:
        print(f"⚠️ Error processing PDF {pdf_path}: {e}")
        return ""

# Extract text from Excel files
def extract_text_from_xlsx(xlsx_path):
    try:
        df = pd.read_excel(xlsx_path, engine="openpyxl")
        return "\n".join(df.astype(str).apply(lambda x: " | ".join(x), axis=1))
    except Exception as e:
        print(f"⚠️ Error extracting text from Excel file {xlsx_path}: {e}")
        return ""

# Extract text from text files
def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"⚠️ Error extracting text from TXT file {txt_path}: {e}")
        return ""

# Process a directory (recursive search but avoids infinite loops)
def process_directory(directory):
    for root, _, files in os.walk(directory):  # Recursively iterate through directories
        for file in files:
            file_path = os.path.join(root, file)
            process_document(file_path)  # Process each file

# Process a new document
def process_document(file_path):
    _, ext = os.path.splitext(file_path)

    # Skip unsupported file types
    if ext.lower() not in SUPPORTED_FILE_TYPES:
        print(f"⚠️ Skipping unsupported file: {file_path}")
        return

    text = ""

    if ext == ".zip":
        extracted_folder = extract_zip(file_path, os.path.dirname(file_path))
        if extracted_folder:
            process_directory(extracted_folder)  # Process extracted files
        return  # Skip indexing ZIP itself

    elif ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".tiff"]:
        text = extract_text_from_image(file_path)
    elif ext in [".xlsx", ".xls"]:
        text = extract_text_from_xlsx(file_path)
    elif ext == ".txt":
        text = extract_text_from_txt(file_path)

    if text.strip():
        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        collection.add(
            documents=chunks,
            metadatas=[{"source": os.path.basename(file_path)}] * len(chunks),
            ids=[f"{os.path.basename(file_path)}-{i}" for i in range(len(chunks))]
        )
        print(f"✅ Indexed: {file_path}")
    else:
        print(f"⚠️ Skipped empty document: {file_path}")

# Watch for new files and index them (real-time monitoring)
class DocumentHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            process_document(event.src_path)

if __name__ == "__main__":
    # Process all existing files at startup
    print(f"📢 Scanning {DOCUMENTS_DIR} for existing documents...")
    process_directory(DOCUMENTS_DIR)

    # Start watchdog for live monitoring
    event_handler = DocumentHandler()
    observer = Observer()
    observer.schedule(event_handler, DOCUMENTS_DIR, recursive=True)
    observer.start()

    print(f"📢 Watching {DOCUMENTS_DIR} for new documents...")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
