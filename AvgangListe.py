import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- Hjelpefunksjon: Last opp JSON uten loop ---
def _load_and_apply_json(uploaded_file, file_id):
    try:
        uploaded_data = json.load(uploaded_file)
        if isinstance(uploaded_data, list):
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

# --- Stil ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .blue-container {
        background-color: #E6F0FF;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1E3A8A;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F0F7FF;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2563EB;
        margin-bottom: 10px;
    }
    .metric-card.tog { border-left-color: #6366F1; background-color: #EDE9FE; }
    .metric-card.bil { border-left-color: #10B981; background-color: #ECFDF5; }
    .metric-card.tralle { border-left-color: #F59E0B; background-color: #FFFBEB; }
    .metric-card.modul { border-left-color: #8B5CF6; background-color: #F3E8FF; }
    .stButton>button {
        background-color: #2563EB;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
        color: white;
    }
    div[data-testid="stExpander"] {
        background-color: #F0F7FF;
        border-radius: 10px;
        border: 1px solid #BFDBFE;
    }
    .edit-form {
        background-color: #E6F0FF;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #1E3A8A;
        margin-bottom: 20px;
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.8rem;
        color: white;
    }
    .stats-container {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .stat-card {
        flex: 1;
        min-width: 120px;
        background-color: #F0F7FF;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #2563EB;
    }
    .stat-card.total { border-left-color: #2563EB; }
    .stat-card.type-tog { border-left-color: #6366F1; background-color: #EDE9FE; }
    .stat-card.type-bil { border-left-color: #10B981; background-color: #ECFDF5; }
    .stat-card.status-card { border-left-color: #10B981; background-color: #ECFDF5; }
    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
    }
    .validation-error {
        color: #EF4444;
        font-size: 0.9rem;
        margin-top: 5px;
        padding: 8px;
        background-color: #FEF2F2;
        border-radius: 4px;
        border-left: 4px solid #EF4444;
    }
    .validation-info {
        color: #3B82F6;
        font-size: 0.85rem;
        margin-top: 4px;
    }
    
    /* Toast meldinger */
    .toast {
        visibility: hidden;
        min-width: 250px;
        margin-left: -125px;
        background-color: #333;
        color: #fff;
        text-align: center;
        border-radius: 10px;
        padding: 16px;
        position: fixed;
        z-index: 1000;
        left: 50%;
        bottom: 30px;
        font-size: 15px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.2);
    }
    .toast.show {
        visibility: visible;
        animation: fadein 0.4s, fadeout 0.4s 2.6s;
    }
    @keyframes fadein {
        from { bottom: 0; opacity: 0; }
        to { bottom: 30px; opacity: 1; }
    }
    @keyframes fadeout {
        from { bottom: 30px; opacity: 1; }
        to { bottom: 0; opacity: 0; }
    }
</style>
""", unsafe_allow_html=True)

# --- Hjelpefunksjoner: Lagring og lasting ---
def load_data():
    if os.path.exists(DATA_FILE_JSON):
        try:
            with open(DATA_FILE_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
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
    st.session_state.last_uploaded_file = None  # Unngå loop ved opplasting

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

# --- Sidebar - Registrer eller Rediger ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🚛 Transportsystem</h1>", unsafe_allow_html=True)

    # Visning basert på modus
    if st.session_state.edit_mode:
        dep = next((d for d in st.session_state.departures if d['id'] == st.session_state.edit_mode), None)
        if dep:
            st.subheader("✏️ REDIGER AVGANG")
            with st.form("edit_form"):
                st.markdown("### 📝 Fyll inn detaljer")
                e_unit = st.text_input("🔢 Enhetsnummer *", dep['unitNumber']).upper()
                e_dest = st.selectbox("📍 Destinasjon *",
                    ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"],
                    index=["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"].index(dep['destination']))
                e_time = datetime.strptime(dep['time'], "%H:%M").time()
                e_time = st.time_input("⏱️ Avgangstid *", e_time)
                e_gate = st.text_input("🚪 Luke *", dep['gate']).upper()
                e_type = st.selectbox("📦 Type *", ["Tog", "Bil", "Tralle", "Modul"],
                    index=["Tog", "Bil", "Tralle", "Modul"].index(dep['type']))
                e_status = st.selectbox("🚦 Status *", ["Levert", "Lager", "Underlasting","Planlaget",],
                    index=["Levert", "Lager", "Underlasting","Planlaget",].index(dep['status']))
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
        st.subheader("➕ REGISTRER NY AVGANG")
        with st.form("departure_form"):
            st.markdown("### 📝 Fyll inn detaljer")
            unit_number = st.text_input("🔢 Enhetsnummer *", placeholder="F.eks. TOG001").upper()
            destination = st.selectbox("📍 Destinasjon *", ["", "TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
            departure_time = st.time_input("⏱️ Avgangstid *", value="now")
            gate = st.text_input("🚪 Luke *", placeholder="F.eks. A1, B2").upper()
            transport_type = st.selectbox("📦 Type *", ["", "Tog", "Bil", "Tralle", "Modul"])
            status = st.selectbox("🚦 Status *", ["", "Levert", "Lager", "Underlasting","Planlaget",])
            comment = st.text_area("💬 Kommentar", placeholder="F.eks. FORSINKET, LASTER NÅ...").upper()

            submitted = st.form_submit_button("✅ REGISTRER")

            if submitted:
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
st.markdown("""
<div class="header">
    <h1>📋 TRANSPORTSYSTEM</h1>
    <p></p>
</div>
""", unsafe_allow_html=True)

# --- 🔔 Bekreftelsesboks: Vises øverst ---
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

    with col2:
        if st.button("❌ AVBRYT", key="confirm_no"):
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

# --- Søk og filtrering ---
st.markdown("### 📋 OVERSIKT OVER AVGANGER")
col1, col2 = st.columns([3, 2])
with col1:
    search_term = st.text_input("🔍 SØK PÅ ENHETSNUMMER ELLER DESTINASJON...").upper()
with col2:
    destinations = sorted(set(d['destination'] for d in st.session_state.departures))
    filter_dest = st.selectbox("FILTRER PÅ DESTINASJON", ["ALLE DESTINASJONER"] + destinations)

# --- Tabell ---
if st.session_state.departures:
    df = pd.DataFrame(st.session_state.departures)
    df['time'] = pd.to_datetime(df['time'], format='%H:%M', errors='coerce').dt.strftime('%H:%M')

    mask = pd.Series([True] * len(df))
    if search_term:
        mask &= df['unitNumber'].str.contains(search_term, case=False) | df['destination'].str.contains(search_term, case=False)
    if filter_dest != "ALLE DESTINASJONER":
        mask &= df['destination'] == filter_dest
    df = df[mask].copy()

    # Vis tabell
    for idx, row in df.iterrows():
        cols = st.columns([2, 2, 2, 2, 2, 2, 3, 2, 2])
        cols[0].write(row['unitNumber'])
        cols[1].write(row['destination'])
        cols[2].write(row['time'])
        cols[3].write(row['gate'])
        cols[4].write(f"{type_icons.get(row['type'], '')} {row['type']}")
        status_color = 'green' if row['status'] == 'Levert' else 'blue' if row['status'] == 'I lager' else 'orange'
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

    # --- STATISTIKK (kompakt) ---
    full_df = pd.DataFrame(st.session_state.departures)
    counts = full_df['type'].value_counts()
    status_counts = full_df['status'].value_counts()

    st.markdown("### 📊 STATISTIKK (TOTALT)")
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-card total">
        <div class="stat-number">{len(full_df)}</div>
        <div class="stat-label">Totalt</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-card type-tog">
        <div class="stat-number">🚂 {counts.get('Tog', 0)}</div>
        <div class="stat-label">Tog</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="stat-card type-bil">
        <div class="stat-number">🚗 {counts.get('Bil', 0)}</div>
        <div class="stat-label">Bil</div>
    </div>
    """, unsafe_allow_html=True)

    levert = status_counts.get('Levert', 0)
    st.markdown(f"""
    <div class="stat-card status-card">
        <div class="stat-number">✅ {levert}</div>
        <div class="stat-label">Levert</div>
    </div>
    """, unsafe_allow_html=True)

   
    # --- Systemhandlinger ---
    st.markdown("### ⚙️ SYSTEMHANDLINGER")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🗑️ TØM ALLE AVGANGER"):
            st.session_state.confirm_action = "clear_all"
            st.session_state.confirm_msg = "ER DU SIKKER PÅ AT DU VIL SLETTE **ALLE** AVGANGER?"
            st.rerun()

    with col2:
        if st.button("🖨️ SKRIV UT"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)

    with col3:
        csv = export_to_csv(st.session_state.departures)
        st.download_button("📄 EKSPORTER TIL CSV", csv, f"avganger_{datetime.now().date()}.csv", "text/csv", key="csv_export")

    with col4:
        st.markdown("### 🔼 LAST OPP DATA")
        uploaded_file = st.file_uploader(
            "Velg JSON-fil for opplasting", 
            type="json", 
            label_visibility="collapsed",
            key="uploader"
        )

        if uploaded_file is not None:
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if st.session_state.last_uploaded_file != file_id:
                _load_and_apply_json(uploaded_file, file_id)
            else:
                st.caption("📄 Fil er allerede lastet.")

        # Knapp for å nullstille opplasting (valgfritt)
        if st.button("🔄 Nullstill opplasting", key="reset_upload"):
            if 'last_uploaded_file' in st.session_state:
                del st.session_state.last_uploaded_file
            st.toast("Opplasting nullstilt.")
            st.rerun()

        # Last ned JSON
        json_data = backup_data()
        st.download_button("💾 LAST NED JSON", json_data, f"backup_{datetime.now().date()}.json", "application/json", key="json_export")

else:
    st.info("INGEN AVGANGER REGISTRERT ENNÅ.")