import streamlit as st
import requests

st.title("Device Documentation Query System")
st.write("Ask any question about device capabilities, configurations, and test plans.")

query = st.text_input("Enter your question:")
if st.button("Ask"):
    if query:
        response = requests.post("http://localhost:8000/ask", json={"query": query})
        st.write("### Answer:")
        st.write(response.json()["answer"])
    else:
        st.warning("Please enter a question.")

