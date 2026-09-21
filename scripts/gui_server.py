#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.request
import urllib.parse
import urllib.error
import math
import os
import sys
import csv
import io
import re

PORT = 3000
BASE = os.environ.get("SCRAPER_BASE_URL", "http://localhost:8080")
KEY = os.environ.get("SCRAPER_API_KEY", "")
UA = "google-maps-scraper-kit/1.0"

# Store lat/lon search cache
GEO_CACHE = {}

def req(method, path, body=None):
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if KEY:
        headers["X-API-Key"] = KEY
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return resp.status, resp.read()

def geocode(place):
    if place in GEO_CACHE:
        return GEO_CACHE[place]
    q = urllib.parse.urlencode({"format": "json", "limit": 1, "q": place})
    url = f"https://nominatim.openstreetmap.org/search?{q}"
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            hits = json.loads(resp.read())
        if hits:
            res = (str(hits[0]["lat"]), str(hits[0]["lon"]))
            GEO_CACHE[place] = res
            return res
    except Exception as e:
        print(f"Geocoding failed for {place}: {e}", file=sys.stderr)
    return None

class ScraperHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Allow cross-origin just in case, and prevent browser caching during dev
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        # Serve the HTML frontend
        if self.path == "/" or self.path == "/index.html":
            try:
                html_path = os.path.join(os.path.dirname(__file__), "gui.html")
                with open(html_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error loading UI: {e}".encode())
            return

        # Status check endpoint: /api/status/<job_id>?limit=50
        if self.path.startswith("/api/status/"):
            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            limit = int(query.get("limit", [50])[0])

            # Extract job_id
            match = re.search(r"^/api/status/([a-zA-Z0-9\-]+)", parsed.path)
            if not match:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing job ID"}).encode())
                return
            
            job_id = match.group(1)

            try:
                # Check status from container
                _, raw = req("GET", f"/api/v1/jobs/{job_id}")
                job_data = json.loads(raw)
                status = job_data.get("Status")

                response = {"status": status}

                if status == "ok":
                    # Get results
                    _, raw_csv = req("GET", f"/api/v1/jobs/{job_id}/download")
                    # Parse CSV
                    f = io.StringIO(raw_csv.decode("utf-8", "replace"))
                    rows = list(csv.DictReader(f))
                    
                    # Keep core lead fields
                    lead_fields = ["title", "phone", "emails", "website", "category", "address", "review_rating", "review_count"]
                    results = []
                    for r in rows:
                        results.append({k: r.get(k, "") for k in lead_fields})
                    
                    # Slice to requested limit
                    response["results"] = results[:limit]
                    response["total_scraped"] = len(rows)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # Default static file serving for anything else (js, css, images)
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/scrape":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode("utf-8"))
                niche = data.get("niche", "").strip()
                location = data.get("location", "").strip()
                limit = int(data.get("limit", 50))

                if not niche or not location:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Business niche and Location are required"}).encode())
                    return

                # Geocode
                coords = geocode(location)
                if not coords:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": f"Could not geocode location: '{location}'"}).encode())
                    return

                lat, lon = coords
                
                # Estimate depth based on lead limit (20 leads per depth scroll page)
                # Cap it between depth 2 and depth 15
                depth = max(2, min(15, math.ceil(limit / 20) + 1))

                # Create container job
                body = {
                    "name": "gui-scrape",
                    "keywords": [f"{niche} in {location}"],
                    "lang": "en",
                    "zoom": 15,
                    "lat": lat,
                    "lon": lon,
                    "fast_mode": False,
                    "radius": 10000,
                    "depth": depth,
                    "email": True,  # Enable email extraction by default
                    "max_time": 600  # 10 minutes max limit
                }

                # Submit to scraper container
                _, raw = req("POST", "/api/v1/jobs", body)
                job_id = json.loads(raw).get("id")

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"job_id": job_id, "status": "working"}).encode())

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

def run():
    # Make sure we use UTF-8 output encoding
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

    handler = ScraperHandler
    # Bind to localhost only
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"🚀 Google Maps Scraper Dashboard running at: http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard server.")

if __name__ == "__main__":
    run()
