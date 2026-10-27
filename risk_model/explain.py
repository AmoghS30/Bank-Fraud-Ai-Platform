"""
Stage 2 — SHAP Waterfall Explanations
Generates per-transaction waterfall plots for the top fraud predictions and
a sample of low-risk transactions, so every flagged case is explainable.

Requires: risk_model/saved/model.pkl and risk_model/saved/test_predictions.csv
Run after train.py: python3 risk_model/explain.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from features import CATEGORICAL_COLS, FEATURE_COLS, build_features

WATERFALL_DIR = "risk_model/plots/waterfall"
SAVED_DIR = "risk_model/saved"
os.makedirs(WATERFALL_DIR, exist_ok=True)


def explain_predictions(n_fraud: int = 5, n_legit: int = 2):
    model = joblib.load(f"{SAVED_DIR}/model.pkl")
    preds = pd.read_csv(f"{SAVED_DIR}/test_predictions.csv")
    explainer = shap.TreeExplainer(model)

    print("Rebuilding test features (needed for waterfall plots)...")
    df = build_features()
    df = df.sort_values("TransactionDT").reset_index(drop=True)
    test_df = df.iloc[int(len(df) * 0.8) :].copy()

    X_test = test_df[FEATURE_COLS].copy()
    for col in CATEGORICAL_COLS:
        X_test[col] = X_test[col].astype("category")

    # Pick top fraud hits and low-risk legit transactions
    top_fraud = preds[preds["isFraud"] == 1].nlargest(n_fraud, "risk_score")
    top_legit = preds[preds["isFraud"] == 0].nsmallest(n_legit, "risk_score")
    cases = pd.concat([top_fraud, top_legit])

    saved = []
    for _, row in cases.iterrows():
        tx_id = int(row["TransactionID"])
        is_fraud = int(row["isFraud"])
        score = float(row["risk_score"])

        mask = test_df["TransactionID"] == tx_id
        if not mask.any():
            print(f"  TX {tx_id} not found in test set — skipping")
            continue

        feat_row = X_test[mask]
        sv = explainer(feat_row)

        fig, ax = plt.subplots(figsize=(11, 6))
        shap.plots.waterfall(sv[0], max_display=10, show=False)
        label = "FRAUD" if is_fraud else "LEGIT"
        plt.title(f"TX {tx_id}  |  {label}  |  Risk score: {score:.3f}", fontsize=12)
        plt.tight_layout()
        out = f"{WATERFALL_DIR}/tx_{tx_id}_{label.lower()}.png"
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved {out}")
        saved.append(out)

    print(f"\nGenerated {len(saved)} waterfall plots → {WATERFALL_DIR}/")


def explain_one(transaction_id: int) -> str:
    """Generate and save a waterfall plot for a single transaction by ID. Returns file path."""
    model = joblib.load(f"{SAVED_DIR}/model.pkl")
    explainer = shap.TreeExplainer(model)
    preds = pd.read_csv(f"{SAVED_DIR}/test_predictions.csv")

    row = preds[preds["TransactionID"] == transaction_id]
    if row.empty:
        raise ValueError(f"TransactionID {transaction_id} not found in test predictions")

    df = build_features()
    df = df.sort_values("TransactionDT").reset_index(drop=True)
    test_df = df.iloc[int(len(df) * 0.8) :]
    X_test = test_df[FEATURE_COLS].copy()
    for col in CATEGORICAL_COLS:
        X_test[col] = X_test[col].astype("category")

    mask = test_df["TransactionID"] == transaction_id
    feat_row = X_test[mask]
    sv = explainer(feat_row)
    score = float(row["risk_score"].values[0])
    is_fraud = int(row["isFraud"].values[0])
    label = "FRAUD" if is_fraud else "LEGIT"

    shap.plots.waterfall(sv[0], max_display=10, show=False)
    plt.title(f"TX {transaction_id}  |  {label}  |  Score: {score:.3f}")
    plt.tight_layout()
    out = f"{WATERFALL_DIR}/tx_{transaction_id}_{label.lower()}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    return out


if __name__ == "__main__":
    explain_predictions()
