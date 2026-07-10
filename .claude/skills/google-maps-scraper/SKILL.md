---
name: google-maps-scraper
description: Scrape Google Maps business listings (name, address, phone, website, rating, reviews, lat/lng, hours, emails) via the local gosom google-maps-scraper REST API. Use when the user wants local-business / lead-gen data, "a list of [businesses] in [place]", or to enrich places with contact info. NOT for Instagram/TikTok/YouTube or any social-media scraping.
---

# Google Maps Scraper

Drive the local Google Maps scraper API to turn a business-type + location into clean, structured rows.

## Mental model
The scraper runs as a local Docker container exposing a REST API at `http://localhost:8080` (no auth —
localhost only). A "scrape" is an **async job**: you create it, poll until it's done, then download a CSV.
One job can run many keywords. Each result has up to **34 fields**.

## Step 0 — Make sure it's running
```bash
curl -s http://localhost:8080/api/v1/jobs >/dev/null 2>&1 && echo UP || echo DOWN
```
If `DOWN`: `docker compose up -d` (from the kit root), wait ~10s, retry. If Docker isn't installed, point
the user to `SETUP.md`.

## Step 1 — Create a job  (`POST /api/v1/jobs`)
**Required fields — the API returns `422` without them:**
- `keywords` — array of search strings. **Bake the location into each term**: `"plumbers in Denver CO"`.
- `lat`, `lon` — **strings**, the city's coordinates: `"39.7392"`, `"-104.9903"`.
- `max_time` — integer **seconds** (max wall-clock for the job), e.g. `300`. (Sent as seconds; the API stores it as nanoseconds internally — just send seconds.)

**Recommended fields:**
- `depth` (default 10) — how far to scroll → roughly how many listings per keyword. Start at `5`.
- `lang` `"en"`, `zoom` `15` (city level), `radius` `10000` (meters), `fast_mode` `false`.
- **`email` `true` — ON by default in this kit.** Emails are the #1 lead field; the scraper visits each
  business website to find them (a bit slower). Only set `false` for a deliberately fast, no-email run.

```bash
curl -s -X POST http://localhost:8080/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"name":"job","keywords":["coffee shops in Austin TX"],"lang":"en","zoom":15,
       "lat":"30.2672","lon":"-97.7431","fast_mode":false,"radius":10000,
       "depth":5,"email":true,"max_time":300}'
# → {"id":"<uuid>"}   (HTTP 201; note: lowercase "id")
```

> **Two things to handle on every scrape:**
> 1. **Emails: on by default** (`email:true`). Don't turn them off unless the user wants a fast run.
> 2. **Socials: ASK first.** Before creating the job, ask the user once whether they also want
>    Instagram/Facebook/LinkedIn (see "Social profiles" below). Don't silently skip it.

## Step 2 — Poll until done  (`GET /api/v1/jobs/{id}`)
The response field is `"Status"` (capital S): `working` → `ok` (success) or `failed`.

> ⚠️ **Claude harness rule:** the Bash tool **blocks foreground `sleep`**. Run the poll loop as a
> **background** Bash command (`run_in_background: true`) and read its output file when notified.
> Do NOT poll with a foreground `sleep`.

Background poll snippet (parses the value safely — match up to the closing quote, don't anchor on `$`):
```bash
ID="<uuid>"
for i in $(seq 1 40); do
  S=$(curl -s "http://localhost:8080/api/v1/jobs/$ID" | grep -oE '"Status":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "status=$S"
  [ "$S" = ok ] && { echo DONE; break; }
  [ "$S" = failed ] && { echo FAILED; break; }
  sleep 15
done
```

## Step 3 — Download + parse  (`GET /api/v1/jobs/{id}/download`)
```bash
curl -s "http://localhost:8080/api/v1/jobs/$ID/download" -o results.csv
```
CSV columns (34): `input_id, link, title, category, address, open_hours, popular_times, website, phone,
plus_code, review_count, review_rating, reviews_per_rating, latitude, longitude, cid, status,
descriptions, reviews_link, thumbnail, timezone, price_range, data_id, place_id, images, reservations,
order_online, menu, owner, complete_address, about, user_reviews, user_reviews_extended, emails`.

### ⭐ Output ONLY money-useful lead fields (default)
The raw CSV has 34 columns and most are noise. **By default, return ONLY these lead fields** — the data you
actually use to contact and qualify a lead — and **drop everything else**:

> `title` (name), `phone`, `emails`, `website`, `category`, `address`, `review_rating`, `review_count`

**DROP by default** (do not show these unless the user explicitly asks): `latitude`/`longitude` (no use for
outreach), `link`, `plus_code`, `cid`, `data_id`, `place_id`, `open_hours`, `popular_times`,
`reviews_per_rating`, `reviews_link`, `thumbnail`, `images`, `timezone`, `price_range`, `status`,
`input_id`, `complete_address`, `reservations`, `order_online`, `menu`, `owner`, `about`, `descriptions`,
`user_reviews`, `user_reviews_extended`.

`scripts/scrape.py` already returns exactly this lead set (use `--full` to keep all columns, or
`--fields "a,b,c"` to customize) and **saves a CSV file by default** (`results-<id>.csv`; pass `--json` for
JSON). If you call the API directly, **strip to the lead fields yourself** before presenting — never dump the
full 34-column row at the user.

### Social profiles — ALWAYS ASK the user (Instagram / Facebook / LinkedIn)
Google Maps has no social links, so this is an enrichment: visit each business's `website` and regex out its
IG/FB/LinkedIn URLs. **Before scraping, ask the user once** whether they want socials too (unless they already
said). If yes → **use the script:** `python3 scripts/scrape.py … --socials`.

- **Token cost — say this to the user when they ask for socials:** the extraction itself is **0 LLM tokens**
  (pure HTTP + regex in the script). It only adds **~40–50 tokens per business** to *your* context **if** you
  load the rows into chat — e.g. ~+2k tokens for 50 leads. Negligible if you keep the file on disk and show a
  sample. Save the file; show a few rows.
- **DO NOT** fetch each website yourself with WebFetch to find socials — that reads every page into your
  context and costs **thousands of tokens**. The script does it for free. Always prefer `--socials`.
- It's **opt-in/slower** (one HTTP fetch per business) and coverage is partial (~40–70%: only businesses that
  link socials on their site; no website → no socials). Mention this if the user expects 100%.

**Shortcuts (prefer these for common cases):**
- One keyword: `scripts/scrape.sh "<keyword>" <lat> <lon> [depth]` (bash) — create→poll→download in one go.
- Auto-geocode (no coords): `python3 scripts/scrape.py "<keyword>" --city "<City, ST>" [--depth N]` — resolves
  lat/lon via OpenStreetMap Nominatim. You can also geocode the city yourself and pass coords.
  **Emails come back by default** (use `--no-email` to skip); add `--socials` if the user asked for socials.
- **Batch (many keywords, ONE job):** `python3 scripts/scrape.py --keywords-file <file> --city "<City, ST>"`.
  The API takes a `keywords` array, so put all terms in a single job rather than firing many jobs.
Do the manual curl flow only for custom job bodies (e.g. setting `proxies`).

## Other endpoints
- `GET /api/v1/jobs` — list jobs. `DELETE /api/v1/jobs/{id}` — delete a job + free disk.
- Browser UI + OpenAPI docs: `http://localhost:8080` and `http://localhost:8080/api/docs`.

## Best practices (from the upstream docs)
- **Depth:** higher `depth` = more results but slower and more block-prone. Start low (5), raise as needed.
- **One job at a time** locally. Many concurrent jobs without proxies → throttling/blocks by Google.
- **Email extraction (`email:true`)** visits each business's website → slower, but it's **on by default** here
  because emails are the key lead field. Pass `--no-email` (script) or `email:false` (raw API) for a fast run.
- **`fast_mode:true`** returns reduced data, up to ~21 results/query, faster — good for quick lookups.
- **Proxies:** for large/repeated jobs, set `"proxies"` (array of `socks5://`/`http://`/`https://` URLs,
  auth supported). The scraper has built-in rotation. This is the main defense against rate-limiting.
- **`zoom`/`radius`** control the search area around `lat`/`lon`. Widen `radius` if results are too few.
- **Extended reviews** are available but heavy — don't enable unless the user asks for review text.

## Rate limits, bans & proxies (read before large jobs)
This hits Google Maps for real. The upstream project's only formal note is a disclaimer:
> "Please use this scraper responsibly and in accordance with applicable laws and regulations. Unauthorized scraping may violate terms of service."

There is **no published hard threshold** for bans, so be conservative:
- Google may **temporarily rate-limit / block your IP** if you scrape too fast or too much. It clears in
  minutes–hours and does **not** ban your Google account — but jobs start failing meanwhile.
- **Block signals to watch:** jobs returning `failed`, empty or unusually short results, or a sudden drop
  in row counts vs. a prior identical run. If you see these, **back off** (pause, lower depth) or add proxies.
- **Concurrency ↔ blocking** (upstream): *"Higher concurrency … can increase blocking or failures,
  especially without proxies. Start with the default for a first run."* Reference throughput ≈ **120
  places/min** at `-c 8 -depth 1`. Locally, run **one job at a time** and start at `depth 5`.

**When to add proxies** (upstream: *"For larger scraping jobs, proxies help avoid rate limiting"*):
large jobs, many keywords, repeated/scheduled runs, or after you see block signals.
- Set the `"proxies"` array in the job body. Types: `socks5`, `socks5h`, `http`, `https`.
- Format: `protocol://user:pass@host:port` (auth optional), e.g.
  `"proxies": ["socks5://user:pass@host:port", "http://host2:port2"]`. The scraper rotates them automatically.

## Safety & guardrails
- **WARN, don't block.** When a request is large/high-volume (high `depth`, many keywords, repeated runs,
  or `email:true`), **proceed with it** but first print ONE short warning about temporary IP-block risk and
  suggest proxies. Do **not** gate, force-stop, or demand confirmation just because a normal scrape is big.
  Refuse outright **only** for clearly abusive/illegal use (surveilling individuals, spam/harassment).
- **Never expose** the API beyond `localhost` without an auth proxy; never print any API key if one exists.
- **PII:** scraped emails/phones are personal data. If the user will store or contact them, remind them to
  comply with GDPR/CCPA/CAN-SPAM (lawful basis, opt-outs, suppression). Don't help with spam/harassment.
- **Google ToS:** scraping Maps is against Google's Terms — keep volume modest, treat output as leads to
  verify, don't resell raw Google data. Refuse uses aimed at surveilling individuals.
- **Output hygiene:** don't dump huge CSVs into chat — save the file to disk, summarize counts, show a few
  sample rows. Dedupe by `place_id`/`cid` before storing.
- **Disk:** results pile up in the Docker volume; offer to `DELETE` old jobs periodically.

## Troubleshooting
- `422 missing max time` → add `max_time` (seconds). `422 missing geo coordinates` → add string `lat`/`lon`.
- Stuck `working` → lower `depth` / raise `max_time` / IP throttled (add proxies or wait).
- Empty CSV → keyword too narrow or geo wrong → widen `radius`, fix coordinates.
- Connection refused → container down → `docker compose up -d`.
