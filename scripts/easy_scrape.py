#!/usr/bin/env python3
"""Simplified Google Maps Scraper Interface.

Usage:
    python scripts/easy_scrape.py "niche" "location" leads_count

Example:
    python scripts/easy_scrape.py "dentists" "Austin, TX" 15
"""
import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

BASE = os.environ.get("SCRAPER_BASE_URL", "http://localhost:8080")
KEY = os.environ.get("SCRAPER_API_KEY", "")
UA = "google-maps-scraper-kit/1.0 (https://github.com/Mahanaicoach/google-maps-scraper-kit)"
LEAD_FIELDS = ["title", "phone", "emails", "website", "category", "address", "review_rating", "review_count"]


def req(method, path, body=None):
    headers = {"Content-Type": "application/json", "User-Agent": UA}
    if KEY:
        headers["X-API-Key"] = KEY
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=60) as resp:
        return resp.status, resp.read()


def geocode(place):
    """Resolve location to lat/lon strings using Nominatim."""
    q = urllib.parse.urlencode({"format": "json", "limit": 1, "q": place})
    url = f"https://nominatim.openstreetmap.org/search?{q}"
    r = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            hits = json.loads(resp.read())
        time.sleep(1)  # Respect Nominatim's rate limit
        if hits:
            return str(hits[0]["lat"]), str(hits[0]["lon"])
    except Exception as e:
        print(f"  (Geocoding failed: {e})", file=sys.stderr)
    return None


def main():
    ap = argparse.ArgumentParser(description="Easy Google Maps Scraper")
    ap.add_argument("niche", help="Type of business (e.g. dentists, cafes, plumbers)")
    ap.add_argument("location", help="City and State/Country (e.g. 'Austin, TX', 'London')")
    ap.add_argument("leads", type=int, help="Number of leads wanted")
    a = ap.parse_args()

    niche = a.niche.strip()
    location = a.location.strip()
    leads_wanted = a.leads

    if leads_wanted <= 0:
        sys.exit("✗ Number of leads must be greater than 0.")

    # 1. Geocode location
    print(f"▶ Geocoding location \"{location}\"…")
    coords = geocode(location)
    if not coords:
        sys.exit(f"✗ Could not find location '{location}'. Please try a clearer city name.")
    lat, lon = coords
    print(f"  → Latitude: {lat}, Longitude: {lon}")

    # 2. Estimate required depth (approx. 20 results per scroll/depth unit)
    depth = max(1, (leads_wanted + 19) // 20)
    query = f"{niche} in {location}"

    # 3. Check scraper health
    try:
        req("GET", "/api/v1/jobs")
    except Exception as e:
        sys.exit(f"✗ Scraper API not reachable at {BASE}. Ensure the Docker container is running.\n  ({e})")

    # 4. Create scraper job
    body = {
        "name": "easy-scrape",
        "keywords": [query],
        "lang": "en",
        "zoom": 15,
        "lat": lat,
        "lon": lon,
        "fast_mode": False,
        "radius": 10000,
        "depth": depth,
        "email": True,  # Keep email extraction active as requested by default
        "max_time": 600
    }
    print(f"▶ Creating job for: '{query}' (Targeting {leads_wanted} leads, depth={depth})")
    
    try:
        _, raw = req("POST", "/api/v1/jobs", body)
    except urllib.error.HTTPError as e:
        sys.exit(f"✗ Job creation failed: HTTP {e.code} — {e.read().decode()[:200]}")
        
    job_id = json.loads(raw).get("id")
    if not job_id:
        sys.exit("✗ Scraper API did not return a Job ID.")
    print(f"  Job ID: {job_id}")

    # 5. Poll job status
    print("▶ Scraping Google Maps (polling status)…")
    status = None
    for i in range(150):
        _, raw = req("GET", f"/api/v1/jobs/{job_id}")
        status = json.loads(raw).get("Status")
        print(f"\r  Status: {str(status):<10} (check {i + 1})", end="", flush=True)
        if status == "ok":
            print(); break
        if status == "failed":
            sys.exit("\n✗ Job failed. You may be temporarily rate-limited by Google. Please wait a bit or configure proxies.")
        time.sleep(8)
    else:
        sys.exit("\n✗ Job timed out.")

    # 6. Download results and parse
    _, raw = req("GET", f"/api/v1/jobs/{job_id}/download")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8", "replace"))))
    
    # 7. Truncate to the requested amount of leads
    results = [{k: r.get(k, "") for k in LEAD_FIELDS} for r in rows]
    results = results[:leads_wanted]

    # Save to a clean filename
    safe_niche = "".join(c if c.isalnum() else "_" for c in niche.lower())
    safe_loc = "".join(c if c.isalnum() else "_" for c in location.lower())
    filename = f"leads_{safe_niche}_{safe_loc}.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEAD_FIELDS)
        w.writeheader()
        w.writerows(results)

    print(f"✓ Success! Retrieved {len(results)} leads.")
    print(f"  Saved to file → {filename}")
    print("\n--- LEADS DATA ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
