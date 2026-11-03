HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{
  --bg:#06080d;--sidebar:#0c1018;--card:#111827;--card2:#1a2332;
  --border:#1e293b;--border2:#334155;
  --accent:#818cf8;--accent2:#6366f1;--green:#34d399;--green2:#059669;
  --red:#f87171;--yellow:#fbbf24;
  --text:#e2e8f0;--dim:#64748b;--bright:#f8fafc;
}
html,body{height:100%;overflow:hidden;font-family:'Inter',sans-serif;background:var(--bg);color:var(--text)}
body{display:flex}

.sidebar{
  width:260px;min-width:260px;background:linear-gradient(180deg,#0e1420 0%,#0a0e17 100%);
  border-right:1px solid var(--border);display:flex;flex-direction:column;
  position:relative;z-index:10;
}
.sidebar::after{
  content:'';position:absolute;top:0;right:0;width:1px;height:100%;
  background:linear-gradient(180deg,var(--accent2) 0%,transparent 60%);opacity:0.3;
}
.logo{
  padding:24px 20px 2px;font-size:24px;font-weight:800;letter-spacing:2px;
  background:linear-gradient(135deg,#a5b4fc,#818cf8,#6366f1);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.divider{height:1px;background:var(--border);margin:12px 20px}

.btn{
  margin:4px 16px;padding:10px 14px;border:none;border-radius:8px;
  font-size:12px;font-weight:600;cursor:pointer;transition:all .2s ease;
  font-family:'Inter',sans-serif;outline:none;text-align:center;
}
.btn-ghost{background:var(--card);color:var(--text);border:1px solid var(--border)}
.btn-ghost:hover{background:var(--card2);border-color:var(--border2)}
.btn-green{
  background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff;border:none;
  box-shadow:0 2px 12px rgba(34,197,94,.15);
}
.btn-green:hover{box-shadow:0 4px 20px rgba(34,197,94,.3)}
.btn-green.disabled{background:#1e293b;color:var(--dim);cursor:not-allowed;box-shadow:none;border:1px solid var(--border)}

.btn-red{
  background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;border:none;
  box-shadow:0 2px 12px rgba(239,68,68,.15);
}
.btn-red:hover{box-shadow:0 4px 20px rgba(239,68,68,.3)}

.folder-path{
  padding:0 20px;margin-bottom:10px;font-size:10px;color:var(--dim);
  word-break:break-all;line-height:1.4;min-height:16px;
}

.stats{
  margin:6px 16px;padding:12px 14px;border-radius:10px;
  background:rgba(17,24,39,.6);border:1px solid var(--border);
}
.stats-title{font-size:9px;font-weight:700;color:var(--dim);letter-spacing:1.5px;margin-bottom:8px;text-transform:uppercase}
.stat-row{display:flex;align-items:center;gap:8px;padding:3px 0;font-size:12px}
.stat-row .label{color:var(--dim);flex:1}
.stat-row .value{font-weight:700;font-family:'JetBrains Mono',monospace;font-size:12px}
.stat-row.cards .value{color:var(--green)}
.stat-row.bins .value{color:var(--accent)}

/* Progress Bar */
.progress-container {
  width: 100%; height: 4px; background: var(--border); border-radius: 2px;
  overflow: hidden; margin-top: 10px; display: none;
}
.progress-container.active { display: block; }
.progress-bar {
  height: 100%; background: var(--green); width: 0%;
  transition: width 0.3s ease;
}

.spacer{flex:1}

.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.header{
  padding:14px 20px 10px;display:flex;align-items:center;gap:10px;
  border-bottom:1px solid var(--border);flex-wrap:wrap;
}
.header h2{font-size:14px;font-weight:700;color:var(--bright)}
.badge{
  background:var(--accent2);color:#fff;padding:2px 10px;border-radius:16px;
  font-size:11px;font-weight:700;
}
.filter-group { display:flex; gap:8px; margin-left:auto; flex-wrap:wrap; }
.filter-input{
  padding:6px 10px;background:var(--card);border:1px solid var(--border);
  border-radius:6px;color:var(--text);font-size:12px;font-family:'Inter',sans-serif;
  outline:none;width:150px;transition:border-color .2s;
}
.filter-select {
  padding:6px 8px;background:var(--card);border:1px solid var(--border);
  border-radius:6px;color:var(--text);font-size:11px;font-family:'Inter',sans-serif;
  outline:none;max-width:120px;
}
.filter-input:focus, .filter-select:focus{border-color:var(--accent)}
.filter-input::placeholder{color:var(--dim)}

.table-wrap{flex:1;overflow:auto;margin:0 12px 8px;border-radius:10px;border:1px solid var(--border);background:var(--bg)}
table{width:100%;border-collapse:collapse}
thead{position:sticky;top:0;z-index:5}
thead th{
  background:var(--card);padding:8px 10px;text-align:left;
  font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;
  color:var(--accent);cursor:pointer;user-select:none;
  border-bottom:2px solid var(--border);white-space:nowrap;
}
thead th:hover{color:var(--bright)}
thead th.sorted{color:var(--green)}
tbody tr{border-bottom:1px solid rgba(30,41,59,.4);transition:background .12s; cursor:pointer;}
tbody tr:nth-child(even){background:rgba(17,24,39,.3)}
tbody tr:hover{background:rgba(99,102,241,.08)}
tbody td{padding:6px 10px;font-size:11px;font-family:'JetBrains Mono',monospace;white-space:nowrap;color:var(--text)}
tbody td.waiting{color:var(--dim);font-style:italic}
tbody td.cc-col{color:var(--bright);font-weight:500}
.cc-blurred { filter: blur(4.5px); transition: filter 0.3s ease; user-select: none; }
.cc-blurred.revealed { filter: blur(0); user-select: text; }
tbody td.email-col{color:var(--yellow);font-family:'Inter',sans-serif;font-size:11px}
tbody td.phone-col{color:var(--accent);font-family:'Inter',sans-serif;font-size:11px}
tbody td.ip-col{color:var(--green)}
tbody td.holder-col{color:#c084fc;font-family:'Inter',sans-serif;font-size:11px}

.status-bar{
  padding:5px 20px;background:var(--sidebar);border-top:1px solid var(--border);
  font-size:11px;color:var(--dim);display:flex;align-items:center;gap:8px;
}
.pulse{width:8px;height:8px;border-radius:50%;background:var(--green);animation:pulse 1.5s infinite;display:none}
.pulse.active{display:inline-block}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}

.toast{
  position:fixed;bottom:50px;right:20px;padding:10px 18px;
  background:var(--accent2);color:#fff;border-radius:8px;
  font-size:12px;font-weight:600;opacity:0;transform:translateY(10px);
  transition:all .3s cubic-bezier(.4,0,.2,1);z-index:100;
  box-shadow:0 8px 24px rgba(99,102,241,.3);pointer-events:none;
}
.toast.show{opacity:1;transform:translateY(0)}

/* Modal */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.2s;
}
.modal-overlay.show { opacity: 1; pointer-events: auto; }
.modal {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; width: 450px; max-width: 90%;
  box-shadow: 0 10px 40px rgba(0,0,0,0.5);
  transform: translateY(20px); transition: transform 0.2s;
  display: flex; flex-direction: column; max-height: 90vh;
}
.modal-overlay.show .modal { transform: translateY(0); }
.modal-header {
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.modal-header h3 { font-size: 15px; color: var(--bright); }
.close-btn { background: none; border: none; color: var(--dim); cursor: pointer; font-size: 18px; }
.close-btn:hover { color: var(--red); }
.modal-body { padding: 20px; font-size: 12px; line-height: 1.6; overflow-y: auto; }
.modal-row { display: flex; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 6px; }
.modal-row .mlabel { width: 100px; color: var(--dim); font-weight: 600; }
.modal-row .mvalue { flex: 1; color: var(--text); font-family: 'JetBrains Mono', monospace; word-break: break-all; }
.modal-row .mvalue.path { color: var(--accent); font-family: 'Inter', sans-serif; cursor: pointer; }
.modal-row .mvalue.path:hover { text-decoration: underline; }

::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:#4b5563}
</style>
</head>
<body>

<div class="sidebar">
  <div class="logo">
    <div style="font-weight: 700; font-size: 20px;">ZCCV - v5</div>
    <div style="font-size: 10px; color: var(--green); margin-top: 2px;">Make by @thaituluckkystopdz :3</div>
  </div>
  <div class="divider"></div>

  <button class="btn btn-ghost" onclick="callBackend('selectFolder')">Select Folder</button>
  <div class="folder-path" id="folderPath">No folder selected</div>

  <div style="display:flex; gap:8px; margin: 0 16px;">
    <button class="btn btn-green disabled" id="btnScan" onclick="callBackend('startScan')" style="flex:1; margin:0">Scan &amp; Check</button>
    <button class="btn btn-red" id="btnStop" onclick="callBackend('stopScan')" style="display:none; margin:0">Stop</button>
  </div>

  <div class="divider" style="margin-top:14px"></div>

  <div class="stats">
    <div class="stats-title">Statistics</div>
    <div class="stat-row files">
      <span class="label">Files</span>
      <span class="value" id="statFiles">0 / 0</span>
    </div>
    <div class="stat-row cards">
      <span class="label">Cards</span>
      <span class="value" id="statCards">0</span>
    </div>
    <div class="stat-row bins">
      <span class="label">BINs</span>
      <span class="value" id="statBins">0 / 0</span>
    </div>
    <div class="progress-container" id="progressCont">
      <div class="progress-bar" id="progressBar"></div>
    </div>
  </div>

  <div class="spacer"></div>

  <button class="btn btn-ghost" onclick="callBackend('copyAll')" style="margin-bottom:3px">Copy All Cards</button>
  <button class="btn btn-ghost" onclick="callBackend('exportAll')" style="margin-bottom:3px">Export to TXT</button>
  <button class="btn btn-ghost" onclick="callBackend('exportCSV')" style="margin-bottom:16px">Export to CSV</button>
</div>

<div class="main">
  <div class="header">
    <h2>Extracted Cards</h2>
    <span class="badge" id="badge">0</span>
    <div class="filter-group">
      <select class="filter-select" id="filterBrand" onchange="filterTable()">
        <option value="">All Brands</option>
      </select>
      <select class="filter-select" id="filterLevel" onchange="filterTable()">
        <option value="">All Levels</option>
      </select>
      <select class="filter-select" id="filterCountry" onchange="filterTable()">
        <option value="">All Countries</option>
      </select>
      <input class="filter-input" id="filterInput" type="text" placeholder="Search..." oninput="filterTable()">
    </div>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th onclick="sortTable(0)">Card Number</th>
          <th onclick="sortTable(1)">Exp</th>
          <th onclick="sortTable(2)">CVV</th>
          <th onclick="sortTable(3)">Brand</th>
          <th onclick="sortTable(4)">Type</th>
          <th onclick="sortTable(5)">Level</th>
          <th onclick="sortTable(6)">Bank</th>
          <th onclick="sortTable(7)">Country</th>
          <th onclick="sortTable(8)">Email</th>
          <th onclick="sortTable(9)">Phone</th>
          <th onclick="sortTable(10)">IP</th>
          <th onclick="sortTable(11)">Holder</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
  <div class="pagination-controls" style="display:flex; justify-content:center; align-items:center; gap:10px; margin-top:10px; margin-bottom:10px;">
    <button class="btn btn-red" id="prevPage" onclick="changePage(-1)">Previous</button>
    <span id="pageInfo" style="color:var(--text); font-size:13px; font-weight:bold;">Page 1 of 1</span>
    <button class="btn btn-green" id="nextPage" onclick="changePage(1)">Next</button>
  </div>

  <div class="status-bar">
    <span class="pulse" id="pulse"></span>
    <span id="statusText">Ready</span>
  </div>
</div>

<div class="toast" id="toast"></div>

<!-- Welcome Modal -->
<div class="modal-overlay show" id="welcomeModal" onclick="if(event.target===this) document.getElementById('welcomeModal').classList.remove('show')">
  <div class="modal" style="width: 500px; text-align: center;">
    <div class="modal-header">
      <h3 style="color: var(--green);">Welcome to ZCCV v4</h3>
      <button class="close-btn" onclick="document.getElementById('welcomeModal').classList.remove('show')">×</button>
    </div>
    <div class="modal-body" style="font-size: 13px; padding: 30px 20px;">
      Hi cảm ơn bro mua tools nhé đây tools bản v4 của bản ZCCV phiên bản scan COCA đầu tiên bên team mình đây thể gọi phiên bản mạnh hơn ! mong các bro tôn trọng nhau vì không nên chơi leaks suor nhé
      <br><br>
      <button class="btn btn-green" onclick="document.getElementById('welcomeModal').classList.remove('show')">Got it!</button>
    </div>
  </div>
</div>

<!-- Modal Overlay -->
<div class="modal-overlay" id="detailModal" onclick="if(event.target===this) closeModal()">
  <div class="modal">
    <div class="modal-header">
      <h3>Card Details</h3>
      <button class="close-btn" onclick="closeModal()">×</button>
    </div>
    <div class="modal-body" id="modalBody">
      <!-- content injected via JS -->
    </div>
  </div>
</div>

<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>
let backend = null;
let sortCol = -1, sortAsc = true;
let pageReady = false;

new QWebChannel(qt.webChannelTransport, function(ch) {
    backend = ch.objects.backend;
    pageReady = true;
    backend.pageLoaded();
});

function callBackend(method, arg) {
    if (!backend) return;
    if (arg !== undefined) {
        backend[method](arg);
    } else {
        backend[method]();
    }
}

function onFolderSelected(path) {
    document.getElementById('folderPath').textContent = path;
    document.getElementById('btnScan').classList.remove('disabled');
}

function onScanStarted() {
    document.getElementById('btnScan').classList.add('disabled');
    document.getElementById('btnScan').textContent = 'Scanning...';
    document.getElementById('btnStop').style.display = 'block';
    document.getElementById('pulse').classList.add('active');
    document.getElementById('tbody').innerHTML = '';
    document.getElementById('progressCont').classList.add('active');
    document.getElementById('progressBar').style.width = '0%';
    allCardsData = [];
    filteredCards = [];
    renderTable();
}

let allCardsData = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 100;
let filteredCards = [];

function addCards(batch) {
    allCardsData = allCardsData.concat(batch);
    for (var i = 0; i < batch.length; i++) {
        var c = batch[i];
        updateDropdown('filterBrand', c.brand);
        updateDropdown('filterLevel', c.level);
        updateDropdown('filterCountry', c.country);
    }
    filterTable(); // also renders
}

function updateBin(data) {
    for (var i = 0; i < allCardsData.length; i++) {
        if (allCardsData[i].bin === data.bin) {
            allCardsData[i].brand = data.brand;
            allCardsData[i].type = data.type;
            allCardsData[i].level = data.level;
            allCardsData[i].bank = data.bank;
            allCardsData[i].country = data.country;
            
            updateDropdown('filterBrand', data.brand);
            updateDropdown('filterLevel', data.level);
            updateDropdown('filterCountry', data.country);
        }
    }
    renderTable();
}

function updateStats(s) {
    document.getElementById('statFiles').textContent = s.files + ' / ' + s.totalFiles;
    document.getElementById('statCards').textContent = s.cards;
    document.getElementById('statBins').textContent = s.bins + ' / ' + s.totalBins;
    document.getElementById('badge').textContent = s.cards;
    if(s.totalFiles > 0) {
        var pct = (s.files / s.totalFiles) * 100;
        document.getElementById('progressBar').style.width = pct + '%';
    }
}

function setStatus(msg) {
    document.getElementById('statusText').textContent = msg;
}

function onScanComplete(msg) {
    document.getElementById('btnScan').classList.remove('disabled');
    document.getElementById('btnScan').textContent = 'Scan & Check';
    document.getElementById('btnStop').style.display = 'none';
    document.getElementById('pulse').classList.remove('active');
    document.getElementById('progressCont').classList.remove('active');
    setStatus(msg);
}

function showToast(msg) {
    var t = document.getElementById('toast');
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(function(){ t.classList.remove('show'); }, 2500);
}

function filterTable() {
    currentPage = 1;
    var q = document.getElementById('filterInput').value.toUpperCase();
    var fBrand = document.getElementById('filterBrand').value.toUpperCase();
    var fLevel = document.getElementById('filterLevel').value.toUpperCase();
    var fCountry = document.getElementById('filterCountry').value.toUpperCase();

    filteredCards = allCardsData.filter(function(c) {
        var text = (c.cc + ' ' + c.exp + ' ' + c.cvv + ' ' + (c.brand||'') + ' ' + (c.type||'') + ' ' + (c.level||'') + ' ' + (c.bank||'') + ' ' + (c.country||'') + ' ' + (c.email||'') + ' ' + (c.phone||'') + ' ' + (c.ip||'') + ' ' + (c.holder||'')).toUpperCase();
        var matchQ = q === '' || text.indexOf(q) >= 0;
        var matchB = fBrand === '' || (c.brand || '').toUpperCase() === fBrand;
        var matchL = fLevel === '' || (c.level || '').toUpperCase() === fLevel;
        var matchC = fCountry === '' || (c.country || '').toUpperCase() === fCountry;
        return matchQ && matchB && matchL && matchC;
    });
    renderTable();
}

function changePage(delta) {
    var maxPage = Math.ceil(filteredCards.length / ITEMS_PER_PAGE) || 1;
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    if (currentPage > maxPage) currentPage = maxPage;
    renderTable();
}

function renderTable() {
    var tbody = document.getElementById('tbody');
    var maxPage = Math.ceil(filteredCards.length / ITEMS_PER_PAGE) || 1;
    document.getElementById('pageInfo').textContent = 'Page ' + currentPage + ' of ' + maxPage;
    
    var start = (currentPage - 1) * ITEMS_PER_PAGE;
    var end = start + ITEMS_PER_PAGE;
    var pageItems = filteredCards.slice(start, end);
    
    var html = '';
    for (var i = 0; i < pageItems.length; i++) {
        var c = pageItems[i];
        var hasInfo = c.brand && c.brand !== '...';
        var w = hasInfo ? '' : ' class="waiting"';
        var rowData = encodeURIComponent(JSON.stringify(c));
        
        html += '<tr data-bin="' + c.bin + '" data-card="' + rowData + '" onclick="showModal(this.getAttribute(\'data-card\'))">' +
            '<td class="cc-col cc-blurred" onclick="event.stopPropagation(); this.classList.toggle(\\\'revealed\\\')" title="Click to reveal/hide">' + c.cc + '</td>' +
            '<td>' + c.exp + '</td>' +
            '<td>' + c.cvv + '</td>' +
            '<td' + w + ' data-col="brand">' + (c.brand || '...') + '</td>' +
            '<td' + w + '>' + (c.type || '...') + '</td>' +
            '<td' + w + ' data-col="level">' + (c.level || '...') + '</td>' +
            '<td' + w + '>' + (c.bank || '...') + '</td>' +
            '<td' + w + ' data-col="country">' + (c.country || '...') + '</td>' +
            '<td class="email-col">' + (c.email || '') + '</td>' +
            '<td class="phone-col">' + (c.phone || '') + '</td>' +
            '<td class="ip-col">' + (c.ip || '') + '</td>' +
            '<td class="holder-col">' + (c.holder || '') + '</td></tr>';
    }
    tbody.innerHTML = html;
}

function updateDropdown(id, val) {
    if(!val || val==='...' || val==='N/A') return;
    var sel = document.getElementById(id);
    for(var i=0; i<sel.options.length; i++) {
        if(sel.options[i].value === val) return;
    }
    var opt = document.createElement('option');
    opt.value = val;
    opt.textContent = val;
    sel.appendChild(opt);
}

function sortTable(col) {
    if (sortCol === col) { sortAsc = !sortAsc; } else { sortCol = col; sortAsc = true; }
    var ths = document.querySelectorAll('thead th');
    for (var i = 0; i < ths.length; i++) {
        ths[i].classList.toggle('sorted', i === col);
        ths[i].textContent = ths[i].textContent.replace(/ [▲▼]$/, '');
        if (i === col) ths[i].textContent += sortAsc ? ' ▲' : ' ▼';
    }
    var tbody = document.getElementById('tbody');
    var rows = Array.from(tbody.rows);
    rows.sort(function(a, b) {
        var va = a.cells[col].textContent, vb = b.cells[col].textContent;
        return sortAsc ? va.localeCompare(vb, undefined, {numeric:true})
                       : vb.localeCompare(va, undefined, {numeric:true});
    });
    for (var i = 0; i < rows.length; i++) tbody.appendChild(rows[i]);
}

function showModal(encodedData) {
    var c = JSON.parse(decodeURIComponent(encodedData));
    var mb = document.getElementById('modalBody');
    var html = '';
    var fields = [
        {label: 'Card', val: c.cc + '|' + c.exp + '|' + c.cvv},
        {label: 'Log Path', val: c.log_root || 'Unknown', isPath: true},
        {label: 'Brand', val: c.brand},
        {label: 'Type', val: c.type},
        {label: 'Level', val: c.level},
        {label: 'Bank', val: c.bank},
        {label: 'Country', val: c.country},
        {label: 'Email', val: c.email},
        {label: 'Phone', val: c.phone},
        {label: 'IP', val: c.ip},
        {label: 'Holder', val: c.holder}
    ];
    for(var i=0; i<fields.length; i++) {
        if(fields[i].val && fields[i].val !== '...' && fields[i].val !== 'N/A') {
            var valClass = fields[i].isPath ? 'mvalue path' : 'mvalue';
            var onClick = fields[i].isPath ? ' onclick="callBackend(\\\'openFolder\\\', \\\'' + fields[i].val.replace(/\\/g, '\\\\') + '\\\')"' : '';
            html += '<div class="modal-row"><div class="mlabel">' + fields[i].label + '</div><div class="' + valClass + '"' + onClick + ' title="' + (fields[i].isPath ? 'Click to open folder' : '') + '">' + fields[i].val + '</div></div>';
        }
    }
    mb.innerHTML = html;
    document.getElementById('detailModal').classList.add('show');
}

function closeModal() {
    document.getElementById('detailModal').classList.remove('show');
}
</script>
</body>
</html>"""
