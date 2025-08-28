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
            # Rensk data ved opplasting
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

# --- CSS: Mørk modus med god lesbarhet på PC og mobil ---
st.markdown("""
<style>
    /* --- MØRK MODUS --- */
    body {
        background-color: #0F172A;
        color: #E2E8F0;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
        font-size: 16px;
    }

    [data-testid="stMain"] {
        background-color: #0F172A;
    }

    .stSidebar {
        background-color: #1E293B;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #60A5FA;
        font-weight: 700;
    }

    /* --- HEADER --- */
    h1 {
        font-size: 1.8rem;
        text-align: center;
        margin-bottom: 1rem;
        color: #60A5FA;
    }

    @media (min-width: 1024px) {
        h1 {
            font-size: 2.2rem;
        }
    }

    /* --- INPUT-FELTER --- */
    .stTextInput input, 
    .stSelectbox select, 
    .stTextArea textarea, 
    .stTimeInput input {
        background-color: #334155 !important;
        color: #E2E8F0 !important;
        border: 1px solid #475569 !important;
        border-radius: 8px;
        padding: 0.5rem;
        font-size: 1rem;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #94A3B8 !important;
        opacity: 0.8;
    }

    /* --- KNAPPER --- */
    .stButton > button {
        width: 100%;
        background-color: #60A5FA;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem;
        font-weight: 600;
        font-size: 1rem;
    }

    .stButton > button:hover {
        background-color: #3B82F6;
    }

    /* --- STATUSMERKER --- */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.6rem;
        border-radius: 14px;
        font-size: 0.9rem;
        font-weight: 600;
        color: white;
        white-space: nowrap;
    }
    .status-levert { background-color: #10B981; }
    .status-lager { background-color: #3B82F6; }
    .status-underlasting { background-color: #F59E0B; }
    .status-planlaget { background-color: #8B5CF6; }

    /* --- TABELL: Responsiv grid --- */
    .departure-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 8px;
        padding: 0.8rem;
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        margin-bottom: 0.6rem;
        font-size: 1rem;
    }

    .dep-label {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 500;
    }

    .dep-value {
        font-weight: 500;
        color: #E2E8F0;
    }

    /* --- STATISTIKK-KORT --- */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
        gap: 12px;
        margin: 1rem 0;
    }

    .stat-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }

    .stat-number {
        font-size: 1.3rem;
        font-weight: bold;
        color: #60A5FA;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #94A3B8;
    }

    /* --- TOAST --- */
    .toast {
        visibility: hidden;
        min-width: 280px;
        margin-left: -140px;
        background-color: #334155;
        color: #fff;
        text-align: center;
        border-radius: 8px;
        padding: 14px;
        position: fixed;
        z-index: 10000;
        left: 50%;
        bottom: 70px;
        font-size: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
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
        .departure-row {
            font-size: 0.9rem;
            grid-template-columns: 1fr 1fr;
            gap: 6px 8px;
        }
        .dep-label, .dep-value {
            font-size: 0.85rem;
        }
        .stat-number {
            font-size: 1.1rem;
        }
        h1 {
            font-size: 1.6rem;
        }
        .stButton > button {
            font-size: 0.9rem;
            padding: 0.5rem;
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
            # Rensk gamle verdier
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
type_icons = {
    "Tog": "🚂",
    "Bil": "🚗",
    "Tralle": "🛒",
    "Modul": "📦"
}

status_icons = {
    "Levert": "✅",
    "Lager": "📦",
    "Underlasting": "🚚",
    "Planlaget": "📅"
}

# --- Sidebar - Registrer eller Rediger ---
with st.sidebar:
    st.markdown("<h1 style='color: #60A5FA; text-align: center;'>🚛</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #E2E8F0;'>Transportsystem</h3>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.edit_mode:
        dep = next((d for d in st.session_state.departures if d['id'] == st.session_state.edit_mode), None)
        if dep:
            with st.form("edit_form"):
                st.subheader("✏️ Rediger avgang")
                e_unit = st.text_input("🔢 Enhetsnummer *", dep['unitNumber']).upper()

                dest_options = ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"]
                current_dest = dep['destination'] if dep['destination'] in dest_options else dest_options[0]
                e_dest = st.selectbox("📍 Destinasjon *", dest_options, index=dest_options.index(current_dest))

                e_time = datetime.strptime(dep['time'], "%H:%M").time()
                e_time = st.time_input("⏱️ Avgangstid *", e_time)

                e_gate = st.text_input("🚪 Luke *", dep['gate']).upper()

                type_options = ["Tog", "Bil", "Tralle", "Modul"]
                e_type = st.selectbox("📦 Type *", type_options, index=type_options.index(dep['type']))

                status_options = ["Levert", "Lager", "Underlasting", "Planlaget"]
                e_status = st.selectbox("🚦 Status *", status_options, index=status_options.index(dep['status']))

                e_comment = st.text_area("💬 Kommentar", dep['comment'] or "").upper()

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Oppdater"):
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
        with st.form("departure_form"):
            st.subheader("➕ Ny avgang")
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
                    st.toast("✅ Registrert!", icon="🎉")
                    st.rerun()

# --- Hovedinnhold ---
st.markdown("<h1>📋 TRANSPORTSYSTEM</h1>", unsafe_allow_html=True)

# --- Bekreftelsesboks ---
if 'confirm_action' in st.session_state:
    st.warning(st.session_state.get('confirm_msg', 'Er du sikker?'), icon="⚠️")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Bekreft", key="confirm_yes"):
            action = st.session_state.confirm_action
            if action == "delete":
                st.session_state.departures = [d for d in st.session_state.departures if d['id'] != st.session_state.confirm_id]
            elif action == "clear_all":
                st.session_state.departures = []
            save_data(st.session_state.departures)
            st.toast("Handling utført!")
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()
    with col2:
        if st.button("❌ Avbryt", key="confirm_no"):
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# --- Søk, filter og sortering ---
st.markdown("### 🔍 SØK OG FILTRER")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_term = st.text_input("Søk", placeholder="Enhetsnummer eller destinasjon").upper()
with col2:
    destinations = sorted(set(d['destination'] for d in st.session_state.departures))
    filter_dest = st.selectbox("Destinasjon", ["Alle"] + destinations)
with col3:
    sort_by = st.selectbox("Sorter etter", ["Ingen", "Destinasjon", "Status", "Avgangstid"])

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

    # Sortering
    if sort_by == "Destinasjon":
        filtered_df = filtered_df.sort_values("destination")
    elif sort_by == "Status":
        filtered_df = filtered_df.sort_values("status")
    elif sort_by == "Avgangstid":
        filtered_df = filtered_df.sort_values("time")

    # Vis hver rad
    for _, row in filtered_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="departure-row">
                <div><span class="dep-label">Nr:</span> <span class="dep-value">{row['unitNumber']}</span></div>
                <div><span class="dep-label">Dest:</span> <span class="dep-value">{row['destination']}</span></div>
                <div><span class="dep-label">Tid:</span> <span class="dep-value">{row['time']}</span></div>
                <div><span class="dep-label">Luke:</span> <span class="dep-value">{row['gate']}</span></div>
                <div><span class="dep-label">Type:</span> <span class="dep-value">{type_icons.get(row['type'], '📦')} {row['type']}</span></div>
                <div><span class="dep-label">Status:</span> <span class="dep-value">
                    <div class='status-badge status-{row['status'].lower().replace(' ', '-')}'>{status_icons.get(row['status'], '📍')} {row['status']}</div>
                </span></div>
                <div><span class="dep-label">Kommentar:</span> <span class="dep-value">{row['comment'] or '–'}</span></div>
            </div>
            """, unsafe_allow_html=True)

        # Knapper
        btn_col1, btn_col2 = st.columns([1, 4])
        with btn_col1:
            if st.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_mode = row['id']
                st.rerun()
        with btn_col2:
            if st.button("🗑️", key=f"del_{row['id']}"):
                st.session_state.confirm_action = "delete"
                st.session_state.confirm_id = row['id']
                st.session_state.confirm_msg = f"Slette {row['unitNumber']} til {row['destination']}?"
                st.rerun()

    # --- Statistikk ---
    st.markdown("### 📊 OVERSIKT")
    full_df = pd.DataFrame(st.session_state.departures)
    stats = [
        ("📋", "Totalt", len(full_df)),
        ("✅", "Levert", len(full_df[full_df['status'] == 'Levert'])),
        ("🚚", "Underveis", len(full_df[full_df['status'].isin(['Lager', 'Underlasting', 'Planlaget'])])),
        ("🚂", "Tog", len(full_df[full_df['type'] == 'Tog'])),
        ("🚗", "Bil", len(full_df[full_df['type'] == 'Bil'])),
        ("🛒", "Traller", len(full_df[full_df['type'] == 'Tralle'])),
        ("📦", "Moduler", len(full_df[full_df['type'] == 'Modul'])),
    ]

    cols = st.columns(len(stats))
    for i, (icon, label, value) in enumerate(stats):
        with cols[i]:
            st.markdown(f"""
            <div class="stat-card">
                <div>{icon}</div>
                <div class="stat-number">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- Systemhandlinger ---
    st.markdown("### ⚙️ HANDLINGER")
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
        csv = export_to_csv(st.session_state.departures)
        st.download_button("📄 CSV", csv, f"avganger_{datetime.now().date()}.csv", "text/csv", key="csv_export")
    with d:
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