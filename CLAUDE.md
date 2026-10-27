# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## What This Project Is

An AI-Powered Banking Fraud & Compliance Intelligence Platform — a portfolio/academic mini-project that detects fraudulent transactions, maps fraud networks as a knowledge graph, scores transaction risk in real time, and auto-generates regulatory reports (SARs) using RAG + Claude API.

**The project is not yet implemented.** The repo currently holds planning documents, architecture diagrams, and a learning curriculum. Code is built incrementally through 7 stages. Check `PROGRESS.md` to see which stages are done.

**Three graded deliverables:**
1. A **knowledge graph** (Neo4j) linking transactions, KYC, and behavioural data — so fraud rings hidden across accounts become visible
2. A **transaction risk-scoring model** (LightGBM) — assigns a 0–1 fraud probability to every transaction in real time, with SHAP explanations for why
3. A **Compliance Assistant** — RAG pipeline that retrieves relevant regulations and uses Claude API to auto-draft a Suspicious Activity Report (SAR) for a flagged case

---

## How the System Works End-to-End

```
Raw transaction data (PaySim / IEEE-CIS datasets)
          │
          ▼
  [Stage 1] Load into Neo4j knowledge graph
  — accounts, devices, phone numbers become nodes
  — "transferred to", "shares device", "registered with" become edges
  — fraud rings (accounts sharing identifiers) become visible as clusters
          │
          ├──► [Stage 2] Feature engineering → LightGBM → risk score (0–1)
          │    — features: amount deviation, velocity, novelty, graph-hop flags
          │    — SHAP explains which features drove the score
          │
          ├──► [Stage 3 — stretch] Export graph → PyTorch Geometric → GNN
          │    — GNN sees the account's full neighbourhood, not just its row
          │    — compare recall/precision against Stage 2 baseline
          │
          ├──► [Stage 4] Flagged case + retrieved regulations → Claude API → SAR draft
          │    — vector DB holds embedded regulatory docs (PMLA, RBI circulars)
          │    — RAG retrieves relevant chunks → Claude writes the SAR narrative
          │
          └──► [Stage 5] FastAPI backend + React frontend ties it together
               — transaction list with risk scores
               — interactive graph view of the fraud network
               — "Generate SAR" button calls the Stage 4 pipeline
```

---

## Repo Structure (create in Stage 0)

```
Bank-Fraud-Ai-Platform/
├── data/
│   ├── raw/              ← downloaded datasets (gitignored — too large)
│   └── processed/        ← cleaned CSVs ready for loading (gitignored)
├── knowledge_graph/      ← Stage 1: Cypher scripts, graph loading code
├── risk_model/           ← Stage 2: training notebooks, saved model, SHAP plots
├── gnn_model/            ← Stage 3 (stretch): PyG training code
├── compliance_assistant/ ← Stage 4: RAG pipeline, regulatory docs, SAR generation
│   ├── documents/        ← PMLA, RBI circulars, FATF reports (source PDFs)
│   └── vector_store/     ← Chroma DB index (gitignored — rebuilt from documents/)
├── dashboard/            ← Stage 5: FastAPI backend + React frontend
│   ├── backend/          ← FastAPI app (main.py, routers/)
│   └── frontend/         ← React app (src/, public/)
├── tests/                ← Stage 6: pytest suites
├── scripts/              ← Utility scripts (setup-new-machine.sh, etc.)
├── project-plan/         ← Learning curriculum and implementation stage files
├── Reports/              ← Decks, diagrams, synopsis docs for submission
├── docker-compose.yml    ← Spins up Neo4j + backend together
├── .env.example          ← Template for required secrets
├── DECISIONS.md          ← Running log of every design choice made
└── PROGRESS.md           ← Current stage completion status
```

---

## Environment Setup — Every Command Explained

### 1. Python virtual environment

```bash
python3 -m venv .venv
```
Creates an isolated Python environment in `.venv/`. Without this, packages installed for this project could conflict with system Python packages. The `.venv/` folder is gitignored — each machine creates its own.

```bash
source .venv/bin/activate
```
Activates the environment so `python` and `pip` point to `.venv/bin/` instead of the system Python. Run this at the start of every session. Your shell prompt will show `(.venv)` when active.

```bash
pip install -r requirements.txt
```
Installs all project dependencies pinned to specific versions. Add packages stage by stage as you need them — don't install everything upfront. Keep `requirements.txt` updated with `pip freeze > requirements.txt` after adding each new package.

---

### 2. Neo4j (the knowledge graph database)

```bash
docker run -d --name fraud-graph \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  -v $(pwd)/neo4j_data:/data \
  neo4j:5
```

Breaking this down flag by flag:
- `-d` — runs the container in the background (detached), so your terminal stays free
- `--name fraud-graph` — gives the container a name so you can reference it with `docker stop fraud-graph` / `docker start fraud-graph` instead of a hash
- `-p 7474:7474` — exposes port 7474 (Neo4j's HTTP browser UI) from the container to your machine — open `http://localhost:7474` to use the visual query tool
- `-p 7687:7687` — exposes port 7687 (the Bolt protocol) — this is the port your Python code and the Neo4j MCP server connect to when running queries
- `-e NEO4J_AUTH=neo4j/your_password_here` — sets the username (`neo4j`) and password — must match `NEO4J_PASSWORD` in your `.env`
- `-v $(pwd)/neo4j_data:/data` — mounts a local folder `neo4j_data/` into the container so graph data persists when the container stops. Without this, all your graph data disappears when the container is removed. `neo4j_data/` is gitignored.
- `neo4j:5` — uses Neo4j version 5, the current major version

**To check it's running:**
```bash
docker ps | grep fraud-graph        # should show the container as "Up"
# then open http://localhost:7474 in a browser and log in
```

**To stop/start without losing data:**
```bash
docker stop fraud-graph
docker start fraud-graph
```

---

### 3. Environment secrets (.env)

```bash
cp .env.example .env
```
Creates your local secrets file from the template. Open `.env` and fill in real values. This file is gitignored — never commit it. The `.env.example` file (committed) shows exactly which keys are needed without containing any real values.

The Python code loads these at runtime via:
```python
from dotenv import load_dotenv
load_dotenv()
uri = os.getenv("NEO4J_URI")
```

Required keys and what uses them:
- `ANTHROPIC_API_KEY` — Stage 4 compliance assistant (Claude API calls for SAR generation)
- `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` — all stages that talk to Neo4j
- `GITHUB_TOKEN` — GitHub MCP server (repo operations from Claude)
- `HUGGINGFACE_TOKEN` — Stage 4 (downloading embedding models for the RAG vector store)

---

### 4. New machine setup (one command)

```bash
bash scripts/setup-new-machine.sh
```
This script runs all the above steps in order: checks prerequisites exist (node, python3, docker, claude), copies `.env.example` to `.env`, creates and activates the venv, installs requirements if they exist, installs Playwright browsers, and starts the Neo4j container. Run it once after cloning on a new machine, then fill in `.env` manually.

---

## Implementation Stages — What's Happening and Why

### Stage 0 — Environment Setup

**Goal:** A working dev environment, correct repo structure, and raw datasets on disk — so every later stage starts from a known baseline.

**What you're doing:**
- Creating the folder structure listed above
- Getting Neo4j running (see commands above)
- Downloading raw datasets into `data/raw/` — PaySim from Kaggle (`ealaxi/paysim1`) for transaction graph structure, and optionally IEEE-CIS Fraud Detection for richer device/identity columns. Don't process anything yet.
- Confirming your Anthropic API key works with a minimal test call
- Starting `DECISIONS.md` — first entry should be which dataset you chose and why

**Done when:** `docker ps` shows Neo4j running, Python venv activates cleanly, `.env` has your API key and is gitignored (run `git status` — it must not appear), raw data files are in `data/raw/`.

---

### Stage 1 — Data & Knowledge Graph

**Goal:** Objective 1 complete — a populated Neo4j graph where fraud rings hidden across accounts are findable with a single Cypher query.

**What you're doing and why each step matters:**

**Step 1 — Clean the data (`knowledge_graph/clean.py`)**
Load the raw PaySim CSV with pandas. Standardise account ID formats (e.g. `"C1001"` vs `1001` vs `"ACC-1001"` all referring to the same account creates duplicate nodes — this is the single most common bug at this stage). Parse timestamps. Drop rows with null IDs. Output cleaned CSVs to `data/processed/`.

**Step 2 — Design the graph schema**
Decide what becomes a **node** vs what becomes a **property**:
- Node: something that has its own identity and connects to multiple other things. Phone numbers, devices, IP addresses — these should be nodes because a single phone number connecting to 5 accounts is the fraud signal you're looking for. If you model phone number as a property on Account, you can't query "which accounts share this phone number" without a full table scan.
- Property: something that only describes one entity. Transaction amount, timestamp — these live as properties on the Transaction node.

Schema:
```
(Account)-[:SENT]->(Transaction)-[:TO]->(Account)
(Account)-[:USES_DEVICE]->(Device)
(Account)-[:REGISTERED_WITH]->(PhoneNumber)
(Account)-[:FLAGGED_AS]->(FraudCase)   ← optional
```

**Step 3 — Write the loading script (`knowledge_graph/load_graph.py`)**
Uses the `neo4j` Python driver to insert nodes and relationships. Critical: use `MERGE` not `CREATE` so re-running the script doesn't create duplicates. MERGE checks if a node with that ID already exists before creating it.

```python
# Example: idempotent account node creation
session.run("""
    MERGE (a:Account {account_id: $account_id})
    SET a.opened_date = $opened_date
""", account_id=row["account_id"], opened_date=row["opened_date"])
```

**Step 4 — Inject synthetic fraud rings**
Public datasets have `is_fraud` labels but don't explicitly link fraud accounts by shared identifiers. You need to manually pick 4–5 "normal" accounts and assign them the same synthetic phone number and device ID — this creates a detectable fraud ring that your demo will find. Without this, Stage 3 and Stage 5 have nothing interesting to show.

**Step 5 — Write and save investigative Cypher queries (`knowledge_graph/queries.cypher`)**
These are the queries your dashboard and custom skills will run. Key ones:
```cypher
// Find accounts sharing a device with a flagged account (2-hop)
MATCH (flagged:Account {is_flagged: true})-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other:Account)
WHERE other <> flagged
RETURN other.account_id, d.device_id

// Shortest path between two accounts (money trail)
MATCH p = shortestPath(
  (a:Account {account_id: $id1})-[*..6]-(b:Account {account_id: $id2})
)
RETURN p

// All accounts reachable within 2 hops from a suspect account
MATCH (a:Account {account_id: $id})-[*1..2]-(connected)
RETURN connected
```

**Step 6 — Visual sanity check**
Open `http://localhost:7474`, run a small MATCH query, and look at the rendered graph. Confirm the fraud ring you injected actually shows up as a visually connected cluster. If accounts that should be connected are isolated, there's a data loading bug.

**Done when:** The idempotency check passes (run load script twice, node count stays the same), a Cypher query finds the synthetic fraud ring, and you can explain why every node/edge type is modelled the way it is.

---

### Stage 2 — Risk Scoring Model

**Goal:** Objective 2 (core) complete — a LightGBM model that scores any transaction 0–1 for fraud probability in milliseconds, with SHAP explanations showing which features drove the score.

**What you're doing and why each step matters:**

**Step 1 — Feature engineering (`risk_model/features.py`)**
LightGBM works on tabular features, not raw transaction rows. You need to compute:
- **Amount z-score**: `(tx_amount - account_mean_amount) / account_std_amount` — how many standard deviations above this account's typical transaction size is this one?
- **Velocity**: count of transactions from this account in the last 1h / 24h / 7d — smurfs make many small transactions rapidly
- **Time-of-day deviation**: is this transaction happening at an unusual hour for this account?
- **Novelty flags**: boolean — new device seen? new recipient? new geographic region?
- **Graph-derived features** (query Neo4j): number of flagged accounts within 2 hops, how many accounts share this account's device

These features are the difference between a model that catches fraud and one that doesn't. Hyperparameter tuning matters far less than good features.

**Step 2 — Time-based train/test split (critical — do not use random split)**
Sort all transactions by timestamp. Train on the earliest 70–80%, test on the latest 20–30%. A random split would let transactions from the same account appear in both train and test — the model would memorise account behaviour rather than learning generalisable fraud patterns, inflating test scores artificially. In real deployment, the model always sees future transactions it hasn't trained on — the time split mirrors this.

**Step 3 — Handle class imbalance**
Fraud is rare — maybe 1–2% of transactions. If you train naively, the model will learn to just predict "not fraud" for everything and get 98% accuracy while catching zero fraud. Fix with `scale_pos_weight = (number of non-fraud rows) / (number of fraud rows)` in LightGBM — this tells the model to treat each fraud example as if it appeared `scale_pos_weight` times.

**Step 4 — Train LightGBM**
```python
import lightgbm as lgb
model = lgb.LGBMClassifier(
    scale_pos_weight=scale_pos_weight,
    n_estimators=500,
    learning_rate=0.05,
    num_leaves=31
)
model.fit(X_train, y_train)
```
LightGBM is used here (not XGBoost or a neural net) because: fast inference (milliseconds per transaction at runtime), handles tabular data well, and SHAP has native TreeExplainer support for it.

**Step 5 — Evaluate with the right metrics**
Do NOT report accuracy. For imbalanced fraud data:
- **Precision**: of all transactions we flagged, what fraction were real fraud? (False positive cost)
- **Recall**: of all real fraud transactions, what fraction did we catch? (False negative cost)
- **AUPRC** (Area Under the Precision-Recall Curve): single number summarising the precision/recall tradeoff across all thresholds — the right summary metric for imbalanced classification
- **Operating threshold**: pick a specific threshold (e.g. 0.65) and state what you get — "at this threshold we catch 83% of fraud at a 12% false-positive rate among flagged transactions"

**Step 6 — SHAP explanations (`risk_model/explain.py`)**
SHAP (SHapley Additive exPlanations) computes how much each feature contributed to a specific prediction:
```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
# For one transaction, shows: amount_zscore pushed score up by +0.23,
# new_device pushed up by +0.18, time_deviation pushed up by +0.09, etc.
shap.plots.waterfall(shap_values[i])
```
This is your explainability deliverable. Every flagged transaction should be explainable in plain English: "Flagged because: transaction is 4.2× the account average, from a new device, at 3am."

**Step 7 — Save and expose inference interface**
```python
import joblib
joblib.dump(model, "risk_model/model.pkl")
```
Then write `risk_model/score.py` with a function `score_transaction(features: dict) -> dict` that loads the model and returns `{"risk_score": 0.87, "top_features": [...]}`. Stage 5's FastAPI backend calls this function.

**Done when:** Model saved to disk, evaluation report with AUPRC exists, SHAP plots saved for 5+ predictions, inference function callable standalone.

---

### Stage 3 — GNN Fraud Detection (Stretch)

**Only start if Stage 2 is fully done and you have 2+ weeks left.**

**Goal:** A GraphSAGE model that uses the full account network (not just the transaction row) to classify fraud — then an honest numeric comparison against the Stage 2 baseline.

**What you're doing and why it's different from Stage 2:**

LightGBM sees each transaction as a row of features. It can include graph-derived features, but those are precomputed summaries (e.g. "2 flagged accounts within 2 hops") — it doesn't see the actual network structure.

A Graph Neural Network processes the graph directly. For each account node, GraphSAGE aggregates feature information from its neighbours, then from neighbours-of-neighbours. This means the model's representation of account A is influenced by what accounts B, C, D (connected to A) look like — if B and C were flagged, A's representation shifts toward "suspicious" even if A's own features look normal.

**Step 1 — Export Neo4j graph to PyTorch Geometric format**
```python
# Pull from Neo4j, build PyG Data object
from torch_geometric.data import Data
import torch

# x: node feature matrix [num_nodes, num_features]
# edge_index: [2, num_edges] — source and destination node indices
# y: labels [num_nodes] — 0 or 1
data = Data(x=node_features, edge_index=edge_index, y=labels)
```

**Step 2 — Build a GraphSAGE model (2 layers)**
```python
from torch_geometric.nn import SAGEConv
class FraudGNN(torch.nn.Module):
    def __init__(self):
        self.conv1 = SAGEConv(in_channels, 64)
        self.conv2 = SAGEConv(64, 2)
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index).relu()
        return self.conv2(x, edge_index)
```
Use 2–3 layers. More layers cause over-smoothing — every node's representation converges to the same average, losing the local structure you're trying to capture.

**Step 3 — Time-split carefully**
Same principle as Stage 2, but harder: edges can connect a "past" node to a "future" node, leaking test information into training through the graph. Be deliberate — mask out test-period edges during training.

**Step 4 — Compare honestly against Stage 2**
Compute the same metrics (AUPRC, Precision, Recall at your chosen threshold) on the same conceptual test set. Write a one-paragraph comparison. An honest "GNN didn't clearly beat LightGBM on this small dataset but here's why it would matter at production scale" is more credible than a suspicious perfect improvement.

---

### Stage 4 — Compliance Assistant (RAG + SAR Generation)

**Goal:** Objective 3 complete — given a flagged account ID, the system retrieves the relevant regulations and generates a complete, cited SAR draft using Claude API.

**What you're doing and why each step matters:**

**Step 1 — Assemble a regulatory document corpus (`compliance_assistant/documents/`)**
Collect 5–10 key documents as PDFs/text files:
- PMLA 2002 (Prevention of Money Laundering Act) — sections on reporting obligations
- RBI Master Direction on KYC
- FIU-IND SAR format/guidance
- 1–2 FATF typology reports on smurfing and layering

These are the documents the RAG pipeline will search through. They must be real regulatory text — the whole point of RAG is that Claude answers from retrieved facts, not from its training memory.

**Step 2 — Build the ingestion pipeline (`compliance_assistant/ingest.py`)**
```
Documents (PDF/text)
    → Load (LangChain document loaders)
    → Chunk (split into ~500-token segments, respecting section boundaries)
    → Embed (sentence-transformers: all-MiniLM-L6-v2 converts each chunk to a vector)
    → Store (Chroma saves the vectors + original text to compliance_assistant/vector_store/)
```

Why Chroma over Pinecone/Weaviate: free, local, no API key needed, sufficient for a corpus of 10 documents. Log this in `DECISIONS.md`.

Why chunking matters: if you split a regulatory requirement mid-sentence across two chunks, neither retrieved chunk has the complete rule. Chunk at section/paragraph boundaries where possible.

**Step 3 — Build the retrieval step**
```python
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = Chroma(persist_directory="compliance_assistant/vector_store", embedding_function=embeddings)

# At query time:
relevant_chunks = vector_store.similarity_search(query, k=5)
```
The query is constructed from the case context: "SAR filing requirements structuring smurfing PMLA 2002" — not the analyst's raw question verbatim.

**Step 4 — Build the SAR generation step with Claude API**
```python
import anthropic
import os

# Using AWS Bedrock bearer token auth (simpler than IAM key+secret)
# SDK picks up AWS_BEARER_TOKEN_BEDROCK from environment automatically
client = anthropic.AnthropicBedrock(
    aws_region=os.getenv("AWS_REGION", "us-east-1"),
)

system = """You are a compliance analyst. Generate a Suspicious Activity Report.
Only make claims supported by the provided regulatory excerpts.
Cite the source document and section for every regulatory claim."""

prompt = f"""
Case data:
- Account: {account_data}
- Transactions: {transaction_history}
- Risk score: {risk_score}, driven by: {shap_explanation}
- Graph connections: {graph_summary}

Relevant regulations:
{retrieved_chunks}

Generate a structured SAR with these sections:
1. Subject information
2. Suspicious activity description
3. Regulatory basis (cite retrieved sections)
4. Supporting evidence
5. Recommended action
"""

response = client.messages.create(
    model=os.getenv("BEDROCK_MODEL_ID"),
    max_tokens=2048,
    system=system,
    messages=[{"role": "user", "content": prompt}]
)
```

**Step 5 — Verify grounding manually**
For 3+ test cases, read the generated SAR and cross-check every regulatory citation against the actual source document. LLMs can cite section numbers that don't say what's claimed — this manual spot-check is your quality evidence for the report.

**Step 6 — Build the analyst Q&A endpoint**
Same retrieval + generation pipeline, but for freeform questions: "Does this qualify as smurfing under PMLA 2002?" The retrieval query is the question itself; the generation prompt asks Claude to answer only from retrieved text.

**Done when:** 3 generated SARs manually verified to have accurate citations, Q&A answers 2–3 test compliance questions correctly, `DECISIONS.md` notes the embeddings model choice.

---

### Stage 5 — Dashboard & Demo Assembly

**Goal:** A single demoable interface tying all three objectives into one coherent flow: transaction arrives → risk scored → network visualised → SAR generated.

**What you're building:**

**FastAPI backend (`dashboard/backend/main.py`)**
FastAPI auto-generates Swagger docs at `/docs` — use this to test endpoints before the frontend exists.

Key endpoints and what they do:
```
GET  /accounts/{id}           → queries Neo4j for account details + direct connections
POST /score                   → calls risk_model/score.py, returns risk score + SHAP top features
GET  /accounts/{id}/network   → queries Neo4j for 2-hop subgraph, returns nodes + edges as JSON
POST /generate-sar            → pulls case data from Neo4j + risk score, calls Stage 4 pipeline
```

Run the backend:
```bash
cd dashboard/backend
uvicorn main:app --reload --port 8000
# --reload restarts the server on every file save during development
# Swagger UI at http://localhost:8000/docs
```

**React frontend (`dashboard/frontend/`)**
Three panels, not four — one tight flow beats four half-finished panels:

1. **Transaction list** — calls `POST /score` for each transaction, renders rows colour-coded by risk tier (green < 0.4, yellow 0.4–0.7, orange 0.7–0.9, red > 0.9)
2. **Network graph** — for a selected flagged account, calls `GET /accounts/{id}/network`, renders with `react-force-graph` (simpler than raw D3 for node-link graphs — less setup, interactive by default)
3. **Case panel** — shows the SHAP explanation for the selected transaction, plus a "Generate SAR" button that calls `POST /generate-sar` and streams the response

Run the frontend:
```bash
cd dashboard/frontend
npm install
npm start        # starts dev server at http://localhost:3000
```

**Prepare specific demo scenarios before your review**
Pick 2–3 account IDs from your synthetic fraud ring (Stage 1) that you know produce an interesting graph and a high risk score. Hardcode these as "demo cases" in the UI. Do not rely on randomly browsing live data during the actual review — the demo should be scripted and rehearsed.

The canonical demo flow (from the deck's End-to-End Flow diagram):
1. Show a transaction with risk score 0.93 arriving
2. Click it — SHAP panel shows "new device (+0.21), 3am (+0.14), 4× average amount (+0.18)"
3. Click "View Network" — graph expands showing the account shares a device with 3 other flagged accounts
4. Click "Generate SAR" — SAR draft appears, citing PMLA Section 12 (retrieved from vector store)

---

### Stage 6 — Testing & Validation

Write `tests/` with pytest. Key things to test:
- The graph loading script is idempotent (node count unchanged on second run)
- The inference function returns a score in 0–1 range for valid inputs
- The RAG retrieval returns non-empty results for known regulatory terms
- The SAR generation pipeline returns all required sections
- FastAPI endpoints return correct status codes and response shapes

Run tests:
```bash
pytest tests/ -v
```

---

### Stage 7 — Deployment (Optional)

If time allows: write a `docker-compose.yml` that spins up Neo4j + FastAPI backend together, so the whole project runs with one command on any machine.

```yaml
services:
  neo4j:
    image: neo4j:5
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    volumes:
      - ./neo4j_data:/data
  backend:
    build: ./dashboard/backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [neo4j]
```

---

## Custom Skills — What Each One Does

Skills live in `.claude/commands/` and are invoked with a slash command. They're committed to git so they work on any machine after clone.

**`/cypher-query <query>`**
Runs a Cypher query against the local Neo4j instance. Checks Neo4j is running first, executes the query with connection config from `.env`, and formats the results as a readable table. Use for ad-hoc graph exploration during Stages 1–3 without leaving Claude Code.

**`/risk-score <transaction JSON>`**
Feeds a transaction's features through the saved LightGBM model and returns the fraud probability score + the top 5 SHAP drivers. Use during Stage 2 development to test the model on individual cases, and during Stage 5 to verify the inference pipeline end-to-end. Will tell you if Stage 2 isn't complete yet.

**`/sar-draft <case_id>`**
Pulls the case's transaction history from Neo4j, feeds it with the risk score into the Stage 4 RAG pipeline, and generates a SAR draft. Use during Stage 4 development to test generation quality, and during Stage 5 as the backend call behind the "Generate SAR" button. Will tell you if Stage 4 isn't complete yet.

**`/graph-explain <account_id>`**
Pulls the 2-hop subgraph around an account from Neo4j and explains every connection in plain English — how many flagged neighbours, what identifiers are shared, which known fraud patterns the structure matches. Ends with a one-line network-level risk verdict. Use from Stage 1 onwards to investigate any flagged account without writing Cypher manually.

---

## Built-in Claude Code Skills — When to Use Each

| Skill | Invoke | Use when |
|---|---|---|
| `/run` | Stage 5 onwards | Starts FastAPI + React dev servers; also useful in Stage 1 to confirm the Neo4j loader completes cleanly |
| `/verify` | Stage 5/6 | Walk through a full fraud scenario in the running UI — confirms risk scores, graph visualisation, and SAR generation actually work end-to-end |
| `/code-review` | Before marking any stage done | Especially Stage 2: checks for data leakage in train/test splits, SHAP correctness. Stage 4: checks RAG grounding quality |
| `/security-review` | Stage 0 and Stage 4 | Stage 0: confirms `.env` is gitignored, no secrets in code. Stage 4: checks for Cypher injection in Neo4j queries, API key exposure in logs |
| `/fewer-permission-prompts` | After Stage 0 | Run once when your toolchain is settled — stops repeated permission prompts for common bash/python commands |
| `/loop` | Stage 2/3 training runs | Monitors a long model training process and notifies you when it finishes |

---

## Resuming on a New Machine

Everything Claude needs travels with this repo. After cloning:

```bash
# 1. One-command setup: creates .env, sets up venv, starts Neo4j, installs Playwright
bash scripts/setup-new-machine.sh

# 2. Fill in real secrets (the script creates .env from .env.example but leaves values blank)
nano .env   # add ANTHROPIC_API_KEY, NEO4J_PASSWORD, GITHUB_TOKEN, HUGGINGFACE_TOKEN

# 3. Open Claude Code — .claude/settings.json loads permissions automatically
claude .
```

**What travels with the repo (git):** CLAUDE.md, `.claude/commands/` (all four skills), `.claude/settings.json` (MCP + permissions), `PROGRESS.md`, `DECISIONS.md`, `.env.example`, `scripts/setup-new-machine.sh`

**What you recreate per machine:** `.env` (secrets), `neo4j_data/` (repopulate from Stage 1 scripts), `.venv/` (setup script handles this), model files (retrain or copy manually)

**Orient Claude after clone:** Say "Read CLAUDE.md and PROGRESS.md and tell me where we are." That gives a fresh Claude instance full project context without needing conversation history.

---

## Design Decisions Log

Every time you choose X over Y, add one line to `DECISIONS.md`:
```
[Stage N] Using Chroma instead of Pinecone — free, local, no API key, sufficient for 10-document corpus
[Stage 1] Using PaySim as primary dataset — synthetic fraud patterns with explicit account sender/receiver IDs
```
This feeds directly into your review defense and project report. Start it in Stage 0.
