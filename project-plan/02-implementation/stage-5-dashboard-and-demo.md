# Stage 5 — Dashboard & Demo Assembly

## Prerequisites from Phase A

- File 07 (Systems & Tech Stack) — FastAPI and React basics.

## Prerequisites from Phase B

- Stages 1, 2, and 4 all have working, callable components (graph queries,
  risk-scoring inference, SAR generation). Stage 3 optional.

## Goal / deliverable

A single demoable interface that ties the three objectives together into
one coherent story: a transaction comes in → gets a risk score with
explanation → its network is visible in the graph → a SAR can be generated
for it. This is what you'll actually show in your review/demo video.

You do **not** need to build all four dashboard components described in the
original platform pitch (live monitoring, graph visualizer, compliance
copilot, feedback interface) at full production quality. Build one clean,
working flow through a **single-page app** that touches all three
objectives — depth over breadth.

## Tasks

1. **Build a FastAPI backend** exposing endpoints such as:
   - `GET /accounts/{id}` — account details + graph connections (calls
     Stage 1's Neo4j queries)
   - `POST /score` — takes transaction features, returns risk score + SHAP
     explanation (calls Stage 2's inference function)
   - `GET /accounts/{id}/network` — returns the subgraph around an account
     for visualization
   - `POST /generate-sar` — takes a case/account ID, returns the generated
     SAR draft (calls Stage 4's pipeline)

2. **Build a minimal React frontend** with three views/panels:
   - A **transaction list** showing recent transactions with their risk
     scores, color-coded by tier (low/medium/high/critical) — pulls from
     `/score`.
   - A **network graph view** for a selected flagged account — use
     **react-force-graph** or **Cytoscape.js** (much less setup than raw
     D3 for an interactive node-link graph; see file 07's tool notes) —
     pulls from `/accounts/{id}/network`.
   - A **case panel** showing the SHAP explanation for the selected
     transaction and a "Generate SAR" button that calls `/generate-sar` and
     displays the structured draft.

3. **Prepare 2–3 concrete demo scenarios** ahead of time — don't rely on
   live, unpredictable data during your actual review. Walk through the
   money-mule scenario from your deck's End-to-End Flow diagram as one of
   them: show the transaction, its computed risk score, the shared-device
   connection surfacing in the graph view, and the generated SAR draft, in
   that order.

4. **Record a demo video** (per the deck's suggested 3–5 minute structure,
   already outlined in the original markdown source): problem → transaction
   flagged in real time → graph revealing the network → SAR generated →
   summary metrics from Stage 2's/Stage 6's evaluation.

## Definition of done

- [ ] FastAPI backend runs locally and its endpoints are testable
      (e.g. via the auto-generated `/docs` Swagger UI).
- [ ] React frontend runs locally, calls the backend, and displays real
      data (not hardcoded mock data) for at least one full scenario.
- [ ] The network graph view renders and is interactive (click a node,
      see its connections) for at least the synthetic fraud ring you built
      in Stage 1.
- [ ] Clicking "Generate SAR" for a real flagged case produces a real
      Stage 4 output, not a placeholder.
- [ ] 2–3 demo scenarios are scripted and rehearsed before the actual
      review.

## Common pitfalls

- **Trying to build all four original dashboard components at production
  polish.** This is a mini-project demo, not a shipped product — one tight,
  working flow beats four half-finished panels.
- **Relying on live/random data during the actual review.** Prepare specific
  account IDs / scenarios you know produce a good demo, and use those.
- **Skipping the video** if it's part of your deliverable requirements —
  check your course's actual submission requirements for this; the deck
  already outlines a suggested structure from the original project brief.
