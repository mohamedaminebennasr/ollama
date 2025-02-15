from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint
from langchain_ollama import OllamaEmbeddings

# ✅ Use Ollama for embeddings
embedding_model = OllamaEmbeddings(model="mistral")  # Change model as needed

app = FastAPI()
qdrant = QdrantClient(url="http://localhost:6333")

class QueryRequest(BaseModel):
    query: str

def generate_query_vector(query):
    """Generate a vector embedding for the query using Ollama."""
    return embedding_model.embed_query(query)

@app.post("/ask")
async def ask_device_question(request: QueryRequest):
    query_text = request.query

    try:
        # ✅ Generate query vector using the same model as document embeddings
        query_vector = generate_query_vector(query_text)

        # ✅ Search in Qdrant
        search_results = qdrant.search(
            collection_name="iot_docs",
            query_vector=query_vector,
            limit=3
        )

        if not search_results:
            return {"answer": "No relevant documents found."}

        retrieved_text = "\n\n".join([doc.payload["text"] for doc in search_results if "text" in doc.payload])
        # ✅ AI model generates an answer
        response = ollama.chat(
            model="mistral",
            messages=[
                {"role": "system", "content": "Answer user questions based on provided documentation."},
                {"role": "user", "content": f"Docs:\n{retrieved_text}\n\nQuestion: {query_text}"}
            ],
             options={"temperature": 0}  # Makes responses deterministic
        )

        return {"answer": response["message"]["content"]}

    except Exception as e:
        print(f"❌ Error in /ask: {e}")
        return {"error": "Internal Server Error"}
