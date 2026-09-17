# Phase A — Learning Roadmap

Goal: understand every concept this project touches well enough to (a) make
good design decisions without copying a tutorial blindly, and (b) explain
your project confidently to a reviewer who asks "why did you use a GNN here
instead of just XGBoost?"

This is **not** a general computer science curriculum. Each file below is
scoped tightly to what this specific project needs. Read them in order —
later files assume you know the earlier ones.

| # | Topic | Why you need it | Rough time |
|---|---|---|---|
| 1 | [Fraud & AML Fundamentals](01-fraud-and-aml-fundamentals.md) | You cannot design detection logic for a problem you don't understand operationally | 2–3 days |
| 2 | [Graphs & Knowledge Graphs](02-graphs-and-knowledge-graphs.md) | The core data structure of the whole platform | 3–4 days |
| 3 | [Graph Neural Networks](03-graph-neural-networks.md) | Powers Objective 2 (risk scoring) if you go the GNN route | 5–7 days |
| 4 | [ML for Risk Scoring](04-ml-for-risk-scoring.md) | The simpler, faster path to Objective 2 — and the honest baseline you compare a GNN against | 3–4 days |
| 5 | [LLMs, RAG & Compliance AI](05-llms-rag-and-compliance-ai.md) | Powers Objective 3 (SAR generation) | 4–5 days |
| 6 | [Explainable AI](06-explainable-ai.md) | Every objective needs this — it's not optional polish | 2 days |
| 7 | [Systems & Tech Stack](07-systems-and-tech-stack.md) | The practical tools (Neo4j, FastAPI, Docker, etc.) you'll actually type commands into | ongoing, as-needed |

Total: roughly **3 weeks** if studied focused and part-time (2–3 hrs/day).
You do not need to finish this before touching code — see the pacing table
in the top-level `project-plan/README.md`.

## How to actually learn this (not just skim it)

For each topic:
1. Read the concept explanation in that file first — don't jump to a course
   before you know *why* the topic matters to your project.
2. Do the recommended free resource (course/article/interactive tool).
3. Answer the "Checkpoint" question at the bottom of the file **in your own
   words, out loud or in writing**, without looking at your notes. If you
   can't, you haven't learned it yet — that's fine, just go back.
4. Optional but valuable: explain the concept to someone else (or write a
   one-paragraph summary in your own README). Teaching is the fastest way to
   find the gaps in your understanding.

## A note on scope discipline

It is very easy to fall down a rabbit hole here — GNN theory alone is a full
graduate course if you let it be. Each file tells you explicitly what depth
is "enough for this project" vs. what's a nice-to-have for later curiosity.
When in doubt, prefer *shipping the mini-project* over *mastering the theory*
— you can always go deeper after the deadline.
