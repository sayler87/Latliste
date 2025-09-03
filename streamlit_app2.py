import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# --- Konfig ---
st.set_page_config(page_title="🚛 Transportsystem", layout="wide")
GITHUB_RAW_URL = "https://raw.githubusercontent.com/sayler87/Latliste/main/app.html"

# --- Datakilde (her brukes JSON-fil i appen, men kan være database) ---
DATA_FILE = "departures.json"

@st.cache_data(ttl=60)
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    # Invalidér cache
    st.cache_data.clear()

# --- Hent og modifiser HTML ---
@st.cache_data(ttl=600)
def fetch_and_patch_html(url, departures):
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_text = response.text

        # Parse HTML
        soup = BeautifulSoup(html_text, "html.parser")

        # Finn tabellens tbody
        tbody = soup.find("tbody")
        if not tbody:
            return html_text

        # Tøm eksisterende rader
        tbody.clear()

        # Lag nye rader fra Streamlit-data
        type_icons = {
            "Tog": "🚂",
            "Bil": "🚗",
            "Tralle": "🛒",
            "Modul": "📦"
        }
        for d in departures:
            tr = soup.new_tag("tr")
            tc = "#e74c3c" if d["type"] == "Tog" else "#f312e8" if d["type"] == "Bil" else "#3498db" if d["type"] == "Tralle" else "#9b59b6"
            sc = "#27ae60" if d["status"] == "LEVERT" else "#3498db" if d["status"] == "LAGER" else "#f39c12"

            tr.append(BeautifulSoup(f"""
                <td>{d['unitNumber']}</td>
                <td>{d['destination']}</td>
                <td>{d['time']}</td>
                <td>{d['gate']}</td>
                <td><span class="type-icon">{type_icons.get(d['type'], '📦')}</span><span style="color:{tc};font-weight:bold">{d['type']}</span></td>
                <td><span style="color:{sc};font-weight:bold">{d['status']}</span></td>
                <td>{d.get('comment', '<em>Ingen</em>')}</td>
                <td class="action-buttons">
                  <button class="btn btn-secondary" onclick="editDeparture({d['id']})">✏️</button>
                  <button class="btn btn-danger" onclick="deleteDeparture({d['id']})">🗑️</button>
                </td>
            """, "html.parser"))
            tbody.append(tr)

        # Oppdater JavaScript-variabelen `departures` i skriptet
        script_tag = soup.find("script")
        if script_tag and script_tag.string:
            # Erstatt `let departures = ...` med ny data
            js_data = json.dumps(departures, ensure_ascii=False, indent=2)
            new_script = script_tag.string.replace(
                "let departures = JSON.parse(localStorage.getItem('departures')) || [];",
                f"let departures = {js_data};"
            )
            script_tag.string.replace_with(new_script)

        return str(soup)
    except Exception as e:
        st.error(f"❌ Feil ved modifisering av HTML: {e}")
        return html_text

# --- Hovedapp ---
data = load_data()

# Vis statistikk først
st.markdown("### 📊 Statusoversikt")
cols = st.columns(5)
total = len(data)
levert = len([d for d in data if d["status"] == "LEVERT"])
laster = len([d for d in data if d["status"] == "LASTER NÅ"])
tog = len([d for d in data if d["type"] == "Tog"])
st.stats = len([d for d in data if d["type"] == "Bil"])

cols[0].metric("Totalt", total)
cols[1].metric("Levert", levert)
cols[2].metric("Laster nå", laster)
cols[3].metric("Tog", tog)
cols[4].metric("Bil", st.stats)

# Knapper for handling
col1, col2 = st.columns([1, 4])
if col1.button("🔁 Oppdater side"):
    st.rerun()

if col2.button("💾 Lagre data (dummy i demo)"):
    st.info("Data lagret lokalt!")

# Hent og patch HTML
html_content = fetch_and_patch_html(GITHUB_RAW_URL, data)

# Inject CSS/JS fix for iframe
st.markdown(
    """
    <style>
    .block-container { padding: 0; }
    iframe { width: 100%; height: 90vh; border: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.components.v1.html(html_content, height=1000, scrolling=True)