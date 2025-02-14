from kafka import KafkaProducer
import json
import os
from kafka import KafkaConsumer
import json
import requests
import pdfminer.high_level
from PIL import Image
import pytesseract
import docx
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import hashlib

KAFKA_BROKER = "localhost:9092"
TOPIC = "document-uploads"

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

DOCUMENTS_DIR = "/home/ai-bench/Documents"

# Scan and send new document events to Kafka
def send_new_documents():
    for root, _, files in os.walk(DOCUMENTS_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[-1].lower()
            if ext in [".pdf", ".docx", ".txt", ".png", ".jpg", ".xlsx"]:
                event_data = {"file_path": file_path, "file_name": file}
                producer.send(TOPIC, event_data)
                print(f"📤 Sent to Kafka: {file}")

# Connect to Qdrant for vector search
qdrant = QdrantClient(url="http://localhost:6333")

# Function to extract text from PDFs
def extract_text_from_pdf(file_path):
    return pdfminer.high_level.extract_text(file_path)

# Function to extract text from images using OCR
def extract_text_from_image(file_path):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

# Function to extract text from Word documents
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs])

# Function to extract text from Excel files
def extract_text_from_xlsx(file_path):
    df = pd.read_excel(file_path, engine="openpyxl")
    return "\n".join(df.astype(str).apply(lambda x: " | ".join(x), axis=1))

# Process incoming documents from Kafka
for message in consumer:
    file_data = message.value
    file_path = file_data["file_path"]
    file_name = file_data["file_name"]

    text = ""
    ext = os.path.splitext(file_name)[-1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext in [".jpg", ".png"]:
        text = extract_text_from_image(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    elif ext == ".xlsx":
        text = extract_text_from_xlsx(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

    if text.strip():
        # Generate document ID
        doc_id = hashlib.sha256(file_name.encode()).hexdigest()

        # Store document text embeddings in Qdrant
        qdrant.upsert(
            collection_name="iot_docs",
            points=[
                PointStruct(id=doc_id, vector=[0.1] * 512, payload={"text": text, "filename": file_name})
            ]
        )
        print(f"✅ Indexed: {file_name}")

if __name__ == "__main__":
    send_new_documents()
