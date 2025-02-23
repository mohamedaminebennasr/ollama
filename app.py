from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint
from langchain_ollama import OllamaEmbeddings
import logging

from sklearn.decomposition import PCA
import numpy as np

# ✅ Pre-train PCA on random sample data before using it
pca = PCA(n_components=512)

def train_pca():
    """Train PCA with random sample data (required for dimensionality reduction)."""
    sample_vectors = np.random.rand(1000, 4096)  # Generate 1000 random 4096-d vectors
    pca.fit(sample_vectors)  # ✅ Fit PCA on sample data

train_pca()  # 🔥 Ensure PCA is trained before using it


# ✅ Configure logging to store errors in 'app.log'
logging.basicConfig(filename="app.log", level=logging.ERROR, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Use Ollama for embeddings
embedding_model = OllamaEmbeddings(model="mistral")  # Change model as needed

app = FastAPI()
qdrant = QdrantClient(url="http://localhost:6333")


# Get all documents in the collection
collection_info = qdrant.count(collection_name="iot_docs")
print(f"Total documents in Qdrant: {collection_info.count}")

class QueryRequest(BaseModel):
    query: str

def generate_query_vector(query):
    """Generate a vector embedding for the query using Ollama and reduce to 512 dimensions."""
    vector = embedding_model.embed_query(query)  # 4096-dimensional vector

    if len(vector) != 4096:
        print(f"⚠️ Unexpected query vector size: {len(vector)} (Expected: 4096)")
        return vector  # Return original if incorrect size

    vector_reshaped = np.array(vector).reshape(1, -1)  # ✅ Reshape to 2D
    reduced_vector = pca.transform(vector_reshaped)[0]  # ✅ Apply PCA

    return reduced_vector.tolist()  # ✅ Return reduced 512-d vector


@app.post("/ask")
async def ask_device_question(request: QueryRequest):
    query_text = request.query

    try:
        # ✅ Generate query vector using the same model as document embeddings
        query_vector = generate_query_vector(query_text)

        # 🔥 **Improved Hybrid Search (Vector + Metadata Filtering)**
        search_results = qdrant.search(
            collection_name="iot_docs",
            query_vector=query_vector,
            limit=100,  # Adjust based on your needs
            with_payload=True,  # ✅ Retrieve full metadata
            #filter={  
             #   "must": [
              #      {"key": "category", "match": {"value": "iot"}}  # Example category filter
               # ]
            #}
        )

        if not search_results:
            return {"answer": "No relevant documents found."}

        # ✅ Extract relevant document text
        retrieved_text = "\n\n".join([doc.payload["text"] for doc in search_results if "text" in doc.payload])

        # ✅ Use AI model (Ollama Mistral) to generate an answer
        response = ollama.chat(
            model="mistral",
            messages=[
                {"role": "system", "content": "Answer user questions based on provided documentation."},
                {"role": "user", "content": f"Docs:\n{retrieved_text}\n\nQuestion: {query_text}"}
            ],
            options={"temperature": 0}  # ✅ Keep responses deterministic
        )

        return {"answer": response["message"]["content"]}

    except Exception as e:
        logging.error(f"❌ Error in /ask: {e}")
        return {"error": "Internal Server Error"}

