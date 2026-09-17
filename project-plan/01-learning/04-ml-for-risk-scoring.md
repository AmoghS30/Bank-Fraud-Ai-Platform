# 4. Machine Learning for Risk Scoring

## Why this matters for the project

This is the **fastest, most reliable path to Objective 2**
("implement an AI-based transaction risk-scoring model"). Even if you
eventually add a GNN, you need a working baseline model first — both as a
safety net (something to demo if the GNN isn't ready in time) and as the
honest comparison point that makes your GNN result meaningful ("the GNN
improved recall by X% over the LightGBM baseline" is a real result; a GNN
with no baseline to compare against is just a number).

## Core concepts to learn

- **Gradient-boosted trees (LightGBM / XGBoost)**: understand at a working
  level how an ensemble of decision trees, trained sequentially to correct
  each other's errors, produces a single risk score. You don't need to
  derive the math — you need to know how to use it well and interpret it.
- **Feature engineering for transactions**: this is where most of your
  actual effort goes. Learn to construct features like:
  - transaction amount vs. the account's historical average/std-dev
  - time-of-day / day-of-week deviation from the account's normal pattern
  - velocity features (number of transactions in the last 1h/24h/7d)
  - is-new-device, is-new-recipient, is-new-country flags
  - graph-derived features once Stage 1 is done (e.g. "number of flagged
    accounts within 2 hops")
- **Class imbalance handling**: fraud datasets are typically 0.1–2% positive
  class. Learn `scale_pos_weight` (LightGBM/XGBoost), SMOTE oversampling, and
  why you should almost always prefer class-weighting over oversampling for
  tabular fraud data (oversampling of rare, information-poor minority
  classes tends to overfit).
- **Evaluation metrics that actually matter here**: Precision, Recall,
  F1, and especially **AUPRC (Area Under Precision-Recall Curve)** — not
  accuracy, and not even AUROC alone, since with severe class imbalance
  AUROC can look great while precision is still terrible. Understand the
  practical trade-off: a bank cares about "how many false positives per
  true fraud caught," which is a precision-at-fixed-recall question.
- **Train/validation/test splitting for time-series-like data**: you must
  split fraud data **by time** (train on earlier transactions, test on
  later ones), never randomly — random splitting leaks future information
  and will make your model look far better than it really is. This is one
  of the most common mistakes in fraud-detection tutorials online; don't
  copy that mistake.
- **Model explainability tool: SHAP**: learn to produce a SHAP explanation
  for an individual prediction ("this transaction was flagged because of
  device novelty [+0.31], amount deviation [+0.22], time-of-day [+0.09]").
  This directly feeds Stage 4's explainability requirement and the
  Explainable AI concept file.

## Recommended resources (free)

- **Kaggle "Credit Card Fraud Detection" dataset + top kernels**:
  https://www.kaggle.com/mlg-ulb/creditcardfraud — the classic small,
  clean, heavily-imbalanced dataset. Good for your first working model.
- **Kaggle "IEEE-CIS Fraud Detection" dataset**:
  https://www.kaggle.com/c/ieee-fraud-detection/data — larger, messier,
  much closer to real transaction data with device/identity features. Use
  this once your pipeline works on the small dataset.
- **PaySim synthetic mobile-money dataset**:
  https://www.kaggle.com/datasets/ealaxi/paysim1 — simulates
  mobile-money transactions and is designed to resemble real fraud
  patterns (including money-laundering-like behavior). Good fit for this
  project's money-mule scenario.
- **LightGBM official docs — Python Quick Start**:
  https://lightgbm.readthedocs.io/en/latest/Python-Intro.html
- **"Practical Fraud Detection" style guide — Google's own ML crash course
  section on imbalanced data**:
  https://developers.google.com/machine-learning/crash-course/imbalanced-data
  — short, practical, no fluff.
- **SHAP official docs + tutorial notebooks**:
  https://shap.readthedocs.io/en/latest/example_notebooks.html — use the
  "Tree explainer" examples directly (LightGBM/XGBoost compatible).

## Checkpoint

> "You train a fraud model on a dataset that's 99.5% legitimate transactions
> and get 99.5% accuracy. Explain why that number is meaningless, what
> metric you'd report instead, and how you'd split the data to avoid leaking
> future information into training."

If you can answer all three parts cleanly, move on.
