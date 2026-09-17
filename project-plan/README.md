# Project Plan — AI-Powered Banking Fraud & Compliance Intelligence Platform

This folder is the working plan for taking this project from "I don't know this
domain yet" to a working, demoable mini-project. It is split into two phases:

```
project-plan/
├── README.md                      ← you are here (roadmap + how to use this)
├── 01-learning/                   ← Phase A: understand every concept from scratch
│   ├── README.md
│   ├── 01-fraud-and-aml-fundamentals.md
│   ├── 02-graphs-and-knowledge-graphs.md
│   ├── 03-graph-neural-networks.md
│   ├── 04-ml-for-risk-scoring.md
│   ├── 05-llms-rag-and-compliance-ai.md
│   ├── 06-explainable-ai.md
│   └── 07-systems-and-tech-stack.md
└── 02-implementation/              ← Phase B: build it, stage by stage
    ├── README.md
    ├── stage-0-environment-setup.md
    ├── stage-1-data-and-knowledge-graph.md
    ├── stage-2-risk-scoring-model.md
    ├── stage-3-fraud-detection-gnn.md
    ├── stage-4-compliance-assistant-rag.md
    ├── stage-5-dashboard-and-demo.md
    ├── stage-6-testing-and-validation.md
    └── stage-7-deployment-optional.md
```

## Why two phases, not one

The deck (`Reports/phase-1/banking_fraud_ai_platform_presentation.pptx`) already
committed to **3 core objectives** for grading purposes:

1. Build a unified knowledge graph linking transaction, KYC and behavioural data.
2. Implement an AI-based transaction risk-scoring model (GNN/anomaly-detection driven).
3. Automate SAR draft generation from flagged cases using a RAG-grounded LLM.

Everything in `02-implementation/` is built around actually delivering those
three things — not the full six-agent vision from the platform pitch. The
fuller vision (AML network agent, customer profiler, investigation-graph UI)
is marked **optional / stretch** in the relevant stages, so you can extend the
project after the core is working if time allows.

You cannot build any of this well without first understanding, at a working
level:
- What fraud and money laundering actually look like operationally (not just
  the definitions — the *patterns*).
- What a graph database is and why fraud rings are easier to see in graph form
  than in tables.
- How a Graph Neural Network differs from a normal classifier, and why it's
  the right tool here.
- What RAG is, and why "just ask an LLM" is not enough for a regulatory
  document task.
- What "explainable AI" concretely requires from your pipeline (not just a
  slogan).

`01-learning/` is scoped to *exactly* the concepts you need for this project —
not a general ML/graph theory degree. Each file tells you what to learn, why
it matters here, where to learn it for free, and a checkpoint question to
confirm you actually understood it before moving on.

## Suggested pacing

| Week | Focus |
|---|---|
| 1 | `01-learning`: fundamentals (fraud/AML) + graphs/knowledge graphs |
| 2 | `01-learning`: GNNs + ML for risk scoring, **in parallel** start `stage-0` (env setup) |
| 3 | `01-learning`: RAG/LLMs + explainable AI + tech stack basics; start `stage-1` (data + graph) |
| 4–5 | `stage-2`: risk-scoring model |
| 6–7 | `stage-3`: GNN fraud detection (or skip to stretch if time-constrained — see stage file) |
| 8 | `stage-4`: compliance assistant (RAG + SAR generation) |
| 9 | `stage-5`: dashboard + demo assembly |
| 10 | `stage-6`: testing, validation, and demo rehearsal |

This roughly matches the "Project Execution Plan — Timeline" slide already in
the deck (10 weeks), but gives you weeks 1–3 of *overlapping* learning +
early setup instead of assuming you already know the material.

## How to use these files

- Work top to bottom within `01-learning/`, but don't block implementation on
  finishing 100% of the learning — the pacing table above interleaves them
  deliberately. You learn graph theory *while* your Neo4j instance is
  ingesting data; you don't need to finish a GNN course before writing your
  first Cypher query.
- Each implementation stage file lists its own prerequisites from
  `01-learning/` at the top — check those before starting that stage.
- Treat every "Definition of done" section as a hard checkpoint. Don't move
  to the next stage until you can tick every box — a project like this fails
  quietly (a model that "sort of works," a graph with wrong relationships)
  if you skip verification.
- Update these files as you go. This is a working plan, not a document to
  follow blindly — if you discover a step is wrong-sized (too big, too small,
  wrong order), edit the file. Treat it the way you'd treat a living design
  doc, not a syllabus handed down from someone else.
