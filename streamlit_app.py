import streamlit as st
import base64

# Tittel på Streamlit-appen (vises i fanen, ikke nødvendigvis i UI)
st.set_page_config(page_title="Transportsystem", layout="wide")

# Les inn HTML-filen
def read_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

# Sti til HTML-filen
html_file_path = "app.html"

try:
    html_content = read_html_file(html_file_path)

    # Injiser CSS for å fjerne Streamlit-meny og padding
    st.markdown(
        """
        <style>
        /* Fjern Streamlit-standard padding */
        .block-container {
            padding: 0;
            margin: 0;
        }
        iframe {
            width: 100%;
            height: 100vh;
            border: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Vis HTML-filen via iframe (anbefalt for bedre kompatibilitet med JS/CSS)
    st.components.v1.html(html_content, height=1000, scrolling=True)

except FileNotFoundError:
    st.error("❌ Kunne ikke finne `app.html`. Sørg for at filen ligger i samme mappe som dette scriptet.")
except Exception as e:
    st.error(f"❌ En feil oppstod ved lasting av HTML: {e}")