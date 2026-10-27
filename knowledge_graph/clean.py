"""
Stage 1 — Data Cleaning
Joins IEEE-CIS train_transaction.csv + train_identity.csv,
selects relevant columns, normalises identifiers, outputs to data/processed/.
"""

import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

RAW = "data/raw"
PROCESSED = "data/processed"


def clean():
    print("Loading train_transaction.csv...")
    tx = pd.read_csv(
        f"{RAW}/train_transaction.csv",
        usecols=[
            "TransactionID", "isFraud", "TransactionDT", "TransactionAmt",
            "ProductCD",
            "card1", "card2", "card4", "card6",   # card identifiers
            "addr1", "addr2",                       # billing address
            "P_emaildomain", "R_emaildomain",       # purchaser / recipient email
        ],
    )
    print(f"  Rows: {len(tx):,}  |  Fraud: {tx['isFraud'].sum():,}")

    print("Loading train_identity.csv...")
    idf = pd.read_csv(
        f"{RAW}/train_identity.csv",
        usecols=["TransactionID", "DeviceType", "DeviceInfo", "id_30", "id_31"],
        # id_30 = OS version, id_31 = browser — secondary device fingerprint
    )
    print(f"  Rows: {len(idf):,}")

    print("Joining on TransactionID (left join — not all transactions have identity)...")
    df = tx.merge(idf, on="TransactionID", how="left").copy()
    print(f"  Joined shape: {df.shape}")
    print(f"  Transactions with device info: {df['DeviceInfo'].notna().sum():,}")

    # --- Account ID ---
    # card1 is the card sub-bin — best single-column proxy for same cardholder in this dataset.
    # Not perfect (multiple cardholders can share a sub-bin) but standard practice for IEEE-CIS.
    # Prefixed with ACC_ to make Neo4j node IDs unambiguous.
    df.loc[:, "account_id"] = "ACC_" + df["card1"].fillna(0).astype(int).astype(str)

    # --- Device ---
    # Only use DeviceInfo values that contain "Build/" — these are specific hardware
    # fingerprints (e.g. "SAMSUNG SM-G892A Build/NRD90M"). Generic strings like
    # "Windows", "iOS Device", "MacOS", "rv:11.0" are OS/browser names shared by
    # thousands of accounts and carry no fraud-ring signal.
    raw_device = df["DeviceInfo"].fillna("Unknown").str.strip()
    df.loc[:, "device_info"] = raw_device.where(raw_device.str.contains("Build/", na=False), other="Unknown")
    df.loc[:, "device_type"] = df["DeviceType"].fillna("Unknown").str.strip()

    # --- Email domains ---
    df.loc[:, "p_email_domain"] = df["P_emaildomain"].fillna("unknown").str.lower().str.strip()
    df.loc[:, "r_email_domain"] = df["R_emaildomain"].fillna("unknown").str.lower().str.strip()

    # --- Card metadata ---
    df.loc[:, "card_network"] = df["card4"].fillna("unknown").str.lower().str.strip()
    df.loc[:, "card_type"] = df["card6"].fillna("unknown").str.lower().str.strip()

    os.makedirs(PROCESSED, exist_ok=True)

    output_cols = [
        "TransactionID", "account_id", "card_network", "card_type",
        "addr1", "TransactionAmt", "TransactionDT", "ProductCD", "isFraud",
        "device_info", "device_type", "p_email_domain", "r_email_domain",
        "id_30", "id_31",
    ]
    out_path = f"{PROCESSED}/transactions.csv"
    df[output_cols].to_csv(out_path, index=False)

    print(f"\nSaved {len(df):,} rows → {out_path}")
    print(f"Fraud rate:              {df['isFraud'].mean():.2%}")
    print(f"Unique accounts (card1): {df['account_id'].nunique():,}")
    print(f"Unique devices:          {(df['device_info'] != 'Unknown').sum():,} transactions with real device")
    print(f"Unique DeviceInfo values:{df.loc[df['device_info'] != 'Unknown', 'device_info'].nunique():,}")
    print(f"Unique p_email_domain:   {df['p_email_domain'].nunique():,}")
    print(f"Unique r_email_domain:   {df['r_email_domain'].nunique():,}")

    return df


if __name__ == "__main__":
    clean()
