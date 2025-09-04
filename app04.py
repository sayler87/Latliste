import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- Hjelpefunksjon: Last opp JSON ---
def _load_and_apply_json(uploaded_file, file_id):
    try:
        uploaded_data = json.load(uploaded_file)
        if isinstance(uploaded_data, list):
            for item in uploaded_data:
                if item.get("status") == "I lager":
                    item["status"] = "Lager"
                if item.get("status") == "Planlagt":
                    item["status"] = "Planlaget"
            st.session_state.departures = uploaded_data
            save_data(st.session_state.departures)
            st.session_state.last_uploaded_file = file_id
            st.toast("✅ Data lastet opp!", icon="🎉")
            st.rerun()
        else:
            st.error("Ugyldig format: Forventet liste av avganger.")
    except Exception as e:
        st.error(f"Feil ved lasting av JSON: {e}")

# --- Konfigurasjon ---
DATA_FILE_JSON = "avganger.json"
DATA_FILE_CSV = "avganger.csv"

# --- App konfigurasjon ---
st.set_page_config(page_title="🚛 Transportsystem", layout="wide")

# --- CSS: Modern design med gradient og kart (Streamlit-safe) ---
st.markdown("""
<style>
    /* --- GRADIENT BAKGRUNN --- */
    .main-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
    }
    .header {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 30px;
        text-align: center;
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .header h1 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: 300;
    }
    .header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 10px 0 0 0;
    }

    /* --- KORT OG SEKSJONER --- */
    .section {
        background:  #E6F0FF;
        border-radius: 10px;
        padding: 30px;
        border-left: 5px solid #3498db;
        margin-bottom: 30px;
    }

    /* --- KNAPPER --- */
    .stButton > button {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 25px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
    }

    /* --- INPUT-FELTER --- */
    .stTextInput input, .stSelectbox select, .stTextArea textarea, .stTimeInput input {
        border: 2px solid #e0e6ed !important;
        border-radius: 8px;
        padding: 12px 15px;
        background: white !important;
        color: #333 !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
        border-color: #3498db !important;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1) !important;
    }

    /* --- LABELS --- */
    .stTextInput label, .stSelectbox label, .stTextArea label, .stTimeInput label {
        font-weight: 600;
        color: #2c3e50;
        font-size: 0.95rem;
    }

    /* --- STATISTIKK-KORT --- */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin: 20px 0;
    }
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        border-top: 4px solid #3498db;
    }
    .stat-card.type-tog { border-top-color: #090deb; }
    .stat-card.type-bil { border-top-color: #f39c12; }
    .stat-card.type-tralle { border-top-color: #3498db; }
    .stat-card.type-modul { border-top-color: #9b59b6; }
    .stat-card.status-levert { border-top-color: #27ae60; }
    .stat-card.status-lager { border-top-color: #34495e; }

    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 8px 0;
    }
    .stat-label {
        color: #7f8c8d;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.9rem;
    }

    /* --- TOAST --- */
    .stToast {
        background: #333;
        color: white;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- Hjelpefunksjoner: Lagring og lasting ---
def load_data():
    if os.path.exists(DATA_FILE_JSON):
        try:
            with open(DATA_FILE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if item.get("status") == "I lager":
                    item["status"] = "Lager"
                if item.get("status") == "Planlagt":
                    item["status"] = "Planlaget"
            return data
        except Exception as e:
            st.warning(f"Kunne ikke lese lokal JSON-fil: {e}")
            return []
    return []

def save_data(data):
    try:
        with open(DATA_FILE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        df = pd.DataFrame(data)
        df.to_csv(DATA_FILE_CSV, index=False, encoding='utf-8')
        return True
    except Exception as e:
        st.error(f"Lagringsfeil: {e}")
        return False

# --- Initialiser session_state ---
if 'departures' not in st.session_state:
    st.session_state.departures = load_data()

if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = None

if 'last_uploaded_file' not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- Hjelpefunksjoner ---
def generate_id():
    return int(datetime.now().timestamp())

def export_to_csv(data):
    df = pd.DataFrame(data)
    return df.to_csv(index=False, encoding='utf-8')

def backup_data():
    return json.dumps(st.session_state.departures, indent=2, ensure_ascii=False)

# --- Ikonmapping ---
type_icons = {"Tog": "🚂", "Bil": "🚗", "Tralle": "🛒", "Modul": "📦"}
status_icons = {"Levert": "✅", "Lager": "📦", "Underlasting": "🚚", "Planlaget": "📅"}

# --- Header ---
st.markdown("""
<div class="main-container">
  <div class="header">
    <h1>📋 TRANSPORTSYSTEM</h1>
    <p>Registrering og oversikt over alle avganger</p>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar - Registrer / Rediger ---
with st.sidebar:
    st.markdown("<h3 style='text-align: center; color: #2c3e50;'>🚛 Transportsystem</h3>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.edit_mode:
        dep = next((d for d in st.session_state.departures if d['id'] == st.session_state.edit_mode), None)
        if dep:
            st.subheader("✏️ Rediger Avgang")
            with st.form("edit_form"):
                e_unit = st.text_input("🔢 Enhetsnummer *", dep['unitNumber']).upper()

                dest_options = ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"]
                current_dest = dep['destination'] if dep['destination'] in dest_options else dest_options[0]
                e_dest = st.selectbox("📍 Destinasjon *", dest_options, index=dest_options.index(current_dest))

                e_time = datetime.strptime(dep['time'], "%H:%M").time()
                e_time = st.time_input("⏱️ Avgangstid *", e_time)

                e_gate = st.text_input("🚪 Luke *", dep['gate']).upper()

                e_type = st.selectbox("📦 Type *", ["Tog", "Bil", "Tralle", "Modul"], index=["Tog", "Bil", "Tralle", "Modul"].index(dep['type']))

                e_status = st.selectbox("🚦 Status *", ["Levert", "Lager", "Underlasting", "Planlaget"], index=["Levert", "Lager", "Underlasting", "Planlaget"].index(dep['status']))

                e_comment = st.text_area("💬 Kommentar", dep['comment'] or "").upper()

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Oppdater"):
                        dep.update({
                            'unitNumber': e_unit, 'destination': e_dest, 'time': e_time.strftime("%H:%M"),
                            'gate': e_gate, 'type': e_type, 'status': e_status, 'comment': e_comment or None
                        })
                        save_data(st.session_state.departures)
                        st.session_state.edit_mode = None
                        st.toast("🔁 Oppdatert!")
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Avbryt"):
                        st.session_state.edit_mode = None
                        st.rerun()
    else:
        st.subheader("➕ Ny Avgang")
        with st.form("departure_form"):
            unit_number = st.text_input("🔢 Enhetsnummer *", placeholder="TOG001").upper()
            destination = st.selectbox("📍 Destinasjon *", [""] + ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
            departure_time = st.time_input("⏱️ Avgangstid *", value="now")
            gate = st.text_input("🚪 Luke *", placeholder="A1").upper()
            transport_type = st.selectbox("📦 Type *", ["", "Tog", "Bil", "Tralle", "Modul"])
            status = st.selectbox("🚦 Status *", ["", "Levert", "Lager", "Underlasting", "Planlaget"])
            comment = st.text_area("💬 Kommentar", placeholder="FORSINKET...").upper()

            if st.form_submit_button("✅ Registrer"):
                if not all([unit_number.strip(), destination, gate.strip(), transport_type, status]):
                    st.toast("❌ Mangler felt!", icon="⚠️")
                elif any(d['unitNumber'] == unit_number for d in st.session_state.departures):
                    st.toast(f"❌ {unit_number} eksisterer!", icon="🚨")
                else:
                    st.session_state.departures.append({
                        "id": generate_id(),
                        "unitNumber": unit_number,
                        "destination": destination,
                        "time": departure_time.strftime("%H:%M"),
                        "gate": gate,
                        "type": transport_type,
                        "status": status,
                        "comment": comment or None
                    })
                    save_data(st.session_state.departures)
                    st.toast("✅ Registrert!")
                    st.rerun()

# --- Bekreftelsesboks ---
if 'confirm_action' in st.session_state:
    st.warning(st.session_state.get('confirm_msg', 'Er du sikker?'), icon="⚠️")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ BEKREFT", key="confirm_yes"):
            action = st.session_state.confirm_action
            if action == "delete":
                id_to_delete = st.session_state.confirm_id
                st.session_state.departures = [d for d in st.session_state.departures if d['id'] != id_to_delete]
                save_data(st.session_state.departures)
                st.toast("🗑️ Avgang slettet!", icon="✅")
            elif action == "clear_all":
                st.session_state.departures = []
                if 'last_uploaded_file' in st.session_state:
                    del st.session_state.last_uploaded_file
                save_data(st.session_state.departures)
                st.toast("🗑️ Alle avganger slettet!", icon="✅")

            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()

# --- Søk og filtrering ---
st.markdown('<div class="section"><h2>🔍 Søk og Filtrer</h2>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    search_term = st.text_input("Søk på enhetsnummer eller destinasjon").upper()
with col2:
    destinations = sorted(set(d['destination'] for d in st.session_state.departures))
    filter_dest = st.selectbox("Filter på destinasjon", ["Alle"] + destinations)

st.markdown('</div>', unsafe_allow_html=True)

# --- Tabellvisning ---
# Filter departures based on search and destination filter
filtered_departures = [
    d for d in st.session_state.departures
    if (search_term in d['unitNumber'] or search_term in d['destination'])
    and (filter_dest == "Alle" or d['destination'] == filter_dest)
]
df = pd.DataFrame(filtered_departures)

if not df.empty:
    for idx, row in df.iterrows():
        cols = st.columns([2, 2, 2, 2, 2, 2, 3, 2, 2])
        cols[0].write(row['unitNumber'])
        cols[1].write(row['destination'])
        cols[2].write(row['time'])
        cols[3].write(row['gate'])
        cols[4].write(f"{type_icons.get(row['type'], '')} {row['type']}")
        status_color = 'green' if row['status'] == 'Levert' else 'blue' if row['status'] == 'Lager' else 'orange'
        cols[5].markdown(f"<span style='color:{status_color}; font-weight:bold'>{row['status']}</span>", unsafe_allow_html=True)
        cols[6].write(row['comment'] or "INGEN")

        with cols[8]:
            if st.button(f"🗑️", key=f"btn_delete_{row['id']}"):
                st.session_state.confirm_action = "delete"
                st.session_state.confirm_id = row['id']
                st.session_state.confirm_msg = f"Vil du slette avgang **{row['unitNumber']}** til **{row['destination']}**?"
                st.rerun()

        with cols[7]:
            if st.button(f"✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_mode = row['id']
                st.rerun()
else:
    st.info("📭 Ingen avganger registrert ennå. Legg til en ny avgang i siden til venstre.")

# --- Statistikk ---
st.markdown('<div class="section"><h2>📊 Statistikk</h2>', unsafe_allow_html=True)
full_df = pd.DataFrame(st.session_state.departures)
stats = [
    ("📋", "Totalt", len(full_df), ""),
    ("✅", "Levert", len(full_df[full_df['status'] == 'Levert']), "status-levert"),
    ("📦", "Lager", len(full_df[full_df['status'] == 'Lager']), "status-lager"),
    ("🚚", "Underlasting", len(full_df[full_df['status'] == 'Underlasting']), "status-underlasting"),
    ("📅", "Planlaget", len(full_df[full_df['status'] == 'Planlaget']), "status-planlaget"),
    ("🚂", "Tog", len(full_df[full_df['type'] == 'Tog']), "type-tog"),
    ("🚗", "Bil", len(full_df[full_df['type'] == 'Bil']), "type-bil"),
    ("🛒", "Tralle", len(full_df[full_df['type'] == 'Tralle']), "type-tralle"),
    ("📦", "Modul", len(full_df[full_df['type'] == 'Modul']), "type-modul"),
]
st.markdown('<div class="stats-container">', unsafe_allow_html=True)
for icon, label, value, cls in stats:
    st.markdown(f"""
    <div class="stat-card {cls}">
      <div>{icon}</div>
      <div class="stat-number">{value}</div>
      <div class="stat-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div></div>', unsafe_allow_html=True)

# --- Systemhandlinger ---
st.markdown('<div class="section"><h2>⚙️ Handlinger</h2>', unsafe_allow_html=True)
a, b, c, d = st.columns(4)
with a:
    if st.button("🗑️ Tøm alt"):
        st.session_state.confirm_action = "clear_all"
        st.session_state.confirm_msg = "Sikker på at du vil slette **alle** avganger?"
        st.rerun()
with b:
    if st.button("🖨️ Skriv ut"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
with c:
    st.download_button("📄 Eksporter CSV", export_to_csv(st.session_state.departures), "avganger.csv", "text/csv")
with d:
    st.download_button("💾 Eksporter JSON", backup_data(), "backup.json", "application/json")
st.markdown('</div>', unsafe_allow_html=True)

# --- Opplasting ---
st.markdown('<div class="section"><h2>🔼 Last opp data</h2>', unsafe_allow_html=True)
uploaded = st.file_uploader("Velg JSON-fil", type="json", label_visibility="collapsed")
if uploaded:
    file_id = f"{uploaded.name}_{uploaded.size}"
    if st.session_state.last_uploaded_file != file_id:
        _load_and_apply_json(uploaded, file_id)
    else:
        st.caption("📄 Fil er allerede lastet.")
st.markdown('</div>', unsafe_allow_html=True)