"""
Stage 1 — Neo4j Graph Loader
Reads data/processed/transactions.csv and loads it into Neo4j.

Schema:
  (Account)-[:MADE]->(Transaction)
  (Account)-[:USES_DEVICE]->(Device)      ← only when DeviceInfo is known
  (Account)-[:FROM_EMAIL]->(EmailDomain)  ← purchaser email domain
  (Transaction)-[:TO_EMAIL]->(EmailDomain) ← recipient email domain

Run: python3 knowledge_graph/load_graph.py
Idempotent: safe to re-run, uses MERGE throughout.
"""

import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

PROCESSED = "data/processed/transactions.csv"
BATCH_SIZE = 500  # rows per Cypher transaction — balances speed vs memory

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD")),
)


def create_constraints(session):
    """Uniqueness constraints also create indexes — run once."""
    constraints = [
        "CREATE CONSTRAINT account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.account_id IS UNIQUE",
        "CREATE CONSTRAINT tx_id IF NOT EXISTS FOR (t:Transaction) REQUIRE t.tx_id IS UNIQUE",
        "CREATE CONSTRAINT device_info IF NOT EXISTS FOR (d:Device) REQUIRE d.device_info IS UNIQUE",
        "CREATE CONSTRAINT email_domain IF NOT EXISTS FOR (e:EmailDomain) REQUIRE e.domain IS UNIQUE",
    ]
    for c in constraints:
        session.run(c)
    print("Constraints created.")


def load_batch(session, batch):
    """Load one batch of rows as nodes + relationships."""
    session.run(
        """
        UNWIND $rows AS row

        // Account node
        MERGE (a:Account {account_id: row.account_id})
        SET a.card_network = row.card_network,
            a.card_type    = row.card_type,
            a.addr1        = row.addr1

        // Transaction node
        MERGE (tx:Transaction {tx_id: row.tx_id})
        SET tx.amount     = row.amount,
            tx.dt         = row.dt,
            tx.product    = row.product,
            tx.is_fraud   = row.is_fraud

        // Account → Transaction
        MERGE (a)-[:MADE]->(tx)

        // Device node — only when known
        WITH a, tx, row
        WHERE row.device_info <> 'Unknown'
        MERGE (d:Device {device_info: row.device_info})
        SET d.device_type = row.device_type
        MERGE (a)-[:USES_DEVICE]->(d)
        """,
        rows=batch,
    )

    # Email domain edges in a separate query (avoids WITH clause complexity with optional matches)
    session.run(
        """
        UNWIND $rows AS row

        // Purchaser email domain → Account
        MERGE (pe:EmailDomain {domain: row.p_email_domain})
        WITH pe, row
        MATCH (a:Account {account_id: row.account_id})
        MERGE (a)-[:FROM_EMAIL]->(pe)

        // Recipient email domain → Transaction
        WITH row
        MERGE (re:EmailDomain {domain: row.r_email_domain})
        WITH re, row
        MATCH (tx:Transaction {tx_id: row.tx_id})
        MERGE (tx)-[:TO_EMAIL]->(re)
        """,
        rows=batch,
    )


def load():
    print(f"Reading {PROCESSED}...")
    df = pd.read_csv(PROCESSED)
    print(f"  {len(df):,} rows to load")

    rows = [
        {
            "account_id":    row["account_id"],
            "card_network":  row["card_network"],
            "card_type":     row["card_type"],
            "addr1":         str(row["addr1"]) if pd.notna(row["addr1"]) else "unknown",
            "tx_id":         int(row["TransactionID"]),
            "amount":        float(row["TransactionAmt"]),
            "dt":            int(row["TransactionDT"]),
            "product":       str(row["ProductCD"]),
            "is_fraud":      bool(row["isFraud"]),
            "device_info":   str(row["device_info"]),
            "device_type":   str(row["device_type"]),
            "p_email_domain": str(row["p_email_domain"]),
            "r_email_domain": str(row["r_email_domain"]),
        }
        for _, row in df.iterrows()
    ]

    total = len(rows)
    with driver.session() as session:
        create_constraints(session)

        for i in range(0, total, BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            load_batch(session, batch)
            print(f"  Loaded {min(i + BATCH_SIZE, total):,} / {total:,}", end="\r")

    print(f"\nDone. {total:,} transactions loaded into Neo4j.")

    # Idempotency check
    with driver.session() as session:
        counts = session.run("""
            MATCH (a:Account) WITH count(a) AS accounts
            MATCH (t:Transaction) WITH accounts, count(t) AS txs
            MATCH (d:Device) WITH accounts, txs, count(d) AS devices
            MATCH (e:EmailDomain) WITH accounts, txs, devices, count(e) AS emails
            RETURN accounts, txs, devices, emails
        """).single()
        print(f"\nGraph counts:")
        print(f"  Accounts:     {counts['accounts']:,}")
        print(f"  Transactions: {counts['txs']:,}")
        print(f"  Devices:      {counts['devices']:,}")
        print(f"  EmailDomains: {counts['emails']:,}")

    driver.close()


if __name__ == "__main__":
    load()
