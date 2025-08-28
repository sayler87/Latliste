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

# --- CSS: Mørk modus + Mobilvennlig + Sortering ---
st.markdown("""
<style>
    /* --- MØRK MODUS --- */
    body {
        background-color: #0F172A;
        color: #E2E8F0;
        font-family: 'Segoe UI', sans-serif;
    }

    [data-testid="stMain"] {
        background-color: #0F172A;
    }

    .stSidebar {
        background-color: #1E293B;
    }

    h1, h2, h3 {
        color: #E2E8F0;
    }

    /* --- HEADER --- */
    h1 {
        font-size: 1.8rem;
        text-align: center;
        margin-bottom: 1rem;
        color: #60A5FA;
        font-weight: 700;
    }

    @media (max-width: 768px) {
        h1 {
            font-size: 1.6rem;
        }
    }

    /* --- INPUT OG FILTER --- */
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #334155 !important;
        color: #E2E8F0 !important;
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 0.5rem;
    }

    .stTextInput input::placeholder {
        color: #94A3B8 !important;
    }

    /* --- KNAPPER --- */
    .stButton > button {
        width: 100%;
        background-color: #60A5FA;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* --- STATUSMERKER --- */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.25rem 0.6rem;
        border-radius: 14px;
        font-size: 0.8rem;
        font-weight: 600;
        color: white;
        white-space: nowrap;
    }
    .status-levert { background-color: #10B981; }
    .status-lager { background-color: #3B82F6; }
    .status-underlasting { background-color: #F59E0B; }
    .status-planlaget { background-color: #8B5CF6; }

    /* --- TABELL PÅ MOBIL --- */
    .departure-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 4px 8px;
        padding: 0.6rem;
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }

    .dep-label {
        font-size: 0.8rem;
        color: #94A3B8;
    }

    .dep-value {
        font-weight: 500;
    }

    /* --- STATISTIKK KORT --- */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 10px;
        margin: 1rem 0;
    }

    .stat-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }

    .stat-number {
        font-size: 1.2rem;
        font-weight: bold;
        color: #60A5FA;
    }

    .stat-label {
        font-size: 0.8rem;
        color: #94A3B8;
    }

    /* --- TOAST --- */
    .toast {
        visibility: hidden;
        min-width: 250px;
        margin-left: -125px;
        background-color: #334155;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 12px;
        position: fixed;
        z-index: 10000;
        left: 50%;
        bottom: 70px;
        font-size: 14px;
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
        .main-header, h1 {
            font-size: 1.6rem;
        }
        .stButton > button {
            font-size: 0.85rem;
            padding: 0.4rem;
        }
        .status-badge {
            font-size: 0.75rem;
            padding: 0.2rem 0.5rem;
        }
        .dep-label, .dep-value {
            font-size: 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Hjelpefunksjoner ---
def load_data():
    if os.path.exists(DATA_FILE_JSON):
        try:
            with open(DATA_FILE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in 
                if item.get("status") == "I lager":
                    item["status"] = "Lager"
                if item.get("status") == "Planlagt":
                    item["status"] = "Planlaget"
            return data
        except Exception as e:
            st.warning(f"Kunne ikke lese fil: {e}")
            return []
    return []

def save_data(data):
    try:
        with open(DATA_FILE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        pd.DataFrame(data).to_csv(DATA_FILE_CSV, index=False, encoding='utf-8')
        return True
    except Exception as e:
        st.error(f"Lagringsfeil: {e}")
        return False

# --- Initialisering ---
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
    return pd.DataFrame(data).to_csv(index=False, encoding='utf-8')

def backup_data():
    return json.dumps(st.session_state.departures, indent=2, ensure_ascii=False)

# --- Ikonmapping ---
type_icons = {"Tog": "🚂", "Bil": "🚗", "Tralle": "🛒", "Modul": "📦"}
status_icons = {"Levert": "✅", "Lager": "📦", "Underlasting": "🚚", "Planlaget": "📅"}

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h1 style='color: #60A5FA; text-align: center;'>🚛</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #E2E8F0;'>Transportsystem</h3>", unsafe_allow_html=True)
    st.divider()

    if st.session_state.edit_mode:
        dep = next((d for d in st.session_state.departures if d['id'] == st.session_state.edit_mode), None)
        if dep:
            with st.form("edit_form"):
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
                    if st.form_submit_button("✅ OPPDATER"):
                        dep.update({
                            'unitNumber': e_unit, 'destination': e_dest, 'time': e_time.strftime("%H:%M"),
                            'gate': e_gate, 'type': e_type, 'status': e_status, 'comment': e_comment or None
                        })
                        save_data(st.session_state.departures)
                        st.session_state.edit_mode = None
                        st.toast("Oppdatert!")
                        st.rerun()
                with col2:
                    if st.form_submit_button("❌ Avbryt"):
                        st.session_state.edit_mode = None
                        st.rerun()
    else:
        with st.form("departure_form"):
            st.subheader("➕ Ny avgang")
            unit_number = st.text_input("🔢 Enhetsnummer *").upper()
            destination = st.selectbox("📍 Destinasjon *", [""] + ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
            departure_time = st.time_input("⏱️ Avgangstid *", value="now")
            gate = st.text_input("🚪 Luke *").upper()
            transport_type = st.selectbox("📦 Type *", ["", "Tog", "Bil", "Tralle", "Modul"])
            status = st.selectbox("🚦 Status *", ["", "Levert", "Lager", "Underlasting", "Planlaget"])
            comment = st.text_area("💬 Kommentar").upper()

            if st.form_submit_button("✅ REGISTRER"):
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

# --- Hovedinnhold ---
st.markdown("<h1>📋 TRANSPORTSYSTEM</h1>", unsafe_allow_html=True)

# --- Bekreftelse ---
if 'confirm_action' in st.session_state:
    st.warning(st.session_state.get('confirm_msg', 'Er du sikker?'), icon="⚠️")
    yes, no = st.columns(2)
    with yes:
        if st.button("✅ BEKREFT", key="yes"):
            if st.session_state.confirm_action == "delete":
                st.session_state.departures = [d for d in st.session_state.departures if d['id'] != st.session_state.confirm_id]
            elif st.session_state.confirm_action == "clear_all":
                st.session_state.departures = []
            save_data(st.session_state.departures)
            st.toast("Handling utført!")
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()
    with no:
        if st.button("❌ AVBRYT", key="no"):
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

# --- Filter og Sortering ---
st.markdown("### 🔍 FILTRER OG SORTER")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_term = st.text_input("Søk", placeholder="Enhetsnummer eller destinasjon").upper()
with col2:
    filter_dest = st.selectbox("Destinasjon", ["Alle"] + sorted(set(d['destination'] for d in st.session_state.departures)))
with col3:
    sort_by = st.selectbox("Sorter etter", ["Ingen", "Destinasjon", "Status", "Avgangstid"])

# --- Tabell ---
if st.session_state.departures:
    df = pd.DataFrame(st.session_state.departures)
    df['time'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

    mask = pd.Series([True] * len(df))
    if search_term:
        mask &= df['unitNumber'].str.contains(search_term, na=False) | df['destination'].str.contains(search_term, na=False)
    if filter_dest != "Alle":
        mask &= df['destination'] == filter_dest
    df = df[mask].copy()

    # Sortering
    if sort_by == "Destinasjon":
        df = df.sort_values("destination")
    elif sort_by == "Status":
        df = df.sort_values("status")
    elif sort_by == "Avgangstid":
        df = df.sort_values("time")

    # Visning på mobil: vertikal grid
    for _, row in df.iterrows():
        with st.container():
            st.markdown("""
            <div class="departure-row">
                <div><span class="dep-label">Enhetsnr:</span> <span class="dep-value">""" + row['unitNumber'] + """</span></div>
                <div><span class="dep-label">Dest:</span> <span class="dep-value">""" + row['destination'] + """</span></div>
                <div><span class="dep-label">Tid:</span> <span class="dep-value">""" + row['time'] + """</span></div>
                <div><span class="dep-label">Luke:</span> <span class="dep-value">""" + row['gate'] + """</span></div>
                <div><span class="dep-label">Type:</span> <span class="dep-value">""" + f"{type_icons.get(row['type'], '📦')} {row['type']}" + """</span></div>
                <div><span class="dep-label">Status:</span> <span class="dep-value">
                    <div class='status-badge status-""" + row['status'].lower().replace(' ', '-') + """'>""" + status_icons.get(row['status'], "📍") + """ """ + row['status'] + """</div>
                </span></div>
                <div><span class="dep-label">Kommentar:</span> <span class="dep-value">""" + (row['comment'] or "–") + """</span></div>
            </div>
            """, unsafe_allow_html=True)

        # Knapper
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            if st.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_mode = row['id']
                st.rerun()
        with col_btn2:
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

    # --- Handlinger ---
    st.markdown("### ⚙️ HANDLINGER")
    a, b, c, d = st.columns(4)
    with a: st.button("🗑️ Tøm alt", on_click=lambda: st.session_state.update(confirm_action="clear_all", confirm_msg="Slette ALLE?"))
    with b: st.button("🖨️ Skriv ut", on_click=lambda: st.write("<script>window.print()</script>", unsafe_allow_html=True))
    with c: st.download_button("📄 CSV", export_to_csv(st.session_state.departures), "avganger.csv", "text/csv")
    with d: st.download_button("💾 JSON", backup_data(), "backup.json", "application/json")

    # --- Opplasting ---
    st.markdown("### 🔼 Last opp JSON")
    uploaded = st.file_uploader("Velg JSON", type="json", label_visibility="collapsed", key="upload")
    if uploaded:
        file_id = f"{uploaded.name}_{uploaded.size}"
        if st.session_state.last_uploaded_file != file_id:
            _load_and_apply_json(uploaded, file_id)
        else:
            st.caption("📄 Allerede lastet")
else:
    st.info("📭 Ingen avganger")