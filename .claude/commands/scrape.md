---
description: Scrape Google Maps business listings for a query + city (drives the google-maps-scraper skill)
argument-hint: <business type> in <city, ST> [depth]
---
The user wants to scrape Google Maps business listings. Query: **$ARGUMENTS**

Use the `google-maps-scraper` skill. Execute:

1. **Health-check** the API: `curl -s http://localhost:8080/api/v1/jobs`. If it's down, run `docker compose up -d` from the kit root, wait ~10s, and retry.
2. **Parse** the business type and city from the query. Look up the city's **latitude/longitude** (as strings).
3. **ASK about social profiles — always, before scraping.** Ask the user ONE short question:
   *"Want me to also grab their social profiles (Instagram / Facebook / LinkedIn)? Emails are already included by default. (yes / no)"*
   Wait for the answer. **Skip the question only if** the user already said yes/no to socials in their request.
   If **yes** → add `--socials` in step 4. If **no** → leave it off. (Socials add no LLM-token cost and one extra HTTP fetch per site — see the skill.)
4. **Create the job with EMAIL EXTRACTION ON** (`"email": true` in the body — emails are the #1 lead field). Required fields — `keywords` (location baked into each term), `lat`/`lon` (strings), `max_time` (seconds, default `300`), `depth` (the number in the query, else `5`). Easiest path: `python3 scripts/scrape.py "<keyword>" --city "<City, ST>" --depth <n>` (emails are already on by default; append `--socials` if the user said yes in step 3).
5. **Poll to completion in the BACKGROUND** (the Bash tool blocks foreground `sleep` — use `run_in_background: true` and read the output file when notified). Then download the CSV.
6. **Save a CSV file** (the default — `scripts/scrape.py` writes `results-<id>.csv`; if you use the raw API, save the parsed lead fields to a `.csv` yourself). Then **present ONLY money-useful lead fields** in a clean markdown table: `name (title), phone, emails, website, category, address, review_rating, review_count` (+ `instagram, facebook, linkedin` if socials were requested). **Drop everything else** — especially `latitude`/`longitude`, IDs, hours, images, review blobs. Do NOT dump the full 34-column CSV into chat; show a few sample rows and tell the user the CSV path. (Include dropped fields only if the user explicitly asks.)

**Emails:** on by default in this kit — the scraper visits each business website to find them, which is a bit slower. Some businesses simply don't publish an email, so coverage is partial. For a deliberately fast run with no emails, pass `--no-email`.

**Socials:** when the user says yes, `scripts/scrape.py … --socials` pulls Instagram/Facebook/LinkedIn. Extraction is **0 LLM tokens** (runs in code); it only adds ~40–50 tokens/business if you load rows into chat. **Never** WebFetch each website yourself to find socials — that costs thousands of tokens.

**Warn, don't block:** if the request is high-volume (high `depth`, many keywords, or repeated runs),
print ONE short warning that over-use can get their IP temporarily rate-limited by Google and suggest
adding proxies — then **proceed with the scrape anyway**. Do not gate or demand confirmation just for a
big job. Only refuse outright for clearly abusive use (surveilling individuals, spam/harassment). Also
remind the user about PII / Google ToS if they'll store or contact the data.
