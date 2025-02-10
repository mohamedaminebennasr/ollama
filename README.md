sudo apt update
sudo apt install python3 python3-venv python3-pip -y

#create separate python venv
python3 -m venv myenv
source myenv/bin/activate

#install native ollama
curl -fsSL https://ollama.com/install.sh | sh

#install open-webui docker
docker stop open-webui
docker rm open-webui
sudo docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
#note: you need to point to ollma 127.0.0.1:11436 in open-webui
#Intall this package to be able to implemente your python script
#install deepseek-r1 by using the UI open-webui

pip install ollama langchain chromadb pdfminer.six fastapi uvicorn sentence-transformers

uvicorn app:app --host 0.0.0.0 --port 8000 --reload
#Run the script to index documents:
python process_docs.py

curl -X 'POST' \
  'http://localhost:8000/ask' \
  -H 'Content-Type: application/json' \
  -d '{"query": "How do I configure Device X for LTE?"}'


#to have a user interface
pip install streamlit
streamlit run query_ui.py






