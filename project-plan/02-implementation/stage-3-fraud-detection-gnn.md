# Stage 3 — GNN Fraud Detection (Stretch / Optional)

## Prerequisites from Phase A

- File 03 (Graph Neural Networks) — full checkpoint passed.
- Stage 2 completed and evaluated first — **do not start this stage before
  Stage 2 has a working, evaluated baseline.** This stage's entire value is
  in comparing against that baseline.

## Should you do this stage at all?

Re-read the "Scope decision" section in `01-learning/03-graph-neural-networks.md`.
Only proceed here if:
- Stage 1 and Stage 2 are fully done and evaluated, **and**
- You have at least 1.5–2 weeks of runway left before your deadline.

If not, skip this stage and instead write a short "Future Work" section in
your report describing what a GNN extension would look like — citing your
own literature survey papers as the basis. That is a completely legitimate,
honest outcome and is explicitly anticipated by how Objective 2 was worded
("GNN/anomaly-detection driven" — the "/" is doing real work there).

## Goal / deliverable (if you proceed)

A GraphSAGE (or GAT) model trained on the Neo4j graph from Stage 1,
performing node or edge classification for fraud, with a clear, honest
comparison against Stage 2's LightGBM baseline on the same evaluation
metrics.

## Tasks

1. **Export the graph from Neo4j into PyTorch Geometric format.** Use
   `neo4j`'s Python driver to pull nodes/edges, or use the
   `Neo4j Graph Data Science (GDS)` library's export utilities. Construct a
   PyG `Data` object: node feature matrix `x`, edge index, and labels `y`
   (fraud / not fraud) for the nodes or edges you're classifying.
2. **Decide node vs. edge classification.** For this project, node
   classification on `Account` nodes (is this account associated with fraud)
   is usually simpler to set up and evaluate than edge classification on
   `Transaction` edges — start there unless your data strongly suggests
   otherwise.
3. **Build a GraphSAGE model** using PyG's `SAGEConv` layers (2–3 layers is
   typically enough — more layers cause over-smoothing, a known GNN
   failure mode worth knowing about and mentioning if asked).
4. **Train with the same time-based split logic as Stage 2** — don't let
   test-set nodes' information leak into training via graph connections
   that span the split boundary; this is a graph-specific version of the
   same leakage mistake from Stage 2, and it's subtler here because edges
   can connect a "past" node to a "future" node.
5. **Handle class imbalance** — same problem as Stage 2, solved similarly
   (weighted loss function, e.g. weighted binary cross-entropy).
6. **Evaluate with the same metrics as Stage 2** (Precision/Recall/F1/AUPRC)
   on the same conceptual test set, so the comparison is apples-to-apples.
7. **Write the comparison.** One paragraph, with numbers: did the GNN
   improve recall/precision over the LightGBM baseline? By how much? Is the
   added complexity (training time, infra, harder to explain) worth it for
   that gain? An honest "the GNN didn't clearly beat the baseline on this
   dataset, but here's why we'd still expect it to matter at bank scale with
   denser fraud rings" is a **better, more credible** result than a
   suspiciously perfect improvement — reviewers trust honest negative/mixed
   results from a mini-project far more than implausibly clean wins.

## Definition of done

- [ ] Graph data successfully exported from Neo4j into PyG format.
- [ ] A GraphSAGE (or GAT) model trains without errors and converges (loss
      decreases over epochs — plot it).
- [ ] Evaluation metrics computed on a properly time-respecting split.
- [ ] A written, numeric comparison against the Stage 2 baseline exists.
- [ ] You can explain, in your own words, one concrete case where the GNN's
      graph context caught something the tabular baseline's row-level
      features couldn't (or, honestly, why it didn't on this dataset).

## Common pitfalls

- **Starting this stage before Stage 2 is solid.** You'll have no baseline
  to compare against and won't know if a bad result is the GNN or your
  pipeline.
- **Graph data leakage across the time split** — the subtler, graph-specific
  version of Stage 2's split mistake. Be deliberate about it.
- **Over-engineering the architecture** (5+ GNN layers, complex attention
  variants) before confirming a simple 2-layer GraphSAGE even runs
  end-to-end. Get the simple version working first.
