import streamlit as st
import requests

# Set full-page layout
st.set_page_config(page_title="AI Document Query System", layout="wide")

# Custom CSS for professional styling
st.markdown(
    """
    <style>
    .title-text {
        font-size: 28px;
        font-weight: bold;
        color: #1F2937;
        text-align: center;
    }
    .subtext {
        font-size: 16px;
        color: #4B5563;
        text-align: center;
        margin-bottom: 20px;
    }
    .query-box {
        border: 2px solid #6366F1;
        border-radius: 10px;
        padding: 10px;
    }
    .response-container {
        background-color: #F8F9FA;
        border-left: 5px solid #6366F1;
        padding: 20px;
        border-radius: 8px;
        font-size: 18px;
        color: #333;
        margin-top: 20px;
        box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.1);
        width: 100%;
    }
    .copy-button {
        background-color: #6366F1;
        color: white;
        border: none;
        padding: 8px 15px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        margin-top: 10px;
    }
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #F8F9FA;
        color: #6C757D;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: bold;
        border-top: 1px solid #DEE2E6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header Section
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("logo.png", width=120)

st.markdown('<p class="title-text">AI-Powered Documentation Query</p>', unsafe_allow_html=True)
st.markdown('<p class="subtext">Enter your query below to retrieve relevant information from your documents.</p>', unsafe_allow_html=True)

st.write("---")  # Divider

# Multi-line Input Box
query = st.text_area(
    "🔍 Enter Your Question:",
    height=120,
    placeholder="Type your query here, e.g., 'What are the device configurations?'"
)

# Ask Button Centered
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

            # Full-width response container
            st.markdown('<p class="title-text">📌 AI Response:</p>', unsafe_allow_html=True)
            st.markdown(f'<div class="response-container">{answer}</div>', unsafe_allow_html=True)

            # Copy Button
            st.markdown(
                f'<button class="copy-button" onclick="navigator.clipboard.writeText(`{answer}`)">📋 Copy</button>',
                unsafe_allow_html=True
            )

        else:
            st.warning("⚠️ Please enter a valid query.")

st.write("---")  # Divider

# Footer with Copyright
st.markdown(
    """
    <div class="footer">
        © 2025 IoT Squared. All rights reserved.
    </div>
    """,
    unsafe_allow_html=True
)
