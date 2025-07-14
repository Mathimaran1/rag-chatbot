import streamlit as st
from openai import OpenAI
import docx
import PyPDF2
import pandas as pd
import os

# ---- Streamlit Page Config ----
st.set_page_config(page_title="📚 RAG Chatbot", layout="wide")

# ---- Styling ----
st.markdown("""
    <style>
        .main-title {
            text-align: center;
            font-size: 38px;
            font-weight: bold;
            color: #333;
            margin-top: 1rem;
        }
        .chat-box {
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 10px;
            background-color: #f1f1f1;
        }
        .user-msg {
            background-color: #d1f7c4;
            align-self: flex-end;
        }
        .assistant-msg {
            background-color: #fff;
            align-self: flex-start;
        }
    </style>
""", unsafe_allow_html=True)

# ---- Header ----
st.markdown("<div class='main-title'>💬 General Chatbot with Document Upload</div>", unsafe_allow_html=True)
st.caption("Powered by Meta-LLaMA-3.1-8B via SambaNova | With RAG")

# ---- API Setup ----
api_key = "dbe981d7-9c3a-42d6-9333-2e9be5c446ad"  # Replace with os.getenv("API_KEY") for deployment
base_url = "https://api.sambanova.ai/v1"
client = OpenAI(api_key=api_key, base_url=base_url)

# ---- Session State Initialization ----
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": "You are a helpful assistant."}]

# ---- Sidebar: Upload Files ----
st.sidebar.header("📂 Upload Reference Files")
uploaded_files = st.sidebar.file_uploader(
    "Supported formats: .docx, .pdf, .txt, .csv",
    type=["docx", "pdf", "txt", "csv"],
    accept_multiple_files=True
)

# ---- RAG: Extract Content ----
rag_docs = ""
if uploaded_files:
    all_texts = []
    for file in uploaded_files:
        try:
            if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(file)
                text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            elif file.type == "application/pdf":
                reader = PyPDF2.PdfReader(file)
                text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif file.type == "text/plain":
                text = file.read().decode("utf-8")
            elif file.type == "text/csv":
                df = pd.read_csv(file)
                text = df.to_string(index=False)
            else:
                text = ""
            all_texts.append(text)
        except Exception as e:
            st.sidebar.error(f"Error reading {file.name}: {e}")
    rag_docs = "\n\n".join(all_texts)
    st.sidebar.success("✅ Documents loaded successfully!")

# ---- Display Chat History ----
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# ---- Chat Input + Logic ----
user_input = st.chat_input("💬 Type your question here...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤖 Thinking..."):
            try:
                full_prompt = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "system", "content": f"Reference document:\n{rag_docs}"}
                ] + st.session_state.chat_history

                response = client.chat.completions.create(
                    model="Meta-Llama-3.1-8B-Instruct",
                    messages=full_prompt,
                    temperature=0.3,
                    top_p=1.0
                )

                reply = response.choices[0].message.content
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"❌ Error from model: {e}")

# ---- Clear Chat Button ----
with st.sidebar:
    if st.button("🧹 Clear Chat"):
        st.session_state.chat_history = [{"role": "system", "content": "You are a helpful assistant."}]
        st.rerun()
