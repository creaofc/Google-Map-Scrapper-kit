#!/usr/bin/env python3
"""
Google Maps Lead Scraper - Beautiful Web UI
Run: python scripts/ui_server.py
Then open: http://localhost:5000
"""
import json
import urllib.request
import urllib.parse
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys
import time

SCRAPER_BASE = "http://localhost:8080"
UI_PORT = 3000
UA = "google-maps-scraper-kit/1.0 (https://github.com/Mahanaicoach/google-maps-scraper-kit)"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Google Maps Lead Scraper</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#06060f;
  --card:rgba(255,255,255,0.04);
  --card-border:rgba(255,255,255,0.08);
  --accent:#7c3aed;
  --accent2:#2563eb;
  --text:#e2e8f0;
  --muted:#94a3b8;
  --success:#10b981;
  --danger:#ef4444;
  --warn:#f59e0b;
}
html{scroll-behavior:smooth}
body{
  font-family:'Inter',sans-serif;
  background:var(--bg);
  background-image:
    radial-gradient(ellipse 60% 40% at 20% 10%, rgba(124,58,237,0.18) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 80% 90%, rgba(37,99,235,0.16) 0%, transparent 60%);
  min-height:100vh;
  color:var(--text);
  overflow-x:hidden;
}

/* ── Header ── */
header{
  text-align:center;
  padding:60px 24px 40px;
}
.logo-icon{
  font-size:48px;
  display:block;
  margin-bottom:16px;
  filter:drop-shadow(0 0 30px rgba(124,58,237,0.6));
  animation:float 3s ease-in-out infinite;
}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
header h1{
  font-size:clamp(28px,5vw,48px);
  font-weight:800;
  background:linear-gradient(135deg,#a78bfa,#60a5fa,#34d399);
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
  line-height:1.15;
  margin-bottom:12px;
}
header p{
  color:var(--muted);
  font-size:16px;
  max-width:480px;
  margin:0 auto;
}

/* ── Main container ── */
.wrap{max-width:960px;margin:0 auto;padding:0 24px 80px}

/* ── Input card ── */
.card{
  background:var(--card);
  border:1px solid var(--card-border);
  border-radius:20px;
  padding:32px;
  backdrop-filter:blur(20px);
  margin-bottom:24px;
}
.card-title{
  font-size:13px;
  font-weight:600;
  letter-spacing:0.1em;
  text-transform:uppercase;
  color:var(--muted);
  margin-bottom:24px;
}
.inputs-row{
  display:grid;
  grid-template-columns:1fr 1fr auto;
  gap:16px;
  align-items:end;
}
@media(max-width:640px){.inputs-row{grid-template-columns:1fr}}
.field label{
  display:block;
  font-size:13px;
  font-weight:500;
  color:var(--muted);
  margin-bottom:8px;
}
.field input{
  width:100%;
  background:rgba(255,255,255,0.05);
  border:1px solid rgba(255,255,255,0.10);
  border-radius:12px;
  padding:14px 16px;
  color:var(--text);
  font-family:'Inter',sans-serif;
  font-size:15px;
  transition:border-color 0.2s,box-shadow 0.2s;
  outline:none;
}
.field input::placeholder{color:rgba(148,163,184,0.5)}
.field input:focus{
  border-color:rgba(124,58,237,0.6);
  box-shadow:0 0 0 3px rgba(124,58,237,0.15);
}
.btn{
  display:flex;
  align-items:center;
  gap:8px;
  padding:14px 28px;
  border-radius:12px;
  border:none;
  font-family:'Inter',sans-serif;
  font-size:15px;
  font-weight:600;
  cursor:pointer;
  transition:all 0.2s;
  white-space:nowrap;
}
.btn-primary{
  background:linear-gradient(135deg,#7c3aed,#2563eb);
  color:#fff;
  box-shadow:0 4px 24px rgba(124,58,237,0.35);
}
.btn-primary:hover{
  transform:translateY(-2px);
  box-shadow:0 8px 32px rgba(124,58,237,0.5);
}
.btn-primary:active{transform:translateY(0)}
.btn-primary:disabled{
  opacity:0.5;cursor:not-allowed;transform:none;
  box-shadow:0 4px 24px rgba(124,58,237,0.2);
}
.btn-secondary{
  background:rgba(255,255,255,0.06);
  border:1px solid rgba(255,255,255,0.1);
  color:var(--text);
}
.btn-secondary:hover{background:rgba(255,255,255,0.10)}

/* ── Status area ── */
#status-box{display:none}
.status-inner{
  display:flex;
  align-items:center;
  gap:16px;
  padding:20px 24px;
  border-radius:14px;
  border:1px solid;
}
.status-inner.working{
  background:rgba(245,158,11,0.08);
  border-color:rgba(245,158,11,0.25);
  color:var(--warn);
}
.status-inner.success{
  background:rgba(16,185,129,0.08);
  border-color:rgba(16,185,129,0.25);
  color:var(--success);
}
.status-inner.error{
  background:rgba(239,68,68,0.08);
  border-color:rgba(239,68,68,0.25);
  color:var(--danger);
}
.spinner{
  width:22px;height:22px;
  border:2px solid rgba(245,158,11,0.3);
  border-top-color:var(--warn);
  border-radius:50%;
  animation:spin 0.8s linear infinite;
  flex-shrink:0;
}
.status-inner.success .spinner{display:none}
.status-inner.error .spinner{display:none}
@keyframes spin{to{transform:rotate(360deg)}}
.status-text{font-size:14px;font-weight:500;flex:1}

/* ── Results ── */
#results-box{display:none}
.results-header{
  display:flex;
  align-items:center;
  justify-content:space-between;
  margin-bottom:20px;
  flex-wrap:wrap;
  gap:12px;
}
.results-header h2{
  font-size:20px;
  font-weight:700;
}
.badge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  background:rgba(16,185,129,0.12);
  border:1px solid rgba(16,185,129,0.25);
  color:var(--success);
  font-size:13px;
  font-weight:600;
  padding:4px 12px;
  border-radius:999px;
}
.table-wrap{
  overflow-x:auto;
  border-radius:16px;
  border:1px solid var(--card-border);
}
table{width:100%;border-collapse:collapse;font-size:14px}
thead{background:rgba(124,58,237,0.12);border-bottom:1px solid rgba(124,58,237,0.25)}
thead th{
  padding:14px 16px;
  text-align:left;
  font-size:12px;
  font-weight:600;
  letter-spacing:0.06em;
  text-transform:uppercase;
  color:#a78bfa;
  white-space:nowrap;
}
tbody tr{
  border-bottom:1px solid rgba(255,255,255,0.04);
  transition:background 0.15s;
}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:rgba(255,255,255,0.04)}
tbody td{
  padding:14px 16px;
  vertical-align:middle;
  max-width:220px;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}
.cell-name{font-weight:600;color:#e2e8f0;max-width:180px}
.cell-phone{color:#60a5fa;font-family:monospace;font-size:13px}
.cell-website a{
  color:#a78bfa;text-decoration:none;
  overflow:hidden;text-overflow:ellipsis;display:block;max-width:160px;
}
.cell-website a:hover{text-decoration:underline}
.cell-cat{
  background:rgba(124,58,237,0.12);
  color:#a78bfa;
  font-size:12px;
  padding:3px 10px;
  border-radius:999px;
  border:1px solid rgba(124,58,237,0.2);
  white-space:nowrap;
  display:inline-block;
}
.cell-addr{color:var(--muted);font-size:13px;max-width:200px}
.cell-rating{
  display:flex;align-items:center;gap:4px;font-weight:600;white-space:nowrap;
}
.stars{color:#f59e0b}
.cell-email{color:#34d399;font-size:13px}
.no-data{color:var(--muted);font-style:italic}

/* ── Empty/Error states ── */
.empty{
  text-align:center;
  padding:60px 24px;
  color:var(--muted);
}
.empty .icon{font-size:48px;margin-bottom:16px;display:block}

/* ── Footer actions ── */
.actions-row{
  display:flex;gap:12px;margin-top:20px;flex-wrap:wrap;
}
</style>
</head>
<body>

<header>
  <span class="logo-icon">🗺️</span>
  <h1>Google Maps Lead Scraper</h1>
  <p>Enter your niche, location and how many leads you want — we'll do the rest.</p>
</header>

<div class="wrap">

  <!-- Input Card -->
  <div class="card">
    <div class="card-title">🔍 Scrape Settings</div>
    <div class="inputs-row">
      <div class="field">
        <label for="niche">Business Niche</label>
        <input id="niche" type="text" placeholder="e.g. Dentists, Cafes, Plumbers…" />
      </div>
      <div class="field">
        <label for="location">Location</label>
        <input id="location" type="text" placeholder="e.g. Austin, TX" />
      </div>
      <div class="field" style="min-width:140px">
        <label for="leads">Number of Leads</label>
        <input id="leads" type="number" value="10" min="1" max="200" />
      </div>
    </div>
    <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap">
      <button class="btn btn-primary" id="scrape-btn" onclick="startScrape()">
        <span id="btn-icon">🚀</span> <span id="btn-text">Scrape Leads</span>
      </button>
    </div>
  </div>

  <!-- Status -->
  <div id="status-box" class="card" style="padding:0;background:transparent;border:none">
    <div class="status-inner working" id="status-inner">
      <div class="spinner" id="status-spinner"></div>
      <div class="status-text" id="status-text">Starting…</div>
    </div>
  </div>

  <!-- Results -->
  <div id="results-box">
    <div class="results-header">
      <h2 id="results-title">Leads</h2>
      <span class="badge" id="results-badge">✓ 0 leads found</span>
    </div>
    <div class="table-wrap">
      <table id="leads-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Business Name</th>
            <th>Phone</th>
            <th>Email</th>
            <th>Website</th>
            <th>Category</th>
            <th>Address</th>
            <th>Rating</th>
            <th>Reviews</th>
          </tr>
        </thead>
        <tbody id="leads-body"></tbody>
      </table>
    </div>
    <div class="actions-row">
      <button class="btn btn-secondary" onclick="exportCSV()">⬇️ Export CSV</button>
      <button class="btn btn-secondary" onclick="resetUI()">🔄 New Search</button>
    </div>
  </div>

</div>

<script>
let currentResults = [];
let currentJobId = null;
let pollInterval = null;

function setStatus(type, msg){
  const box = document.getElementById('status-box');
  const inner = document.getElementById('status-inner');
  const text = document.getElementById('status-text');
  box.style.display = 'block';
  inner.className = 'status-inner ' + type;
  text.textContent = msg;
  const spinner = document.getElementById('status-spinner');
  spinner.style.display = (type === 'working') ? 'block' : 'none';
}

function hideStatus(){
  document.getElementById('status-box').style.display = 'none';
}

function setBtn(loading){
  const btn = document.getElementById('scrape-btn');
  const icon = document.getElementById('btn-icon');
  const txt = document.getElementById('btn-text');
  btn.disabled = loading;
  if(loading){ icon.textContent = '⏳'; txt.textContent = 'Scraping…'; }
  else { icon.textContent = '🚀'; txt.textContent = 'Scrape Leads'; }
}

async function startScrape(){
  const niche = document.getElementById('niche').value.trim();
  const location = document.getElementById('location').value.trim();
  const leads = parseInt(document.getElementById('leads').value) || 10;

  if(!niche){ alert('Please enter a business niche.'); return; }
  if(!location){ alert('Please enter a location.'); return; }
  if(leads < 1){ alert('Please enter at least 1 lead.'); return; }

  setBtn(true);
  document.getElementById('results-box').style.display = 'none';
  currentResults = [];

  // Step 1: Geocode
  setStatus('working', `📍 Looking up coordinates for "${location}"…`);
  let lat, lon;
  try {
    const r = await fetch(`/proxy/geocode?q=${encodeURIComponent(location)}`);
    const d = await r.json();
    if(!d.lat){ throw new Error(d.error || 'Location not found'); }
    lat = d.lat; lon = d.lon;
  } catch(e){
    setStatus('error', `❌ Could not geocode "${location}": ${e.message}`);
    setBtn(false); return;
  }

  // Step 2: Create job
  const depth = Math.max(1, Math.ceil(leads / 20));
  const query = `${niche} in ${location}`;
  setStatus('working', `🕵️ Creating scrape job for "${query}"…`);

  let jobId;
  try {
    const body = {
      name: 'ui-scrape',
      keywords: [query],
      lang: 'en', zoom: 15,
      lat: String(lat), lon: String(lon),
      fast_mode: false, radius: 10000,
      depth: depth, email: true, max_time: 600
    };
    const r = await fetch('/proxy/jobs', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const d = await r.json();
    if(!d.id){ throw new Error(d.error || 'No job ID returned'); }
    jobId = d.id;
    currentJobId = jobId;
  } catch(e){
    setStatus('error', `❌ Failed to create job: ${e.message}`);
    setBtn(false); return;
  }

  // Step 3: Poll
  let checks = 0;
  setStatus('working', `🔄 Scraping Google Maps… (check 1)`);

  pollInterval = setInterval(async () => {
    checks++;
    try {
      const r = await fetch(`/proxy/jobs/${jobId}`);
      const d = await r.json();
      const status = d.Status;
      if(status === 'ok'){
        clearInterval(pollInterval);
        setStatus('working', `📥 Downloading results…`);
        await downloadResults(jobId, leads, niche, location);
      } else if(status === 'failed'){
        clearInterval(pollInterval);
        setStatus('error', `❌ Job failed. You may be rate-limited by Google. Wait a moment and try again.`);
        setBtn(false);
      } else {
        setStatus('working', `🔄 Scraping Google Maps… (check ${checks})`);
      }
    } catch(e){
      clearInterval(pollInterval);
      setStatus('error', `❌ Error polling status: ${e.message}`);
      setBtn(false);
    }
  }, 6000);
}

async function downloadResults(jobId, limit, niche, location){
  try {
    const r = await fetch(`/proxy/jobs/${jobId}/download`);
    const text = await r.text();
    const rows = parseCSV(text);
    currentResults = rows.slice(0, limit);

    hideStatus();
    showResults(currentResults, niche, location);
    setBtn(false);
  } catch(e){
    setStatus('error', `❌ Failed to download results: ${e.message}`);
    setBtn(false);
  }
}

function parseCSV(text){
  const lines = text.trim().split('\n');
  if(lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g,''));
  return lines.slice(1).map(line => {
    const vals = [];
    let cur = ''; let inQ = false;
    for(let c of line){
      if(c==='"'){ inQ=!inQ; }
      else if(c===',' && !inQ){ vals.push(cur); cur=''; }
      else { cur+=c; }
    }
    vals.push(cur);
    const obj = {};
    headers.forEach((h,i) => obj[h] = (vals[i]||'').trim().replace(/^"|"$/g,''));
    return obj;
  }).filter(r => r.title || r['title']);
}

function showResults(rows, niche, location){
  document.getElementById('results-box').style.display = 'block';
  document.getElementById('results-title').textContent = `${niche} in ${location}`;
  document.getElementById('results-badge').textContent = `✓ ${rows.length} leads found`;

  const tbody = document.getElementById('leads-body');
  tbody.innerHTML = '';
  rows.forEach((r, i) => {
    const rating = parseFloat(r.review_rating || r['review_rating'] || 0);
    const stars = rating >= 4.5 ? '⭐⭐⭐⭐⭐' : rating >= 4 ? '⭐⭐⭐⭐' : rating >= 3 ? '⭐⭐⭐' : '';
    const website = r.website || r['website'] || '';
    const email = r.emails || r['emails'] || '';
    const phone = r.phone || r['phone'] || '';
    const category = r.category || r['category'] || '';
    const address = r.address || r['address'] || '';
    const count = r.review_count || r['review_count'] || '';
    const title = r.title || r['title'] || '';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:var(--muted);font-size:12px">${i+1}</td>
      <td class="cell-name" title="${title}">${title}</td>
      <td class="cell-phone">${phone || '<span class="no-data">—</span>'}</td>
      <td class="cell-email">${email || '<span class="no-data">—</span>'}</td>
      <td class="cell-website">${website ? `<a href="${website}" target="_blank" title="${website}">${new URL(website).hostname.replace('www.','')}</a>` : '<span class="no-data">—</span>'}</td>
      <td><span class="cell-cat">${category || '—'}</span></td>
      <td class="cell-addr" title="${address}">${address.replace(', United States','')}</td>
      <td class="cell-rating"><span class="stars">${stars}</span> ${rating ? rating.toFixed(1) : '—'}</td>
      <td style="color:var(--muted)">${count || '—'}</td>
    `;
    tbody.appendChild(tr);
  });
  document.getElementById('results-box').scrollIntoView({behavior:'smooth', block:'start'});
}

function exportCSV(){
  if(!currentResults.length) return;
  const fields = ['title','phone','emails','website','category','address','review_rating','review_count'];
  const header = fields.join(',');
  const rows = currentResults.map(r => fields.map(f => `"${(r[f]||'').replace(/"/g,'""')}"`).join(','));
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], {type:'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'leads.csv'; a.click();
  URL.revokeObjectURL(url);
}

function resetUI(){
  if(pollInterval) clearInterval(pollInterval);
  setBtn(false);
  hideStatus();
  document.getElementById('results-box').style.display = 'none';
  document.getElementById('niche').focus();
}

// Enter key support
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('leads').addEventListener('keydown', e => { if(e.key==='Enter') startScrape(); });
  document.getElementById('location').addEventListener('keydown', e => { if(e.key==='Enter') startScrape(); });
});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # Suppress default access logs

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def proxy_get(self, url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                ct = resp.headers.get("Content-Type", "application/json")
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.HTTPError as e:
            self.send_json(e.code, {"error": e.reason})
        except Exception as e:
            self.send_json(502, {"error": str(e)})

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/proxy/geocode"):
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            q = params.get("q", [""])[0]
            if not q:
                self.send_json(400, {"error": "Missing q param"})
                return
            url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
                "format": "json", "limit": 1, "q": q
            })
            try:
                req = urllib.request.Request(url, headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    hits = json.loads(resp.read())
                if hits:
                    self.send_json(200, {"lat": hits[0]["lat"], "lon": hits[0]["lon"]})
                else:
                    self.send_json(404, {"error": "Location not found"})
            except Exception as e:
                self.send_json(500, {"error": str(e)})

        elif self.path.startswith("/proxy/jobs/") and self.path.endswith("/download"):
            job_id = self.path.split("/proxy/jobs/")[1].replace("/download", "")
            self.proxy_get(f"{SCRAPER_BASE}/api/v1/jobs/{job_id}/download")

        elif self.path.startswith("/proxy/jobs/"):
            job_id = self.path.split("/proxy/jobs/")[1].rstrip("/")
            self.proxy_get(f"{SCRAPER_BASE}/api/v1/jobs/{job_id}")

        elif self.path == "/proxy/jobs":
            self.proxy_get(f"{SCRAPER_BASE}/api/v1/jobs")

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/proxy/jobs":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                req = urllib.request.Request(
                    f"{SCRAPER_BASE}/api/v1/jobs",
                    data=body,
                    headers={"Content-Type": "application/json", "User-Agent": UA},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_body = resp.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(resp_body)))
                    self.end_headers()
                    self.wfile.write(resp_body)
            except urllib.error.HTTPError as e:
                self.send_json(e.code, {"error": e.read().decode()[:200]})
            except Exception as e:
                self.send_json(502, {"error": str(e)})
        else:
            self.send_response(404)
            self.end_headers()


def main():
    print("")
    print("  Google Maps Lead Scraper UI")
    print("  -----------------------------------")
    print(f"  [OK] Server running at: http://localhost:{UI_PORT}")
    print(f"  [>>] Proxying scraper:  {SCRAPER_BASE}")
    print(f"  [>>] Open in Chrome:    http://localhost:{UI_PORT}")
    print("  -----------------------------------")
    print("  Press Ctrl+C to stop.")
    print("")
    server = HTTPServer(("0.0.0.0", UI_PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
