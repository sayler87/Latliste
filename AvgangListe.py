import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# --- Hjelpefunksjon: Last opp JSON uten loop ---
def _load_and_apply_json(uploaded_file, file_id):
    try:
        uploaded_data = json.load(uploaded_file)
        if isinstance(uploaded_data, list):
            # Rensk data ved opplasting
            for item in uploaded_data:
                if item.get("status") == "I lager":
                    item["status"] = "Lager"
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

# --- CSS: Lys tema + Horisontale statistikk-kort ---
st.markdown("""
<style>
    /* --- LYS TEMA --- */
    body {
        background-color: #FFFFFF;
        color: #1F2937;
        font-family: 'Segoe UI', sans-serif;
    }

    [data-testid="stMain"] {
        background-color: #FFFFFF;
    }

    .stSidebar {
        background-color: #F9FAFB;
    }

    h1, h2, h3 {
        color: #1F2937;
    }

    /* --- HEADER --- */
    h1 {
        font-size: 2rem;
        text-align: center;
        margin-bottom: 1rem;
        color: #2563EB;
        font-weight: 700;
    }

    /* --- INPUT-FELTER --- */
    .stTextInput input, .stSelectbox select, .stTextArea textarea, .stTimeInput input {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
        padding: 0.5rem;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9CA3AF !important;
    }

    /* --- KNAPPER --- */
    .stButton > button {
        width: 100%;
        background-color: #2563EB;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #1D4ED8;
    }

    /* --- STATUSMERKER --- */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.6rem;
        border-radius: 14px;
        font-size: 0.85rem;
        font-weight: 600;
        color: white;
        white-space: nowrap;
    }
    .status-levert { background-color: #10B981; }
    .status-lager { background-color: #3B82F6; }
    .status-underlasting { background-color: #F59E0B; }
    .status-planlaget { background-color: #6B7280; }

    /* --- TOAST --- */
    .toast {
        visibility: hidden;
        min-width: 250px;
        margin-left: -125px;
        background-color: #374151;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 12px;
        position: fixed;
        z-index: 10000;
        left: 50%;
        bottom: 50px;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .toast.show {
        visibility: visible;
        opacity: 1;
        animation: fadeOut 3s ease forwards;
    }
    @keyframes fadeOut {
        0% { opacity: 1; }
        100% { opacity: 0; }
    }

    /* --- MOBIL --- */
    @media (max-width: 768px) {
        h1 {
            font-size: 1.8rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Hjelpefunksjoner: Lagring og lasting ---
def load_data():
    if os.path.exists(DATA_FILE_JSON):
        try:
            with open(DATA_FILE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Rensk data: konverter gamle statusverdier
            for item in data:
                if item.get("status") == "I lager":
                    item["status"] = "Lager"
                if item.get("status") == "Under laste" or item.get("status") == "Laster":
                    item["status"] = "Underlasting"
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
type_icons = {
    "Tog": "🚂",
    "Bil": "🚗",
    "Tralle": "🛒",
    "Modul": "📦"
}

# --- Status-ikonmapping ---
status_icons = {
    "Levert": "✅",
    "Lager": "📦",
    "Underlasting": "🚚",
    "Planlaget": "📅"
}

# --- Sidebar - Registrer eller Rediger ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; font-size: 1.8rem;'>🚛 Transportsystem</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

    if st.session_state.edit_mode:
        dep = next((d for d in st.session_state.departures if d['id'] == st.session_state.edit_mode), None)
        if dep:
            st.subheader("✏️ REDIGER AVGANG")
            with st.form("edit_form"):
                e_unit = st.text_input("🔢 Enhetsnummer *", dep['unitNumber']).upper()
                
                # Destinasjon
                dest_options = ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"]
                current_dest = dep['destination']
                if current_dest not in dest_options:
                    current_dest = dest_options[0]
                e_dest = st.selectbox("📍 Destinasjon *", dest_options, index=dest_options.index(current_dest))
                
                # Tid
                e_time = datetime.strptime(dep['time'], "%H:%M").time()
                e_time = st.time_input("⏱️ Avgangstid *", e_time)
                
                # Luke
                e_gate = st.text_input("🚪 Luke *", dep['gate']).upper()
                
                # Type
                type_options = ["Tog", "Bil", "Tralle", "Modul"]
                current_type = dep['type']
                if current_type not in type_options:
                    current_type = type_options[0]
                e_type = st.selectbox("📦 Type *", type_options, index=type_options.index(current_type))
                
                # Status
                status_options = ["Levert", "Lager", "Underlasting", "Planlaget"]
                current_status = dep['status']
                if current_status not in status_options:
                    current_status = "Planlaget"
                e_status = st.selectbox("🚦 Status *", status_options, index=status_options.index(current_status))
                
                # Kommentar
                e_comment = st.text_area("💬 Kommentar", dep['comment'] or "").upper()

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ OPPDATER"):
                        dep.update({
                            'unitNumber': e_unit,
                            'destination': e_dest,
                            'time': e_time.strftime("%H:%M"),
                            'gate': e_gate,
                            'type': e_type,
                            'status': e_status,
                            'comment': e_comment or None
                        })
                        save_data(st.session_state.departures)
                        st.session_state.edit_mode = None
                        st.toast("🔁 Oppdatert!", icon="✅")
                        st.rerun()

                with col2:
                    if st.form_submit_button("❌ Avbryt"):
                        st.session_state.edit_mode = None
                        st.rerun()
    else:
        st.subheader("➕ NY AVGANG")
        with st.form("departure_form"):
            unit_number = st.text_input("🔢 Enhetsnummer *", placeholder="TOG001").upper()
            destination = st.selectbox("📍 Destinasjon *", [""] + ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
            departure_time = st.time_input("⏱️ Avgangstid *", value="now")
            gate = st.text_input("🚪 Luke *", placeholder="A1").upper()
            transport_type = st.selectbox("📦 Type *", ["", "Tog", "Bil", "Tralle", "Modul"])
            status = st.selectbox("🚦 Status *", ["", "Levert", "Lager", "Underlasting", "Planlaget"])
            comment = st.text_area("💬 Kommentar", placeholder="FORSINKET, LASTER NÅ...").upper()

            if st.form_submit_button("✅ REGISTRER"):
                if not all([unit_number.strip(), destination, gate.strip(), transport_type, status]):
                    st.toast("❌ Mangler obligatoriske felt!", icon="⚠️")
                elif any(d['unitNumber'] == unit_number for d in st.session_state.departures):
                    st.toast(f"❌ {unit_number} eksisterer allerede!", icon="🚨")
                else:
                    new_entry = {
                        "id": generate_id(),
                        "unitNumber": unit_number,
                        "destination": destination,
                        "time": departure_time.strftime("%H:%M"),
                        "gate": gate,
                        "type": transport_type,
                        "status": status,
                        "comment": comment or None
                    }
                    st.session_state.departures.append(new_entry)
                    save_data(st.session_state.departures)
                    st.toast("✅ Avgang registrert!", icon="🎉")
                    st.rerun()

# --- Hovedinnhold ---
st.markdown("<h1>📋 TRANSPORTSYSTEM</h1>", unsafe_allow_html=True)

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
                st.session_state.pop('last_uploaded_file', None)
                save_data(st.session_state.departures)
                st.toast("🗑️ Alle slettet!", icon="✅")

            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()

    with col2:
        if st.button("❌ AVBRYT", key="confirm_no"):
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# --- Søk og filtrering ---
st.markdown("### 🔍 SØK OG FILTRER")
col1, col2 = st.columns([2, 1])
with col1:
    search_term = st.text_input("Enhetsnummer eller destinasjon...", placeholder="Søk her...").upper()
with col2:
    destinations = sorted(set(d['destination'] for d in st.session_state.departures))
    filter_dest = st.selectbox("Destinasjon", ["Alle"] + destinations)

# --- Tabellvisning ---
if st.session_state.departures:
    df = pd.DataFrame(st.session_state.departures)
    df['time'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

    mask = pd.Series([True] * len(df))
    if search_term:
        mask &= df['unitNumber'].str.contains(search_term, na=False) | df['destination'].str.contains(search_term, na=False)
    if filter_dest != "Alle":
        mask &= df['destination'] == filter_dest
    filtered_df = df[mask].copy()

    # Vis hver rad
    for _, row in filtered_df.iterrows():
        cols = st.columns([2, 2, 2, 2, 2, 3, 4, 1, 1])
        cols[0].markdown(f"**{row['unitNumber']}**")
        cols[1].write(row['destination'])
        cols[2].write(row['time'])
        cols[3].write(row['gate'])
        cols[4].write(f"{type_icons.get(row['type'], '📦')} {row['type']}")

        # Status med ikon og farge
        status_icon = status_icons.get(row['status'], "📍")
        status_class = f"status-{row['status'].lower().replace(' ', '-')}"
        cols[5].markdown(f"<div class='status-badge {status_class}'>{status_icon} {row['status']}</div>", unsafe_allow_html=True)

        cols[6].write(row['comment'] or "–")

        with cols[7]:
            if st.button("✏️", key=f"edit_{row['id']}", help="Rediger"):
                st.session_state.edit_mode = row['id']
                st.rerun()

        with cols[8]:
            if st.button("🗑️", key=f"del_{row['id']}", help="Slett"):
                st.session_state.confirm_action = "delete"
                st.session_state.confirm_id = row['id']
                st.session_state.confirm_msg = f"Vil du slette **{row['unitNumber']}** til **{row['destination']}**?"
                st.rerun()

    # --- HORISONTAL STATISTIKK-KORT (ved siden av hverandre) ---
    st.markdown("### 📊 OVERSIKT")

    full_df = pd.DataFrame(st.session_state.departures)
    stats = [
        {"label": "Totalt", "icon": "📋", "value": len(full_df)},
        {"label": "Levert", "icon": "✅", "value": len(full_df[full_df['status'] == 'Levert'])},
        {"label": "Underveis", "icon": "🚚", "value": len(full_df[full_df['status'].isin(['Lager', 'Underlasting', 'Planlaget'])])},
        {"label": "Tog", "icon": "🚂", "value": len(full_df[full_df['type'] == 'Tog'])},
        {"label": "Bil", "icon": "🚗", "value": len(full_df[full_df['type'] == 'Bil'])},
        {"label": "Tralle", "icon": "🛒", "value": len(full_df[full_df['type'] == 'Tralle'])},
        {"label": "Modul", "icon": "📦", "value": len(full_df[full_df['type'] == 'Modul'])},
    ]

    n_cols = min(len(stats), 7)
    cols = st.columns(n_cols)

    for i, stat in enumerate(stats):
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    background-color: #F3F4F6;
                    border: 1px solid #E5E7EB;
                    border-radius: 8px;
                    padding: 10px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                ">
                    <div style="font-size: 1.4rem;">{stat['icon']}</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: #111827;">{stat['value']}</div>
                    <div style="font-size: 0.8rem; color: #6B7280;">{stat['label']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- SYSTEMHANDLINGER ---
    st.markdown("### ⚙️ HANDLINGER")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🗑️ Tøm alt"):
            st.session_state.confirm_action = "clear_all"
            st.session_state.confirm_msg = "Sikker på at du vil slette **alle** avganger?"
            st.rerun()

    with col2:
        if st.button("🖨️ Skriv ut"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    with col3:
        csv = export_to_csv(st.session_state.departures)
        st.download_button("📄 CSV", csv, f"avganger_{datetime.now().date()}.csv", "text/csv", key="csv_export")

    with col4:
        st.download_button("💾 JSON", backup_data(), f"backup_{datetime.now().date()}.json", "application/json", key="json_export")

    # --- Opplasting ---
    st.markdown("### 🔼 Last opp JSON")
    uploaded_file = st.file_uploader("Velg JSON-fil", type="json", label_visibility="collapsed", key="uploader")
    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.last_uploaded_file != file_id:
            _load_and_apply_json(uploaded_file, file_id)
        else:
            st.caption("📄 Fil er allerede lastet.")

    if st.button("🔄 Nullstill opplasting", key="reset_upload"):
        st.session_state.pop('last_uploaded_file', None)
        st.toast("Opplasting nullstilt.")
        st.rerun()

else:
    st.info("📭 Ingen avganger registrert ennå. Legg til en ny avgang i siden til venstre.")