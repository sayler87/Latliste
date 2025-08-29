import streamlit as st
from pathlib import Path

st.set_page_config(page_title="AvgangListe", layout="wide")

html_file = Path("registrer_avganger04.html")
if not html_file.exists():
    st.error("registrer_avganger04.html")
else: 
 html_code = html_file.read_text(encoding="utf-8")
 st.components.v1.html(html_code, height=900, scrolling=True)

st.caption("")
