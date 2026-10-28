# Running the Platform (Windows / Mac / Linux)

## Prerequisites

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/

2. **Increase Docker memory to at least 4GB** (the graph database needs ~1.5GB):
   - Open Docker Desktop → Settings → Resources → Memory → set to 4 GB → Apply & Restart

3. Make sure Docker Desktop is **running** before continuing.

---

## One-command start

Open a terminal (PowerShell on Windows, Terminal on Mac), navigate to this folder, then run:

```bash
docker compose up --build
```

First run downloads images and builds everything — takes **5–10 minutes**. Subsequent starts are instant.

**What you'll see:**
- Neo4j restores ~600K transaction graph (takes ~60 seconds on first boot)
- App starts and waits for Neo4j to be ready
- Look for the line: `Network URL: http://0.0.0.0:8501`

Then open: **http://localhost:8501**

---

## To stop

```
Ctrl+C
```

or in another terminal:
```bash
docker compose down
```

To also delete all data (graph, etc):
```bash
docker compose down -v
```

---

## Ports used

| Port | What it is |
|------|-----------|
| 8501 | Streamlit dashboard (open this in your browser) |
| 7474 | Neo4j browser UI (http://localhost:7474) |
| 7687 | Neo4j Bolt (used internally) |
