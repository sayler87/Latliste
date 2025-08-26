import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
import base64

# Fil for lagring
DATA_FILE = "departures.json"

# Ikon-ordbok
TYPE_ICONS = {
    "Tog": "🚂",
    "Bil": "🚗",
    "Tralle": "🛒",
    "Modul": "📦"
}

DESTINATIONS = ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"]

# Last data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                # Sikre at alle poster har ID
                for item in data:
                    if "id" not in item:
                        item["id"] = int(datetime.now().timestamp())
                return data
            except:
                return []
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

# Tittel
st.markdown("<h1 style='text-align: center;'>🚛 Transportsystem</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Registrering og oversikt over avganger</p>", unsafe_allow_html=True)
st.markdown("---")

# --- SKJEMA ---
st.sidebar.header("🚛 Registrer Avgang")

# Hent redigeringsdata hvis eksisterer
editing = None
if st.session_state.editing_id is not None:
    editing = next((d for d in st.session_state.departures if d["id"] == st.session_state.editing_id), None)

unit_number = st.sidebar.text_input(
    "Enhetsnummer *",
    value=editing["unitNumber"].upper() if editing else "",
    placeholder="F.eks. TOG001"
).upper()

destination = st.sidebar.selectbox(
    "Destinasjon *",
    DESTINATIONS,
    index=DESTINATIONS.index(editing["destination"]) if editing and editing["destination"] in DESTINATIONS else 0
)

time = st.sidebar.text_input(
    "Avgangstid *",
    value=editing["time"] if editing else datetime.now().strftime("%H:%M")
)

gate = st.sidebar.text_input(
    "Luke *",
    value=editing["gate"] if editing else "",
    placeholder="F.eks. A1, B2"
)

type_ = st.sidebar.selectbox(
    "Type *",
    ["Tog", "Bil", "Tralle", "Modul"],
    index=["Tog", "Bil", "Tralle", "Modul"].index(editing["type"]) if editing else 0
)

status = st.sidebar.selectbox(
    "Status *",
    ["Levert", "I lager", "Underlasting"],
    index=["Levert", "I lager", "Underlasting"].index(editing["status"]) if editing else 0
)

comment = st.sidebar.text_area(
    "Kommentar",
    value=editing["comment"] if editing and editing["comment"] else ""
)

# Knapp for registrering/opdatering
if st.sidebar.button("✅ Registrer Avgang" if not editing else "🔁 Oppdater Avgang"):
    if not all([unit_number, destination, time, gate, type_, status]):
        st.sidebar.error("Vennligst fyll ut alle obligatoriske felt.")
    elif not editing and any(d["unitNumber"] == unit_number for d in st.session_state.departures):
        st.sidebar.error(f"Enhetsnummer {unit_number} eksisterer allerede!")
    else:
        new_entry = {
            "id": editing["id"] if editing else int(datetime.now().timestamp()),
            "unitNumber": unit_number,
            "destination": destination,
            "time": time,
            "gate": gate,
            "type": type_,
            "status": status,
            "comment": comment if comment else None
        }

        if editing:
            idx = next(i for i, d in enumerate(st.session_state.departures) if d["id"] == editing["id"])
            st.session_state.departures[idx] = new_entry
            st.success(f"✅ Avgang {unit_number} oppdatert!")
            st.session_state.editing_id = None
        else:
            st.session_state.departures.append(new_entry)
            st.success(f"✅ Avgang {unit_number} registrert!")

        save_data(st.session_state.departures)

# Knapp for å avbryte redigering
if st.session_state.editing_id is not None:
    if st.sidebar.button("❌ Avbryt redigering"):
        st.session_state.editing_id = None
        st.experimental_rerun()

st.sidebar.markdown("---")

# --- SØK OG FILTRERING ---
st.header("📋 Oversikt over Avganger")

search_term = st.text_input("Søk på enhetsnummer eller destinasjon...")
selected_dest = st.selectbox("Filtrer på destinasjon", ["Alle destinasjoner"] + DESTINATIONS)

# Filtrer data
filtered = st.session_state.departures
if search_term:
    filtered = [d for d in filtered if search_term.lower() in d["unitNumber"].lower() or search_term.lower() in d["destination"].lower()]
if selected_dest != "Alle destinasjoner":
    filtered = [d for d in filtered if d["destination"] == selected_dest]

# Konverter til DataFrame for enklere håndtering
df = pd.DataFrame(filtered) if filtered else pd.DataFrame(columns=["unitNumber", "destination", "time", "gate", "type", "status", "comment", "id"])
df = df[["unitNumber", "destination", "time", "gate", "type", "status", "comment"]]

# Vis tabell
if not df.empty:
    # Legg til ikoner og farger
    def format_row(row):
        icon = TYPE_ICONS.get(row["type"], "")
        type_color = {"Tog": "color:red;", "Bil": "color:orange;", "Tralle": "color:blue;", "Modul": "color:purple;"}.get(row["type"], "")
        status_color = {"Levert": "color:green;", "I lager": "color:blue;", "Underlasting": "color:orange;"}.get(row["status"], "")
        comment = row["comment"] or "<em>Ingen</em>"
        return pd.Series([
            row["unitNumber"],
            row["destination"],
            row["time"],
            row["gate"],
            f'<span style="{type_color} font-weight:bold;">{icon} {row["type"]}</span>',
            f'<span style="{status_color} font-weight:bold;">{row["status"]}</span>',
            comment
        ])

    styled_df = df.apply(format_row, axis=1)
    styled_df.columns = ["Enhetsnummer", "Destinasjon", "Tid", "Luke", "Type", "Status", "Kommentar"]

    st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("Ingen avganger funnet.")

# --- HANDLINGSKNAPPER ---
st.markdown("---")
st.header("⚙️ Systemhandlinger")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🗑️ Tøm alle avganger"):
        if st.session_state.departures:
            if st.checkbox("Bekreft sletting av alle data", key="confirm_clear"):
                st.session_state.departures = []
                save_data(st.session_state.departures)
                st.success("✅ Alle avganger slettet!")
                st.experimental_rerun()
        else:
            st.warning("Ingen avganger å slette.")

with col2:
    if st.button("🖨️ Skriv ut"):
        st.info("Bruk nettleserens utskrift (Ctrl+P) for å skrive ut siden.")

with col3:
    if st.button("📄 Eksporter til CSV"):
        csv = pd.DataFrame(st.session_state.departures).to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="avganger.csv">Last ned CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

with col4:
    if st.button("💾 Last ned backup (JSON)"):
        json_str = json.dumps(st.session_state.departures, ensure_ascii=False, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="backup.json">Last ned JSON</a>'
        st.markdown(href, unsafe_allow_html=True)

# --- STATISTIKK OG DIAGRAMMER ---
st.markdown("---")
st.header("📊 Statistikk og Diagrammer")

if st.session_state.departures:
    df_full = pd.DataFrame(st.session_state.departures)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Avganger per Type")
        type_counts = df_full["type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        type_counts["icon"] = type_counts["type"].map(TYPE_ICONS)
        type_counts["label"] = type_counts["icon"] + " " + type_counts["type"]

        fig1 = px.pie(type_counts, values="count", names="label", title="Per Type")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Avganger per Destinasjon")
        dest_counts = df_full["destination"].value_counts().reset_index()
        dest_counts.columns = ["destination", "count"]

        fig2 = px.bar(dest_counts, x="destination", y="count", title="Per Destinasjon", color="count", color_continuous_scale="Blues")
        st.plotly_chart(fig2, use_container_width=True)

    # Statistikk-kort
    st.subheader("Statistikk")
    col1, col2, col3 = st.columns(3)
    col1.metric("Totalt", len(df_full))
    col2.metric("Levert", len(df_full[df_full["status"] == "Levert"]))
    col3.metric("I lager", len(df_full[df_full["status"] == "I lager"]))

    # Tabell med antall per type
    st.write("**Fordeling:**")
    st.dataframe(df_full.groupby("type").size().reset_index(name="Antall"))

else:
    st.info("Ingen data tilgjengelig for statistikk.")

# --- REDIGERING VIA KNAPPER I TABELL? ---
# (Vi kan legge til en kolonne med "Rediger"-knapp hvis ønskelig – fortell meg!)

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.9em;'>Utskriftsdato: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>", unsafe_allow_html=True)