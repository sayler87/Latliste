import streamlit as st
import requests

# Sett tittel og layout
st.set_page_config(page_title="Transportsystem", layout="wide")

# URL til den rå HTML-filen på GitHub
GITHUB_RAW_URL = "https://raw.githubusercontent.com/sayler87/Latliste/refs/heads/main/app.html"

# Last ned HTML-innhold fra GitHub
@st.cache_data(ttl=600)  # Cache i 10 minutter
def get_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Kunne ikke laste HTML-filen: {e}")
        return None

# Hent innholdet
html_content = get_html_content(GITHUB_RAW_URL)

if html_content:
    # Fjern Streamlit-padding og stil for bedre visning
    st.markdown(
        """
        <style>
        .block-container { padding: 0; margin: 0; }
        iframe { width: 100%; height: 100vh; border: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Vis HTML via Streamlit-komponent
    st.components.v1.html(html_content, height=1000, scrolling=True)
else:
    st.stop()