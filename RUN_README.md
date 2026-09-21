# Google Maps Scraper Kit — Run Guide

Follow these steps to start and run the entire lead scraping system on your machine.

---

## Step 1: Start Docker Desktop
Ensure that **Docker Desktop** is open and running on your computer. (Verify the engine status says "Engine running" in the bottom-left corner).

---

## Step 2: Start the Scraper Container
Open your terminal (PowerShell, Command Prompt, or Git Bash) in this project folder and start the scraper container:

```bash
docker compose up -d
```

*This starts the core scraping engine on port **`8080`**.*

---

## Step 3: Start the Web Dashboard
In the same terminal or a new terminal window inside this folder, start the local Python dashboard server.

### On Windows (PowerShell - Recommended):
To prevent character encoding errors with Unicode symbols on Windows, run:
```powershell
$env:PYTHONUTF8=1; python scripts/gui_server.py
```

### On macOS / Linux (or Git Bash):
```bash
python3 scripts/gui_server.py
```

*This starts the user interface server on port **`3000`**.*

---

## Step 4: Open and Scrape!
Open your web browser and navigate to:
👉 **[http://localhost:3000](http://localhost:3000)**

1. Enter the **Business Niche** (e.g. `Dental Clinics`, `Gyms`, `Restaurants`).
2. Enter the **Location** (e.g. `Badlapur`, `Miami, FL`, `London`).
3. Enter the **Leads Scrape Limit** (e.g. `20`, `50`, `100`).
4. Click **Start Scraping Leads**.
5. Once completed, download your leads directly via **Export CSV** or **Export JSON**.

---

## How it Works (Ports Summary)
* **Port 3000:** The user-facing dashboard page where you enter search terms and view/export results.
* **Port 8080:** The background Docker engine running headless Chrome browsers to perform the actual scraping.
