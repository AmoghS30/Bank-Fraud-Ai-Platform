"""
Risk model test suite.
Tests 1-4 as specified. Run from repo root with:
    OMP_NUM_THREADS=1 python3 tests/run_risk_model_tests.py
"""

import os
import sys
import traceback

import pandas as pd
import numpy as np

# Ensure repo root is on path so risk_model imports work
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from risk_model.features import build_features, FEATURE_COLS, CATEGORICAL_COLS
from risk_model.score import score_transaction

SEPARATOR = "=" * 70

# ---------------------------------------------------------------------------
# TEST 1  Training-data rows
# ---------------------------------------------------------------------------

def test1_training_data():
    print(SEPARATOR)
    print("TEST 1: Training-data rows — rebuild features from raw data, compare to saved risk_score")
    print(SEPARATOR)

    preds = pd.read_csv(os.path.join(REPO_ROOT, "risk_model/saved/test_predictions.csv"))
    # 3 fraud, 2 legit
    fraud_rows  = preds[preds["isFraud"] == 1].head(3)
    legit_rows  = preds[preds["isFraud"] == 0].head(2)
    sample      = pd.concat([fraud_rows, legit_rows]).reset_index(drop=True)

    print(f"Sample rows selected (TransactionID, isFraud, saved_risk_score, account_id):")
    print(sample.to_string())
    print()

    # Load full processed CSV and rebuild features for those 5 accounts only
    raw = pd.read_csv(os.path.join(REPO_ROOT, "data/processed/transactions.csv"))

    # Keep only rows whose account_id appears in our sample (need full history for velocity/zscore)
    account_ids = sample["account_id"].tolist()
    subset      = raw[raw["account_id"].isin(account_ids)].copy()

    print(f"  Rows in subset (all txs for those 5 accounts): {len(subset)}")
    print("  Calling build_features(include_graph=True) ...")
    feat_df = build_features(df=subset, include_graph=True)

    # Filter to only the 5 target TransactionIDs
    target_ids  = sample["TransactionID"].tolist()
    feat_sample = feat_df[feat_df["TransactionID"].isin(target_ids)].copy()

    if len(feat_sample) == 0:
        print("  ERROR: No matching rows found after build_features — check TransactionID column")
        return

    print(f"\n{'TransactionID':<14}  {'isFraud':>8}  {'saved_score':>12}  {'live_score':>12}  {'abs_error':>10}")
    print("-" * 65)

    for _, pred_row in sample.iterrows():
        tid = pred_row["TransactionID"]
        saved_score = pred_row["risk_score"]
        is_fraud    = pred_row["isFraud"]

        matching = feat_sample[feat_sample["TransactionID"] == tid]
        if matching.empty:
            print(f"{tid:<14}  {is_fraud:>8}  {saved_score:>12.6f}  {'NOT FOUND':>12}  {'N/A':>10}")
            continue

        feat_row  = matching.iloc[0]
        feat_dict = {col: feat_row[col] for col in FEATURE_COLS if col in feat_row}
        try:
            result     = score_transaction(feat_dict)
            live_score = result["risk_score"]
            abs_err    = abs(live_score - saved_score)
            print(f"{tid:<14}  {is_fraud:>8}  {saved_score:>12.6f}  {live_score:>12.6f}  {abs_err:>10.6f}")
        except Exception as e:
            print(f"{tid:<14}  {is_fraud:>8}  {saved_score:>12.6f}  ERROR: {e}")
            traceback.print_exc()


# ---------------------------------------------------------------------------
# TEST 2  Synthetic feature dicts
# ---------------------------------------------------------------------------

def test2_synthetic_features():
    print()
    print(SEPARATOR)
    print("TEST 2: Synthetic feature dicts — clearly fraudulent / legit / edge-case")
    print(SEPARATOR)

    cases = [
        {
            "label": "Clearly FRAUDULENT",
            "features": {
                "TransactionAmt": 9800.0,
                "amt_zscore":          8.5,   # 8.5 std devs above mean — huge outlier
                "amt_to_mean_ratio":  15.0,   # 15× normal spend
                "account_tx_count":    3,
                "tx_hour":             3,     # 3 am
                "tx_day_of_week":      6,     # Sunday
                "velocity_1h":        12,     # 12 txs in last hour — smurfing
                "velocity_24h":       45,
                "velocity_7d":       120,
                "amt_velocity_24h": 85000.0,
                "addr1":             -1,      # unknown address
                "fraud_neighbors":    4,      # 4 flagged neighbours in graph
                "shared_device_accounts": 7,
                "device_known":        0,
                "is_new_device":       1,
                "is_new_p_email":      1,
                "is_new_r_email":      1,
                "ProductCD":         "H",
                "card_network":      "visa",
                "card_type":         "credit",
                "device_type":       "mobile",
                "p_email_domain":    "anonymous.com",
                "r_email_domain":    "anonymous.com",
            },
        },
        {
            "label": "Clearly LEGITIMATE",
            "features": {
                "TransactionAmt":   52.0,
                "amt_zscore":        0.1,    # right on the mean
                "amt_to_mean_ratio": 1.02,
                "account_tx_count": 320,     # long-established account
                "tx_hour":          14,      # 2 pm
                "tx_day_of_week":    2,      # Wednesday
                "velocity_1h":       0,
                "velocity_24h":      1,
                "velocity_7d":       5,
                "amt_velocity_24h":  52.0,
                "addr1":            299,
                "fraud_neighbors":   0,
                "shared_device_accounts": 0,
                "device_known":      1,
                "is_new_device":     0,
                "is_new_p_email":    0,
                "is_new_r_email":    0,
                "ProductCD":        "W",
                "card_network":     "visa",
                "card_type":        "debit",
                "device_type":      "desktop",
                "p_email_domain":   "gmail.com",
                "r_email_domain":   "gmail.com",
            },
        },
        {
            "label": "EDGE CASE (moderate risk signals, ambiguous)",
            "features": {
                "TransactionAmt":  450.0,
                "amt_zscore":        2.1,   # elevated but not extreme
                "amt_to_mean_ratio": 3.2,
                "account_tx_count":  18,
                "tx_hour":           22,    # late evening
                "tx_day_of_week":    4,
                "velocity_1h":        1,
                "velocity_24h":       3,
                "velocity_7d":        9,
                "amt_velocity_24h": 900.0,
                "addr1":            150,
                "fraud_neighbors":    1,   # one flagged neighbour
                "shared_device_accounts": 2,
                "device_known":       1,
                "is_new_device":      1,   # new device, but account looks established
                "is_new_p_email":     0,
                "is_new_r_email":     1,
                "ProductCD":         "C",
                "card_network":      "mastercard",
                "card_type":         "credit",
                "device_type":       "mobile",
                "p_email_domain":    "yahoo.com",
                "r_email_domain":    "protonmail.com",
            },
        },
    ]

    for case in cases:
        label    = case["label"]
        features = case["features"]
        print(f"\n--- {label} ---")
        try:
            result = score_transaction(features)
            score  = result["risk_score"]
            tier   = result["risk_tier"]
            print(f"  risk_score : {score:.4f}   tier: {tier}")
            print(f"  Top SHAP features:")
            for f in result["top_features"]:
                arrow = "▲" if f["direction"] == "increases_risk" else "▼"
                print(f"    {arrow} {f['feature']:<35s}  SHAP={f['shap_value']:+.4f}")
            # Intuition check
            if label.startswith("Clearly FRAUDULENT") and score >= 0.5:
                print("  INTUITION CHECK: PASS (score >= 0.5 for clearly fraudulent case)")
            elif label.startswith("Clearly FRAUDULENT"):
                print(f"  INTUITION CHECK: UNEXPECTED — score {score:.4f} is below 0.5 for fraudulent case")
            elif label.startswith("Clearly LEGITIMATE") and score < 0.4:
                print("  INTUITION CHECK: PASS (score < 0.4 for clearly legitimate case)")
            elif label.startswith("Clearly LEGITIMATE"):
                print(f"  INTUITION CHECK: UNEXPECTED — score {score:.4f} is >= 0.4 for legit case")
            else:
                print(f"  INTUITION CHECK: Edge case — score {score:.4f}, no hard expectation")
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()


# ---------------------------------------------------------------------------
# TEST 3  Categorical boundary — unseen category value
# ---------------------------------------------------------------------------

def test3_categorical_boundary():
    print()
    print(SEPARATOR)
    print("TEST 3: Unseen categorical value (card_network='diners_club')")
    print(SEPARATOR)

    features = {
        "TransactionAmt":   200.0,
        "amt_zscore":         1.5,
        "amt_to_mean_ratio":  2.0,
        "account_tx_count":  10,
        "tx_hour":           12,
        "tx_day_of_week":     1,
        "velocity_1h":        0,
        "velocity_24h":       1,
        "velocity_7d":        4,
        "amt_velocity_24h": 200.0,
        "addr1":             200,
        "fraud_neighbors":    0,
        "shared_device_accounts": 0,
        "device_known":       1,
        "is_new_device":      0,
        "is_new_p_email":     0,
        "is_new_r_email":     0,
        "ProductCD":         "W",
        "card_network":      "diners_club",   # <-- unseen category
        "card_type":         "credit",
        "device_type":       "desktop",
        "p_email_domain":    "gmail.com",
        "r_email_domain":    "gmail.com",
    }

    try:
        result = score_transaction(features)
        score  = result["risk_score"]
        print(f"  PASS — Did not crash.")
        print(f"  risk_score : {score:.4f}   tier: {result['risk_tier']}")
        # Confirm fallback happened: card_network should have been mapped to cats[0]
        import joblib
        saved_dir = os.path.join(REPO_ROOT, "risk_model/saved")
        model = joblib.load(os.path.join(saved_dir, "model.pkl"))
        cat_idx = list(["ProductCD", "card_network", "card_type", "device_type",
                         "p_email_domain", "r_email_domain"]).index("card_network")
        cats = model._Booster.pandas_categorical[cat_idx]
        fallback_val = cats[0]
        print(f"  'diners_club' not in training categories — fell back to cats[0]='{fallback_val}'")
        print(f"  Training card_network categories: {list(cats)}")
    except Exception as e:
        print(f"  FAIL — Crashed with: {e}")
        traceback.print_exc()


# ---------------------------------------------------------------------------
# TEST 4  Missing-key test — empty dict
# ---------------------------------------------------------------------------

def test4_empty_dict():
    print()
    print(SEPARATOR)
    print("TEST 4: Empty dict — score_transaction({}) must not crash")
    print(SEPARATOR)

    try:
        result = score_transaction({})
        score  = result["risk_score"]
        tier   = result["risk_tier"]
        in_range = 0.0 <= score <= 1.0
        print(f"  PASS — Did not crash.")
        print(f"  risk_score : {score:.4f}   tier: {tier}")
        print(f"  Score in [0,1]: {'YES' if in_range else 'NO — out of range!'}")
        print(f"  All {len(FEATURE_COLS)} features defaulted to 0.")
    except Exception as e:
        print(f"  FAIL — Crashed with: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    test1_training_data()
    test2_synthetic_features()
    test3_categorical_boundary()
    test4_empty_dict()
    print()
    print(SEPARATOR)
    print("All tests complete.")
    print(SEPARATOR)
