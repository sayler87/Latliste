import streamlit as st
import pandas as pd
import json
from datetime import datetime

# --- Datahåndtering ---
DATA_FILE = "departures.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return pd.DataFrame(json.load(f))
    except:
        return pd.DataFrame(columns=["id", "unitNumber", "destination", "time", "gate", "type", "status", "comment"])

def save_data(df):
    with open(DATA_FILE, "w") as f:
        json.dump(df.to_dict("records"), f, indent=2)

# --- UI ---
st.set_page_config("🚛 Transportsystem", layout="wide")
st.title("🚛 Transportsystem")
st.markdown("Registrering og oversikt over alle avganger")

df = load_data()

with st.form("registrer_avgang"):
    col1, col2 = st.columns(2)
    unit = col1.text_input("Enhetsnummer *").upper()
    dest = col2.selectbox("Destinasjon *", ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"])
    time = col1.time_input("Tid *", value="now")
    gate = col2.text_input("Luke *")
    typ = col1.selectbox("Type *", ["Tog", "Bil", "Tralle", "Modul"])
    status = col2.selectbox("Status *", ["LEVERT", "LAGER", "planlaget", "LASTER NÅ"])
    comment = st.text_area("Kommentar")
    if st.form_submit_button("✅ Registrer"):
        if not unit or not dest or not gate or not typ or not status:
            st.error("Vennligst fyll ut alle obligatoriske felt.")
        elif unit in df["unitNumber"].values:
            st.warning("Enhetsnummer eksisterer allerede!")
        else:
            new_row = {
                "id": int(datetime.now().timestamp()),
                "unitNumber": unit,
                "destination": dest,
                "time": time.strftime("%H:%M"),
                "gate": gate,
                "type": typ,
                "status": status,
                "comment": comment or ""
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Avgang registrert!")
            st.rerun()

# Vis tabell
st.dataframe(df, use_container_width=True)

# Eksporter
if st.button("📥 Eksporter til CSV"):
    csv = df.to_csv(index=False)
    st.download_button("Last ned CSV", csv, "avganger.csv", "text/csv")