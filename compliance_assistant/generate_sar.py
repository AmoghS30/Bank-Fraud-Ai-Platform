"""
Stage 4 — SAR Generation Pipeline
Given an account ID, pulls case data from Neo4j + risk model, retrieves
relevant regulation chunks, and uses AWS Bedrock (Claude) to draft a SAR.

Also exposes answer_compliance_question() for the Q&A tab in the Streamlit demo.
"""

import json
import os
import sys

import boto3
from chromadb import PersistentClient
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from neo4j import GraphDatabase

load_dotenv()

# Set thread limits BEFORE any ML library imports to prevent OpenMP deadlock
# between LightGBM's thread pool and PyTorch's thread pool.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

sys.path.insert(0, "risk_model")
from score import score_transaction  # noqa: E402

VECTOR_DIR = "compliance_assistant/vector_store"
COLLECTION_NAME = "regulatory_docs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_embedder = None
_collection = None
_neo4j_driver = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceEmbeddings(
            model_name=EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedder


def _get_collection():
    global _collection
    if _collection is None:
        client = PersistentClient(path=VECTOR_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def _get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD")),
        )
    return _neo4j_driver


def retrieve_regulations(query: str, k: int = 5) -> list[dict]:
    """Retrieve top-k regulatory chunks relevant to the query."""
    embedder = _get_embedder()
    collection = _get_collection()
    query_embedding = embedder.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        source = os.path.basename(meta.get("source", "unknown"))
        chunks.append({"text": doc, "source": source, "score": round(1 - dist, 3)})
    return chunks


def get_case_data(account_id: str) -> dict:
    """Pull account summary, transactions, and graph context from Neo4j."""
    driver = _get_neo4j()
    with driver.session() as session:
        # Account + transactions (limit for speed — enough for SAR context)
        tx_data = session.run(
            """
            MATCH (a:Account {account_id: $account_id})-[:MADE]->(t:Transaction)
            RETURN a.account_id AS account_id,
                   a.card_network AS card_network,
                   a.card_type    AS card_type,
                   a.addr1        AS addr1,
                   t.tx_id        AS tx_id,
                   t.amount       AS amount,
                   t.dt           AS dt,
                   t.product      AS product,
                   t.is_fraud     AS is_fraud
            ORDER BY t.is_fraud DESC, t.amount DESC
            LIMIT 200
            """,
            account_id=account_id,
        ).data()

        if not tx_data:
            return {}

        # Device connections
        devices = session.run(
            """
            MATCH (a:Account {account_id: $account_id})-[:USES_DEVICE]->(d:Device)
            RETURN d.device_info AS device_info, d.device_type AS device_type
            LIMIT 3
            """,
            account_id=account_id,
        ).data()

        # Accounts sharing device with this account (limit for speed)
        ring = session.run(
            """
            MATCH (a:Account {account_id: $account_id})-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other:Account)
            WHERE other <> a
            WITH a, other, d LIMIT 50
            OPTIONAL MATCH (other)-[:MADE]->(ft:Transaction {is_fraud: true})
            WITH other.account_id AS linked_account,
                 d.device_info AS shared_device,
                 count(ft) AS fraud_txs
            RETURN linked_account, shared_device, fraud_txs
            ORDER BY fraud_txs DESC
            LIMIT 10
            """,
            account_id=account_id,
        ).data()

        # Email domains
        emails = session.run(
            """
            MATCH (a:Account {account_id: $account_id})-[:MADE]->(t:Transaction)-[:TO_EMAIL]->(e:EmailDomain)
            RETURN DISTINCT e.domain AS domain, count(t) AS tx_count
            ORDER BY tx_count DESC LIMIT 5
            """,
            account_id=account_id,
        ).data()

    account_info = {
        "account_id": tx_data[0]["account_id"],
        "card_network": tx_data[0]["card_network"],
        "card_type": tx_data[0]["card_type"],
        "addr1": tx_data[0]["addr1"],
    }
    transactions = [
        {
            "tx_id": r["tx_id"],
            "amount": r["amount"],
            "dt": r["dt"],
            "product": r["product"],
            "is_fraud": r["is_fraud"],
        }
        for r in tx_data
    ]
    fraud_txs = [t for t in transactions if t["is_fraud"]]

    return {
        "account": account_info,
        "transactions": transactions,
        "fraud_transactions": fraud_txs,
        "devices": devices,
        "linked_accounts": ring,
        "recipient_domains": emails,
    }


def score_case(case: dict) -> dict:
    """Score the highest-risk transaction in the case using the LightGBM model."""
    if not case.get("fraud_transactions"):
        return {"risk_score": 0.0, "risk_tier": "low", "top_features": []}

    # Use the first flagged transaction with basic features
    ft = case["fraud_transactions"][0]
    txs = case["transactions"]
    tx_amt = ft["amount"]
    all_amts = [t["amount"] for t in txs]
    mean_amt = sum(all_amts) / len(all_amts) if all_amts else tx_amt
    std_amt = (sum((a - mean_amt) ** 2 for a in all_amts) / len(all_amts)) ** 0.5 or 1

    device_known = 1 if case["devices"] else 0
    fraud_neighbors = sum(1 for la in case["linked_accounts"] if la["fraud_txs"] > 0)
    shared_device_accounts = len(case["linked_accounts"])

    features = {
        "TransactionAmt": tx_amt,
        "amt_zscore": (tx_amt - mean_amt) / max(std_amt, 1),
        "amt_to_mean_ratio": tx_amt / max(mean_amt, 0.01),
        "account_tx_count": len(txs),
        "tx_hour": (ft["dt"] % 86400) // 3600,
        "tx_day_of_week": (ft["dt"] // 86400) % 7,
        "velocity_1h": 0,
        "velocity_24h": 0,
        "velocity_7d": 0,
        "amt_velocity_24h": 0.0,
        "addr1": int(float(case["account"].get("addr1") or -1)),
        "fraud_neighbors": fraud_neighbors,
        "shared_device_accounts": shared_device_accounts,
        "device_known": device_known,
        "is_new_device": 0,
        "is_new_p_email": 0,
        "is_new_r_email": 0,
        "ProductCD": ft.get("product", "W"),
        "card_network": case["account"].get("card_network", "unknown"),
        "card_type": case["account"].get("card_type", "unknown"),
        "device_type": case["devices"][0]["device_type"] if case["devices"] else "Unknown",
        "p_email_domain": "unknown",
        "r_email_domain": (case["recipient_domains"][0]["domain"] if case["recipient_domains"] else "unknown"),
    }
    return score_transaction(features)


def generate_sar(account_id: str) -> dict:
    """
    Full SAR generation pipeline:
    1. Pull case data from Neo4j
    2. Score the case
    3. Retrieve relevant regulations
    4. Generate SAR with Claude via Bedrock

    Returns: {"sar_text": str, "risk_score": float, "retrieved_chunks": list, "case": dict}
    """
    print(f"Generating SAR for {account_id}...")

    case = get_case_data(account_id)
    if not case:
        return {"error": f"Account {account_id} not found in Neo4j"}

    scoring = score_case(case)

    # Build retrieval query from case context
    fraud_count = len(case["fraud_transactions"])
    linked_count = len(case["linked_accounts"])
    retrieval_query = (
        f"suspicious transaction report structuring smurfing layering shared device "
        f"PMLA Section 12 STR filing obligation money laundering bank fraud "
        f"{'shared device multiple accounts fraud ring' if linked_count > 0 else ''}"
    )
    chunks = retrieve_regulations(retrieval_query, k=5)
    reg_text = "\n\n".join(
        f"[SOURCE: {c['source']}]\n{c['text']}" for c in chunks
    )

    # Format case summary
    fraud_txs_summary = "\n".join(
        f"  - TX {t['tx_id']}: ₹{t['amount']:,.2f} | Product: {t['product']} | Time offset: {t['dt']}"
        for t in case["fraud_transactions"][:5]
    )
    linked_summary = "\n".join(
        f"  - {la['linked_account']} (shared device: {la['shared_device'][:50]}..., fraud txs: {la['fraud_txs']})"
        for la in case["linked_accounts"][:5]
    )
    shap_summary = "\n".join(
        f"  - {f['feature']}: {f['direction'].replace('_', ' ')} (SHAP={f['shap_value']:+.3f})"
        for f in scoring.get("top_features", [])
    )

    prompt = f"""You are a compliance analyst at a bank. Draft a complete Suspicious Activity Report (STR/SAR) for the following case.
Only cite regulations that are directly quoted or summarised in the "Relevant Regulations" section below.
Do not cite any regulation not present in the provided text. Every regulatory claim must include the exact source document and section.

=== CASE SUMMARY ===
Account ID: {account_id}
Card Type: {case['account'].get('card_type', 'unknown')} | Network: {case['account'].get('card_network', 'unknown')}
Total Transactions: {len(case['transactions'])}
Flagged Transactions: {fraud_count}
AI Risk Score: {scoring.get('risk_score', 0):.3f} / 1.000 [{scoring.get('risk_tier', 'unknown').upper()}]

Flagged Transaction Details:
{fraud_txs_summary if fraud_txs_summary else '  None explicitly flagged'}

AI Model Risk Drivers (SHAP explanation):
{shap_summary if shap_summary else '  Not available'}

Devices Used:
{chr(10).join(f"  - {d['device_info']}" for d in case['devices']) if case['devices'] else '  No specific device fingerprint recorded'}

Linked Accounts (sharing same device):
{linked_summary if linked_summary else '  No linked accounts detected'}

Recipient Email Domains:
{chr(10).join(f"  - {e['domain']} ({e['tx_count']} txs)" for e in case['recipient_domains'][:3]) if case['recipient_domains'] else '  Not available'}

=== RELEVANT REGULATIONS (retrieved by RAG) ===
{reg_text}

=== INSTRUCTIONS ===
Draft a Suspicious Activity Report with the following sections:

1. SUBJECT INFORMATION
2. SUMMARY OF SUSPICIOUS ACTIVITY
3. TRANSACTION DETAILS
4. NETWORK ANALYSIS (shared device / linked accounts)
5. REGULATORY BASIS (cite specific provisions from the regulations provided above — include document name and section number)
6. AI MODEL EVIDENCE (reference the risk score and key SHAP drivers)
7. RECOMMENDED ACTION

Write in formal regulatory language. Be specific and factual. Do not speculate beyond what the data shows."""

    client = boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "ap-south-1"),
    )
    response = client.converse(
        modelId=os.getenv("BEDROCK_MODEL_ID", "in.anthropic.claude-sonnet-5"),
        system=[{"text": "You are a senior compliance analyst specialising in Anti-Money Laundering (AML) and Suspicious Activity Report (SAR) drafting under Indian regulatory framework."}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    content_blocks = response["output"]["message"]["content"]
    sar_text = next((b["text"] for b in content_blocks if "text" in b), "")

    return {
        "sar_text": sar_text,
        "risk_score": scoring.get("risk_score", 0),
        "risk_tier": scoring.get("risk_tier", "unknown"),
        "top_features": scoring.get("top_features", []),
        "retrieved_chunks": chunks,
        "case": case,
    }


def answer_compliance_question(question: str) -> dict:
    """
    RAG Q&A: answer a compliance question using retrieved regulatory chunks.
    Returns: {"answer": str, "sources": list}
    """
    chunks = retrieve_regulations(question, k=4)
    reg_text = "\n\n".join(
        f"[SOURCE: {c['source']}]\n{c['text']}" for c in chunks
    )

    prompt = f"""Answer the following compliance question using ONLY the provided regulatory excerpts below.
If the answer is not in the provided text, say so explicitly — do not use your general knowledge.
Cite the source document and section for every claim.

Question: {question}

Regulatory Excerpts:
{reg_text}"""

    client = boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "ap-south-1"),
    )
    response = client.converse(
        modelId=os.getenv("BEDROCK_MODEL_ID", "in.anthropic.claude-sonnet-5"),
        system=[{"text": "You are a compliance expert. Answer only from the provided regulatory text."}],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    content_blocks = response["output"]["message"]["content"]
    answer = next((b["text"] for b in content_blocks if "text" in b), "")

    return {
        "answer": answer,
        "sources": [{"source": c["source"], "excerpt": c["text"][:200] + "..."} for c in chunks],
    }


if __name__ == "__main__":
    # Quick test
    result = generate_sar("ACC_15063")
    print("\n" + "=" * 60)
    print(result["sar_text"][:2000])
    print("..." if len(result["sar_text"]) > 2000 else "")
