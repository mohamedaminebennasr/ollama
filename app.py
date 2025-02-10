from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import ollama

app = FastAPI()

# Load ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="device_docs")

# Define a Pydantic model for the request body
class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask_device_question(request: QueryRequest):
    query_text = request.query

    # Retrieve relevant document snippets
    results = collection.query(query_texts=[query_text], n_results=3)

    # Extract retrieved content correctly
    retrieved_text = "\n\n".join(sum(results["documents"], []))  # Flatten list of lists

    # Send query to DeepSeek via Ollama
    response = ollama.chat(
        model="deepseek-r1",
        messages=[
            {"role": "system", "content": "Answer based on provided documentation."},
            {"role": "user", "content": f"Docs:\n{retrieved_text}\n\nQuestion: {query_text}"}
        ]
    )

    return {"answer": response["message"]["content"]}

