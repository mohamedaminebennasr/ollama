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

# Kafka Configuration
KAFKA_BROKER = "localhost:9092"
TOPIC = "document-uploads"
DOCUMENTS_DIR = "/home/ai-bench/Documents"

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Initialize Kafka Consumer (DO NOT run this in a separate thread)
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    group_id="my-group",
    auto_offset_reset="earliest",  # Start from the beginning
    enable_auto_commit=True,
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
                    producer.send(TOPIC, event_data)
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


# Reset Kafka Consumer Offsets
def reset_consumer_offsets():
    print("🔄 Resetting Kafka consumer offsets...")
    try:
        admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BROKER)
        admin_client.delete_consumer_groups(["my-group"])  # Deletes the consumer group
        print("✅ Kafka Consumer Group Reset Successfully. Offsets will reset to 'earliest'.")
    except Exception as e:
        print(f"❌ Error resetting Kafka consumer offsets: {e}")



def process_documents():
    print("🟢 Listening for new documents from Kafka...")

    # Ensure Qdrant collection exists
    ensure_qdrant_collection()

    while True:
        try:
            for message in consumer:
                file_data = message.value
                print(f"📥 Received Kafka message: {file_data['file_name']}")  # Only file name

                file_path = file_data["file_path"]
                file_name = file_data["file_name"]

                ext = os.path.splitext(file_name)[-1].lower()
                text = extract_text(file_path, ext, file_name)
                if text.strip():
                    doc_id = str(uuid.uuid4())  # Use UUIDs for Qdrant compatibility

                    # Store extracted text in Qdrant
                    print(f"🚀 Storing in Qdrant: {file_name}")
                    qdrant.upsert(
                        collection_name="iot_docs",
                        points=[
                            PointStruct(id=doc_id, vector=[0.1] * 512, payload={"text": text, "filename": file_name})
                        ]
                    )
                    print(f"✅ Indexed: {file_name}")
                else:
                    print(f"⚠️ Skipped empty document: {file_name}")

        except Exception as e:
            print(f"❌ Kafka consumer error: {e}")
            print("🔄 Restarting consumer in 5 seconds...")
            time.sleep(5)  # Wait before restarting the loop
            

# Run producer and consumer separately in the main execution flow
if __name__ == "__main__":
    print("📡 Monitoring directory and processing documents...")
    # Call offset reset function BEFORE starting the consumer loop
    reset_consumer_offsets()
    # Start producer loop in a separate process
    from multiprocessing import Process
    producer_process = Process(target=send_new_documents, daemon=True)
    producer_process.start()

    # Run Kafka consumer in the main thread
    process_documents()
