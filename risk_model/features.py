"""
Stage 2 — Feature Engineering
Builds the feature matrix from data/processed/transactions.csv + Neo4j graph queries.
Call build_features() to get a DataFrame ready for train/test split.
"""

import numpy as np
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

PROCESSED = "data/processed/transactions.csv"

FEATURE_COLS = [
    # Amount
    "TransactionAmt", "amt_zscore", "amt_to_mean_ratio", "account_tx_count",
    # Time
    "tx_hour", "tx_day_of_week",
    # Velocity
    "velocity_1h", "velocity_24h", "velocity_7d", "amt_velocity_24h",
    # Address
    "addr1",
    # Graph
    "fraud_neighbors", "shared_device_accounts",
    # Novelty
    "device_known", "is_new_device", "is_new_p_email", "is_new_r_email",
    # Categorical (LightGBM handles natively)
    "ProductCD", "card_network", "card_type", "device_type",
    "p_email_domain", "r_email_domain",
]

CATEGORICAL_COLS = [
    "ProductCD", "card_network", "card_type", "device_type",
    "p_email_domain", "r_email_domain",
]


def _velocity(times: np.ndarray, window_secs: int) -> np.ndarray:
    """Count prior txs from same account within window_secs. times must be sorted."""
    left = np.searchsorted(times, times - window_secs, side="left")
    return np.arange(len(times)) - left


def _amt_velocity(times: np.ndarray, amounts: np.ndarray, window_secs: int) -> np.ndarray:
    """Sum of prior tx amounts within window_secs. times must be sorted."""
    n = len(times)
    result = np.zeros(n)
    for i in range(n):
        left = np.searchsorted(times[:i], times[i] - window_secs, side="left")
        result[i] = amounts[left:i].sum()
    return result


def _get_graph_features(account_ids: list) -> pd.DataFrame:
    """Per-account: fraud accounts within 2 hops via shared device, and total shared-device peers."""
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD")),
    )
    rows = []
    batch_size = 500
    with driver.session() as session:
        for i in range(0, len(account_ids), batch_size):
            batch = account_ids[i : i + batch_size]
            data = session.run(
                """
                UNWIND $ids AS aid
                MATCH (a:Account {account_id: aid})
                OPTIONAL MATCH (a)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(nb:Account)
                WHERE nb <> a
                OPTIONAL MATCH (nb)-[:MADE]->(t:Transaction {is_fraud: true})
                WITH aid,
                     count(DISTINCT nb) AS shared_device_accounts,
                     count(DISTINCT CASE WHEN t IS NOT NULL THEN nb ELSE null END) AS fraud_neighbors
                RETURN aid AS account_id, shared_device_accounts, fraud_neighbors
                """,
                ids=batch,
            ).data()
            rows.extend(data)
    driver.close()
    return pd.DataFrame(rows)


def build_features(df: pd.DataFrame = None, include_graph: bool = True) -> pd.DataFrame:
    """
    Build full feature matrix.
    Returns df with all FEATURE_COLS + TransactionID + isFraud + TransactionDT.
    """
    if df is None:
        df = pd.read_csv(PROCESSED)

    df = df.sort_values("TransactionDT").reset_index(drop=True).copy()

    # --- Time ---
    df.loc[:, "tx_hour"] = (df["TransactionDT"] % 86400) // 3600
    df.loc[:, "tx_day_of_week"] = (df["TransactionDT"] // 86400) % 7

    # --- Amount per-account stats ---
    acct_stats = (
        df.groupby("account_id")["TransactionAmt"]
        .agg(mean="mean", std="std")
        .rename(columns={"mean": "_acct_mean", "std": "_acct_std"})
    )
    df = df.merge(acct_stats, on="account_id", how="left")
    df.loc[:, "_acct_std"] = df["_acct_std"].fillna(1.0).clip(lower=1.0)
    df.loc[:, "amt_zscore"] = (df["TransactionAmt"] - df["_acct_mean"]) / df["_acct_std"]
    df.loc[:, "amt_to_mean_ratio"] = df["TransactionAmt"] / df["_acct_mean"].clip(lower=0.01)
    df.loc[:, "account_tx_count"] = df.groupby("account_id")["TransactionID"].transform("count")
    df.drop(columns=["_acct_mean", "_acct_std"], inplace=True)

    # --- Velocity (per account, sorted by time) ---
    print("  Computing velocity features...")
    vel_1h = np.zeros(len(df), dtype=np.int32)
    vel_24h = np.zeros(len(df), dtype=np.int32)
    vel_7d = np.zeros(len(df), dtype=np.int32)
    amt_vel_24h = np.zeros(len(df), dtype=np.float64)

    for _, group in df.groupby("account_id", sort=False):
        idx = group.index.values
        times = group["TransactionDT"].values
        amts = group["TransactionAmt"].values
        vel_1h[idx] = _velocity(times, 3600)
        vel_24h[idx] = _velocity(times, 86400)
        vel_7d[idx] = _velocity(times, 86400 * 7)
        amt_vel_24h[idx] = _amt_velocity(times, amts, 86400)

    df.loc[:, "velocity_1h"] = vel_1h
    df.loc[:, "velocity_24h"] = vel_24h
    df.loc[:, "velocity_7d"] = vel_7d
    df.loc[:, "amt_velocity_24h"] = amt_vel_24h

    # --- Novelty flags (cumcount within sorted-by-time df) ---
    df.loc[:, "device_known"] = (df["device_info"] != "Unknown").astype(np.int8)
    df.loc[:, "is_new_device"] = (
        (df.groupby(["account_id", "device_info"]).cumcount() == 0)
        & (df["device_info"] != "Unknown")
    ).astype(np.int8)
    df.loc[:, "is_new_p_email"] = (
        df.groupby(["account_id", "p_email_domain"]).cumcount() == 0
    ).astype(np.int8)
    df.loc[:, "is_new_r_email"] = (
        df.groupby(["account_id", "r_email_domain"]).cumcount() == 0
    ).astype(np.int8)

    # --- Address ---
    df.loc[:, "addr1"] = pd.to_numeric(df["addr1"], errors="coerce").fillna(-1).astype(np.int16)

    # --- Graph features ---
    if include_graph:
        print("  Querying Neo4j for graph features...")
        unique_accounts = df["account_id"].unique().tolist()
        gf = _get_graph_features(unique_accounts)
        df = df.merge(gf, on="account_id", how="left")
        df.loc[:, "shared_device_accounts"] = df["shared_device_accounts"].fillna(0).astype(np.int16)
        df.loc[:, "fraud_neighbors"] = df["fraud_neighbors"].fillna(0).astype(np.int16)
    else:
        df.loc[:, "shared_device_accounts"] = 0
        df.loc[:, "fraud_neighbors"] = 0

    return df
