"""
Stage 2 — LightGBM Training
Time-split train/test, handles class imbalance, evaluates with AUPRC,
saves model + SHAP summary plot + evaluation report.

Run: python3 risk_model/train.py
"""

import os
import sys

# Allow running from repo root
sys.path.insert(0, os.path.dirname(__file__))

import joblib
import lightgbm as lgb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    precision_recall_curve,
    roc_auc_score,
)

from features import CATEGORICAL_COLS, FEATURE_COLS, build_features

PLOTS_DIR = "risk_model/plots"
SAVED_DIR = "risk_model/saved"
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(SAVED_DIR, exist_ok=True)


def time_split(df: pd.DataFrame, train_ratio: float = 0.8):
    """Sort by TransactionDT; train on earliest fraction, test on latest."""
    df = df.sort_values("TransactionDT").reset_index(drop=True)
    cut = int(len(df) * train_ratio)
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def train():
    print("=== Stage 2 — LightGBM Risk Scoring ===\n")

    print("Building features...")
    df = build_features()
    print(f"  {len(df):,} rows | fraud rate: {df['isFraud'].mean():.2%}\n")

    train_df, test_df = time_split(df)
    print(f"Train: {len(train_df):,} rows ({train_df['isFraud'].mean():.2%} fraud)")
    print(f"Test:  {len(test_df):,} rows  ({test_df['isFraud'].mean():.2%} fraud)\n")

    X_train = train_df[FEATURE_COLS].copy()
    y_train = train_df["isFraud"].astype(int)
    X_test = test_df[FEATURE_COLS].copy()
    y_test = test_df["isFraud"].astype(int)

    for col in CATEGORICAL_COLS:
        X_train.loc[:, col] = X_train[col].astype("category")
        X_test.loc[:, col] = X_test[col].astype("category")

    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
    scale_pos_weight = neg / pos
    print(f"Class imbalance: {neg:,} legit / {pos:,} fraud → scale_pos_weight={scale_pos_weight:.1f}\n")

    model = lgb.LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=63,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    print("Training LightGBM (early stopping on AUC, 50 rounds patience)...")
    model.fit(
        X_train, y_train,
        eval_X=X_test,
        eval_y=y_test,
        eval_metric="auc",
        callbacks=[
            lgb.early_stopping(stopping_rounds=50, first_metric_only=True, verbose=False),
            lgb.log_evaluation(period=100),
        ],
    )
    print(f"  Best iteration: {model.best_iteration_}\n")

    # --- Evaluation ---
    y_prob = model.predict_proba(X_test)[:, 1]
    auprc = average_precision_score(y_test, y_prob)
    roc_auc = roc_auc_score(y_test, y_prob)

    print("=== Evaluation ===")
    print(f"  AUPRC:   {auprc:.4f}  (primary metric — precision-recall AUC)")
    print(f"  ROC-AUC: {roc_auc:.4f}\n")

    report_lines = [
        "Stage 2 — LightGBM Evaluation Report",
        "=" * 40,
        f"Dataset:  {len(df):,} transactions | {df['isFraud'].mean():.2%} fraud rate",
        f"Split:    80% train ({len(train_df):,}) / 20% test ({len(test_df):,}) — time-based",
        f"AUPRC:    {auprc:.4f}",
        f"ROC-AUC:  {roc_auc:.4f}",
        "",
    ]

    # Find threshold that maximises F1 on test set
    prec_arr, rec_arr, thresh_arr = precision_recall_curve(y_test, y_prob)
    f1_arr = 2 * prec_arr * rec_arr / (prec_arr + rec_arr + 1e-9)
    best_thresh = float(thresh_arr[np.argmax(f1_arr[:-1])])
    print(f"  Best F1 threshold (auto): {best_thresh:.4f}\n")
    report_lines.append(f"Best F1 threshold (auto-selected): {best_thresh:.4f}\n")

    for threshold in [best_thresh, 0.5]:
        y_pred = (y_prob >= threshold).astype(int)
        report = classification_report(y_test, y_pred, target_names=["legit", "fraud"])
        flag_rate = y_pred.mean()
        header = f"Threshold {threshold:.4f} (flags {flag_rate:.1%} of transactions)"
        print(header)
        print(report)
        report_lines += [header, report]

    with open(f"{SAVED_DIR}/eval_report.txt", "w") as f:
        f.write("\n".join(report_lines))
    print(f"Saved eval report → {SAVED_DIR}/eval_report.txt")

    # --- Precision-recall curve ---
    prec, rec, _ = precision_recall_curve(y_test, y_prob)
    plt.figure(figsize=(8, 5))
    plt.plot(rec, prec, lw=2, color="steelblue")
    plt.fill_between(rec, prec, alpha=0.15, color="steelblue")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision-Recall Curve  (AUPRC = {auprc:.4f})")
    plt.grid(True, alpha=0.4)
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/precision_recall_curve.png", dpi=150)
    plt.close()
    print(f"Saved PR curve → {PLOTS_DIR}/precision_recall_curve.png")

    # --- Score distribution ---
    plt.figure(figsize=(9, 4))
    plt.hist(y_prob[y_test == 0], bins=80, alpha=0.6, label="Legit", color="steelblue", density=True)
    plt.hist(y_prob[y_test == 1], bins=80, alpha=0.6, label="Fraud", color="crimson", density=True)
    plt.xlabel("Risk Score")
    plt.ylabel("Density")
    plt.title("Risk Score Distribution by Class")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/score_distribution.png", dpi=150)
    plt.close()
    print(f"Saved score distribution → {PLOTS_DIR}/score_distribution.png")

    # --- Save model and test predictions ---
    joblib.dump(model, f"{SAVED_DIR}/model.pkl")
    print(f"Saved model → {SAVED_DIR}/model.pkl")

    test_df = test_df.copy()
    test_df["risk_score"] = y_prob
    test_df[["TransactionID", "isFraud", "risk_score", "account_id"]].to_csv(
        f"{SAVED_DIR}/test_predictions.csv", index=False
    )
    print(f"Saved test predictions → {SAVED_DIR}/test_predictions.csv")

    # --- SHAP summary ---
    print("\nComputing SHAP values (1,000-row sample)...")
    sample_idx = X_test.sample(n=min(1000, len(X_test)), random_state=42).index
    X_sample = X_test.loc[sample_idx]
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_sample)
    if isinstance(sv, list):
        sv = sv[1]

    plt.figure()
    shap.summary_plot(sv, X_sample, show=False, max_display=15)
    plt.title("SHAP Feature Importance (fraud class)")
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/shap_summary.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved SHAP summary → {PLOTS_DIR}/shap_summary.png")

    # Save SHAP values for explain.py
    np.save(f"{SAVED_DIR}/shap_sample_values.npy", sv)
    X_sample.reset_index(drop=True).to_pickle(f"{SAVED_DIR}/shap_sample_features.pkl")
    print(f"Saved SHAP sample → {SAVED_DIR}/shap_sample_*.npy/.pkl")

    print("\n=== Stage 2 training complete ===")
    return model


if __name__ == "__main__":
    train()
