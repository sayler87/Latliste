import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px

# --- Konfigurasjon ---
DATA_FILE_JSON = "avganger.json"
DATA_FILE_CSV = "avganger.csv"

# --- App konfigurasjon ---
st.set_page_config(page_title="🚛 Transportsystem", layout="wide")

# --- Stil ---
st.markdown("""
<style>
    .stApp { background-color: #f0f2f6; }
    .main .block-container { max-width: 1400px; padding: 20px; }
    .header { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 30px; text-align: center; border-radius: 12px; margin-bottom: 20px; }
    .form-group label { text-transform: uppercase; font-weight: 600; }
    .stTextInput input, .stSelectbox select, .stTextArea textarea, .stTimeInput input { text-transform: uppercase; }
    .stats-container { display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0; }
    .stat-card { flex: 1; min-width: 150px; background: white; padding: 18px; border-radius: 10px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #3498db; }
    .stat-number { font-size: 1.8rem; font-weight: bold; color: #2c3e50; }
    .stat-label { color: #7f8c8d; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; font-size: 0.85rem; }
    .type-tog { border-top-color: #e74c3c; }
    .type-bil { border-top-color: #f39c12; }
    .type-tralle { border-top-color: #3498db; }
    .type-modul { border-top-color: #9b59b6; }
    .dest { border-top-color: #16a085; }
    table th { background: linear-gradient(135deg, #34495e, #2c3e50); color: white; }
    table td, table th { padding: 12px 15px; }
    tr:hover { background-color: #f8f9fa; }
    .stButton>button { font-weight: 600; letter-spacing: 0.8px; }
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
            st.warning(f"Kunne ikke lese JSON-fil: {e}")
            return []
    return []

def save_data(data):
    try:
        with open(DATA_FILE_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        df = pd.DataFrame(data)
        df.to_csv(DATA_FILE_CSV, index=False, encoding='utf-8')
    except Exception as e:
        st.error(f"Lagringsfeil: {e}")

# --- Initialiser session_state ---
if 'departures' not in st.session_state:
    st.session_state.departures = load_data()

if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

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

# --- Sidebar - Registrer ny avgang ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>🚛 Registrer Avgang</h1>", unsafe_allow_html=True)
    with st.form("departure_form"):
        unit_number = st.text_input("Enhetsnummer *", placeholder="F.eks. TOG001").upper()
        destination = st.selectbox("Destinasjon *", ["", "TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
        departure_time = st.time_input("Avgangstid *", value="now")
        gate = st.text_input("Luke *", placeholder="F.eks. A1, B2").upper()
        transport_type = st.selectbox("Type *", ["", "Tog", "Bil", "Tralle", "Modul"])
        status = st.selectbox("Status *", ["", "Levert", "I lager", "Underlasting"])
        comment = st.text_area("Kommentar", placeholder="F.eks. FORSINKET, LASTER NÅ...").upper()

        submitted = st.form_submit_button("✅ REGISTRER AVGANG")

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
    <h1>🚛 TRANSPORTSYSTEM</h1>
    <p>Registrering og oversikt over alle avganger</p>
</div>
""", unsafe_allow_html=True)

# --- 🔔 Bekreftelsesboks: Vises øverst (etter header) ---
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
                save_data(st.session_state.departures)
                st.toast("🗑️ Alle avganger slettet!", icon="✅")

            # Nullstill
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()

    with col2:
        if st.button("❌ AVBRYT", key="confirm_no"):
            for key in ['confirm_action', 'confirm_id', 'confirm_msg']:
                st.session_state.pop(key, None)
            st.rerun()

    # Legg til avstand før neste innhold
    st.markdown("<br>", unsafe_allow_html=True)

# --- Søk og filtrering ---
st.markdown("### 📋 OVERSIKT OVER AVGANGER")
col1, col2 = st.columns([3, 2])
with col1:
    search_term = st.text_input("SØK PÅ ENHETSNUMMER ELLER DESTINASJON...").upper()
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

        # Slett-knapp
        with cols[8]:
            if st.button(f"🗑️", key=f"btn_delete_{row['id']}"):
                st.session_state.confirm_action = "delete"
                st.session_state.confirm_id = row['id']
                st.session_state.confirm_msg = f"Vil du slette avgang **{row['unitNumber']}** til **{row['destination']}**?"
                st.rerun()

        # Rediger-knapp
        with cols[7]:
            if st.button(f"✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_id = row['id']
                st.rerun()

    # --- Rediger skjema ---
    if st.session_state.edit_id is not None:
        dep = next((d for d in st.session_state.departures if d['id'] == st.session_state.edit_id), None)
        if dep:
            with st.form("edit_form"):
                e_unit = st.text_input("Enhetsnummer", dep['unitNumber']).upper()
                e_dest = st.selectbox("Destinasjon", ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"],
                                      index=["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"].index(dep['destination']))
                e_time = datetime.strptime(dep['time'], "%H:%M").time()
                e_time = st.time_input("Tid", e_time)
                e_gate = st.text_input("Luke", dep['gate']).upper()
                e_type = st.selectbox("Type", ["Tog", "Bil", "Tralle", "Modul"],
                                      index=["Tog", "Bil", "Tralle", "Modul"].index(dep['type']))
                e_status = st.selectbox("Status", ["Levert", "I lager", "Underlasting"],
                                        index=["Levert", "I lager", "Underlasting"].index(dep['status']))
                e_comment = st.text_area("Kommentar", dep['comment'] or "").upper()

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
                    st.session_state.edit_id = None
                    st.toast("🔁 Avgang oppdatert!", icon="✅")
                    st.rerun()

            if st.button("❌ Avbryt redigering"):
                st.session_state.edit_id = None
                st.rerun()

    # --- Statistikk ---
    st.markdown("### 📊 STATISTIKK")
    counts = df['type'].value_counts()
    status_counts = df['status'].value_counts()
    dest_counts = df['destination'].value_counts()

    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    st.markdown(f"<div class='stat-card total'><div class='stat-number'>{len(df)}</div><div class='stat-label'>Totalt</div></div>", unsafe_allow_html=True)
    for t in ["Tog", "Bil", "Tralle", "Modul"]:
        count = counts.get(t, 0)
        icon = type_icons[t]
        cls = f"type-{t.lower()}"
        st.markdown(f"<div class='stat-card {cls}'><div class='stat-number'>{icon} {count}</div><div class='stat-label'>{t}</div></div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Diagrammer
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        if not counts.empty:
            fig1 = px.pie(counts, values=counts.values, names=counts.index, title="Avganger per Type",
                          color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig1, use_container_width=True)
    with chart_col2:
        if not dest_counts.empty:
            fig2 = px.bar(dest_counts, x=dest_counts.index, y=dest_counts.values, title="Avganger per Destinasjon",
                          labels={'x': 'Destinasjon', 'y': 'Antall'}, color_discrete_sequence=['#3498db'])
            st.plotly_chart(fig2, use_container_width=True)

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
        json_data = backup_data()
        st.download_button("💾 LAST NED JSON", json_data, f"backup_{datetime.now().date()}.json", "application/json", key="json_export")

else:
    st.info("INGEN AVGANGER REGISTRERT ENNÅ.")