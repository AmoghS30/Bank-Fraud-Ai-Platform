# Phase B — Implementation, Stage by Stage

This builds exactly the three objectives committed to in the deck, in an
order that de-risks the project: the riskiest/most novel component (the GNN)
is explicitly optional/stretch, so a working demo exists even if you run out
of time.

| Stage | Deliverable | Maps to objective |
|---|---|---|
| [Stage 0](stage-0-environment-setup.md) | Working dev environment, repo structure, data acquired | Prerequisite for all |
| [Stage 1](stage-1-data-and-knowledge-graph.md) | Populated Neo4j knowledge graph from transaction/KYC/behaviour data | Objective 1 |
| [Stage 2](stage-2-risk-scoring-model.md) | Trained, evaluated, explainable risk-scoring model (LightGBM) | Objective 2 (core) |
| [Stage 3](stage-3-fraud-detection-gnn.md) | GNN model trained on the graph, compared against Stage 2's baseline | Objective 2 (stretch) |
| [Stage 4](stage-4-compliance-assistant-rag.md) | RAG pipeline + Claude generating grounded SAR drafts | Objective 3 |
| [Stage 5](stage-5-dashboard-and-demo.md) | A demoable UI tying it all together | Presentation of all 3 |
| [Stage 6](stage-6-testing-and-validation.md) | Validated results, metrics you can defend in a review | Quality gate |
| [Stage 7](stage-7-deployment-optional.md) | Containerized, deployed (optional, only if time remains) | Stretch |

## Ground rules

1. **Each stage has a "Definition of done."** Don't proceed until you hit it.
   A half-working Stage 1 makes Stage 2 and Stage 4 both harder to debug,
   because you won't know if a bug is new or inherited.
2. **Commit your work as you go.** If this repo isn't a git repo yet, make it
   one in Stage 0 — you want a commit history showing incremental progress,
   both for your own sanity (rollback points) and because reviewers often
   like seeing real development history, not one giant commit.
3. **Keep a running "Design Decisions" log.** Stage 0 sets this up. Every
   time you choose X over Y (e.g. "Chroma instead of Pinecone because..."),
   write one line. This becomes free material for your final review defense
   and your project report.
4. **Synthetic/public data is fine and expected.** You are not getting real
   bank data. Say so plainly in your report — use PaySim, IEEE-CIS, or the
   Kaggle credit card dataset, and construct a synthetic KYC/device layer on
   top where the public dataset doesn't have one (Stage 1 shows how).
5. **Re-use, don't rebuild, the diagrams and deck already made.** The
   `Reports/phase-1/` architecture and flow diagrams describe the target
   design — build toward matching them, and update them if your actual
   implementation diverges (it likely will in small ways, and that's fine —
   keep the docs honest).

## Suggested repo structure to create in Stage 0

```
Bank-Fraud-Ai-Platform/
├── Reports/                    (existing — deck, diagrams)
├── project-plan/               (this folder — learning + implementation plan)
├── data/                       (raw/ and processed/ subfolders, gitignored if large)
├── knowledge_graph/             (Stage 1 — Cypher scripts, graph loading code)
├── risk_model/                  (Stage 2 — training scripts, saved model, SHAP notebooks)
├── gnn_model/                   (Stage 3 — optional, PyG training code)
├── compliance_assistant/         (Stage 4 — RAG pipeline, SAR generation)
├── dashboard/                    (Stage 5 — FastAPI backend + React frontend)
├── tests/                        (Stage 6)
└── docker-compose.yml            (Stage 0/7)
```

Each stage file below tells you exactly what goes in its folder.
