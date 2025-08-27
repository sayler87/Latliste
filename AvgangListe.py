import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import time as time_module
from PIL import Image
import requests
from io import BytesIO

# App konfigurasjon
st.set_page_config(
    page_title="Registrer Avganger",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tilpasset CSS for blått fargetema inkludert toast
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
    
    /* Ikoner og farger */
    .type-icon {
        font-size: 20px;
        margin-right: 8px;
        vertical-align: middle;
    }
    .status-icon {
        font-size: 18px;
        margin-right: 8px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# Last inn data fra session state
if 'departures' not in st.session_state:
    st.session_state.departures = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
if 'edit_data' not in st.session_state:
    st.session_state.edit_data = None
if 'toast_message' not in st.session_state:
    st.session_state.toast_message = None
if 'toast_type' not in st.session_state:
    st.session_state.toast_type = None
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False

# Ikoner for typer og status
type_icons = {
    "Tog": "🚆",
    "Bil": "🚚", 
    "Tralle": "🛻",
    "Modul": "📦"
}

status_icons = {
    "Levert": "✅",
    "I lager": "📦",
    "Underlasting": "⏳"
}

status_colors = {
    "Levert": "#10B981",
    "I lager": "#2563EB", 
    "Underlasting": "#F59E0B"
}

type_colors = {
    "Tog": "#6366F1",
    "Bil": "#10B981",
    "Tralle": "#F59E0B",
    "Modul": "#8B5CF6"
}

# Hjelpefunksjoner
def show_toast(message, toast_type="info"):
    """Vis en toast melding"""
    st.session_state.toast_message = message
    st.session_state.toast_type = toast_type

def save_data():
    """Lagre data til session state"""
    st.session_state.departures = st.session_state.departures

def add_departure(unit_number, destination, time_str, gate, type_, status, comment):
    """Legg til en ny avgang"""
    new_id = datetime.now().timestamp()
    new_entry = {
        'id': new_id,
        'unitNumber': unit_number.upper(),
        'destination': destination,
        'time': time_str,
        'gate': gate,
        'type': type_,
        'status': status,
        'comment': comment if comment else None
    }
    st.session_state.departures.append(new_entry)
    save_data()
    show_toast("Avgang registrert!", "success")

def update_departure(index, unit_number, destination, time_str, gate, type_, status, comment):
    """Oppdater en eksisterende avgang"""
    st.session_state.departures[index] = {
        'id': st.session_state.departures[index]['id'],
        'unitNumber': unit_number.upper(),
        'destination': destination,
        'time': time_str,
        'gate': gate,
        'type': type_,
        'status': status,
        'comment': comment if comment else None
    }
    save_data()
    show_toast("Avgang oppdatert!", "edit")
    st.session_state.editing_index = None
    st.session_state.edit_data = None

def delete_departure(index):
    """Slett en avgang"""
    del st.session_state.departures[index]
    save_data()
    show_toast("Avgang slettet!", "delete")

def clear_all_departures():
    """Slett alle avganger"""
    st.session_state.departures = []
    save_data()
    show_toast("Alle avganger er slettet!", "delete")

def export_to_csv():
    """Eksporter data til CSV"""
    if not st.session_state.departures:
        show_toast("Ingen data å eksportere", "info")
        return None
    
    df = pd.DataFrame(st.session_state.departures)
    # Fjern ID-kolonnen for eksport
    df_export = df.drop(columns=['id'], errors='ignore')
    show_toast("Data eksportert til CSV!", "success")
    return df_export.to_csv(index=False, sep=';').encode('utf-8-sig')

def backup_data():
    """Lag backup av data som JSON"""
    if not st.session_state.departures:
        show_toast("Ingen data å sikre", "info")
        return None
    
    show_toast("Backup lastet ned!", "success")
    return json.dumps(st.session_state.departures, indent=2)

def load_backup(uploaded_file):
    """Last opp backup-fil"""
    try:
        data = json.load(uploaded_file)
        st.session_state.departures = data
        save_data()
        show_toast("Backup lastet opp!", "success")
        st.session_state.file_uploaded = True
    except Exception as e:
        show_toast(f"Feil ved lasting av backup: {e}", "error")

# Håndter filopplasting utenfor callback
if st.session_state.file_uploaded:
    st.session_state.file_uploaded = False
    st.rerun()

# Vis toast melding hvis det finnes en
if st.session_state.toast_message:
    toast_icons = {
        "success": "✅",
        "edit": "✏️", 
        "delete": "🗑️",
        "info": "ℹ️",
        "error": "❌"
    }
    
    toast_colors = {
        "success": "#059669",
        "edit": "#0891b2", 
        "delete": "#b91c1c",
        "info": "#d97706",
        "error": "#dc2626"
    }
    
    icon = toast_icons.get(st.session_state.toast_type, "📢")
    color = toast_colors.get(st.session_state.toast_type, "#333")
    
    # HTML for toast
    toast_html = f"""
    <div class="toast show" style="background-color: {color};">
        {icon} {st.session_state.toast_message}
    </div>
    <script>
        setTimeout(function() {{
            var toast = document.querySelector('.toast');
            if (toast) toast.classList.remove('show');
        }}, 3000);
    </script>
    """
    
    st.markdown(toast_html, unsafe_allow_html=True)
    
    # Nullstill toast melding etter visning
    if st.button("OK", key="toast_ok"):
        st.session_state.toast_message = None
        st.session_state.toast_type = None
        st.rerun()

# Sidebar for registrering av nye avganger
with st.sidebar:
    st.markdown('<h1 style="color: #1E3A8A; text-align: center;">🚢 Registrer Avganger</h1>', unsafe_allow_html=True)
    
    # Skjema for registrering med ikoner
    with st.form("departure_form"):
        unit_number = st.text_input("📋 Enhetsnummer:", key="unit_number", max_chars=20)
        
        destination = st.selectbox(
            "📍 Destinasjon:",
            ["", "TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"],
            key="destination"
        )
        
        time_val = st.time_input("⏰ Avgangstid:", key="time_val")
        gate = st.text_input("🚪 Luke:", key="gate", max_chars=10)
        
        type_ = st.selectbox(
            "🚚 Avgangstype:",
            ["", "Tog", "Bil", "Tralle", "Modul"],
            key="type"
        )
        
        status = st.selectbox(
            "📊 Status:",
            ["", "Levert", "I lager", "Underlasting"],
            key="status"
        )
        
        comment = st.text_area("💬 Kommentar (valgfritt):", key="comment", max_chars=100)
        
        submitted = st.form_submit_button("📝 Registrer Avgang")
        
        if submitted:
            if not all([unit_number, destination, gate, type_, status]):
                show_toast("Vennligst fyll ut alle obligatoriske felter", "error")
            else:
                # Konverter til store bokstaver
                unit_number = unit_number.upper()
                
                # Sjekk om enhetsnummer allerede finnes
                existing_ids = [d['unitNumber'] for d in st.session_state.departures]
                
                if unit_number in existing_ids:
                    show_toast(f"Enhetsnummer {unit_number} finnes allerede!", "info")
                else:
                    time_str = time_val.strftime("%H:%M")
                    add_departure(
                        unit_number,
                        destination,
                        time_str,
                        gate,
                        type_,
                        status,
                        comment
                    )
                    st.rerun()

# Hovedinnhold
st.markdown('<div class="main-header">📋 Avgangsoversikt</div>', unsafe_allow_html=True)

# Søk og filter
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("🔍 Søk på enhetsnummer, destinasjon, type...", key="search")
with col2:
    filter_dest = st.selectbox(
        "📍 Filter destinasjon:",
        ["Alle"] + ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"],
        key="filter_dest"
    )

# Vis dato
current_date = datetime.now().strftime("%A, %d. %B %Y")
st.subheader(f"📅 {current_date}")

# Konverter til DataFrame for enklere håndtering
if st.session_state.departures:
    df = pd.DataFrame(st.session_state.departures)
    
    # Filtrer data
    if search_term:
        mask = (
            df['unitNumber'].str.contains(search_term, case=False) |
            df['destination'].str.contains(search_term, case=False) |
            df['type'].str.contains(search_term, case=False) |
            df['status'].str.contains(search_term, case=False) |
            df['comment'].fillna('').str.contains(search_term, case=False)
        )
        df = df[mask]
    
    if filter_dest != "Alle":
        df = df[df['destination'] == filter_dest]
    
    # Vis data i tabell
    if not df.empty:
        # Vis hver avgang i en expander
        for i, row in df.iterrows():
            type_icon = type_icons.get(row['type'], "📦")
            status_icon = status_icons.get(row['status'], "📊")
            type_color = type_colors.get(row['type'], "#000000")
            status_color = status_colors.get(row['status'], "#000000")
            
            with st.expander(f"{type_icon} {row['unitNumber']} - {row['destination']} - {row['time']}", expanded=False):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.write(f"**📋 Enhetsnummer:** {row['unitNumber']}")
                    st.write(f"**📍 Destinasjon:** {row['destination']}")
                    st.write(f"**⏰ Avgangstid:** {row['time']}")
                    st.write(f"**🚪 Luke:** {row['gate']}")
                    st.write(f"**🚚 Type:** <span style='color: {type_color}; font-weight: bold;'>{type_icon} {row['type']}</span>", unsafe_allow_html=True)
                    st.write(f"**📊 Status:** <span style='color: {status_color}; font-weight: bold;'>{status_icon} {row['status']}</span>", unsafe_allow_html=True)
                    st.write(f"**💬 Kommentar:** {row['comment'] if pd.notna(row['comment']) and row['comment'] else 'Ingen'}")
                
                with cols[1]:
                    if st.button("✏️ Rediger", key=f"edit_{i}"):
                        st.session_state.editing_index = i
                        st.session_state.edit_data = row.to_dict()
                        st.rerun()
                    
                    if st.button("🗑️ Slett", key=f"delete_{i}"):
                        delete_departure(i)
                        st.rerun()
    else:
        st.info("❌ Ingen avganger matcher søkekriteriene")
else:
    st.info("📝 Ingen avganger registrert ennå")

# Statistikk og diagrammer
if st.session_state.departures and not df.empty:
    st.markdown("---")
    st.header("📊 Statistikk og diagrammer")
    
    # Beregn statistikk
    type_count = df['type'].value_counts().to_dict()
    status_count = df['status'].value_counts().to_dict()
    dest_count = df['destination'].value_counts().to_dict()
    
    # Vis nøkkeltall med ikoner
    st.subheader("📈 Nøkkeltall")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>📊 Totalt antall</h3><p style="font-size: 24px; font-weight: bold; color: #1E3A8A; margin: 0;">{len(df)}</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card tog"><h3>🚆 Tog</h3><p style="font-size: 24px; font-weight: bold; color: #1E3A8A; margin: 0;">{type_count.get("Tog", 0)}</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card bil"><h3>🚚 Bil</h3><p style="font-size: 24px; font-weight: bold; color: #1E3A8A; margin: 0;">{type_count.get("Bil", 0)}</p></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card tralle"><h3>🛻 Tralle</h3><p style="font-size: 24px; font-weight: bold; color: #1E3A8A; margin: 0;">{type_count.get("Tralle", 0)}</p></div>', unsafe_allow_html=True)
    
    # Diagrammer
    col1, col2 = st.columns(2)
    
    with col1:
        if type_count:
            fig_type = px.pie(
                values=list(type_count.values()),
                names=list(type_count.keys()),
                title="📊 Avganger per Type",
                color_discrete_sequence=['#6366F1', '#10B981', '#F59E0B', '#8B5CF6']
            )
            st.plotly_chart(fig_type, use_container_width=True)
    
    with col2:
        if dest_count:
            fig_dest = px.bar(
                x=list(dest_count.keys()),
                y=list(dest_count.values()),
                title="📍 Avganger per Destinasjon",
                labels={'x': 'Destinasjon', 'y': 'Antall'},
                color=list(dest_count.keys()),
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
            st.plotly_chart(fig_dest, use_container_width=True)

# Nedlastings- og administrasjonsknapper
st.markdown("---")
st.header("💾 Datahåndtering")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🗑️ Tøm alle avganger", type="secondary"):
        if st.session_state.departures:
            if st.checkbox("⚠️ Bekreft at du vil slette ALLE avganger"):
                clear_all_departures()
                st.rerun()
        else:
            show_toast("Ingen avganger å slette", "info")

with col2:
    csv_data = export_to_csv()
    if csv_data:
        st.download_button(
            label="📊 Eksporter til CSV",
            data=csv_data,
            file_name=f"avganger_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv"
        )

with col3:
    backup_json = backup_data()
    if backup_json:
        st.download_button(
            label="💾 Last ned backup (JSON)",
            data=backup_json,
            file_name=f"backup_avganger_{datetime.now().strftime('%Y-%m-%d')}.json",
            mime="application/json"
        )

with col4:
    uploaded_file = st.file_uploader("📤 Last opp backup", type="json", key="backup_uploader")
    if uploaded_file is not None:
        load_backup(uploaded_file)

# Vis redigeringsskjema hvis vi er i redigeringsmodus
if st.session_state.editing_index is not None and st.session_state.edit_data:
    st.markdown('<div class="edit-form">', unsafe_allow_html=True)
    st.markdown("### 🔧 Rediger Avgang")
    
    with st.form("edit_form"):
        # Bruk unike nøkler for redigeringsskjemaet
        edit_unit_number = st.text_input(
            "📋 Enhetsnummer:", 
            value=st.session_state.edit_data['unitNumber'],
            key="edit_unit_number"
        ).upper()
        
        edit_destination = st.selectbox(
            "📍 Destinasjon:",
            ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"],
            index=["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"].index(
                st.session_state.edit_data['destination']
            ),
            key="edit_destination"
        )
        
        # Konverter tidstreng til time-objekt
        try:
            time_obj = datetime.strptime(st.session_state.edit_data['time'], "%H:%M").time()
        except:
            time_obj = datetime.now().time()
            
        edit_time = st.time_input("⏰ Avgangstid:", value=time_obj, key="edit_time")
        edit_gate = st.text_input("🚪 Luke:", value=st.session_state.edit_data['gate'], key="edit_gate")
        
        edit_type = st.selectbox(
            "🚚 Avgangstype:",
            ["Tog", "Bil", "Tralle", "Modul"],
            index=["Tog", "Bil", "Tralle", "Modul"].index(st.session_state.edit_data['type']),
            key="edit_type"
        )
        
        edit_status = st.selectbox(
            "📊 Status:",
            ["Levert", "I lager", "Underlasting"],
            index=["Levert", "I lager", "Underlasting"].index(st.session_state.edit_data['status']),
            key="edit_status"
        )
        
        edit_comment = st.text_area(
            "💬 Kommentar (valgfritt):", 
            value=st.session_state.edit_data['comment'] if st.session_state.edit_data['comment'] else "",
            key="edit_comment"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Oppdater Avgang")
        with col2:
            cancel = st.form_submit_button("❌ Avbryt")
        
        if submitted:
            if not all([edit_unit_number, edit_destination, edit_gate, edit_type, edit_status]):
                show_toast("Vennligst fyll ut alle obligatoriske felter", "error")
            else:
                time_str = edit_time.strftime("%H:%M")
                update_departure(
                    st.session_state.editing_index,
                    edit_unit_number,
                    edit_destination,
                    time_str,
                    edit_gate,
                    edit_type,
                    edit_status,
                    edit_comment
                )
                st.rerun()
        
        if cancel:
            st.session_state.editing_index = None
            st.session_state.edit_data = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)