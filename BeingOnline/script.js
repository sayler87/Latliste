// Firebase Konfigurasjon 
const firebaseConfig = {
  apiKey: "DIN_EGEN_API_KEY",
  authDomain: "DITT_PROSJEKT.firebaseapp.com",
  databaseURL: "https://DITT_PROSJEKT-default-rtdb.firebaseio.com",
  projectId: "DITT_PROSJEKT",
  storageBucket: "DITT_PROSJEKT.appspot.com",
  messagingSenderId: "DITT_NUMMER",
  appId: "1:DITT_NUMMER:web:DIN_UNIK_ID"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const database = firebase.database();
const departuresRef = database.ref('departures');

// --- DOM Elements ---
const form = document.getElementById('departureForm');
const searchInput = document.getElementById('searchInput');
const filterDestination = document.getElementById('filterDestination');
const tableBody = document.querySelector('#departuresTable tbody');
const toast = document.getElementById('toast');

// --- State ---
let departures = []; // Firebase vil fylle denne
let editingIndex = null;
let currentSort = { key: null, asc: true };

// Type-ikoner
const typeIcons = {
  Tog: '🚂',
  Bil: '🚗',
  Tralle: '🛒',
  Modul: '📦'
};

// --- Oppdater siste sync-tidspunkt ---
function updateLastSync() {
  const now = new Date();
  const options = { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: false 
  };
  document.getElementById('lastSync').textContent = now.toLocaleString('no-NO', options);
}

// --- Sett dagens tid ---
document.getElementById('time').value = new Date().toTimeString().slice(0, 5);

// --- Store bokstaver ---
document.getElementById('unitNumber').addEventListener('input', e => {
  e.target.value = e.target.value.toUpperCase();
});

// --- Toast ---
function showToast(message, type = 'info') {
  const colors = { success: '#27ae60', error: '#e74c3c', info: '#3498db', delete: '#e74c3c', edit: '#f39c12' };
  toast.textContent = message;
  toast.style.backgroundColor = colors[type] || '#333';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// --- Oppdater tabell (filtrering og sortering) ---
function displayDepartures() {
  const term = searchInput.value.toLowerCase();
  const dest = filterDestination.value;
  let filtered = departures.filter(d =>
    (term === '' || d.unitNumber.toLowerCase().includes(term) || d.destination.toLowerCase().includes(term)) &&
    (dest === '' || d.destination === dest)
  );

  if (currentSort.key) {
    filtered.sort((a, b) => {
      let av = a[currentSort.key] || '', bv = b[currentSort.key] || '';
      if (currentSort.key === 'time') av = av.replace(':', ''), bv = bv.replace(':', '');
      const res = av < bv ? -1 : av > bv ? 1 : 0;
      return currentSort.asc ? res : -res;
    });
  }

  tableBody.innerHTML = filtered.map(d => {
    const tc = d.type === 'Tog' ? '#e74c3c' : d.type === 'Bil' ? '#f31230ff' : d.type === 'Tralle' ? '#3498db' : '#9b59b6';
    const statusColors = {
      'LEVERT': '#37f308ff',
      'LAGER': '#3498db',
      'planlaget': '#eb960fff',
      'LASTER NÅ': '#e62222ff'
    };
    const sc = statusColors[d.status] || '#808080';

    return `
      <tr>
        <td>${d.unitNumber}</td>
        <td>${d.destination}</td>
        <td>${d.time}</td>
        <td>${d.gate}</td>
        <td><span class="type-icon">${typeIcons[d.type]}</span><span style="color:${tc};font-weight:bold">${d.type}</span></td>
        <td><span style="color:${sc};font-weight:bold">${d.status}</span></td>
        <td>${d.comment || '<em>Ingen</em>'}</td>
        <td class="action-buttons">
          <button class="btn btn-secondary" onclick="editDeparture(${d.id})">✏️ Rediger</button>
          <button class="btn btn-danger" onclick="deleteDeparture(${d.id})">🗑️ Slett</button>
        </td>
      </tr>`;
  }).join('');

  // Oppdater sorteringsindikatorer
  document.querySelectorAll('th[data-sort]').forEach(th => {
    th.classList.remove('sort-asc', 'sort-desc');
    if (th.dataset.sort === currentSort.key) th.classList.add(currentSort.asc ? 'sort-asc' : 'sort-desc');
  });

  updateStatistics(); // Oppdater statistikk etter visning
}

// --- Sortering ---
document.querySelectorAll('th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.sort;
    currentSort.asc = currentSort.key === key ? !currentSort.asc : true;
    currentSort.key = key;
    displayDepartures();
  });
});

// --- Skjema: Legg til/rediger avgang ---
form.addEventListener('submit', e => {
  e.preventDefault();
  const data = {
    id: editingIndex !== null ? departures[editingIndex].id : Date.now(),
    unitNumber: document.getElementById('unitNumber').value.trim().toUpperCase(),
    destination: document.getElementById('destination').value,
    time: document.getElementById('time').value,
    gate: document.getElementById('gate').value.trim(),
    type: document.getElementById('type').value,
    status: document.getElementById('status').value,
    comment: document.getElementById('comment').value.trim() || null
  };

  if (Object.values(data).some(v => v === '' && v !== null)) {
    showToast('Vennligst fyll ut alle obligatoriske felt.', 'info');
    return;
  }

  if (editingIndex === null && departures.some(d => d.unitNumber === data.unitNumber)) {
    showToast(`Enhetsnummer ${data.unitNumber} eksisterer allerede!`, 'info');
    return;
  }

  if (editingIndex !== null) {
    // Oppdater eksisterende
    const updatedDepartures = [...departures];
    updatedDepartures[editingIndex] = data;
    departuresRef.set(updatedDepartures);
    editingIndex = null;
    form.querySelector('button[type="submit"]').textContent = '✅ Registrer Avgang';
    showToast('Oppdatert!', 'edit');
  } else {
    // Legg til ny
    const newDepartures = [...departures, data];
    departuresRef.set(newDepartures);
    showToast('Registrert!', 'success');
  }

  // Tilbakestill skjema
  form.reset();
  document.getElementById('time').value = new Date().toTimeString().slice(0, 5);
});

// --- Rediger avgang ---
window.editDeparture = (id) => {
  const idx = departures.findIndex(d => d.id === id);
  if (idx === -1) return;
  const d = departures[idx];
  Object.keys(d).forEach(k => {
    if (document.getElementById(k)) document.getElementById(k).value = d[k];
  });
  editingIndex = idx;
  form.querySelector('button[type="submit"]').textContent = '🔁 Oppdater';
  window.scrollTo(0, 0);
};

// --- Slett avgang ---
window.deleteDeparture = (id) => {
  if (confirm('Slette denne avgangen?')) {
    const newDepartures = departures.filter(d => d.id !== id);
    departuresRef.set(newDepartures);
    showToast('Slettet!', 'delete');
  }
};

// --- Tøm alle avganger ---
window.clearAllDepartures = () => {
  if (departures.length === 0) {
    showToast('Ingen avganger å slette.', 'info');
    return;
  }
  if (confirm('Slette ALLE avganger?')) {
    departuresRef.set([]);
    showToast('Alt tømt!', 'delete');
  }
};

// --- Eksport til CSV (lokal for brukeren) ---
function exportToCSV() {
  const headers = ['Enhetsnummer','Destinasjon','Tid','Luke','Type','Status','Kommentar'];
  const rows = departures.map(d => [
    d.unitNumber, d.destination, d.time, d.gate, d.type, d.status, d.comment || ''
  ].map(s => `"${s}"`).join(','));
  downloadFile([headers.join(','), ...rows].join('\n'), `avganger_${new Date().toISOString().slice(0,10)}.csv`, 'text/csv');
  showToast('Eksportert til CSV!', 'success');
  updateLastSync();
}

// --- Last ned backup (JSON) ---
function backupData() {
  downloadFile(JSON.stringify(departures, null, 2), `backup_${new Date().toISOString().slice(0,10)}.json`, 'application/json');
  showToast('Backup lastet ned!', 'info');
  updateLastSync();
}

// --- Last opp backup (JSON) ---
function importFromJSON(input) {
  const file = input.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const imported = JSON.parse(e.target.result);

      if (Array.isArray(imported) && imported.every(d => d.id && d.unitNumber && d.destination)) {
        const overwrite = confirm(
          `Fant ${imported.length} avganger i filen.\n\nTrykk 'OK' for å ERSTATTE alle eksisterende avganger.\nTrykk 'Avbryt' for å LEGGE TIL sammen med eksisterende.`
        );

        if (overwrite) {
          departuresRef.set(imported);
        } else {
          const existingIds = new Set(departures.map(d => d.id));
          let importedCount = 0;
          const merged = [...departures];
          imported.forEach(d => {
            if (!existingIds.has(d.id)) {
              merged.push(d);
              importedCount++;
            }
          });
          departuresRef.set(merged);
          showToast(`Lagt til ${importedCount} nye avganger.`, 'info');
        }
        showToast('Data importert!', 'success');
      } else {
        throw new Error('Ugyldig format');
      }
    } catch (err) {
      showToast('Feil ved lesing av JSON-fil!', 'error');
      console.error(err);
    }
  };
  reader.readAsText(file);
  input.value = '';
}

// --- Hjelpefunksjon: Last ned fil ---
function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// --- Oppdater statistikk i sanntid ---
function updateStatistics() {
  const total = departures.length;
  document.getElementById('totalDepartures').textContent = total;

  // Destinasjoner
  const destinations = ['TRONDHEIM', 'ÅLESUND', 'MOLDE', 'FØRDE', 'HAUGESUND', 'STAVANGER'];
  destinations.forEach(dest => {
    const count = departures.filter(d => d.destination === dest).length;
    document.getElementById(`dest${dest}`).textContent = count;
  });

  // Status
  const statusMap = {
    'LEVERT': 'LEVERT',
    'LAGER': 'LAGER',
    'planlaget': 'Planlaget',
    'LASTER NÅ': 'LASTER'
  };

  const statuses = ['LEVERT', 'LAGER', 'Planlaget', 'LASTER'];
  statuses.forEach(status => {
    let count = 0;
    if (status === 'LASTER') {
      count = departures.filter(d => d.status === 'LASTER NÅ').length;
    } else if (status === 'Planlaget') {
      count = departures.filter(d => d.status === 'planlaget').length;
    } else {
      count = departures.filter(d => d.status === status).length;
    }
    document.getElementById(`status${status}`).textContent = count;
  });
}

// --- Lytt etter endringer i Firebase (sanntid!) ---
function loadDeparturesFromFirebase() {
  departuresRef.on('value', (snapshot) => {
    const data = snapshot.val();
    departures = data ? Object.values(data) : [];
    displayDepartures();
    updateLastSync();
  });
}

// --- Init: Start lytter og vis data ---
loadDeparturesFromFirebase();
searchInput.addEventListener('input', displayDepartures);
filterDestination.addEventListener('change', displayDepartures);

// --- Horisontal navigasjon for bedre UX ---
function setupHorizontalNav() {
  const mainContent = document.querySelector('.main-content');
  if (!mainContent) return;

  // Legg til navigasjonspiler
  const leftArrow = document.createElement('button');
  const rightArrow = document.createElement('button');
  
  leftArrow.innerHTML = '‹';
  rightArrow.innerHTML = '›';
  
  leftArrow.style.cssText = `
    position: fixed;
    top: 50%;
    left: 10px;
    transform: translateY(-50%);
    background: rgba(52, 152, 219, 0.8);
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    font-size: 24px;
    cursor: pointer;
    z-index: 100;
    display: none;
  `;
  
  rightArrow.style.cssText = `
    position: fixed;
    top: 50%;
    right: 10px;
    transform: translateY(-50%);
    background: rgba(52, 152, 219, 0.8);
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    font-size: 24px;
    cursor: pointer;
    z-index: 100;
    display: none;
  `;

  document.body.appendChild(leftArrow);
  document.body.appendChild(rightArrow);

  // Oppdater piler basert på scrollposisjon
  function updateArrows() {
    const { scrollLeft, scrollWidth, clientWidth } = mainContent;
    leftArrow.style.display = scrollLeft > 0 ? 'block' : 'none';
    rightArrow.style.display = scrollLeft < scrollWidth - clientWidth - 10 ? 'block' : 'none';
  }

  mainContent.addEventListener('scroll', updateArrows);

  // Navigeringsfunksjoner
  leftArrow.addEventListener('click', () => {
    mainContent.scrollBy({ left: -window.innerWidth, behavior: 'smooth' });
  });

  rightArrow.addEventListener('click', () => {
    mainContent.scrollBy({ left: window.innerWidth, behavior: 'smooth' });
  });

  // Tastaturstøtte
  window.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') {
      mainContent.scrollBy({ left: -window.innerWidth, behavior: 'smooth' });
    } else if (e.key === 'ArrowRight') {
      mainContent.scrollBy({ left: window.innerWidth, behavior: 'smooth' });
    }
  });

  // Vis piler ved hover (PC) eller alltid (mobil)
  if (window.innerWidth >= 900) {
    mainContent.addEventListener('mouseenter', () => {
      updateArrows();
      leftArrow.style.opacity = '0.7';
      rightArrow.style.opacity = '0.7';
    });
    mainContent.addEventListener('mouseleave', () => {
      leftArrow.style.opacity = '0';
      rightArrow.style.opacity = '0';
      leftArrow.style.pointerEvents = 'none';
      rightArrow.style.pointerEvents = 'none';
    });
  } else {
    leftArrow.style.opacity = '0.9';
    rightArrow.style.opacity = '0.9';
  }
}

// Kall funksjonen når siden er lastet
window.addEventListener('load', setupHorizontalNav);

// ✅ FORBEDELT UTGAVE AV PRINT-FUNKSJON — SJEKKER OM DATA ER TILGJENGELIG
window.printWithHeader = function() {
  // Sjekk om det finnes rader i tabellen
  const rowCount = document.querySelectorAll('#departuresTable tbody tr').length;

  if (rowCount === 0) {
    // Hvis ingen rader: vis melding og avbryt
    showToast("Ingen data å skrive ut. Vent til tabellen er lastet.", "info");
    return;
  }

  // Sett dynamisk dato i header for utskrift
  const header = document.querySelector('.header p');
  const now = new Date();
  const options = { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit', 
    minute: '2-digit'
  };
  header.dataset.printDate = now.toLocaleString('no-NO', options);

  // Vent 150ms for å sikre at CSS/DOM oppdateres før utskrift
  setTimeout(() => {
    window.print();
  }, 150);
};