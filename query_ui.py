import streamlit as st
import requests

# 🔹 Set page title & layout
st.set_page_config(page_title="AI Document Query System", layout="centered")

# 🔹 Custom CSS for Professional UI
st.markdown(
    """
    <style>
    body {
        font-family: 'Arial', sans-serif;
        background-color: #f8f9fa;
    }
    .title-text {
        font-size: 28px;
        font-weight: 700;
        color: #1F2937;
        text-align: center;
    }
    .subtext {
        font-size: 16px;
        color: #4B5563;
        text-align: center;
    }
    .query-box {
        border: 2px solid #6366F1;
        border-radius: 10px;
        padding: 10px;
    }
    .response-box {
        background-color: #F3F4F6;
        border-left: 5px solid #6366F1;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🔹 Header Section (Logo + Title)
col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    st.image("logo.png", width=120)

st.markdown('<p class="title-text">AI-Powered Documentation Query</p>', unsafe_allow_html=True)
st.markdown('<p class="subtext">Enter your query below to find relevant information from your documents.</p>', unsafe_allow_html=True)

st.write("---")  # Divider

# 🔹 Multi-line Input Box with Placeholder
query = st.text_area(
    "🔍 Enter Your Question:",
    height=180,
    placeholder="Type your query here, e.g., 'What are the device configurations?'"
)

# 🔹 Ask Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔎 Ask AI", use_container_width=True):
        if query.strip():
            with st.spinner("⏳ Processing your request..."):
                try:
                    response = requests.post("http://localhost:8000/ask", json={"query": query})
                    answer = response.json().get("answer", "No response received.")
                except requests.exceptions.RequestException:
                    answer = "⚠️ Error: Could not connect to the AI service."

            # 🔹 Display AI Response
            st.markdown('<p class="title-text">📌 AI Response:</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-box">{answer}</div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Please enter a valid query.")

st.write("---")  # Divider
st.markdown('<p class="subtext">🔹 AI-Powered by Open-Source LLMs | Built for Scalable Document Search</p>', unsafe_allow_html=True)


st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #F8F9FA;  /* Light theme background */
        color: #6C757D;  /* Text color to match page */
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        border-top: 1px solid #DEE2E6; /* Subtle top border for separation */
    }
    </style>
    <div class="footer">
        © 2025 iot squared. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
