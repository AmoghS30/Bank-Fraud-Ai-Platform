# Stage 2 — Risk-Scoring Model (Core Objective 2)

## Prerequisites from Phase A

- File 04 (ML for Risk Scoring) — this stage is that file's checkpoint,
  applied for real.
- File 06 (Explainable AI) — for the SHAP explanation task.

## Goal / deliverable

**Objective 2, core version satisfied**: a trained LightGBM model that
assigns a real-time risk score to a transaction, evaluated with metrics that
actually mean something for imbalanced fraud data, with SHAP-based
explanations for individual predictions.

This is the single most important stage to get right — it's your primary,
guaranteed-working deliverable for Objective 2, independent of whether
Stage 3's GNN pans out.

## Tasks

1. **Feature engineering.** Using the transaction data from Stage 1 (and,
   once available, simple graph-derived features from Neo4j), build:
   - Amount vs. account's historical mean/std (z-score-style deviation)
   - Time-of-day / day-of-week deviation from the account's typical pattern
   - Velocity: transaction count in the trailing 1h / 24h / 7d windows
   - Novelty flags: new device, new recipient, new country/region
   - Graph-derived (query Neo4j directly, or precompute and join): number of
     flagged accounts within 2 hops, shared-device count
2. **Time-based train/test split.** Sort by timestamp, train on the earlier
   ~70–80%, test on the later ~20–30%. Do **not** use a random split — see
   file 04's checkpoint on why.
3. **Handle class imbalance** with `scale_pos_weight` in LightGBM (ratio of
   negative to positive class counts), rather than oversampling, as a first
   approach.
4. **Train the LightGBM classifier.** Start with reasonable defaults, then
   do a small hyperparameter search (number of leaves, learning rate, number
   of estimators) — don't over-invest in tuning before you know the feature
   set is solid.
5. **Evaluate properly**: report Precision, Recall, F1, and AUPRC on the
   time-based test set. Plot the precision-recall curve. Pick and justify an
   operating threshold (e.g. "at this threshold, we catch 85% of fraud at a
   15% false-positive rate among flagged transactions" — a concrete,
   defensible number for your report, in the same spirit as the
   "90–95% reduction" claim in your deck, but one you've actually measured).
6. **Add SHAP explanations.** Use `shap.TreeExplainer` on the trained model;
   produce a force plot or waterfall plot for a handful of individual
   flagged transactions, showing which features drove the score. This is
   your explainability deliverable for this stage.
7. **Save the model artifact** (`risk_model/model.pkl` or LightGBM's native
   format) and a small inference script that takes a transaction's raw
   features and returns `{risk_score, top_contributing_features}` — this is
   the interface Stage 5's dashboard will call.

## Definition of done

- [ ] A trained LightGBM model exists, saved to disk, loadable without
      re-training.
- [ ] Evaluation report (`risk_model/evaluation.md` or a notebook) shows
      Precision/Recall/F1/AUPRC on a **time-based** test split, with the
      precision-recall curve plotted.
- [ ] You can state your chosen operating threshold and what it trades off,
      in one sentence, from memory.
- [ ] SHAP explanations work for at least 5 individual predictions and are
      saved as plots or notebook output.
- [ ] An inference function/script exists that takes transaction features in
      and returns a risk score + explanation out, callable independent of
      the training code.

## Common pitfalls

- **Random train/test split.** This is the single most common mistake in
  fraud-detection tutorials — it leaks information and inflates your
  reported performance. Time-based split, always, for this kind of data.
- **Reporting accuracy.** If your report or slides mention "99% accuracy,"
  that's a red flag to any reviewer who knows fraud detection — lead with
  precision/recall/AUPRC instead.
- **Tuning hyperparameters before your features are good.** Feature
  engineering has far more impact than hyperparameter tuning here; don't
  reverse that priority.
- **Skipping SHAP because "the deadline is close."** This is graded
  explicitly on explainability per your deck's own claims — don't cut this
  corner.
