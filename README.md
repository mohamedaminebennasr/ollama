#create separate python venv
pip install ollama langchain chromadb pdfminer.six fastapi uvicorn sentence-transformers

Install ollama
Install deepseek-r1

uvicorn app:app --host 0.0.0.0 --port 8000 --reload


#Run the script to index documents:
python process_docs.py

curl -X 'POST' \
  'http://localhost:8000/ask' \
  -H 'Content-Type: application/json' \
  -d '{"query": "How do I configure Device X for LTE?"}'


  pip install streamlit


