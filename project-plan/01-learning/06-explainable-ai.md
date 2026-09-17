# 6. Explainable AI (XAI)

## Why this matters for the project

Your Conclusion slide and Limitations-of-Existing-System slide both argue
that explainability is a core gap in existing solutions and a core strength
of this project. That's only true if you actually implement it — it cannot
be a slide-only claim. Concretely, every one of your three objectives needs
an explainability answer:

1. Knowledge graph → can you show *which* connections (shared phone, shared
   device) led to a risk assessment?
2. Risk-scoring model → can you show *why* a specific transaction got a high
   score (not just the number)?
3. SAR generation → can the draft cite *which* regulation and *which*
   transaction evidence it's based on?

## Core concepts to learn

- **Why "black box" is a real problem, not just an academic complaint**:
  understand the actual stakeholders who need an explanation and what they
  need it *for* — a regulator auditing a decision, a customer disputing a
  frozen account, an analyst deciding whether to override the model. Each
  wants a different level/style of explanation.
- **Global vs. local explainability**: global = "what does this model
  generally weigh across all predictions" (e.g. feature importance overall);
  local = "why did it flag *this* transaction" (e.g. a SHAP explanation for
  one row). You need local explanations for your demo — that's what an
  analyst actually looks at case-by-case.
- **SHAP (SHapley Additive exPlanations)**: the specific technique you'll
  use in Stage 2/3 to explain individual model predictions, based on
  cooperative game theory (each feature's contribution to pushing the
  prediction away from a baseline). You already scoped this in the ML file
  — this file is about the *concept*, that one is about the *application*.
- **Graph-based explanation**: for the knowledge-graph side, "explanation"
  is often just a **visualized subgraph** — showing the analyst the actual
  path of shared identifiers that led to a connection being flagged. This is
  simpler than SHAP and is exactly what your Fraud Investigation Graph
  concept (from the platform pitch) is for, even in a stripped-down demo.
- **Explanation-as-text (for the LLM side)**: for the Compliance Assistant,
  "explainability" means citation — the SAR draft states which transactions
  and which regulatory clauses justify each claim. This overlaps with what
  you learned in the RAG file's "grounding & citation" section.

## Recommended resources (free)

- **"Interpretable Machine Learning" by Christoph Molnar (free online book)**:
  https://christophm.github.io/interpretable-ml-book/ — read the chapters
  on SHAP and on the general local-vs-global distinction. This is the
  standard free reference on the topic; you don't need the whole book.
- **SHAP official docs** (same link as the ML file):
  https://shap.readthedocs.io/en/latest/example_notebooks.html
- **Google's PAIR (People + AI Research) "Explainability" guidebook**:
  https://pair.withgoogle.com/guidebook/ — good for the *stakeholder-needs*
  framing (who needs what kind of explanation), less about the math.
- **Your own literature survey** — re-read the MDPI 18(4):179 paper (XAI +
  federated learning for fraud) and arXiv 2505.10050 (XAI + stacking
  ensembles) now with this vocabulary; they show concrete implementations
  of exactly what you're being asked to build.

## Checkpoint

> "A customer calls to ask why their account was frozen. Describe, in plain
> language they'd understand, what your system would tell them — and where
> in your pipeline that explanation actually comes from (not a hypothetical
> — point to the specific component)."

If you can answer this by pointing at a real part of your design (SHAP
output, a graph path, a cited regulation), move on to the tech stack file.
