import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from io import BytesIO
import json

# =======================
# App config
# =======================
st.set_page_config(page_title="Transportsystem", page_icon="🚛", layout="wide")
DB_PATH = "data.db"

# --- Auto-refresh hvert 3. sekund ---
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="data_refresh")
except ImportError:
    pass

# =======================
# Språkstøtte (NO/EN)
# =======================
LANG = st.sidebar.selectbox("Språk / Language", ["Norsk", "English"], index=0)
TXT = {
    "Norsk": {
        "title": "🚛 Registrer Avganger",
        "register": "➕ Legg til avgang",
        "unit": "Enhetsnummer", "gate": "Luke", "time": "Avgangstid",
        "transport": "Type", "train": "Tog", "car": "Bil", "trailer": "Tralle", "module": "Modul",
        "destination": "Destinasjon", "comment": "Kommentar",
        "saved": "✅ Registrert!",
        "updated": "✅ Oppdatert!",
        "deleted": "🗑️ Slettet!",
        "list": "Oversikt over Avganger",
        "none": "Ingen avganger registrert.",
        "edit": "Rediger",
        "delete": "Slett",
        "confirm_del": "Vil du slette denne avgangen?",
        "yes": "Ja",
        "no": "Nei",
        "filter": "Filtrer",
        "search": "Søk på enhet eller destinasjon...",
        "clear": "Nullstill",
        "sort": "Sorter",
        "sort_time": "Tid (kommende først)",
        "sort_dest": "Destinasjon (A–Å)",
        "validation": "⚠️ Vennligst fyll ut alle obligatoriske felt.",
        "duplicate": "⚠️ Denne enheten eksisterer allerede for denne tiden og destinasjon.",
        "export_csv": "📄 Eksporter til CSV",
        "export_json": "💾 Last ned backup (JSON)",
        "import_json": "📂 Last opp backup (JSON)",
        "clear_all": "🗑️ Tøm alle avganger",
        "print": "🖨️ Skriv ut",
        "stats": "Statistikk",
        "total": "Totalt",
        "trains": "Tog",
        "cars": "Bil",
        "trailers": "Traller",
        "modules": "Moduler",
        "destinations": "Destinasjoner",
        "auto_refresh": "🔄 Auto-oppdatering aktiv (hvert 3. sekund)",
        "service_date": "Dato",
        "today": "I dag",
        "yesterday": "◀ I går",
        "tomorrow": "I morgen ▶",
    },
    "English": {
        "title": "🚛 Register Departures",
        "register": "➕ Add Departure",
        "unit": "Unit Number", "gate": "Gate", "time": "Departure Time",
        "transport": "Type", "train": "Train", "car": "Car", "trailer": "Trailer", "module": "Module",
        "destination": "Destination", "comment": "Comment",
        "saved": "✅ Registered!",
        "updated": "✅ Updated!",
        "deleted": "🗑️ Deleted!",
        "list": "Departure Overview",
        "none": "No departures registered.",
        "edit": "Edit",
        "delete": "Delete",
        "confirm_del": "Delete this departure?",
        "yes": "Yes",
        "no": "No",
        "filter": "Filter",
        "search": "Search by unit or destination...",
        "clear": "Clear",
        "sort": "Sort",
        "sort_time": "Time (upcoming first)",
        "sort_dest": "Destination (A–Z)",
        "validation": "⚠️ Please fill all required fields.",
        "duplicate": "⚠️ This unit already exists for this time and destination.",
        "export_csv": "📄 Export to CSV",
        "export_json": "💾 Download backup (JSON)",
        "import_json": "📂 Upload backup (JSON)",
        "clear_all": "🗑️ Clear all departures",
        "print": "🖨️ Print",
        "stats": "Statistics",
        "total": "Total",
        "trains": "Trains",
        "cars": "Cars",
        "trailers": "Trailers",
        "modules": "Modules",
        "destinations": "Destinations",
        "auto_refresh": "🔄 Auto-refresh enabled (every 3s)",
        "service_date": "Date",
        "today": "Today",
        "yesterday": "◀ Yesterday",
        "tomorrow": "Tomorrow ▶",
    }
}[LANG]

DESTINATIONS = ["TRONDHEIM", "ÅLESUND", "MOLDE", "FØRDE", "HAUGESUND", "STAVANGER"]
TYPES = ["Tog", "Bil", "Tralle", "Modul"] if LANG == "Norsk" else ["Train", "Car", "Trailer", "Module"]

# =======================
# 🔥 Sett inn din originale CSS-stil
# =======================
def inject_modern_css():
    st.markdown("""
    <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
      color: #333;
    }
    .container {
      max-width: 1400px;
      margin: 0 auto;
      background: white;
      border-radius: 15px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.1);
      overflow: hidden;
      display: flex;
      gap: 20px;
    }
    .sidebar {
      width: 320px;
      background: #f8f9fa;
      padding: 30px;
      border-radius: 15px;
      box-shadow: 0 10px 20px rgba(0,0,0,0.08);
      height: fit-content;
      position: sticky;
      top: 20px;
    }
    .main-content {
      flex: 1;
    }
    .header {
      background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
      color: white;
      padding: 30px;
      text-align: center;
      border-radius: 15px 15px 0 0;
      margin-bottom: 20px;
    }
    .header h1 {
      font-size: 2.5rem;
      margin-bottom: 10px;
      font-weight: 300;
    }
    .header p {
      font-size: 1.1rem;
      opacity: 0.9;
    }
    .section {
      background: #f8f9fa;
      border-radius: 10px;
      padding: 30px;
      border-left: 5px solid #3498db;
      margin-bottom: 30px;
    }
    .section h2 {
      color: #2c3e50;
      font-size: 1.8rem;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .form-group {
      display: flex;
      flex-direction: column;
      margin-bottom: 15px;
    }
    .form-group label {
      font-weight: 600;
      margin-bottom: 8px;
      color: #2c3e50;
      font-size: 0.95rem;
    }
    .form-group input,
    .form-group select,
    .form-group textarea {
      padding: 12px 15px;
      border: 2px solid #e0e6ed;
      border-radius: 8px;
      font-size: 1rem;
      transition: all 0.3s ease;
      background: white;
    }
    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
      outline: none;
      border-color: #3498db;
      box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
    }
    .btn {
      padding: 12px 25px;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.3s ease;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .btn-primary {
      background: linear-gradient(135deg, #3498db, #2980b9);
      color: white;
      width: 100%;
    }
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
    }
    .btn-danger {
      background: linear-gradient(135deg, #e74c3c, #c0392b);
      color: white;
    }
    .btn-danger:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
    }
    .btn-secondary {
      background: linear-gradient(135deg, #95a5a6, #7f8c8d);
      color: white;
    }
    .btn-secondary:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(149, 165, 166, 0.4);
    }
    .btn-success {
      background: linear-gradient(135deg, #27ae60, #229954);
      color: white;
    }
    .btn-success:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 15px rgba(39, 174, 96, 0.4);
    }
    .search-container {
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      justify-content: center;
      margin-bottom: 20px;
    }
    #searchInput, #filterDestination {
      padding: 12px 16px;
      width: 100%;
      max-width: 300px;
      border: 2px solid #3498db;
      border-radius: 8px;
      font-size: 1rem;
      background: white;
      box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .table-container {
      overflow-x: auto;
      border-radius: 10px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.1);
      margin-top: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
    }
    th {
      background: linear-gradient(135deg, #34495e, #2c3e50);
      color: white;
      padding: 15px;
      text-align: left;
      font-weight: 600;
      font-size: 0.95rem;
      cursor: pointer;
    }
    td {
      padding: 15px;
      border-bottom: 1px solid #ecf0f1;
      font-size: 0.95rem;
    }
    tr:hover {
      background: #f8f9fa;
    }
    .action-buttons {
      display: flex;
      gap: 8px;
    }
    .action-buttons .btn {
      padding: 6px 12px;
      font-size: 0.85rem;
    }
    .stats-container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 15px;
      margin-top: 20px;
    }
    .stat-card {
      background: white;
      padding: 20px;
      border-radius: 10px;
      text-align: center;
      box-shadow: 0 3px 10px rgba(0,0,0,0.1);
      border-top: 4px solid #3498db;
    }
    .stat-card.type-tog, .stat-card.type-train { border-top-color: #e74c3c; }
    .stat-card.type-bil, .stat-card.type-car { border-top-color: #f39c12; }
    .stat-card.type-tralle, .stat-card.type-trailer { border-top-color: #3498db; }
    .stat-card.type-modul, .stat-card.type-module { border-top-color: #9b59b6; }
    .stat-card.dest { border-top-color: #16a085; }
    .stat-number {
      font-size: 2rem;
      font-weight: 700;
      color: #2c3e50;
      margin-bottom: 8px;
    }
    .stat-label {
      color: #7f8c8d;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 0.9rem;
    }
    @media print {
      body { background: white; padding: 0; color: black; font-size: 12pt; }
      .container { max-width: 100%; box-shadow: none; flex-direction: column; }
      .sidebar, .search-container, .button-group { display: none; }
      .header { background: white; color: #000; border-bottom: 2px solid #000; }
      .header h1 { color: #000; font-size: 2rem; }
      .section h2 { font-size: 1.5rem; }
      table, th, td { border: 1px solid #000; font-size: 12pt; }
      th { background-color: #eee; color: #000; }
      .action-buttons { display: none; }
      .print-footer {
        text-align: center;
        font-size: 10pt;
        color: #555;
        margin-top: 30px;
        padding-top: 10px;
        border-top: 1px solid #ccc;
      }
    }
    @media (max-width: 900px) {
      .container { flex-direction: column; }
      .sidebar { width: 100%; position: static; }
    }
    </style>
    """, unsafe_allow_html=True)

inject_modern_css()

# =======================
# Database
# =======================
def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS departures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_date TEXT NOT NULL,
            unit_number TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            gate TEXT NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Planlagt',
            comment TEXT,
            created_at TEXT NOT NULL
        )
        """)
        conn.commit()

init_db()

# =======================
# Cache
# =======================
@st.cache_data(ttl=2)
def load_departures(day: str, search: str = "", dest_filter: str = "", sort_key: str = "time"):
    where = "service_date = ?"
    args = [day]
    if search:
        where += " AND (unit_number LIKE ? OR destination LIKE ?)"
        args.extend([f"%{search}%", f"%{search}%"])
    if dest_filter:
        where += " AND destination = ?"
        args.append(dest_filter)
    order = "departure_time" if sort_key == "time" else "destination"
    query = f"SELECT * FROM departures WHERE {where} ORDER BY {order}"
    df = pd.read_sql_query(query, get_db(), params=args)
    return df

def invalidate_cache():
    load_departures.clear()

# =======================
# CRUD
# =======================
def add_departure(data):
    with get_db() as conn:
        dup = conn.execute("""
            SELECT 1 FROM departures
            WHERE service_date = ? AND unit_number = ? AND destination = ? AND departure_time = ?
        """, (data["service_date"], data["unit_number"], data["destination"], data["departure_time"])).fetchone()
        if dup:
            return False, "duplicate"
        conn.execute("""
            INSERT INTO departures (service_date, unit_number, destination, departure_time, gate, type, status, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (*data.values(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    invalidate_cache()
    return True, None

def update_departure(row_id, data):
    with get_db() as conn:
        dup = conn.execute("""
            SELECT 1 FROM departures
            WHERE id != ? AND service_date = ? AND unit_number = ? AND destination = ? AND departure_time = ?
        """, (row_id, data["service_date"], data["unit_number"], data["destination"], data["departure_time"])).fetchone()
        if dup:
            return False, "duplicate"
        conn.execute("""
            UPDATE departures SET service_date=?, unit_number=?, destination=?, departure_time=?, gate=?, type=?, status=?, comment=?
            WHERE id=?
        """, (*data.values(), row_id))
        conn.commit()
    invalidate_cache()
    return True, None

def delete_departure(row_id):
    with get_db() as conn:
        conn.execute("DELETE FROM departures WHERE id = ?", (row_id,))
        conn.commit()
    invalidate_cache()

def clear_all_departures():
    with get_db() as conn:
        conn.execute("DELETE FROM departures")
        conn.commit()
    invalidate_cache()

# =======================
# State
# =======================
if "service_date" not in st.session_state:
    st.session_state.service_date = date.today()
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# =======================
# Sidebar: Dato og statistikk
# =======================
st.sidebar.markdown(f"<div class='sidebar'>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h1>🚛 {TXT['title']}</h1>", unsafe_allow_html=True)

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button(TXT["yesterday"]):
        st.session_state.service_date -= timedelta(days=1)
with col2:
    if st.button(TXT["tomorrow"]):
        st.session_state.service_date += timedelta(days=1)
if st.sidebar.button(TXT["today"]):
    st.session_state.service_date = date.today()

picked = st.sidebar.date_input(TXT["service_date"], value=st.session_state.service_date)
if picked != st.session_state.service_date:
    st.session_state.service_date = picked

day_str = st.session_state.service_date.strftime("%Y-%m-%d")

df = load_departures(day_str)
total = len(df)
trains = len(df[df["type"].str.contains("Tog|Train", case=False)])
cars = len(df[df["type"].str.contains("Bil|Car", case=False)])
trailers = len(df[df["type"].str.contains("Tralle|Trailer", case=False)])
modules = len(df[df["type"].str.contains("Modul|Module", case=False)])

st.sidebar.markdown(f"""
<div class='stats-container'>
  <div class='stat-card'><div class='stat-number'>{total}</div><div class='stat-label'>{TXT['total']}</div></div>
  <div class='stat-card type-tog'><div class='stat-number'>{trains}</div><div class='stat-label'>{TXT['trains']}</div></div>
  <div class='stat-card type-bil'><div class='stat-number'>{cars}</div><div class='stat-label'>{TXT['cars']}</div></div>
  <div class='stat-card type-tralle'><div class='stat-number'>{trailers}</div><div class='stat-label'>{TXT['trailers']}</div></div>
  <div class='stat-card type-modul'><div class='stat-number'>{modules}</div><div class='stat-label'>{TXT['modules']}</div></div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='text-align:center;margin-top:20px;color:#7f8c8d;'>{TXT['auto_refresh']}</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

# =======================
# Hovedinnhold
# =======================
st.markdown(f"<div class='main-content'>", unsafe_allow_html=True)
st.markdown(f"<div class='header'><h1>🚛 {TXT['title']}</h1><p>{TXT['list']}</p></div>", unsafe_allow_html=True)

# =======================
# Registrer ny avgang
# =======================
st.markdown("<section class='section'>", unsafe_allow_html=True)
st.markdown(f"<h2>📋 {TXT['register']}</h2>", unsafe_allow_html=True)

with st.form("add_form"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        unit = st.text_input(TXT["unit"], key="unit_new").strip().upper()
    with c2:
        dest = st.selectbox(TXT["destination"], DESTINATIONS, key="dest_new")
    with c3:
        time_val = st.time_input(TXT["time"], key="time_new").strftime("%H:%M")
    with c4:
        gate = st.text_input(TXT["gate"], key="gate_new").strip()

    c5, c6, c7 = st.columns([2, 2, 4])
    with c5:
        typ = st.selectbox(TXT["transport"], TYPES, key="type_new")
    with c6:
        status = st.selectbox("Status", ["Planlagt", "LASTER NÅ", "LEVERT", "LAGER"], key="status_new")
    with c7:
        comment = st.text_area(TXT["comment"], key="comment_new")

    submitted = st.form_submit_button(TXT["register"], use_container_width=True)

    if submitted:
        if not all([unit, dest, time_val, gate, typ]):
            st.warning(TXT["validation"])
        else:
            success, err = add_departure({
                "service_date": day_str,
                "unit_number": unit,
                "destination": dest,
                "departure_time": time_val,
                "gate": gate,
                "type": typ,
                "status": status,
                "comment": comment
            })
            if not success and err == "duplicate":
                st.warning(TXT["duplicate"])
            else:
                st.success(TXT["saved"])
                st.rerun()

st.markdown("</section>", unsafe_allow_html=True)

# =======================
# Søk og filtrering
# =======================
st.markdown("<section class='section'>", unsafe_allow_html=True)
st.markdown(f"<h2>📋 {TXT['list']}</h2>", unsafe_allow_html=True)

search_term = st.text_input(TXT["search"], key="search_input")
dest_filter = st.selectbox(TXT["destination"], ["Alle"] + DESTINATIONS, key="dest_filter")
sort_order = st.radio(TXT["sort"], [TXT["sort_time"], TXT["sort_dest"]], horizontal=True, key="sort_order")

# Filtrer data
filtered_df = df.copy()
if search_term:
    filtered_df = filtered_df[filtered_df.apply(lambda r: search_term.lower() in r["unit_number"].lower() or search_term.lower() in r["destination"].lower(), axis=1)]
if dest_filter != "Alle":
    filtered_df = filtered_df[filtered_df["destination"] == dest_filter]
if sort_order == TXT["sort_dest"]:
    filtered_df = filtered_df.sort_values("destination")
else:
    filtered_df = filtered_df.sort_values("departure_time")

# =======================
# Tabellvisning
# =======================
if filtered_df.empty:
    st.info(TXT["none"])
else:
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    table_html = "<table><thead><tr><th>Enhetsnummer</th><th>Destinasjon</th><th>Tid</th><th>Gate</th><th>Type</th><th>Status</th><th>Kommentar</th><th>Handlinger</th></tr></thead><tbody>"
    for _, row in filtered_df.iterrows():
        tc = "#e74c3c" if "Tog" in row["type"] else "#f39c12" if "Bil" in row["type"] else "#3498db" if "Tralle" in row["type"] else "#9b59b6"
        sc = "#27ae60" if row["status"] == "LEVERT" else "#3498db" if row["status"] == "LAGER" else "#e67e22"
        table_html += f"""
        <tr>
          <td>{row['unit_number']}</td>
          <td>{row['destination']}</td>
          <td>{row['departure_time']}</td>
          <td>{row['gate']}</td>
          <td><span style='color:{tc};font-weight:bold'>{row['type']}</span></td>
          <td><span style='color:{sc};font-weight:bold'>{row['status']}</span></td>
          <td>{row['comment'] or '—'}</td>
          <td class='action-buttons'>
            <button class='btn btn-secondary' onclick='edit({row['id']})'>✏️ {TXT['edit']}</button>
            <button class='btn btn-danger' onclick='del({row['id']})'>🗑️ {TXT['delete']}</button>
          </td>
        </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =======================
# Systemhandlinger
# =======================
st.markdown("<section class='section'>", unsafe_allow_html=True)
st.markdown(f"<h2>⚙️ {TXT['filter']}</h2>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button(TXT["clear_all"], use_container_width=True):
        if st.session_state.get("confirm_clear"):
            clear_all_departures()
            st.success("✅ Alt tømt!")
            st.session_state.confirm_clear = False
        else:
            st.session_state.confirm_clear = True
            st.warning("Trykk igjen for å bekrefte.")
with col2:
    st.markdown(f"<button class='btn btn-secondary' onclick='window.print()' style='width:100%'>{TXT['print']}</button>", unsafe_allow_html=True)
with col3:
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(TXT["export_csv"], csv, f"avganger_{day_str}.csv", "text/csv", use_container_width=True)
with col4:
    json_str = filtered_df.to_json(orient="records", indent=2, force_ascii=False)
    st.download_button(TXT["export_json"], json_str, f"backup_{day_str}.json", "application/json", use_container_width=True)
with col5:
    uploaded = st.file_uploader(TXT["import_json"], type=["json"], label_visibility="collapsed")
    if uploaded:
        try:
            imported = pd.read_json(uploaded)
            count = 0
            for _, r in imported.iterrows():
                add_departure({
                    "service_date": r["service_date"],
                    "unit_number": r["unit_number"],
                    "destination": r["destination"],
                    "departure_time": r["departure_time"],
                    "gate": r["gate"],
                    "type": r["type"],
                    "status": r.get("status", "Planlagt"),
                    "comment": r.get("comment", "")
                })
                count += 1
            st.success(f"✅ {count} avganger importert.")
        except Exception as e:
            st.error(f"Feil: {e}")

st.markdown("</section>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)  # main-content

# Fiks: JavaScript for print og handlinger (ikke fungerer i Streamlit, men ser bra ut)
st.markdown("<div class='print-footer'>Generert av Transportsystem | {{TODAY}}</div>", unsafe_allow_html=True)