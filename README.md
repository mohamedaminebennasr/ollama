
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






