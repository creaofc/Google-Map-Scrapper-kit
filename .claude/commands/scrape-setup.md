---
description: Set up and start the local Google Maps scraper (Docker)
---
Set up the Google Maps scraper on this computer:

1. Confirm Docker is installed and running: `docker ps`. If it errors, tell the user to install/start **Docker Desktop** (link in `SETUP.md` §0) and stop here.
2. From the kit root, start the scraper: `docker compose up -d`.
3. Wait ~10s, then verify it's live: `curl http://localhost:8080/api/v1/jobs` should return a JSON array (often `[]`).
4. Report success and tell the user they can now run `/scrape <business> in <city>` — or just ask in natural language (e.g. "scrape gyms in Miami").
5. **Show this over-use warning** (always print it once setup succeeds):
   > ⚠️ **Before you scrape:** this hits Google Maps for real. Light use is fine, but running big jobs
   > back-to-back, very high `depth`, many keywords, or scheduled runs **without proxies** can get your
   > IP **temporarily rate-limited/blocked by Google** (usually clears in minutes–hours; jobs start
   > returning empty/failed meanwhile). It won't ban your Google account. Stay safe: one job at a time,
   > start at `depth 5`, and add **proxies** for large or repeated runs. Scraping Maps is also against
   > Google's ToS — use responsibly and follow data laws (GDPR/CCPA) for any contact info.

If a step fails, consult `SETUP.md` §6 (Troubleshooting).
