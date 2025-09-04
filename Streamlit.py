import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Fil for lagring
DATA_FILE = "departures.json"

# Last data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Konverter tilbake til liste hvis nødvendig
            if isinstance(data, list):
                return data
    return []

# Lagre data
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Initialiser session state
if 'departures' not in st.session_state:
    st.session_state.departures = load_data()

if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# Emojis for typer
type_icons = {
    "Tog": "🚂",
    "Bil": "🚗",
    "Tralle": "🛒",
    "Modul": "📦"
}

# --- SIDEBAR: Registrer ny avgang ---
st.sidebar.title("🚛 Registrer Avgang")
form = st.sidebar.form(key="departure_form")

with form:
    unit_number = st.text_input(
        "Enhetsnummer *", 
        value=st.session_state.get('edit_unit', ''),
        placeholder="F.eks. TOG001"
    ).upper()

    destination = st.selectbox(
        "Destinasjon *",
        ["", "TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"]
    )

    time = st.time_input("Avgangstid *", value=datetime.now().time())
    gate = st.text_input("Luke *", placeholder="F.eks. A1, B2")
    
    transport_type = st.selectbox(
        "Type *",
        ["", "Tog", "Bil", "Tralle", "Modul"]
    )

    status = st.selectbox(
        "Status *",
        ["", "LEVERT", "LAGER", "planlaget", "LASTER NÅ"]
    )

    comment = st.text_area("Kommentar", placeholder="F.eks. Forsinket, laster nå...")

    submit = st.form_submit_button("✅ Registrer Avgang")

# Håndter form
if submit:
    if not all([unit_number, destination, gate, transport_type, status]):
        st.sidebar.error("Vennligst fyll ut alle obligatoriske felt.")
    elif st.session_state.editing_id is None and any(d['unitNumber'] == unit_number for d in st.session_state.departures):
        st.sidebar.error(f"Enhetsnummer {unit_number} eksisterer allerede!")
    else:
        # Formater tid
        time_str = time.strftime("%H:%M")

        new_entry = {
            "id": st.session_state.editing_id or int(datetime.now().timestamp()),
            "unitNumber": unit_number,
            "destination": destination,
            "time": time_str,
            "gate": gate,
            "type": transport_type,
            "status": status,
            "comment": comment if comment else None
        }

        if st.session_state.editing_id is not None:
            # Oppdater eksisterende
            idx = next(i for i, d in enumerate(st.session_state.departures) if d["id"] == st.session_state.editing_id)
            st.session_state.departures[idx] = new_entry
            st.session_state.editing_id = None
            st.session_state.edit_unit = ""
            st.success("✅ Avgang oppdatert!")
        else:
            # Ny avgang
            st.session_state.departures.append(new_entry)
            st.success("✅ Avgang registrert!")

        # Lagre til fil
        save_data(st.session_state.departures)

# --- Hovedside ---
st.title("🚛 Transportsystem")
st.markdown("Registrering og oversikt over alle avganger")

# --- Søk og filtrering ---
col1, col2 = st.columns([3, 2])
with col1:
    search_term = st.text_input("Søk på enhetsnummer eller destinasjon")
with col2:
    filter_dest = st.selectbox("Filter destinasjon", ["Alle destinasjoner"] + [
        "TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"
    ])

# --- Filtrering og sortering ---
filtered = st.session_state.departures

if search_term:
    filtered = [d for d in filtered if search_term.lower() in (d['unitNumber'] + d['destination']).lower()]

if filter_dest != "Alle destinasjoner":
    filtered = [d for d in filtered if d['destination'] == filter_dest]

# Konverter til DataFrame for enklere visning
df = pd.DataFrame(filtered)
if not df.empty:
    df = df.sort_values(by="time")

# --- Statistikk ---
st.markdown("### 📊 Statistikk")
cols = st.columns(5)
types = ["Tog", "Bil", "Tralle", "Modul"]
for i, t in enumerate(types):
    count = df[df['type'] == t].shape[0] if not df.empty else 0
    with cols[i]:
        st.metric(f"{type_icons[t]} {t}", count)

if not df.empty:
    dest_counts = df['destination'].value_counts()
    with cols[4]:
        top_dest = dest_counts.index[0] if len(dest_counts) > 0 else "–"
        st.metric("🎯 Topp destinasjon", top_dest)

# --- Tabell med handlinger ---
st.markdown("### 📋 Oversikt over Avganger")

if df.empty:
    st.info("Ingen avganger registrert.")
else:
    # Legg til kolonner for visning
    display_df = df.copy()
    display_df['type_display'] = display_df['type'].map(lambda t: f"{type_icons.get(t, '')} **{t}**")
    display_df['status_color'] = display_df['status'].map(
        lambda s: f"<span style='color:{'#27ae60' if s == 'LEVERT' else '#3498db' if s == 'LAGER' else '#e74c3c'}; font-weight:bold'>{s}</span>"
    )
    display_df['comment'] = display_df['comment'].fillna("Ingen")

    # Bare de kolonnene vi vil vise
    display_df = display_df[[
        'unitNumber', 'destination', 'time', 'gate', 'type_display', 'status_color', 'comment'
    ]]

    # Vis tabell som HTML
    html_table = display_df.to_html(escape=False, index=False, table_id="departures-table", classes="table")
    st.markdown(
        f"""
        <style>
            #departures-table {{ width: 100%; border-collapse: collapse; }}
            #departures-table th, #departures-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
            #departures-table tr:hover {{ background-color: #f5f5f5; }}
            #departures-table th {{ background-color: #2c3e50; color: white; }}
        </style>
        {html_table}
        """,
        unsafe_allow_html=True
    )

    # Handlinger for hver rad
    for _, row in df.iterrows():
        cols = st.columns([6, 1, 1])
        with cols[1]:
            if st.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.editing_id = row['id']
                st.session_state.edit_unit = row['unitNumber']
                st.rerun()
        with cols[2]:
            if st.button("🗑️", key=f"del_{row['id']}"):
                st.session_state.departures = [d for d in st.session_state.departures if d['id'] != row['id']]
                save_data(st.session_state.departures)
                st.success("Avgang slettet!")
                st.rerun()

# --- Systemhandlinger ---
st.markdown("### ⚙️ Systemhandlinger")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("🗑️ Tøm alle"):
        if st.session_state.departures:
            if st.checkbox("Bekreft sletting av alle data", key="confirm_clear"):
                st.session_state.departures = []
                save_data(st.session_state.departures)
                st.success("Alle avganger slettet!")
                st.rerun()
        else:
            st.warning("Ingen avganger å slette.")

with col2:
    @st.experimental_memo
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    if not df.empty:
        csv = convert_df_to_csv(df)
        st.download_button("🖨️ Skriv ut / CSV", csv, f"avganger_{datetime.now().date()}.csv", "text/csv")
    else:
        st.button("🖨️ Skriv ut / CSV", disabled=True)

with col3:
    @st.experimental_memo
    def export_json():
        return json.dumps(st.session_state.departures, ensure_ascii=False, indent=2).encode('utf-8')

    if st.session_state.departures:
        st.download_button("💾 Backup (JSON)", export_json(), f"backup_{datetime.now().date()}.json", "application/json")
    else:
        st.button("💾 Backup", disabled=True)

with col4:
    uploaded_file = st.file_uploader("📂 Last opp JSON", type=["json"], label_visibility="collapsed")
    if uploaded_file:
        try:
            imported = json.load(uploaded_file)
            if isinstance(imported, list) and all('id' in d and 'unitNumber' in d for d in imported):
                overwrite = st.radio("Hvordan vil du importere?", ["Erstatt", "Legg til"])
                if st.button("Importer nå"):
                    if overwrite == "Erstatt":
                        st.session_state.departures = imported
                    else:
                        existing_ids = {d['id'] for d in st.session_state.departures}
                        added = 0
                        for item in imported:
                            if item['id'] not in existing_ids:
                                st.session_state.departures.append(item)
                                added += 1
                        st.success(f"{added} nye avganger lagt til.")
                    save_data(st.session_state.departures)
                    st.success("Data importert!")
                    st.rerun()
            else:
                st.error("Ugyldig JSON-format.")
        except Exception as e:
            st.error(f"Feil ved import: {e}")

with col5:
    if st.button("↻ Oppdater"):
        st.rerun()