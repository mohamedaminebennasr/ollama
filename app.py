from fastapi import FastAPI
from pydantic import BaseModel
import ollama
from qdrant_client import QdrantClient
from qdrant_client.models import Filter

app = FastAPI()

qdrant = QdrantClient(url="http://localhost:6333")

class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask_device_question(request: QueryRequest):
    query_text = request.query

    # Search for relevant documents in Qdrant
    search_results = qdrant.search(
        collection_name="iot_docs",
        query_vector=[0.1] * 512,
        limit=3
    )

    retrieved_text = "\n\n".join([doc.payload["text"] for doc in search_results])

    # AI model generates an answer
    response = ollama.chat(
        #model="deepseek-r1",
        model="mistral", #7b parameter model
        messages=[
            {"role": "system", "content": "Answer user questions based on provided documentation."},
            {"role": "user", "content": f"Docs:\n{retrieved_text}\n\nQuestion: {query_text}"}
        ]
    )

    return {"answer": response["message"]["content"]}
