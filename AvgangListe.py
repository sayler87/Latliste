import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
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

# --- LAST DATA ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in   # Sikrer ID
                    if "id" not in item:
                        item["id"] = int(datetime.now().timestamp())
                return data
        except Exception as e:
            st.warning(f"Feil ved lasting: {e}")
            return []
    return []

# --- LAGRE DATA ---
def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Lagring feilet: {e}")

# --- SESSION STATE ---
if 'departures' not in st.session_state:
    st.session_state.departures = load_data()

if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

# --- TITTEL ---
st.markdown("<h1 style='text-align: center;'>🚛 Transportsystem</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Registrering og oversikt over avganger</p>", unsafe_allow_html=True)
st.markdown("---")

# === SIDEBAR: SKJEMA ===
st.sidebar.header("🚛 Registrer / Oppdater Avgang")

# Hent redigeringsdata
editing = None
if st.session_state.editing_id is not None:
    editing = next((d for d in st.session_state.departures if d["id"] == st.session_state.editing_id), None)

# Skjema-felter
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

# Knapp: Registrer / Oppdater
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
        st.rerun()

# Avbryt redigering
if st.session_state.editing_id is not None:
    if st.sidebar.button("❌ Avbryt redigering"):
        st.session_state.editing_id = None
        st.rerun()

st.sidebar.markdown("---")

# === HOVEDINNHOLD: OVERSIKT ===
st.header("📋 Oversikt over Avganger")

# Søk og filtrering
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("Søk på enhetsnummer eller destinasjon", "")
with col2:
    selected_dest = st.selectbox("Destinasjon", ["Alle destinasjoner"] + DESTINATIONS)

# Filtrer
filtered = st.session_state.departures
if search_term:
    filtered = [d for d in filtered if search_term.lower() in d["unitNumber"].lower() or search_term.lower() in d["destination"].lower()]
if selected_dest != "Alle destinasjoner":
    filtered = [d for d in filtered if d["destination"] == selected_dest]

# Vis tabell med handlinger
if filtered:
    df = pd.DataFrame(filtered)
    df = df[["id", "unitNumber", "destination", "time", "gate", "type", "status", "comment"]]

    # Legg til kolonner for visning
    def format_row(row):
        icon = TYPE_ICONS.get(row["type"], "")
        t_color = {"Tog": "red", "Bil": "orange", "Tralle": "blue", "Modul": "purple"}.get(row["type"], "black")
        s_color = {"Levert": "green", "I lager": "blue", "Underlasting": "orange"}.get(row["status"], "black")
        comment = row["comment"] or "<em>Ingen</em>"
        return pd.Series([
            row["unitNumber"],
            row["destination"],
            row["time"],
            row["gate"],
            f'<span style="color:{t_color}; font-weight:bold;">{icon} {row["type"]}</span>',
            f'<span style="color:{s_color}; font-weight:bold;">{row["status"]}</span>',
            comment,
            f"""
            <div style="display: flex; gap: 5px;">
                <button onclick="window.location.reload()" style="padding:5px 10px; font-size:12px;">✏️ Rediger</button>
                <button onclick="window.location.reload()" style="padding:5px 10px; font-size:12px;">🗑️ Slett</button>
            </div>
            """
        ])

    # Men: Streamlit tillater IKKE onclick i HTML
    # Derfor bruker vi st.form + st.button i en løkke
    st.markdown("""
    <style>
    .action-btn { padding: 5px 10px; font-size: 12px; margin: 2px; }
    </style>
    """, unsafe_allow_html=True)

    for idx, d in enumerate(filtered):
        cols = st.columns([2, 2, 2, 1, 1, 1, 1, 2])
        cols[0].write(d["unitNumber"])
        cols[1].write(d["destination"])
        cols[2].write(d["time"])
        cols[3].write(d["gate"])
        cols[4].markdown(
            f'<span style="color:{{"Tog": "red", "Bil": "orange", "Tralle": "blue", "Modul": "purple"}}.get("{d["type"]}", "black")}; font-weight:bold;">'
            f'{TYPE_ICONS.get(d["type"], "")} {d["type"]}</span>',
            unsafe_allow_html=True
        )
        cols[5].markdown(
            f'<span style="color:{{"Levert": "green", "I lager": "blue", "Underlasting": "orange"}}.get("{d["status"]}", "black")}; font-weight:bold;">'
            f'{d["status"]}</span>',
            unsafe_allow_html=True
        )
        cols[6].write(d["comment"] or "*Ingen*")

        with cols[7]:
            # REDIGER KNAPP
            if st.button(f"✏️", key=f"edit_{d['id']}", help="Rediger"):
                st.session_state.editing_id = d["id"]
                st.rerun()

            # SLETT KNAPP
            if st.button(f"🗑️", key=f"del_{d['id']}", help="Slett"):
                st.session_state.departures = [x for x in st.session_state.departures if x["id"] != d["id"]]
                save_data(st.session_state.departures)
                st.success(f"✅ Avgang {d['unitNumber']} slettet!")
                st.rerun()

else:
    st.info("Ingen avganger funnet.")

# === SYSTEMHANDLINGER ===
st.markdown("---")
st.header("⚙️ Systemhandlinger")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🗑️ Tøm alle avganger"):
        if st.session_state.departures:
            if st.checkbox("✅ Bekreft: Slett ALT", key="confirm_clear_all"):
                st.session_state.departures = []
                save_data(st.session_state.departures)
                st.success("✅ Alt er tømt!")
                st.rerun()
        else:
            st.warning("Ingen avganger å slette.")

with col2:
    if st.button("🖨️ Skriv ut"):
        st.info("Bruk Ctrl+P for å skrive ut siden (nettleserens utskrift).")

with col3:
    if st.button("📄 Eksporter til CSV"):
        df_export = pd.DataFrame(st.session_state.departures)
        csv = df_export.to_csv(index=False, encoding='utf-8')
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:text/csv;base64,{b64}" download="avganger.csv">⬇️ Last ned CSV</a>'
        st.markdown(href, unsafe_allow_html=True)

with col4:
    if st.button("💾 Last ned JSON"):
        json_str = json.dumps(st.session_state.departures, ensure_ascii=False, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:application/json;base64,{b64}" download="backup.json">⬇️ Last ned JSON</a>'
        st.markdown(href, unsafe_allow_html=True)

# === STATISTIKK ===
st.markdown("---")
st.header("📊 Statistikk og Diagrammer")

if st.session_state.departures:
    df_full = pd.DataFrame(st.session_state.departures)

    try:
        import plotly.express as px

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Per Type")
            type_counts = df_full["type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            type_counts["label"] = type_counts["type"].map(lambda t: f"{TYPE_ICONS.get(t, '')} {t}")
            fig1 = px.pie(type_counts, values="count", names="label", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Per Destinasjon")
            dest_counts = df_full["destination"].value_counts().reset_index()
            dest_counts.columns = ["destination", "count"]
            fig2 = px.bar(dest_counts, x="destination", y="count", color="count", color_continuous_scale="Blues")
            st.plotly_chart(fig2, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Totalt", len(df_full))
        c2.metric("Levert", int((df_full["status"] == "Levert").sum()))
        c3.metric("I lager", int((df_full["status"] == "I lager").sum()))

    except ImportError:
        st.warning("Installer `plotly` for diagrammer: legg til i `requirements.txt`")

else:
    st.info("Ingen data tilgjengelig for statistikk.")

# === FOOTER ===
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"<p style='text-align: center; color: #888; font-size: 0.9em;'>"
    f"Utskriftsdato: {datetime.now().strftime('%d.%m.%Y kl. %H:%M')}</p>",
    unsafe_allow_html=True
)