import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Fil for lagring
DATA_FILE = "departures.json"

# --- Hjelpefunksjoner ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Sikre at alle poster har 'id' hvis ikke tilføy
            for d in data:
                if 'id' not in d:
                    d['id'] = d.get('unitNumber', '') + str(hash(d.get('unitNumber', '')))
            return data
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Type-ikoner
TYPE_ICONS = {
    "Tog": "🚂",
    "Bil": "🚗",
    "Tralle": "🛒",
    "Modul": "📦"
}

STATUS_COLORS = {
    "Levert": "color: #27ae60; font-weight: bold;",
    "I lager": "color: #3498db; font-weight: bold;",
    "Underlasting": "color: #f39c12; font-weight: bold;"
}

TYPE_COLORS = {
    "Tog": "#e74c3c",
    "Bil": "#f39c12",
    "Tralle": "#3498db",
    "Modul": "#9b59b6"
}

# --- CSS for utskrift og stil ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .main .block-container { background: white; border-radius: 15px; padding: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #2c3e50 !important; }
    .stButton button { border-radius: 8px; font-weight: 600; }
    .stTextInput input, .stSelectbox select, .stTextArea textarea, .stTimeInput input {
        border: 2px solid #e0e6ed; border-radius: 8px; padding: 10px; }
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
        border-color: #3498db; box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1); }

    /* Utskriftsstil */
    @media print {
        body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        .stApp { background: white !important; }
        .main .block-container, .element-container { background: white !important; color: black !important; }
        [data-testid="stSidebar"] { display: none !important; }
        .element-container:has(.print-hide) { display: none !important; }
        .print-footer { text-align: center; font-size: 12px; color: #555; margin-top: 30px; padding-top: 10px; border-top: 1px solid #ccc; }
        table { font-size: 12pt; border: 1px solid #000; }
        th, td { padding: 8px; border-bottom: 1px solid #ccc; }
        th { background-color: #f0f0f0 !important; color: #000 !important; }
    }
</style>
""", unsafe_allow_html=True)

# --- Tittel ---
st.markdown("<h1 style='text-align: center;'>🚛 Transportsystem</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; opacity: 0.8;'>Registrering og oversikt over alle avganger</p>", unsafe_allow_html=True)

# --- Last inn data ---
if 'departures' not in st.session_state:
    st.session_state.departures = load_data()

departures = st.session_state.departures

# --- Sidebar: Registrer ny avgang ---
with st.sidebar:
    st.title("🚛 Registrer Avgang")
    with st.form("departure_form"):
        unit_number = st.text_input("Enhetsnummer *", placeholder="F.eks. TOG001").upper()
        destination = st.selectbox("Destinasjon *", ["", "TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
        time = st.time_input("Avgangstid *", value="now")
        gate = st.text_input("Luke *", placeholder="F.eks. A1, B2")
        type_ = st.selectbox("Type *", ["", "Tog", "Bil", "Tralle", "Modul"])
        status = st.selectbox("Status *", ["", "Levert", "I lager", "Underlasting"])
        comment = st.text_area("Kommentar", placeholder="F.eks. Forsinket, laster nå...")

        submitted = st.form_submit_button("✅ Registrer Avgang")
        editing = st.session_state.get("editing", False)

    if submitted:
        if not all([unit_number, destination, gate, type_, status]):
            st.error("Vennligst fyll ut alle obligatoriske felt.")
        elif any(d['unitNumber'] == unit_number and not editing for d in departures):
            st.error(f"Enhetsnummer {unit_number} eksisterer allerede!")
        else:
            if editing:
                idx = st.session_state.edit_index
                departures[idx] = {
                    "id": departures[idx]["id"],
                    "unitNumber": unit_number,
                    "destination": destination,
                    "time": time.strftime("%H:%M"),
                    "gate": gate,
                    "type": type_,
                    "status": status,
                    "comment": comment or None
                }
                st.success("Avgang oppdatert!")
                st.session_state.editing = False
            else:
                new_id = str(datetime.now().timestamp())
                departures.append({
                    "id": new_id,
                    "unitNumber": unit_number,
                    "destination": destination,
                    "time": time.strftime("%H:%M"),
                    "gate": gate,
                    "type": type_,
                    "status": status,
                    "comment": comment or None
                })
                st.success("Avgang registrert!")
            st.session_state.departures = departures
            save_data(departures)
            st.rerun()

# --- Hovedinnhold ---
# 🔍 Søk og filter
st.subheader("📋 Oversikt over Avganger")
col1, col2 = st.columns([3, 2])
with col1:
    search_term = st.text_input("Søk på enhetsnummer eller destinasjon")
with col2:
    filter_dest = st.selectbox("Filter på destinasjon", ["Alle destinasjoner"] + sorted(set(d['destination'] for d in departures)))

# Filtrering
filtered = departures.copy()
if search_term:
    filtered = [d for d in filtered if search_term.lower() in d['unitNumber'].lower() or search_term.lower() in d['destination'].lower()]
if filter_dest != "Alle destinasjoner":
    filtered = [d for d in filtered if d['destination'] == filter_dest]

# Konverter til DataFrame for lett håndtering
df = pd.DataFrame(filtered) if filtered else pd.DataFrame(columns=["id", "unitNumber", "destination", "time", "gate", "type", "status", "comment"])

if not df.empty:
    df['type_icon'] = df['type'].map(lambda t: f"{TYPE_ICONS.get(t, '📦')} {t}")
    df['status_styled'] = df['status'].map(lambda s: f"<span style='{STATUS_COLORS.get(s, '')}'>{s}</span>")
    df['type_styled'] = df['type'].map(lambda t: f"<span style='color:{TYPE_COLORS.get(t, '#333')}; font-weight:bold;'>{t}</span>")

# Vis tabell
if not df.empty:
    # Bare vis kolonner vi vil ha
    display_df = df[["unitNumber", "destination", "time", "gate", "type_icon", "status_styled", "comment"]].copy()
    display_df.columns = ["Enhetsnummer", "Destinasjon", "Tid", "Luke", "Type", "Status", "Kommentar"]
    display_df = display_df.fillna("<em>Ingen</em>")

    st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Handlinger (rediger/slett)
    st.write("### Handlinger")
    action_col1, action_col2 = st.columns(len(df))
    for idx, row in df.iterrows():
        with action_col1:
            if st.button(f"✏️ Rediger {row['unitNumber']}", key=f"edit_{row['id']}"):
                st.session_state.editing = True
                st.session_state.edit_index = next(i for i, d in enumerate(departures) if d['id'] == row['id'])
                st.rerun()
        with action_col2:
            if st.button(f"🗑️ Slett {row['unitNumber']}", key=f"del_{row['id']}"):
                st.session_state.departures = [d for d in departures if d['id'] != row['id']]
                save_data(st.session_state.departures)
                st.success(f"Slettet {row['unitNumber']}")
                st.rerun()
else:
    st.info("Ingen avganger registrert.")

# --- Statistikk og diagrammer ---
st.subheader("📊 Statistikk og Diagrammer")

if departures:
    # Statistikk-kort
    total = len(departures)
    counts = {t: sum(1 for d in departures if d['type'] == t) for t in TYPE_ICONS.keys()}
    statuses = {s: sum(1 for d in departures if d['status'] == s) for s in ["Levert", "I lager", "Underlasting"]}
    destinations = {d: sum(1 for a in departures if a['destination'] == d) for d in set(d['destination'] for d in departures)}

    cols = st.columns(3)
    cols[0].metric("Totalt", total)
    cols[1].metric("Levert", statuses["Levert"], delta_color="inverse")
    cols[2].metric("I lager", statuses["I lager"])

    # Diagrammer
    col1, col2 = st.columns(2)

    with col1:
        fig_pie = px.pie(
            names=[f"{TYPE_ICONS[t]} {t}" for t in counts.keys()],
            values=list(counts.values()),
            title="Avganger per Type",
            color_discrete_sequence=list(TYPE_COLORS.values())
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        dest_data = pd.DataFrame(list(destinations.items()), columns=["Destinasjon", "Antall"])
        fig_bar = px.bar(dest_data, x="Destinasjon", y="Antall", title="Avganger per Destinasjon", color_discrete_sequence=["#3498db"])
        st.plotly_chart(fig_bar, use_container_width=True)

# --- Systemhandlinger ---
st.subheader("⚙️ Systemhandlinger")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🗑️ Tøm alle avganger"):
        if departures:
            if st.button("Bekreft sletting av ALT?"):
                st.session_state.departures = []
                save_data([])
                st.success("Alle avganger slettet!")
                st.rerun()
        else:
            st.warning("Ingen avganger å slette.")

with col2:
    if st.button("🖨️ Skriv ut"):
        st.markdown("<script>window.print()</script>", unsafe_allow_html=True)

with col3:
    if st.button("📄 Eksporter til CSV"):
        export_df = pd.DataFrame(departures)[["unitNumber", "destination", "time", "gate", "type", "status", "comment"]]
        csv = export_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button("Last ned CSV", csv, f"avganger_{datetime.now().strftime('%Y-%m-%d')}.csv", "text/csv")

with col4:
    if st.button("💾 Last ned backup (JSON)"):
        json_str = json.dumps(departures, indent=2, ensure_ascii=False)
        st.download_button("Last ned JSON", json_str, f"backup_{datetime.now().strftime('%Y-%m-%d')}.json", "application/json")

# --- Utskriftsfot ---
st.markdown(f"<div class='print-footer'>Utskriftsdato: {datetime.now().strftime('%d.%m.%Y kl. %H:%M')}</div>", unsafe_allow_html=True)