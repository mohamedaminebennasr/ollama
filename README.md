
This repository has 3 files:

1- app.py: Backend using FastAPI

2- process_docs.py: to index your documentation (RAG pipeline)

3- query_ui.py: Frontend using streamlit. The UI created will be used to send the command to the backend

#Note: Why installing ollama package in python and also ollama natively using curl -fsSL https://ollama.com/install.sh | sh?

#The Python package ollama (which you already have in requirements.txt) only provides a client to communicate with the Ollama runtime.
#The actual Ollama engine (native one) needs to be installed separately to run models like deepseek-r1.
#Without installing the Ollama runtime, your application won't be able to load or run DeepSeek models.

sudo apt update

sudo apt install python3 python3-venv python3-pip -y

#create separate python venv

python3 -m venv myenv

source myenv/bin/activate

#Install native ollama

curl -fsSL https://ollama.com/install.sh | sh

#Install open-webui docker

docker stop open-webui

docker rm open-webui

rm -rf ~/.open-webui  # ⚠️ WARNING: This resets Open WebUI's settings!

sudo docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main

#Note: you need to point to ollama 127.0.0.1:11434 in open-webui (open Settings->...)

#Intall this package to be able to implement your python script

#pip install ollama langchain chromadb pdfminer.six fastapi uvicorn sentence-transformers

#pip install -r requirements.txt

#Install deepseek-r1 by using the UI open-webui or vi CLI: ollama pull deepseek-r1 and in this case you don't need open-webui

#To start your backend app.py

uvicorn app:app --host 0.0.0.0 --port 8000 --reload

#Use uvicorn app:app --reload after any modification of app.py if needed.

#Run the script to index documents:

python process_docs.py

#Test via CLI using:

curl -X 'POST' 'http://localhost:8000/ask' -H 'Content-Type: application/json' -d '{"query": "How do I configure Device X for LTE?"}'

#To have a UI from where you will ask your model

pip install streamlit

streamlit run query_ui.py

#You can launch your UI using Streamlit (`query_ui.py`). From this interface, you can send requests to the backend (`app.py`), which will then trigger the Ollama chat using the DeepSeek-R1 model.


#Potential Enhancement

#1. Infrastructure Considerations
#Deploy FastAPI with Uvicorn + Gunicorn for scalability:
#bash
#Copy
#Edit
#pip install gunicorn
#Then, run:
#bash
#Copy
#Edit
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
#Use a persistent database for document storage instead of ChromaDB if needed.
#2. Security Enhancements
#Enable CORS in FastAPI if accessed from different frontends:
#python
#Copy
#Edit
#from fastapi.middleware.cors import CORSMiddleware
#
#app.add_middleware(
#    CORSMiddleware,
#    allow_origins=["*"],  # Adjust as needed
#    allow_credentials=True,
#    allow_methods=["*"],
#    allow_headers=["*"],
#)
#Limit API access with authentication (e.g., API keys, OAuth).
#3. Handling Large-Scale Data
#Optimize ChromaDB indexing:
#Increase memory allocation
#Fine-tune retrieval parameters (n_results)
#Chunk larger documents efficiently to improve retrieval performance.
#4. Deployment & Automation
#Run as a service (Systemd, Docker, or Kubernetes):
#Dockerize for consistent deployments:
#dockerfile
#Copy
#Edit
#FROM python:3.10
#WORKDIR /app
#COPY . .
#RUN pip install --no-cache-dir -r requirements.txt
#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
#Use CI/CD to automate updates.
#5. Monitoring & Logging
#Enable logging for API requests:
#python
#Copy
#Edit
#import logging
#logging.basicConfig(level=logging.INFO)
#Monitor with Prometheus/Grafana for real-time insights.

#Gunicorn: Production ASGI Server for FastAPI
#Gunicorn (Green Unicorn) is a Python WSGI/ASGI HTTP Server used to serve FastAPI applications efficiently in production environments. While uvicorn is great for development, Gunicorn adds:
#
#Process management (spawning multiple workers for better performance)
#Stability (automatic restarts, graceful shutdowns)
#Scalability (handles multiple requests concurrently)
#Why Use Gunicorn with FastAPI?
#Performance: Gunicorn can run multiple worker processes, handling more requests in parallel.
#Reliability: If one worker crashes, Gunicorn will restart it.
#Production-ready: Many cloud services and servers (like Nginx, Kubernetes, AWS, and Docker) support Gunicorn for deployment.
#How to Install Gunicorn
#Since Gunicorn is not in your requirements.txt, add it manually:
#
#bash
#Copy
#Edit
#pip install gunicorn
#Or update your requirements.txt:
#
#plaintext
#Copy
#Edit
#gunicorn
#Running FastAPI with Gunicorn
#To serve your FastAPI app (app.py) efficiently, use:
#
#bash
#Copy
#Edit
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
#Breakdown of the Command:
#gunicorn → Starts Gunicorn.
#-w 4 → Runs 4 worker processes (adjust based on CPU cores).
#-k uvicorn.workers.UvicornWorker → Uses Uvicorn as an ASGI worker to serve FastAPI.
#app:app → app.py file, app is the FastAPI instance.
#Advanced Gunicorn Configurations
#Run on Specific Port
#
#bash
#Copy
#Edit
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app:app
#Run in the Background (Daemon Mode)
#
#bash
#Copy
#Edit
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app:app --daemon
#Auto-restart on Changes (for Development)
#
#bash
#Copy
#Edit
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker --reload app:app
#Logging & Timeout Handling
#
#bash
#Copy
#Edit
#gunicorn -w 4 -k uvicorn.workers.UvicornWorker --timeout 120 --log-level info app:app
#Using Gunicorn with Docker
#If you deploy your app with Docker, use this Dockerfile:
#
#dockerfile
#Copy
#Edit
#FROM python:3.10
#WORKDIR /app
#COPY . .
#RUN pip install --no-cache-dir -r requirements.txt
#CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app:app"]





