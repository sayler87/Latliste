import streamlit as st
from pathlib import Path

st.set_page_config(page_title="AvgangListe", layout="wide")

# Učitaj HTML fajl
html_file = Path("AvgangListe.html")
if not html_file.exists():
st.error("Nedostaje AvgangListe.html u repozitoriju")
else:
html_code = html_file.read_text(encoding="utf-8")
st.components.v1.html(html_code, height=900, scrolling=True)
