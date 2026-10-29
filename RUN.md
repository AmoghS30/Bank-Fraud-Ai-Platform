# Running the Bank Fraud AI Platform

## Step 1 — Install prerequisites

1. **Install Git** (to clone the repo): https://git-scm.com/download/win
2. **Install Git LFS** (for the large database file): https://git-lfs.github.com
3. **Install Docker Desktop**: https://www.docker.com/products/docker-desktop/

After installing Docker Desktop:
- Open it and wait for it to say "Docker Desktop is running"
- Go to **Settings → Resources → Memory** and set it to at least **4 GB** → click "Apply & Restart"

---

## Step 2 — Get the AWS Bedrock API key from Amogh

The SAR generator needs an AWS key to call Claude. Ask Amogh for the key — he will give you a string starting with `ABSK...`.

---

## Step 3 — Clone the repo

Open **PowerShell** (search "PowerShell" in Start menu) and run:

```powershell
git lfs install
git clone https://github.com/AmoghS30/Bank-Fraud-Ai-Platform.git
cd Bank-Fraud-Ai-Platform
```

---

## Step 4 — Create your .env file

Inside the `Bank-Fraud-Ai-Platform` folder, create a file called `.env` (no extension) with this content — replace the key with the one Amogh gave you:

```
AWS_BEARER_TOKEN_BEDROCK=ABSK...paste_key_here...
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=in.anthropic.claude-sonnet-5
```

To create it in PowerShell:
```powershell
notepad .env
```
Paste the lines above, save and close.

---

## Step 5 — Start everything

Still in PowerShell, inside the `Bank-Fraud-Ai-Platform` folder:

```powershell
docker compose up --build
```

**First run takes 5–10 minutes** — it's downloading and building everything.
You'll see a lot of log output. That's normal.

Wait until you see a line like:
```
fraud-app  |   Network URL: http://0.0.0.0:8501
```

---

## Step 4 — Open the app

Open your browser and go to:

**http://localhost:8501**

---

## To stop the app

Press `Ctrl + C` in PowerShell, then run:

```powershell
docker compose down
```

---

## Troubleshooting

**"docker: command not found"** → Docker Desktop is not running. Open Docker Desktop from the Start menu and wait for it to start.

**App crashes or Neo4j keeps restarting** → Not enough memory. Go to Docker Desktop Settings → Resources → increase Memory to 4–6 GB.

**Port 8501 already in use** → Something else is using that port. Run `docker compose down` first, then `docker compose up`.

**Build fails with a network error** → Check your internet connection and retry `docker compose up --build`.
