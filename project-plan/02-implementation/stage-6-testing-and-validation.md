# Stage 6 — Testing & Validation

## Prerequisites

- Stages 1, 2, 4, and 5 functionally complete.

## Goal / deliverable

Confidence — backed by evidence you can show a reviewer — that each
component actually does what you claim in the deck, plus a written summary
of results and honest limitations for your final report.

This stage is a quality gate, not new feature work. Budget real time for it;
it's where a project's actual grade often gets decided (a working demo with
believable, defensible numbers beats a flashier demo with numbers nobody
checked).

## Tasks

1. **Knowledge graph validation** (Objective 1):
   - Confirm query correctness: re-run the Cypher queries from Stage 1
     against a couple of manually-traced examples and verify the results
     match what you'd expect by inspecting the raw data directly.
   - Confirm the synthetic fraud ring(s) you built are actually findable
     via a 2–3 hop query, end to end.

2. **Risk-scoring model validation** (Objective 2):
   - Re-confirm the time-based split was respected (no leakage) — check
     the actual date ranges in train vs. test.
   - Sanity-check a handful of individual predictions manually: pick 3–5
     transactions the model scored high, and 3–5 it scored low, and confirm
     the SHAP explanations make intuitive sense given the raw feature
     values (not just that the code ran without error).
   - If you built Stage 3's GNN, confirm the comparison table numbers were
     computed on the exact same test set as the baseline.

3. **Compliance assistant validation** (Objective 3):
   - For at least 5 generated SAR drafts, manually verify every citation
     against the actual source document text. Log any hallucinated or
     mismatched citations you find — and either fix the prompt/retrieval to
     address the failure mode, or honestly report the failure rate you
     observed (a mini-project that reports "3 of 15 generated citations
     needed correction, and here's why" demonstrates far more rigor than
     one that simply doesn't check).
   - Test the Q&A feature with a couple of adversarial-ish questions (e.g.
     asking about something not in your document corpus) and confirm it
     says it doesn't know, rather than fabricating an answer — this is a
     real, checkable RAG-quality signal.

4. **End-to-end dashboard test**: run through your prepared demo scenarios
   (from Stage 5) start to finish, on a clean environment restart, to
   confirm nothing depends on leftover state from earlier debugging.

5. **Write up results.** Produce (or update) a results document containing:
   - Risk-scoring model metrics (Precision/Recall/F1/AUPRC) with the actual
     numbers, not placeholders.
   - The GNN-vs-baseline comparison, if Stage 3 was done.
   - Compliance assistant citation-accuracy spot-check results.
   - Known limitations, stated plainly (synthetic data, small document
     corpus, no real bank-scale validation) — this is expected and
     valued in a mini-project; concealing limitations reads worse in a
     review than acknowledging them with a plan for how you'd address them
     at scale.

## Definition of done

- [ ] Knowledge graph queries verified against manually-traced ground truth.
- [ ] Risk model metrics reported on a leakage-free split, with at least
      5 manually-inspected individual predictions confirmed sensible.
- [ ] Compliance assistant citations spot-checked on ≥5 generated drafts,
      with results (including any failures found) documented.
- [ ] Demo scenarios run cleanly end-to-end from a fresh environment start.
- [ ] A results/limitations write-up exists and is ready to fold into your
      final report and review talking points.

## Common pitfalls

- **Treating "the code ran without an error" as validation.** It isn't —
  every check above requires you to look at actual outputs and judge them
  against what you know to be true, not just confirm the absence of a
  stack trace.
- **Skipping this stage under time pressure to add more features instead.**
  Resist this — an extra half-built feature helps you less in a review than
  being able to confidently defend the numbers and behavior of what you
  already built.
