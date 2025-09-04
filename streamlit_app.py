import streamlit as st
import requests

# Sett tittel og layout
st.set_page_config(page_title="Transportsystem", layout="wide")

# URL til den rå HTML-filen på GitHub
GITHUB_RAW_URL = "https://raw.githubusercontent.com/sayler87/Latliste/refs/heads/main/app.4.html"

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

@st.cache_data(show_spinner=False, ttl=2)
def count_summary(day: str):
    ...

@st.cache_data(show_spinner=False, ttl=2)
def get_rows(day: str, where_sql: str, where_args: tuple, order_sql: str):
    ...

@st.cache_data(show_spinner=False, ttl=2)
def export_day(day: str):
    ...

def invalidate_caches():
    count_summary.clear()
    get_rows.clear()
    export_day.clear()