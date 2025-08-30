import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Transportsystem", layout="wide")

st.markdown(
    """
    <style>
    iframe { width: 100%; height: 800px; border: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Vis FastAPI-frontend
st.components.v1.iframe("http://localhost:8000", height=800, scrolling=True)

# Valgfritt: Last opp backup
with st.sidebar:
    st.header("⚙️ Admin")
    uploaded = st.file_uploader("Last opp JSON-backup", type=["json"])
    if uploaded:
        import requests
        files = {"file": uploaded.getvalue()}
        res = requests.post("http://localhost:8000/api/upload", files=files)
        if res.status_code == 200:
            st.success("Backup lastet opp!")
        else:
            st.error(f"Feil: {res.json().get('detail')}")