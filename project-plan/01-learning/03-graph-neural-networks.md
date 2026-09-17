# 3. Graph Neural Networks (GNNs)

## Why this matters for the project

This is the most academically "novel" part of the project and the reason
your literature survey is full of GNN papers. But it's also the highest-risk,
highest-effort piece — read `04-ml-for-risk-scoring.md` too, and read the
"Scope decision" note below, before committing time here.

## Scope decision — read this first

A real production GNN pipeline (mini-batch neighborhood sampling, held-out
temporal splits, hyperparameter tuning) is a multi-week effort even for
someone experienced. For a mini-project with a 10-week total timeline, you
have two honest options:

1. **Full GNN route**: train an actual GNN (e.g. GraphSAGE or a GAT) on a
   graph-structured fraud dataset. This is what Stage 3 walks through, and
   it's what makes your project match the literature survey you wrote. Budget
   1.5–2 weeks.
2. **Baseline-first route** (recommended if time is tight): build the
   risk-scoring model with LightGBM/XGBoost first (Stage 2 — this alone
   satisfies Objective 2), get the whole pipeline working end-to-end, and
   *only if time remains*, come back and add a GNN as a stretch enhancement
   you compare against the baseline. This order also happens to be exactly
   what a real ML team would do — never start with the fanciest model.

Either way, you need to understand what a GNN *is* and why it's suited to
this problem, even if you end up shipping the LightGBM baseline as your
primary result and describing the GNN as future work.

## Core concepts to learn

- **Why normal neural networks don't work on graphs**: a normal
  feedforward/CNN network assumes fixed-size, ordered input. A transaction
  network has a variable number of neighbors per node, in no natural order —
  understand this mismatch first, it motivates everything else.
- **Message passing**: the core idea of a GNN — each node updates its
  representation by aggregating information from its neighbors, over
  multiple "hops" (layers). Understand this at the level of: "a node's new
  embedding = some function of its own features + an aggregation of its
  neighbors' embeddings."
- **GraphSAGE**: the specific, practical GNN architecture most fraud papers
  use because it generalizes to unseen nodes (important — new accounts show
  up in a live bank every day, unlike a fixed citation-network dataset).
- **Graph Attention Networks (GAT)**: understand at a conceptual level how
  attention lets the model weigh some neighbors more than others (e.g. a
  transaction to a known-flagged account should matter more than one to a
  long-time trusted merchant).
- **Node classification vs. edge/link prediction vs. graph classification**:
  know which one you're doing. Fraud detection here is typically **node
  classification** (is this account/transaction-node fraudulent?) or
  sometimes **edge classification** (is this specific transaction-edge
  fraudulent?).
- **Class imbalance**: fraud is rare (often <1% of transactions). Understand
  why accuracy is a useless metric here, and why you need precision/recall/
  F1/AUPRC instead — this matters as much for the GNN as for the baseline
  model in Stage 2.

## Recommended resources (free)

- **Stanford CS224W (Machine Learning with Graphs) — public lecture videos
  & slides**: https://web.stanford.edu/class/cs224w/ — the gold-standard
  course. You do **not** need the whole course — watch just the lectures on
  "Message Passing and Node Embeddings" and "GNN Architectures
  (GraphSAGE/GAT)." Skip the theory-heavy later lectures unless curious.
- **PyTorch Geometric (PyG) official tutorials**:
  https://pytorch-geometric.readthedocs.io/en/latest/get_started/introduction.html
  — this is the library you'll actually use in Stage 3. Do the "Introduction
  by Example" tutorial hands-on.
- **"A Gentle Introduction to Graph Neural Networks" (distill.pub-style,
  by Google Research)**: https://distill.pub/2021/gnn-intro/ — excellent
  visual, intuition-first explanation. Read this before the Stanford lectures
  if you want the concept before the math.
- **Your own literature survey papers** (already in the deck's References
  slide) — re-read arXiv 2411.05815 (the GNN fraud detection review) now
  that you have the vocabulary to actually understand it, not just cite it.

## Checkpoint

> "Explain message passing to someone who knows regular neural networks but
> has never heard of a GNN. Then explain, for this project specifically, why
> a transaction's fraud risk might depend on its 2-hop neighborhood, not just
> its own features."

If you can do both without notes, you're ready for Stage 3 (or ready to
correctly justify skipping straight to Stage 2's baseline for now).
