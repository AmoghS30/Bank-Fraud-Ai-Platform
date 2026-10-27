"""
Stage 2 — Inference Interface
score_transaction(features) → {"risk_score": float, "top_features": [...]}

Called by:
  - /risk-score skill (CLI testing)
  - Stage 5 FastAPI backend (POST /score endpoint)

Model is loaded once and cached on first call.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import joblib
import numpy as np
import pandas as pd
import shap

from features import CATEGORICAL_COLS, FEATURE_COLS

_model = None
_explainer = None
_SAVED_DIR = os.path.join(os.path.dirname(__file__), "saved")


def _load():
    global _model, _explainer
    if _model is None:
        model_path = os.path.join(_SAVED_DIR, "model.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                "Model not found. Run `python3 risk_model/train.py` first."
            )
        _model = joblib.load(model_path)
        _explainer = shap.TreeExplainer(_model)


def score_transaction(features: dict) -> dict:
    """
    Score a single transaction.

    Args:
        features: dict with any subset of FEATURE_COLS. Missing keys default to 0.

    Returns:
        {
          "risk_score": float (0–1),
          "risk_tier": str ("low" | "medium" | "high" | "critical"),
          "top_features": [{"feature": str, "shap_value": float, "direction": str}, ...]
        }
    """
    _load()

    row = {col: features.get(col, 0) for col in FEATURE_COLS}
    X = pd.DataFrame([row])

    for col in CATEGORICAL_COLS:
        X.loc[:, col] = X[col].astype("category")

    risk_score = float(_model.predict_proba(X)[0, 1])

    sv = _explainer.shap_values(X)
    if isinstance(sv, list):
        sv = sv[1]
    shap_vec = sv[0]

    top_idx = np.argsort(np.abs(shap_vec))[::-1][:5]
    top_features = [
        {
            "feature": FEATURE_COLS[i],
            "shap_value": float(shap_vec[i]),
            "direction": "increases_risk" if shap_vec[i] > 0 else "decreases_risk",
        }
        for i in top_idx
    ]

    if risk_score < 0.4:
        tier = "low"
    elif risk_score < 0.7:
        tier = "medium"
    elif risk_score < 0.9:
        tier = "high"
    else:
        tier = "critical"

    return {"risk_score": risk_score, "risk_tier": tier, "top_features": top_features}


if __name__ == "__main__":
    # Quick smoke test with dummy features
    result = score_transaction(
        {
            "TransactionAmt": 500.0,
            "amt_zscore": 3.2,
            "amt_to_mean_ratio": 4.1,
            "account_tx_count": 5,
            "tx_hour": 3,
            "tx_day_of_week": 6,
            "velocity_1h": 2,
            "velocity_24h": 5,
            "velocity_7d": 8,
            "amt_velocity_24h": 1200.0,
            "addr1": 299,
            "fraud_neighbors": 2,
            "shared_device_accounts": 5,
            "device_known": 1,
            "is_new_device": 1,
            "is_new_p_email": 0,
            "is_new_r_email": 1,
            "ProductCD": "W",
            "card_network": "visa",
            "card_type": "credit",
            "device_type": "mobile",
            "p_email_domain": "gmail.com",
            "r_email_domain": "anonymous.com",
        }
    )
    print(f"Risk score: {result['risk_score']:.4f}  [{result['risk_tier']}]")
    print("Top features:")
    for f in result["top_features"]:
        print(f"  {f['feature']:35s}  SHAP={f['shap_value']:+.4f}  ({f['direction']})")
