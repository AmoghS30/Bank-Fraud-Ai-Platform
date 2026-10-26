# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a mini-project (academic/portfolio) building an AI-Powered Banking Fraud & Compliance Intelligence Platform. It is **not yet implemented** — the repo currently holds planning documents, architecture diagrams, and a learning curriculum. Code is being written incrementally following the staged plan in `project-plan/02-implementation/`.

The three core deliverables (from `project-plan/README.md`):
1. A **knowledge graph** (Neo4j) linking transaction, KYC, and behavioural data
2. An **AI-based transaction risk-scoring model** (LightGBM + optional GNN with PyTorch Geometric)
3. A **Compliance Assistant** that auto-generates SAR drafts using RAG + Claude API

## Planned Repo Structure (create in Stage 0 before coding)

```
Bank-Fraud-Ai-Platform/
├── data/raw/           ← raw datasets, gitignored
├── data/processed/     ← gitignored
├── knowledge_graph/    ← Neo4j Cypher scripts + graph loading (Stage 1)
├── risk_model/         ← LightGBM training, SHAP notebooks (Stage 2)
├── gnn_model/          ← PyTorch Geometric GNN (Stage 3, stretch)
├── compliance_assistant/ ← RAG pipeline + Claude API SAR generation (Stage 4)
├── dashboard/          ← FastAPI backend + React frontend (Stage 5)
├── tests/              ← Stage 6
└── docker-compose.yml
```

## Environment Setup

Neo4j (via Docker):
```bash
docker run -d --name fraud-graph \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  -v $(pwd)/neo4j_data:/data \
  neo4j:5
# UI at http://localhost:7474
```

Python environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Secrets go in `.env` (gitignored), loaded via `python-dotenv`. Required keys: `ANTHROPIC_API_KEY`.

## Key Architecture Decisions

- **Knowledge graph**: Neo4j — entities are accounts, devices, phone numbers, IP addresses, merchants; edges are relationship types (registered_with, transferred_to, shares_device, etc.)
- **Risk scoring**: LightGBM for fast inference at transaction time; SHAP for explainability
- **GNN (stretch)**: PyTorch Geometric or DGL — runs over the local Neo4j subgraph per transaction
- **RAG**: LangChain + Chroma (local, free) or Pinecone; regulatory documents (PMLA, RBI circulars) embedded and retrieved at query time
- **LLM**: Claude (Anthropic API) for SAR narrative generation and compliance Q&A
- **Backend**: FastAPI; **Frontend**: React + D3.js for graph visualisation
- **Data**: Synthetic/public datasets (PaySim, IEEE-CIS, Kaggle credit card) — not real bank data

## Implementation Stages

Each stage has a "Definition of done" in its file under `project-plan/02-implementation/`. Do not skip to the next stage until all checkboxes pass — a half-working graph corrupts both the risk model and RAG pipeline.

Stage order: 0 (env) → 1 (knowledge graph) → 2 (risk model) → 4 (compliance/RAG) → 5 (dashboard) → 3 (GNN, stretch) → 6 (testing) → 7 (deploy, optional)

## MCP Servers (Third-Party)

Install these into Claude Code. They give Claude direct access to infrastructure and live docs rather than working blind.

| Server | Install | When to add | Why |
|---|---|---|---|
| **Neo4j** (official) | `claude mcp add neo4j npx @neo4j/mcp-server` | Stage 1 | Run Cypher queries directly from Claude — query the graph, inspect schema, debug relationships without copy-pasting |
| **Context7** (upstash/context7) | `claude mcp add context7 -- npx -y @upstash/context7-mcp` | Stage 0 | Pulls live, version-correct docs for PyTorch Geometric, LangChain, FastAPI, Neo4j driver — stops Claude writing against stale APIs |
| **Playwright** (microsoft/playwright-mcp) | `claude mcp add playwright npx @playwright/mcp@latest` | Stage 5 | Real browser control for testing the React dashboard and D3 graph visualiser — screenshots, click, console errors |
| **GitHub** (official) | `claude mcp add github -- npx @modelcontextprotocol/server-github` | Stage 0 | PR management, issue tracking, cross-branch file reads |
| **HuggingFace** (official, beta) | via HF API token | Stage 4 | Search and compare embedding models for the RAG pipeline's regulatory document index |

## Project-Level Custom Skills (create these yourself)

Store in `.claude/skills/<name>/SKILL.md` and commit to the repo. Community patterns: [travisvn/awesome-claude-skills](https://github.com/travisvn/awesome-claude-skills) (10k+ stars).

| Skill | Path | What it does | Stage |
|---|---|---|---|
| `cypher-query` | `.claude/skills/cypher-query/` | Runs a Cypher query against local Neo4j with connection config pre-loaded | 1–3 |
| `risk-score` | `.claude/skills/risk-score/` | Feeds a sample transaction JSON through the LightGBM model, returns score + SHAP explanation | 2+ |
| `sar-draft` | `.claude/skills/sar-draft/` | Takes a case ID, pulls transactions from Neo4j, triggers the RAG → Claude SAR generation pipeline | 4+ |
| `graph-explain` | `.claude/skills/graph-explain/` | Given an account ID, pulls its subgraph from Neo4j and explains connections in plain English | 1+ |

## Claude Code Skills — When to Use Each

| Skill | Invoke with | When |
|---|---|---|
| Claude API | `/claude-api` | Any time you're writing or debugging `compliance_assistant/` code — it handles Anthropic SDK patterns (prompt caching, tool use, streaming) correctly |
| Run | `/run` | Stage 5 onwards — starting the FastAPI backend + React dashboard; also useful in Stage 1 to confirm the Neo4j graph loader completes cleanly |
| Verify | `/verify` | Stage 5/6 — walk through a full fraud scenario in the running UI to confirm risk scores, graph visualisation, and SAR generation work end-to-end |
| Code review | `/code-review` | Before marking any stage "done" — especially Stage 2 (watch for data leakage in train/test splits and SHAP correctness) and Stage 4 (RAG retrieval quality) |
| Security review | `/security-review` | Stage 0 (confirm `.env` is gitignored, no secrets in code) and Stage 4 (check for Cypher injection in Neo4j queries and API key exposure in logs) |
| Fewer permission prompts | `/fewer-permission-prompts` | After Stage 0 once your toolchain is settled — run once to allowlist common Python/bash commands and stop getting prompted repeatedly |
| Loop | `/loop` | Stage 2/3 during long model training runs — monitors the process and notifies you when it finishes |

## Resuming on a New Machine

Everything Claude needs travels with this repo — skills, MCP configs, permissions, and project context. After cloning:

```bash
# 1. Run the setup script (installs dependencies, starts Neo4j, sets up .env)
bash scripts/setup-new-machine.sh

# 2. Fill in secrets
cp .env.example .env   # already done by the script, but edit the values
# Add: ANTHROPIC_API_KEY, NEO4J_PASSWORD, GITHUB_TOKEN, HUGGINGFACE_TOKEN

# 3. Open Claude Code — MCP servers defined in .claude/settings.json load automatically
claude .
```

**What travels with the repo (committed to git):**
- `CLAUDE.md` — full project context for Claude
- `.claude/commands/` — all four custom skills (`/cypher-query`, `/risk-score`, `/sar-draft`, `/graph-explain`)
- `.claude/settings.json` — project-level permissions + MCP server definitions
- `PROGRESS.md` — current stage status so Claude knows where you left off
- `DECISIONS.md` — running log of design decisions
- `.env.example` — template listing every required secret

**What you must recreate on each machine:**
- `.env` — copy from `.env.example` and fill in real keys (never committed)
- Neo4j data — the `neo4j_data/` volume is local; repopulate from Stage 1 scripts
- Python `.venv/` — recreated by the setup script
- Model files — retrain or copy manually if large

**Orienting Claude on a new machine:** Start a session by saying "Read CLAUDE.md and PROGRESS.md and tell me where we are." Claude will have full context from those two files without needing conversation history.

## Design Decisions Log

Maintain `DECISIONS.md` at the repo root — one line per decision (e.g. "Using Chroma instead of Pinecone — free, local, sufficient for this data volume"). This is required by the implementation plan and becomes material for the final review defense.
