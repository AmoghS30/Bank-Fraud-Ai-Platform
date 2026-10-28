# Bank Fraud AI Platform — Demo Guide

> Simple, plain-English explanation of everything built. Read this before your demo.

---

## What the project does in one sentence

The platform detects fraud by looking at the **network of connections** between bank accounts (not just individual transactions), scores each transaction with an AI model that explains *why* it flagged it, and auto-drafts a legal report that banks must file when they spot suspicious activity.

---

## The three deliverables and how they connect

```
Raw transactions (590,540 from IEEE-CIS Kaggle dataset)
        │
        ▼
① Knowledge Graph (Neo4j)        ← finds hidden fraud rings
        │
        ▼
② Risk Scoring Model (LightGBM)  ← scores every transaction 0–1
        │
        ▼
③ Compliance Assistant (Claude)  ← drafts the SAR report
```

Think of it like this: the graph finds *who* is suspicious, the model says *how* suspicious, and the assistant writes *the report*.

---

## Part 1 — Knowledge Graph (Neo4j)

### What is a knowledge graph?
A knowledge graph is like a social network, but for bank accounts. Instead of "person A is friends with person B", it stores "account A and account B used the same phone/device". This matters because fraudsters often control many accounts but accidentally link them by using the same laptop or phone.

### What data we loaded
- **590,540 transactions** from the [IEEE-CIS Fraud Detection dataset](https://www.kaggle.com/c/ieee-fraud-detection) — a real Kaggle competition dataset from Vesta Corporation (a payment processor).
- Each row has the account, amount, time, device fingerprint, email domains, card info.

### How the graph is structured

| Node type | Example | What it represents |
|---|---|---|
| Account | ACC_15063 | A unique card/customer |
| Transaction | TX_3341457 | A single payment |
| Device | SM-G960U Build/R16NW | A phone or laptop fingerprint |
| EmailDomain | anonymous.com | Where money is sent |

| Edge (relationship) | Meaning |
|---|---|
| Account → MADE → Transaction | Account made this payment |
| Account → USES_DEVICE → Device | Account logged in from this device |
| Transaction → TO_EMAIL → EmailDomain | Money was sent to this email domain |

### Why graphs catch fraud that spreadsheets miss
If account A and account B both used device X, a spreadsheet query would miss this unless you join tables manually. In Neo4j you write:

```cypher
MATCH (a:Account)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(b:Account)
WHERE a <> b
RETURN a, d, b
```

This instantly shows every pair of accounts sharing a device — the textbook signature of a **fraud ring** (one person controlling many accounts).

### What we found
A single device fingerprint (`SM-N920V Build/NRD90M`) was shared by over 1,000 accounts, 532 of which had confirmed fraud transactions. That's the fraud ring the demo visualises in Tab 1.

---

## Part 2 — Risk Scoring Model (LightGBM)

### What is LightGBM?
LightGBM is a gradient boosting algorithm — think of it as **244 decision trees working together**. Each tree learns from the mistakes of the previous one. It's the go-to model for tabular (spreadsheet-like) financial data because it's fast, handles missing values, and supports categorical features natively.

We chose it over deep learning because:
- Explainability via SHAP (required for regulatory compliance)
- Trains in minutes on a laptop
- AUPRC of 0.22 on a highly imbalanced dataset (only 3.5% fraud) is competitive

### Why "3.5% fraud" is a problem we had to solve
If 3.5% of transactions are fraud, a model that always says "not fraud" would be 96.5% accurate — but useless. So we set `scale_pos_weight = 27.5`, which means the model treats each fraud example as if it appeared 27.5 times. This forces it to take fraud seriously.

### Train/test split — why we didn't do it randomly
We sorted all 590K transactions by **timestamp** and trained on the first 80% (≈ 472K), tested on the last 20% (≈ 118K). This is called a **time-based split**.

Random splitting would be cheating: a transaction from account A in January and another from account A in June would both end up in the test set, but the model would have seen similar account-A patterns in training. In real deployment, the model always sees future data it hasn't trained on — the time split simulates this honestly.

### The 22 features — what each one means

#### Amount features
| Feature | What it is | Why it matters |
|---|---|---|
| `TransactionAmt` | The raw rupee/dollar amount | Large amounts are correlated with fraud but not exclusively |
| `amt_zscore` | How many standard deviations above this account's average this transaction is | A ₹50 account suddenly making a ₹5000 transaction is suspicious (high z-score) |
| `amt_to_mean_ratio` | This transaction's amount ÷ account's average amount | Similar to z-score but ratio-based; a ratio of 5× means this transaction is 5× the usual size |
| `account_tx_count` | Total lifetime transactions from this account | A brand-new account with only 2 transactions is riskier than an established account with 500 |

#### Time features
| Feature | What it is | Why it matters |
|---|---|---|
| `tx_hour` | Hour of day the transaction happened (0–23) | Fraud is disproportionately made between 1–4am when people are asleep and can't notice |
| `tx_day_of_week` | Day of the week (0=Monday, 6=Sunday) | Weekend transactions have different risk profiles |

#### Velocity features — "how many transactions recently?"
Fraudsters often make many small transactions rapidly (called **structuring** or **smurfing**) to stay under reporting thresholds. Velocity counts how many transactions this account made in the recent past.

| Feature | What it is |
|---|---|
| `velocity_1h` | Transactions in the last 1 hour |
| `velocity_24h` | Transactions in the last 24 hours |
| `velocity_7d` | Transactions in the last 7 days |
| `amt_velocity_24h` | Total amount transacted in the last 24 hours |

Example: if an account makes 8 transactions in 1 hour each for ₹9,999 (just below a ₹10,000 reporting threshold), `velocity_1h = 8` and `amt_velocity_24h ≈ ₹80,000` — both very high, strong fraud signal.

#### Graph features — from Neo4j
| Feature | What it is | Why it matters |
|---|---|---|
| `fraud_neighbors` | How many accounts sharing this device have been flagged as fraud | If 532 of your device-mates are fraudsters, you're probably in the ring too |
| `shared_device_accounts` | Total accounts sharing this device | A device used by 1000 accounts is far more suspicious than one used by 1 |

#### Novelty flags — "is this new?"
| Feature | What it is |
|---|---|
| `device_known` | 1 if we've seen this device before, 0 if it's unknown |
| `is_new_device` | 1 if this is the first time this account used this specific device |
| `is_new_p_email` | 1 if this is the first time this purchaser email appears for this account |
| `is_new_r_email` | 1 if this is the first time money is sent to this recipient email from this account |

A legitimate customer usually transacts from the same laptop/phone. A fraudster testing a stolen card for the first time will always trigger `is_new_device = 1`.

#### Categorical features — identity signals
| Feature | What it is | Example values |
|---|---|---|
| `ProductCD` | Type of product/service purchased | W (transfer), H (hotel?), C (card), S, R |
| `card_network` | Card network | visa, mastercard, american express |
| `card_type` | Type of card | credit, debit, charge card |
| `device_type` | Broad device category | desktop, mobile, Unknown |
| `p_email_domain` | Purchaser's email provider | gmail.com, yahoo.com, anonymous.com |
| `r_email_domain` | Recipient's email provider | gmail.com, anonymous.com |

`anonymous.com` as a recipient email is the single strongest fraud signal in the dataset — it's a disposable email service.

### How SHAP explains individual predictions
SHAP (SHapley Additive exPlanations) comes from game theory. For each transaction, it asks: "how much did each feature contribute to the final score?"

Red bar in the chart = pushes score UP (more fraud risk)
Green bar = pushes score DOWN (less fraud risk)

Example explanation for a 0.96 fraud score:
- `TransactionAmt (+1.19)` — amount is 4× the account average → big red flag
- `r_email_domain (+0.96)` — going to anonymous.com → very suspicious
- `tx_hour (+0.65)` — 3am transaction → suspicious
- `ProductCD (+0.59)` — product type W (transfers) → high-risk category

### Model performance (what the numbers mean)

| Metric | Value | Plain English |
|---|---|---|
| ROC-AUC | 0.829 | If I show the model a random fraud and a random legit transaction, it correctly ranks the fraud higher 83% of the time |
| AUPRC | 0.220 | Precision-recall area — the main metric for imbalanced data. A random classifier would score 0.035 (fraud rate); 0.22 is 6× better |
| Best threshold | 0.744 | If we flag everything above 0.744, we flag 4.7% of transactions and catch 36% of all fraud |

The model doesn't catch all fraud — 64% is missed. That's a known limitation of the IEEE-CIS dataset where many fraud patterns overlap with normal behaviour. In production, this model would be one layer of a multi-layer defence.

---

## Part 3 — Compliance Assistant (RAG + Claude)

### What is a SAR?
A Suspicious Activity Report (SAR), called STR in India, is a legal document that banks **must** file with the Financial Intelligence Unit (FIU-IND) within 7 days of detecting suspicious activity. It's required by PMLA 2002 (Prevention of Money Laundering Act). Failure to file can result in fines and criminal liability for the bank's compliance officer.

Writing a SAR manually takes a compliance analyst 2–4 hours. Our system drafts it in ~30 seconds.

### What is RAG?
RAG = Retrieval-Augmented Generation. Instead of asking Claude to answer from its training memory (which might be wrong or outdated), we:
1. Embed the actual legal text into a searchable database
2. When generating a SAR, find the most relevant regulation chunks
3. Tell Claude: "answer using ONLY these excerpts, cite the source"

This prevents hallucination of fake regulation sections.

### What documents we embedded
| Document | What it covers |
|---|---|
| PMLA 2002 | The Indian anti-money laundering law — defines offences, STR obligations, fines |
| RBI KYC Master Direction 2016 | RBI's rules on customer due diligence and suspicious transaction monitoring |
| FATF Recommendations | International standards — defines smurfing, layering, red flags for digital payments |

Total: 85 chunks of regulatory text embedded as 384-dimensional vectors using `sentence-transformers/all-MiniLM-L6-v2`.

### The embedding process
"Embedding" converts text into a list of 384 numbers (a vector) that captures the meaning. Similar text → similar vectors. When a new query comes in, we embed the query and find the top-5 most similar regulation chunks by cosine similarity.

Example:
- Query: "structuring smurfing PMLA Section 12 STR filing"
- Retrieved chunks: PMLA Section 12A (STR requirements), FATF Recommendation 20, RBI suspicious transaction monitoring guidelines

### The SAR generation pipeline
```
Account ID (e.g. ACC_15063)
    ↓
Neo4j: get all transactions, devices, linked accounts (fraud ring)
    ↓
LightGBM: score the highest-risk transaction + SHAP explanation
    ↓
ChromaDB: retrieve top-5 most relevant regulation chunks
    ↓
Claude (AWS Bedrock, claude-sonnet-5): draft SAR with 7 sections
    ↓
Output: Complete, cited SAR document
```

### What the generated SAR contains
1. **Subject Information** — account ID, card type, total transaction count
2. **Summary of Suspicious Activity** — plain English summary of why this is suspicious
3. **Transaction Details** — table of flagged transactions with amounts and timestamps
4. **Network Analysis** — shared device connections, linked accounts with fraud history
5. **Regulatory Basis** — specific citations from PMLA, RBI, or FATF (retrieved, not hallucinated)
6. **AI Model Evidence** — the risk score (0.721) and top SHAP drivers
7. **Recommended Action** — file STR, freeze account, escalate to FIU-IND

---

## How to run the demo

```bash
# Start Neo4j first (if not already running)
docker start fraud-graph

# Run the Streamlit demo (must use this script — it sets threading env vars)
./run_demo.sh
```

Then open `http://localhost:8501`

### Recommended demo flow (5 minutes)

**Tab 1 — Fraud Network (2 min)**
1. Select `ACC_15063` from the table (or type it in the manual field)
2. Show the linked accounts table: this account shares a device with 10+ other accounts, all with fraud transactions
3. Explain: "Traditional rules look at one account at a time. The graph shows the fraud ring in one query."

**Tab 2 — Risk Scorer (1.5 min)**
1. Open "Load a real test transaction" → pick a 🔴 FRAUD one → click Load
2. Click Score Transaction → show that the predicted score matches the saved score (error < 0.01)
3. Point to the SHAP bar chart and explain the top 2 drivers
4. OR manually set: Product=W, Recipient=anonymous.com, Hour=3, Fraud Neighbours=100, New Device=✓ → show critical score

**Tab 3 — SAR Generator (1.5 min)**
1. Select `ACC_15063`, click Generate SAR
2. While waiting (~30 seconds), explain the RAG pipeline
3. Show the retrieved regulation chunks — point out PMLA Section 12A citation
4. Show the generated SAR — it has all 7 required sections
5. Click Download SAR

---

## Common questions and answers

**Q: Why 3.5% fraud in the dataset — is that realistic?**
A: Yes, typical fraud rates for payment processors are 0.1–5%. The IEEE-CIS dataset reflects real production data from Vesta Corporation.

**Q: Why not use a neural network?**
A: LightGBM is more accurate on tabular financial data, trains in 5 minutes instead of hours, and critically, supports SHAP explanations — which are mandatory for regulatory compliance. A black-box neural net can't explain why it flagged a transaction.

**Q: What's the difference between AUPRC and accuracy?**
A: Accuracy is useless on imbalanced data (96.5% "not fraud" would get 96.5% accuracy). AUPRC measures how well you can rank actual fraud cases above legit ones across all decision thresholds — the right metric when positives are rare.

**Q: What happens if the model sees a card network it's never seen (e.g. Diners Club)?**
A: It safely falls back to the first known category and still returns a score. The system doesn't crash.

**Q: Does Claude make up regulations?**
A: No — the prompt explicitly says "cite only regulations present in the provided text, do not use general knowledge." The RAG system retrieves the actual legal text and Claude must quote it. We verified this manually for 3+ test cases.

**Q: Why does the SAR generation take 30 seconds?**
A: Two slow steps: (1) loading the sentence-transformers embedding model (~3 seconds, cached after first use), and (2) the AWS Bedrock API call to Claude which generates ~800 words (~20 seconds).

---

## Tech stack summary

| Component | Technology | Why |
|---|---|---|
| Data processing | Python / Pandas | Standard for tabular data |
| Knowledge graph | Neo4j 5 (Docker) | Native graph DB, Cypher query language, visual browser at :7474 |
| Risk model | LightGBM + SHAP | Fast, explainable, best-in-class for tabular fraud detection |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 | Fast, small, 384-dim, runs fully offline |
| Vector store | ChromaDB (local) | Free, local, no API key needed, sufficient for 85-chunk corpus |
| LLM | Claude (AWS Bedrock, claude-sonnet-5) | Best-in-class for long-form structured writing |
| Dashboard | Streamlit | Fastest way to build a data science demo UI in Python |
| Visualisation | Plotly | Interactive charts that render well in Streamlit |
