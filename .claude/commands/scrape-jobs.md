---
description: List or clean up Google Maps scrape jobs
argument-hint: "[list | delete <job-id>]"
---
Manage scrape jobs via the API. Request: **$ARGUMENTS** (default to "list" if empty).

- **list** → `GET http://localhost:8080/api/v1/jobs`. Show a tidy table of `ID`, `Name`, `Status`, `Date` (newest first).
- **delete <job-id>** → `DELETE http://localhost:8080/api/v1/jobs/<job-id>` to free disk space, then confirm it returned HTTP 200.
- **download <job-id>** → `GET .../jobs/<job-id>/download` → save CSV and summarize row count.

See the `google-maps-scraper` skill for the full API reference.
