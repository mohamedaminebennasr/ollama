from kafka import KafkaProducer, KafkaConsumer
import json
import os
import time
import pdfminer.high_level
from PIL import Image
import pytesseract
import docx
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import hashlib
import uuid  # Import UUID library
from qdrant_client.models import Distance, VectorParams
from kafka.admin import KafkaAdminClient
from langchain_ollama import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import hashlib
import logging
from sklearn.decomposition import PCA
import numpy as np
import threading



# ✅ Pre-train PCA on random sample data before using it
pca = PCA(n_components=512)

def train_pca():
    """Train PCA with random sample data (required for dimensionality reduction)."""
    sample_vectors = np.random.rand(1000, 4096)  # Generate 1000 random 4096-d vectors
    pca.fit(sample_vectors)  # ✅ Fit PCA on sample data

train_pca()  # 🔥 Ensure PCA is trained before using it

def reduce_vector(vector, target_dim=512):
    """Reduce a vector's dimensionality using PCA."""
    if len(vector) != 4096:
        print(f"⚠️ Unexpected vector size: {len(vector)} (Expected: 4096)")
        return vector  # Return original if incorrect size

    vector_reshaped = np.array(vector).reshape(1, -1)  # ✅ Reshape to 2D array
    reduced_vector = pca.transform(vector_reshaped)[0]  # ✅ Apply PCA

    return reduced_vector  # Return reduced 512-d vector
    

def get_doc_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def document_exists(text):
    """Check if a document with the same hash already exists in Qdrant."""
    doc_hash = get_doc_hash(text)

    response = qdrant.query_points(
        collection_name="iot_docs",
        query_filter={"must": [{"key": "hash", "match": {"value": doc_hash}}]},  # ✅ Corrected: Use `query_filter`
        limit=1,
        with_payload=True
    )

    # ✅ Correct way to check for results
    return len(response.result) > 0  # 🔥 Use `.result` instead of `["result"]`


# ✅ Configure logging to store errors in 'app.log'
logging.basicConfig(filename="app.log", level=logging.ERROR, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Kafka Configuration
KAFKA_BROKER = "127.0.0.1:9092"
TOPIC = "document-uploads"
DOCUMENTS_DIR = "/home/ai-bench/Documents/Data"

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    retries=5,
    acks='all',
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Initialize Kafka Consumer (DO NOT run this in a separate thread)
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id="my-group",
    auto_offset_reset="earliest",  # Start from the beginning
    enable_auto_commit=False,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

# Connect to Qdrant for indexing
qdrant = QdrantClient(url="http://localhost:6333")

# Track processed files
processed_files = set()

# Function to send new document events to Kafka
PROCESSED_LOG = "processed_files.log"

def load_processed_files():
    """ Load processed file list from disk """
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_processed_file(file_path):
    """ Save processed file to disk """
    with open(PROCESSED_LOG, "a") as f:
        f.write(file_path + "\n")

# Producer: Detect new files and send to Kafka
def send_new_documents():
    processed_files = load_processed_files()  # Load from log

    while True:
        for root, _, files in os.walk(DOCUMENTS_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[-1].lower()
                
                if file_path not in processed_files and ext in [".pdf", ".docx", ".txt", ".png", ".jpg", ".xlsx"]:
                    event_data = {"file_path": file_path, "file_name": file}
                    print(f"📤 Sending to Kafka: {event_data}")  # 🔥 Debug log
                    future = producer.send(TOPIC, event_data)
                    result = future.get(timeout=10)  # ✅ Ensure the message is sent successfully
                    processed_files.add(file_path)
                    save_processed_file(file_path)  # Save to log
                    print(f"📤 Sent to Kafka: {file}")

        time.sleep(5)  # Adjust interval as needed

# Function to extract text from documents
def extract_text(file_path, ext, file_name):
    
    try:
        print(f"🔍 Extracting text from {file_name} (Type: {ext})")  # ✅ Now file_name is passed correctly
        
        if ext == ".pdf":
            text = pdfminer.high_level.extract_text(file_path)
        elif ext in [".jpg", ".png"]:
            text = pytesseract.image_to_string(Image.open(file_path))
        elif ext == ".docx":
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext == ".xlsx":
            df = pd.read_excel(file_path, engine="openpyxl")
            text = "\n".join(df.astype(str).apply(lambda x: " | ".join(x), axis=1))
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            print(f"⚠️ Unsupported file type: {file_path} → Skipping!")
            return None  # Return None for unsupported files
        
        print(f"📄 Extracted {len(text)} characters from {file_name}")
        return text
    except Exception as e:
        print(f"❌ Error extracting text from {file_path}: {e}")
        return None


# Function to process documents from Kafka events (Runs in main thread)

def ensure_qdrant_collection():
    """
    Ensure the Qdrant collection exists before inserting documents.
    """
    collection_name = "iot_docs"
    existing_collections = qdrant.get_collections().collections
    collection_names = [col.name for col in existing_collections]

    if collection_name not in collection_names:
        print(f"⚠️ Collection '{collection_name}' not found in Qdrant. Creating it now...")

        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)  # Match vector size to embeddings
        )
        print(f"✅ Collection '{collection_name}' created successfully!")
    else:
        print(f"✅ Collection '{collection_name}' already exists.")

# ✅ Initialize Ollama Embeddings
embedding_model = OllamaEmbeddings(model="mistral")  # Change model as needed	

def generate_document_vector(text):
    """Convert document text into an embedding using Ollama."""
    return embedding_model.embed_query(text)

def split_text(text):
    """Splits long text into smaller chunks for better embedding and retrieval performance."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)
    return text_splitter.split_text(text)
        
def process_documents():
    print("🟢 Listening for new documents from Kafka...")

    # ✅ Ensure Qdrant collection exists
    ensure_qdrant_collection()

    while True:
        try:
            for message in consumer:
                file_data = message.value
                file_path = file_data["file_path"]
                file_name = file_data["file_name"]
                ext = os.path.splitext(file_name)[-1].lower()

                print(f"📥 Received Kafka message: {file_name}")

                text = extract_text(file_path, ext, file_name)

                if text and text.strip():
                    doc_hash = get_doc_hash(text)  # 🔥 Generate hash of the document

                    # 🔥 **Check if the document is already indexed**
                    #if document_exists(doc_hash):
                    #    print(f"⚠️ Duplicate document skipped: {file_name}")
                    #    continue  # ✅ Skip indexing duplicate documents
                    # 🔥 **Split the text into smaller chunks**
                    text_chunks = split_text(text)
                    
                    for chunk in text_chunks:
                        doc_id = str(uuid.uuid4())  # Generate unique document ID for each chunk
                        vector = generate_document_vector(chunk)  # ✅ Generate embedding for chunk
                        #print(f"🔍 Original vector dimension: {len(vector)}")  # 🔥 Debugging step
                        vector = reduce_vector(vector, 512)  # ✅ Reduce to 512 dimensions
                        #print(f"✅ Reduced vector dimension: {len(vector)}")  # 🔥 Confirm PCA worked
                        
                        # ✅ Store in Qdrant with chunked text and document hash
                        qdrant.upsert(
                            collection_name="iot_docs",
                            points=[PointStruct(id=doc_id, vector=vector, payload={"text": chunk, "filename": file_name, "hash": doc_hash})]
                        )

                    print(f"✅ Indexed {len(text_chunks)} chunks from: {file_name}")
                    # 🔥 **Manually commit Kafka offset after successful processing**
                    consumer.commit()
                                        
                else:
                    print(f"⚠️ Skipped empty document: {file_name}")

        except Exception as e:
            logging.error(f"❌ Kafka consumer error: {e}")
            print("🔄 Restarting consumer in 5 seconds...")
            time.sleep(5)  # Wait before restarting the loop

# Run producer and consumer separately in the main execution flow
if __name__ == "__main__":
    print("📡 Monitoring directory and processing documents...")
    # Run Kafka producer in a separate thread
    producer_thread = threading.Thread(target=send_new_documents, daemon=True)
    producer_thread.start()
    # Run Kafka consumer in the main thread
    process_documents()
