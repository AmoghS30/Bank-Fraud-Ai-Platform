# 7. Systems & Tech Stack

## Why this matters for the project

The previous six files are concepts; this one is tools. You don't need to
master all of these before starting — this file is a reference to come back
to as each implementation stage needs a specific tool. Treat it as a
lookup table, not a linear course.

## Tools, mapped to the stage that needs them

| Tool | Used in | What you need to know going in |
|---|---|---|
| **Neo4j** (graph database) | Stage 1 | Installation (Neo4j Desktop or Docker), the Neo4j Browser UI, basic Cypher (from file 02) |
| **Python** (general) | All stages | You should already be comfortable; if not, this is a blocker to resolve before anything else |
| **pandas** | Stage 1, 2 | DataFrame manipulation for cleaning transaction data before loading into the graph/model |
| **LightGBM / XGBoost** | Stage 2 | `pip install lightgbm`, basic `.fit()` / `.predict()` API — see file 04 |
| **PyTorch + PyTorch Geometric** | Stage 3 (GNN) | Basic PyTorch tensors/autograd if you haven't used it; PyG's `Data` object format for graphs |
| **FastAPI** | Stage 4, 5 (backend) | Basic REST API concepts: routes, request/response models (Pydantic), running with `uvicorn` |
| **LangChain** (or a lighter alternative) | Stage 4 | Document loaders, text splitters, vector store integration, retrieval chains |
| **A vector database** | Stage 4 | For a mini-project, consider **Chroma** (free, local, zero-ops) instead of Pinecone/Weaviate unless you specifically want cloud infra experience — see Stage 4 for the trade-off discussion |
| **Anthropic API (Claude)** | Stage 4 | Getting an API key, making a basic `messages.create()` call, prompt structuring |
| **React** | Stage 5 (dashboard) | Components, state (`useState`), fetching from your FastAPI backend |
| **D3.js** (or a simpler graph-viz library) | Stage 5 | For a mini-project, consider **react-force-graph** or **Cytoscape.js** instead of raw D3 — much less code for the same "interactive network graph" result. See Stage 5. |
| **Docker** | Stage 0, 7 | Running Neo4j/Chroma as containers so your environment is reproducible; not full Kubernetes unless you have time for the optional deployment stage |
| **Git** | All stages | You should already have this since this is a git-less local repo currently — see Stage 0 for setting up version control properly |

## Learning approach for this file

Don't sit down and "learn Docker" or "learn React" in the abstract. Instead:
when Stage 0 tells you to containerize Neo4j, look up *only* what you need
for that (`docker run` with the right image and port mapping) and move on.
This is the "just-in-time" learning approach, and it's the right one for
tools (as opposed to concepts, which you do need to front-load — that's why
files 1–6 come before you touch code).

## Recommended resources (free, by tool)

- **Neo4j**: https://graphacademy.neo4j.com/ (already listed in file 02)
- **FastAPI official tutorial**: https://fastapi.tiangolo.com/tutorial/ —
  genuinely excellent, do the first few sections directly.
- **LangChain quickstart**: https://python.langchain.com/docs/introduction/
- **Chroma quickstart**: https://docs.trychroma.com/getting-started
- **PyTorch Geometric "Introduction by Example"**: (already listed in file 03)
- **React official "Quick Start"**: https://react.dev/learn
- **Cytoscape.js documentation**: https://js.cytoscape.org/ — if you go this
  route instead of D3 for the fraud investigation graph view.
- **Docker "Get Started" guide**: https://docs.docker.com/get-started/

## Checkpoint

There's no single conceptual checkpoint for this file — instead, before
Stage 0, confirm you can:

- Run `docker --version` and `python --version` successfully in your
  terminal.
- Start a local Neo4j instance (Desktop app or Docker) and open its browser
  UI at `localhost:7474`.
- Confirm you have (or can get) API access to Claude via the Anthropic
  Console.

Once those three are true, you're unblocked for Stage 0.
