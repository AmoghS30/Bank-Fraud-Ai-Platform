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

## The Three Deliverables — Inputs, What Happens, and Why It Matters

---

### ① Knowledge Graph — Neo4j

#### What is the input?
Raw transaction data from the IEEE-CIS dataset. Every row has:
- An **account ID** (who made the payment)
- A **device fingerprint** (what phone/laptop they used — e.g. `SM-G960U Build/R16NW`)
- An **email domain** (where the money was sent — e.g. `anonymous.com`)
- A **transaction amount and timestamp**

We load 590,540 such rows into Neo4j.

#### What happens in the background?
Instead of storing this as a flat spreadsheet, we model it as a **graph** — a network of connected nodes:

```
Account A ──USES_DEVICE──► Device X ◄──USES_DEVICE── Account B
Account A ──MADE──► Transaction ──TO_EMAIL──► anonymous.com
```

When we run the query:
```cypher
MATCH (a:Account)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(b:Account)
WHERE a <> b
RETURN a, d, b
```
Neo4j instantly shows every pair of accounts that share a device — the textbook signature of a **fraud ring** (one person controlling many fake accounts from the same phone/laptop).

#### What is the output?
- A **list of linked accounts** — e.g. ACC_15063 shares device `SM-N920V Build/NRD90M` with 1,000+ other accounts, 532 of which have confirmed fraud
- Two features that feed into the risk model: `fraud_neighbors` (how many device-mates are fraudsters) and `shared_device_accounts` (how many accounts total share that device)

#### Why is it significant?
A traditional bank system looks at one account at a time. If Account A has no fraud history, it looks clean — even if it shares a device with 532 confirmed fraudsters.

The graph sees the *network*. It finds fraud rings that are invisible in spreadsheet analysis. In real banks, this is how money mule networks and synthetic identity fraud rings are uncovered — not by looking at individual accounts but by mapping the connections between them.

---

### ② Risk Scoring Model — LightGBM

#### What is the input?
22 features for a single transaction. These come from three sources:
- **Raw transaction data** — amount, card type, product code, email domains, device type
- **Computed per-account statistics** — z-score of the amount, velocity counts (transactions in last 1h/24h/7d), account age
- **Graph features from Neo4j** — `fraud_neighbors`, `shared_device_accounts`

Example input (a suspicious transaction):
```
TransactionAmt     = 500.0      ← amount
amt_zscore         = 3.2        ← 3.2 standard deviations above this account's norm
velocity_1h        = 8          ← 8 transactions in the last hour
tx_hour            = 3          ← 3am
r_email_domain     = anonymous.com
is_new_device      = 1          ← first time this account used this device
fraud_neighbors    = 532        ← 532 fraud accounts share this device
```

#### What happens in the background?
LightGBM runs the input through **244 decision trees** that were trained on 472,000 historical transactions. Each tree votes on whether this looks like fraud. The votes are combined into a single probability (0 to 1).

Then SHAP (SHapley Additive exPlanations) runs on top — it asks each of the 22 features: *"how much did you personally push the score up or down?"* This gives a per-feature contribution score for every prediction.

```
Input features
     │
     ▼
244 decision trees vote → probability = 0.92
     │
     ▼
SHAP explains it:
  r_email_domain   +0.96  ← pushed score UP by 0.96
  tx_hour          +0.65  ← pushed score UP by 0.65
  is_new_device    +0.43  ← pushed score UP by 0.43
  amt_zscore       +0.31  ← pushed score UP by 0.31
  velocity_1h      +0.18  ← pushed score UP by 0.18
```

#### What is the output?
- A **risk score** between 0 and 1 (e.g. 0.92)
- A **risk tier**: low (< 0.4), medium (0.4–0.7), high (0.7–0.9), critical (≥ 0.9)
- **Top 5 SHAP drivers** — which features caused this score, with direction and magnitude

#### Why is it significant?
Two reasons:

**Speed** — the model scores a transaction in under 200ms. A human analyst takes hours to investigate one case. The model can screen all 590,540 transactions in minutes.

**Explainability** — regulators (RBI, FIU-IND) require that every fraud flag be *justified*, not just produced by a black box. SHAP gives a plain-English reason for every score: "Flagged because: sending to anonymous.com (+0.96), transaction at 3am (+0.65), new device (+0.43)." A neural network can't do this. LightGBM + SHAP can.

---

### ③ Compliance Assistant — RAG + Claude

#### What is the input?
Three things are assembled automatically when you click "Generate SAR":

1. **Account data from Neo4j** — transaction history, total amount, device connections, linked fraud accounts
2. **Risk model output** — the risk score (e.g. 0.92) and the top SHAP explanation
3. **Relevant regulation excerpts from ChromaDB** — retrieved by searching 85 chunks of actual legal text (PMLA 2002, RBI KYC Master Direction, FATF Recommendations) using semantic similarity

#### What happens in the background?
**Step 1 — Retrieval (RAG):**
The system builds a search query from the case context:
```
"suspicious activity structuring multiple transactions PMLA STR filing obligation"
```
It converts this query into a 384-dimensional vector using `sentence-transformers/all-MiniLM-L6-v2` and searches ChromaDB for the 5 most similar regulation chunks by cosine similarity.

Example retrieved chunks:
- PMLA 2002, Section 12A — obligation to report suspicious transactions within 7 days
- FATF Recommendation 20 — definition of suspicious transaction reporting
- RBI KYC Master Direction — red flags for structuring and smurfing

**Step 2 — Generation:**
Claude (via AWS Bedrock) receives a prompt that includes the account data, risk score, SHAP explanation, and retrieved regulation excerpts. The prompt says:
> "Generate a structured SAR. Cite ONLY regulations present in the provided text. Do not use general knowledge."

Claude writes an 800-word SAR with 7 required sections.

#### What is the output?
A complete, ready-to-submit Suspicious Activity Report:
1. Subject information (account, card type, transaction count)
2. Summary of suspicious activity (plain English)
3. Transaction details (table of flagged transactions)
4. Network analysis (fraud ring connections)
5. Regulatory basis (cited from retrieved PMLA/RBI/FATF text)
6. AI model evidence (risk score + SHAP drivers)
7. Recommended action (file STR, freeze account, escalate)

#### Why is it significant?
A compliance analyst manually writing this SAR takes **2–4 hours** — cross-referencing regulations, pulling transaction records, writing the narrative. Our system does it in **~30 seconds**.

The RAG architecture is critical for trust: Claude is not answering from memory (which could hallucinate wrong section numbers). It retrieves the *actual* legal text and quotes it. Every regulatory citation in the generated SAR can be traced to a real document chunk. This is what makes the output admissible for a real compliance workflow — it's grounded in verified source material, not AI guesswork.

---

## Example Inputs and Expected Outputs — Risk Scorer

Three scenarios showing exactly what to type in the UI and what the model returns.

---

### Scenario A — Critical Fraud (Score ≈ 0.92+)

This represents a stolen credit card being used by a fraudster at 3am, sending money to a disposable email, from a device shared by hundreds of fraud accounts.

| Feature | Value to enter | Why this value screams fraud |
|---|---|---|
| `TransactionAmt` | 500.0 | Significant amount |
| `amt_zscore` | 3.2 | Transaction is 3.2× above this account's normal range |
| `amt_to_mean_ratio` | 4.1 | This transaction is 4× the account's average spend |
| `account_tx_count` | 5 | Brand-new account — only 5 lifetime transactions |
| `tx_hour` | 3 | 3am — owner is asleep, won't notice alert |
| `tx_day_of_week` | 6 | Sunday — reduced bank monitoring |
| `velocity_1h` | 8 | 8 transactions in the last hour — card testing |
| `velocity_24h` | 15 | 15 transactions today |
| `velocity_7d` | 20 | 20 transactions this week |
| `amt_velocity_24h` | 4500.0 | $4,500 moved today |
| `addr1` | -1 | Billing address unknown — AVS bypass attempt |
| `fraud_neighbors` | 100 | 100 confirmed fraud accounts share this device |
| `shared_device_accounts` | 500 | 500 accounts use this one device |
| `device_known` | 0 | Device has never been seen before |
| `is_new_device` | 1 | First time this account used this device |
| `is_new_p_email` | 1 | New purchaser email on this account |
| `is_new_r_email` | 1 | First time money sent to this recipient domain |
| `ProductCD` | W | Transfer/wallet — irreversible, fraudster favourite |
| `card_network` | visa | — |
| `card_type` | credit | Higher limit, delayed billing = victim notices later |
| `device_type` | mobile | — |
| `p_email_domain` | gmail.com | — |
| `r_email_domain` | anonymous.com | Disposable email — strongest single fraud signal |

**Expected output:**
```
Risk Score:  0.92 – 0.97
Risk Tier:   CRITICAL 🔴

Top SHAP drivers:
  r_email_domain    +0.96   increases_risk   ← anonymous.com is a huge red flag
  tx_hour           +0.65   increases_risk   ← 3am transaction
  is_new_device     +0.43   increases_risk   ← first time on this device
  amt_zscore        +0.31   increases_risk   ← amount far above account's norm
  velocity_1h       +0.18   increases_risk   ← 8 transactions in 1 hour
```

---

### Scenario B — Legitimate Transaction (Score ≈ 0.03–0.10)

An established customer making a normal weekday purchase from their usual device to a known email.

| Feature | Value to enter | Why this looks safe |
|---|---|---|
| `TransactionAmt` | 45.0 | Small, normal purchase |
| `amt_zscore` | 0.1 | Right within this account's normal range |
| `amt_to_mean_ratio` | 1.05 | Essentially the same as the account average |
| `account_tx_count` | 200 | Well-established account with long history |
| `tx_hour` | 14 | 2pm — normal business hours |
| `tx_day_of_week` | 2 | Wednesday |
| `velocity_1h` | 1 | Just this one transaction in the last hour |
| `velocity_24h` | 2 | 2 transactions today — completely normal |
| `velocity_7d` | 8 | About 1 per day this week |
| `amt_velocity_24h` | 90.0 | $90 total today |
| `addr1` | 315 | Known billing zip code |
| `fraud_neighbors` | 0 | No fraud accounts share this device |
| `shared_device_accounts` | 1 | Only this one account uses this device |
| `device_known` | 1 | Device seen many times before |
| `is_new_device` | 0 | Same device this account always uses |
| `is_new_p_email` | 0 | Same purchaser email as always |
| `is_new_r_email` | 0 | Sent to the same recipient domain as before |
| `ProductCD` | C | Lower-risk product category |
| `card_network` | visa | — |
| `card_type` | debit | — |
| `device_type` | desktop | — |
| `p_email_domain` | gmail.com | — |
| `r_email_domain` | gmail.com | Normal email domain |

**Expected output:**
```
Risk Score:  0.03 – 0.10
Risk Tier:   LOW 🟢

Top SHAP drivers:
  r_email_domain    -0.41   decreases_risk   ← gmail.com is normal
  device_known      -0.28   decreases_risk   ← familiar device
  fraud_neighbors   -0.22   decreases_risk   ← no fraud ring connections
  account_tx_count  -0.18   decreases_risk   ← established account
  tx_hour           -0.12   decreases_risk   ← daytime transaction
```

---

### Scenario C — Medium Risk (Score ≈ 0.45–0.65)

A real account doing something slightly unusual — not clearly fraud, not clearly safe. This is where the model is most useful: it flags it for human review rather than auto-blocking.

| Feature | Value to enter | What makes it suspicious vs. safe |
|---|---|---|
| `TransactionAmt` | 250.0 | Higher than usual for this account |
| `amt_zscore` | 1.8 | Somewhat above normal but not extreme |
| `amt_to_mean_ratio` | 2.3 | About 2× the usual spend |
| `account_tx_count` | 40 | Moderately established account |
| `tx_hour` | 22 | 10pm — late but not 3am |
| `tx_day_of_week` | 5 | Saturday |
| `velocity_1h` | 2 | 2 transactions in last hour — slightly elevated |
| `velocity_24h` | 4 | 4 today — acceptable |
| `velocity_7d` | 12 | Normal weekly rate |
| `amt_velocity_24h` | 600.0 | $600 today — above typical |
| `addr1` | 299 | Known address |
| `fraud_neighbors` | 2 | 2 fraud accounts share device — slight concern |
| `shared_device_accounts` | 5 | 5 accounts on this device — borderline |
| `device_known` | 1 | Device has been seen before |
| `is_new_device` | 0 | Same device as usual |
| `is_new_p_email` | 0 | Same purchaser email |
| `is_new_r_email` | 1 | Sending to a new recipient for the first time |
| `ProductCD` | W | Transfer — slightly higher risk category |
| `card_network` | mastercard | — |
| `card_type` | credit | — |
| `device_type` | mobile | — |
| `p_email_domain` | gmail.com | — |
| `r_email_domain` | yahoo.com | New recipient, but a normal email domain |

**Expected output:**
```
Risk Score:  0.45 – 0.65
Risk Tier:   MEDIUM 🟡

Top SHAP drivers:
  is_new_r_email    +0.22   increases_risk   ← new recipient domain
  tx_hour           +0.14   increases_risk   ← late evening
  amt_zscore        +0.12   increases_risk   ← slightly above normal amount
  fraud_neighbors   +0.08   increases_risk   ← 2 fraud accounts on this device
  device_known      -0.11   decreases_risk   ← familiar device pulls score down
```

This score sits in the "queue for manual review" zone — an analyst would look at it before deciding whether to block. This is exactly how real bank fraud systems work: auto-block above 0.90, manual review between 0.50–0.90, auto-pass below 0.50.

---

### What the SAR Generator Outputs for ACC_15063

When you click "Generate SAR" for account `ACC_15063` (the demo fraud ring account), here is what gets assembled as input and what Claude returns:

**Input assembled automatically:**
```
Account:          ACC_15063
Transactions:     47 total, highest amount $2,302
Device:           SM-N920V Build/NRD90M
Fraud neighbors:  532 accounts share this device and have fraud transactions
Risk score:       0.72 (on its highest-value transaction)
Top SHAP drivers: fraud_neighbors (+0.44), r_email_domain (+0.38), tx_hour (+0.29)

Retrieved regulations:
  [1] PMLA 2002 Section 12A — reporting obligation within 7 days
  [2] FATF Recommendation 20 — definition of suspicious transactions
  [3] RBI KYC Master Direction — structuring red flags
  [4] PMLA 2002 Section 3 — definition of money laundering
  [5] FATF Recommendation 26 — financial institution monitoring obligations
```

**Output (abridged):**
```
SUSPICIOUS ACTIVITY REPORT

1. SUBJECT INFORMATION
   Account ID: ACC_15063 | Card type: credit | Total transactions: 47

2. SUMMARY OF SUSPICIOUS ACTIVITY
   Account ACC_15063 has conducted 47 transactions totalling $X, including
   high-value transfers to anonymous.com. The account's device is shared with
   532 confirmed fraud accounts, indicating probable fraud ring membership.

3. TRANSACTION DETAILS
   [Table of top 5 flagged transactions with amounts and timestamps]

4. NETWORK ANALYSIS
   Device SM-N920V Build/NRD90M is shared by 1,000+ accounts.
   532 of those accounts have confirmed fraudulent transactions.

5. REGULATORY BASIS
   Per PMLA 2002 Section 12A, reporting entities are obligated to file an STR
   within 7 days of detecting a suspicious transaction. Per FATF Recommendation
   20, transactions that appear to have no legitimate economic purpose and
   involve structuring patterns must be reported...

6. AI MODEL EVIDENCE
   LightGBM risk score: 0.72 (HIGH tier)
   Primary drivers: fraud network connections (+0.44), anonymous.com
   recipient (+0.38), late-night timing (+0.29)

7. RECOMMENDED ACTION
   File STR with FIU-IND within 7 days. Freeze account pending investigation.
   Escalate device SM-N920V Build/NRD90M — 532 linked fraud accounts warrant
   a coordinated ring investigation.
```

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

---

## Deep Dive — Data, Inputs, Background Processing, and Usefulness

This section explains every part of the system from scratch: what raw data we start with, what input each feature takes, what the code does behind the scenes to compute it, and why it helps catch fraud.

---

### The Raw Dataset — Where Everything Starts

**Dataset:** IEEE-CIS Fraud Detection (Kaggle, 2019)
**Source:** Vesta Corporation — a real US payment processing company
**Size:** 590,540 transactions across ~6 months

**What one raw row looks like (simplified):**

| Column | Example value | What it is |
|---|---|---|
| TransactionID | 2987000 | Unique ID for this payment |
| TransactionDT | 86400 | Seconds since a reference point (not a real timestamp — we convert it) |
| TransactionAmt | 68.5 | Dollar amount |
| ProductCD | W | Product category code |
| card1–card6 | 13926, 150, ... | Card number hash, card type, card network, expiry, bank |
| addr1, addr2 | 315, 87 | Billing zip code area codes |
| P_emaildomain | gmail.com | Purchaser's email domain |
| R_emaildomain | anonymous.com | Recipient's email domain |
| DeviceType | mobile | Desktop or mobile |
| DeviceInfo | SM-G960U Build/R16NW | Full device fingerprint string |
| isFraud | 1 | Ground truth label (1 = confirmed fraud) |
| V1–V339 | 1.0, 0.0, ... | Vesta's proprietary engineered features (we ignore most of these) |

**What we do with it:** We ignore most V-columns (opaque, not explainable) and instead build our own 22 meaningful features from the columns above. This makes the model explainable — we can say *why* it flagged something.

---

### Feature-by-Feature Breakdown

#### Feature 1 — `TransactionAmt`

| | |
|---|---|
| **Input range** | $0.50 – $30,000+ (right-skewed, most transactions under $200) |
| **Typical legit value** | $20–$150 |
| **Typical fraud value** | $500–$5,000 (fraudsters test stolen cards with large purchases) |
| **What you enter in the UI** | The raw dollar/rupee amount of the transaction |

**Background processing:** Taken directly from the raw dataset column. No transformation — fed as-is to LightGBM, which learns its own splits (e.g. "amount > $1,200 increases fraud probability by X").

**Why useful:** On its own, amount is a weak signal — legitimate large purchases exist. The model learns it *in combination* with other features. A $5,000 transaction at 3am from a new device is critical-risk; a $5,000 transaction at 2pm from a known device for a regular customer is fine.

---

#### Feature 2 — `amt_zscore`

| | |
|---|---|
| **Input range** | Typically –2 to +10 (can go higher for extreme outliers) |
| **Typical legit value** | –1 to +1 (transaction is near the account's usual range) |
| **Typical fraud value** | +3 to +8 (transaction is far above the account's norm) |
| **What you enter in the UI** | How many standard deviations above normal this transaction is |

**Background processing:**
```
For each account, compute:
  mean_amt = average of all past transactions
  std_amt  = standard deviation of all past transactions
  amt_zscore = (this_transaction_amt - mean_amt) / std_amt
```
Done in `features.py` using a pandas `groupby` on account ID, then joining back.

**Why useful:** This personalises the amount signal. A $500 transaction for an account that normally spends $490 has zscore ≈ 0 (normal). The same $500 for an account that normally spends $12 has zscore ≈ 8 (highly anomalous). Raw amount can't capture this; z-score can.

---

#### Feature 3 — `amt_to_mean_ratio`

| | |
|---|---|
| **Input range** | 0.1 to 50+ |
| **Typical legit value** | 0.5 to 2.0 (within 2× of the usual amount) |
| **Typical fraud value** | 4.0 to 20+ (4× or more above usual) |
| **What you enter in the UI** | This transaction's amount divided by the account's average |

**Background processing:**
```
amt_to_mean_ratio = TransactionAmt / mean_amt_for_this_account
```
Computed alongside z-score in `features.py`. Whereas z-score penalises accounts with low variance, ratio is purely multiplicative — easier to explain to non-technical stakeholders ("this transaction is 7× the customer's usual spend").

**Why useful:** Complements z-score. Together they give the model two perspectives on amount anomaly. Some accounts have very consistent spending (low std) — z-score works well. Others have high variance — ratio works better.

---

#### Feature 4 — `account_tx_count`

| | |
|---|---|
| **Input range** | 1 to 500+ |
| **Typical legit value** | 30–200 (established account with history) |
| **Typical fraud value** | 1–5 (brand new account, or stolen card used for the first time) |
| **What you enter in the UI** | Total number of transactions this account has ever made |

**Background processing:**
```
account_tx_count = COUNT(*) grouped by account_id over the entire dataset
```
Joined back to each transaction row. For real-time deployment, this would be a running counter in a database.

**Why useful:** New accounts are riskier. A stolen card being used for the very first time has `account_tx_count = 1`. Fraudsters also create fake accounts — these also start at 1. An established account with 300 transactions and a consistent history is far less likely to suddenly go fraudulent on this transaction.

---

#### Feature 5 — `tx_hour`

| | |
|---|---|
| **Input range** | 0 to 23 |
| **Typical legit value** | 8 to 22 (normal waking hours) |
| **Typical fraud value** | 0 to 4 (late night / early morning) |
| **What you enter in the UI** | Hour of day the transaction happened (0 = midnight, 3 = 3am, 14 = 2pm) |

**Background processing:**
```
TransactionDT is seconds since a fixed reference point.
tx_hour = (TransactionDT // 3600) % 24
```
The raw dataset has no real timestamps — `TransactionDT` is a relative counter in seconds. We convert it to hour-of-day by dividing by 3600 (seconds per hour) and taking modulo 24.

**Why useful:** Fraudsters act when victims are asleep and unlikely to notice bank alerts. In the training data, transactions between 1–4am have significantly higher fraud rates. A $2,000 transaction at 3am is far more suspicious than the same transaction at 2pm.

---

#### Feature 6 — `tx_day_of_week`

| | |
|---|---|
| **Input range** | 0 (Monday) to 6 (Sunday) |
| **Typical legit value** | 0–4 (weekdays — people shop during the week) |
| **Typical fraud value** | 5–6 (weekends — lower bank staffing, slower fraud response) |
| **What you enter in the UI** | Day of the week (0=Mon, 1=Tue, ..., 6=Sun) |

**Background processing:**
```
tx_day_of_week = (TransactionDT // 86400) % 7
```
Same `TransactionDT` divided by 86400 (seconds per day), modulo 7.

**Why useful:** Fraud response teams are smaller on weekends. Fraudsters know this. Weekend transactions in combination with other red flags (new device, late hour, anonymous.com recipient) form a strong fraud pattern.

---

#### Feature 7 — `velocity_1h`

| | |
|---|---|
| **Input range** | 1 to 20+ |
| **Typical legit value** | 1 (most people make one transaction at a time) |
| **Typical fraud value** | 5–15 (many rapid transactions to drain a card or test it) |
| **What you enter in the UI** | Number of transactions this account made in the last 1 hour |

**Background processing:**
```
Sort transactions by time.
For each transaction T, count how many prior transactions
from the same account_id fall within [T.time - 3600s, T.time].
```
This is a rolling window count. In `features.py` it's done with a sorted merge and cumulative counting per account.

**Why useful:** Fraudsters perform **card testing** — they run many small transactions quickly to check if a stolen card works before making a big purchase. High `velocity_1h` (e.g. 8 transactions in 1 hour) is a classic fraud pattern. Legitimate customers almost never make 8 purchases in an hour.

---

#### Feature 8 — `velocity_24h`

| | |
|---|---|
| **Input range** | 1 to 50+ |
| **Typical legit value** | 1–5 (a few transactions in a day is normal) |
| **Typical fraud value** | 10–30 (sustained fraud activity over a day) |
| **What you enter in the UI** | Number of transactions in the last 24 hours |

**Background processing:** Same rolling window approach as `velocity_1h` but with a 24-hour window (86,400 seconds). Computed in the same pass through the sorted data.

**Why useful:** Captures **smurfing** — splitting a large fraudulent transfer into many smaller ones to avoid detection thresholds. If regulations require reporting transactions above ₹10,000, a smurf makes 10 × ₹9,999 transactions across 24 hours. `velocity_24h = 10` combined with `amt_velocity_24h ≈ ₹100,000` is the textbook smurfing signature.

---

#### Feature 9 — `velocity_7d`

| | |
|---|---|
| **Input range** | 1 to 200+ |
| **Typical legit value** | 5–30 (people shop a few times a week) |
| **Typical fraud value** | 50–150 (sustained campaign — fraudster running a scheme for days) |
| **What you enter in the UI** | Number of transactions in the last 7 days |

**Background processing:** Rolling window of 7 days (604,800 seconds). Gives the model a longer view of activity patterns.

**Why useful:** Some fraud is not rapid but sustained — a fraudster who gained access to an account slowly draining it over a week. High `velocity_7d` relative to the account's historical norm signals this pattern. Also useful for money mule accounts that process many transactions per week as part of a laundering chain.

---

#### Feature 10 — `amt_velocity_24h`

| | |
|---|---|
| **Input range** | $0 to $500,000+ |
| **Typical legit value** | $20–$500 (a day's worth of normal spending) |
| **Typical fraud value** | $5,000–$50,000 (large amounts moved quickly) |
| **What you enter in the UI** | Total dollar amount transacted in the last 24 hours |

**Background processing:**
```
amt_velocity_24h = SUM(TransactionAmt) for all transactions
                   from this account in the last 24 hours
```
Rolling window sum instead of rolling window count. Computed alongside the velocity count features.

**Why useful:** Captures the *scale* of recent activity, not just the count. 10 transactions of $5 each is low risk. 10 transactions of $5,000 each is critical. This feature combined with `velocity_24h` tells you both how many and how much — the combination exposes smurfing perfectly.

---

#### Feature 11 — `addr1`

| | |
|---|---|
| **Input range** | 1 to 540 (billing address area codes from the dataset) |
| **Typical legit value** | Any consistent code the customer usually uses |
| **Typical fraud value** | –1 (unknown/missing — card used with no billing address) |
| **What you enter in the UI** | Billing address area code integer (use –1 if unknown) |

**Background processing:** Taken directly from the dataset's `addr1` column, which Vesta encoded as an integer. Missing values filled with –1.

**Why useful:** A transaction with a missing billing address (`addr1 = –1`) is suspicious — legitimate online merchants usually require billing address for address verification (AVS). Fraudsters with stolen card numbers sometimes don't know the real billing address.

---

#### Feature 12 — `fraud_neighbors`

| | |
|---|---|
| **Input range** | 0 to 1,000+ |
| **Typical legit value** | 0 (device is not shared with any fraudulent accounts) |
| **Typical fraud value** | 100–532 (device is shared with hundreds of fraud accounts) |
| **What you enter in the UI** | How many fraud-confirmed accounts share this device |

**Background processing (Neo4j query):**
```cypher
MATCH (a:Account {account_id: $id})-[:USES_DEVICE]->(d:Device)
      <-[:USES_DEVICE]-(other:Account)-[:MADE]->(t:Transaction {isFraud: 1})
RETURN count(DISTINCT other) as fraud_neighbors
```
This graph query finds all accounts that share a device with the target account AND have at least one confirmed fraud transaction. The result is joined into the feature table.

**Why useful:** This is the graph's unique contribution — a feature that's impossible to compute from a single transaction row. If 532 accounts sharing your device are confirmed fraudsters, you are almost certainly part of the same fraud ring. No amount of individual transaction analysis would reveal this — it requires the graph.

---

#### Feature 13 — `shared_device_accounts`

| | |
|---|---|
| **Input range** | 1 to 1,000+ |
| **Typical legit value** | 1–3 (only your own accounts use your personal device) |
| **Typical fraud value** | 100–1,200 (one device used across hundreds of fake accounts) |
| **What you enter in the UI** | Total accounts (fraud and legit) sharing this device |

**Background processing (Neo4j query):**
```cypher
MATCH (a:Account {account_id: $id})-[:USES_DEVICE]->(d:Device)
      <-[:USES_DEVICE]-(other:Account)
RETURN count(DISTINCT other) as shared_device_accounts
```
Similar to `fraud_neighbors` but counts *all* accounts sharing the device, not just fraudulent ones.

**Why useful:** Even if none of the device-sharing accounts have been *confirmed* as fraud yet, a device shared across 500 accounts is still deeply suspicious. Legitimate users don't share their personal phone with 500 other bank accounts. This feature catches fraud rings before the fraud labels are confirmed — acting as an early warning.

---

#### Feature 14 — `device_known`

| | |
|---|---|
| **Input range** | 0 or 1 (binary) |
| **Typical legit value** | 1 (device has been seen before in the dataset) |
| **Typical fraud value** | 0 (completely new device, never seen before) |
| **What you enter in the UI** | Toggle: 1 = known device, 0 = unknown device |

**Background processing:**
```
device_known = 1 if DeviceInfo appears more than once in the full dataset
             = 0 if this is the first and only time this device string appears
```
Computed by grouping on the `DeviceInfo` column and checking count > 1.

**Why useful:** A device that appears exactly once in 590K transactions is likely either a brand-new device being used for the first time (possible) or a spoofed device fingerprint (common fraud technique — fraudsters randomise device strings to avoid detection). Combined with `is_new_device`, this gives the model two angles on device novelty.

---

#### Feature 15 — `is_new_device`

| | |
|---|---|
| **Input range** | 0 or 1 (binary) |
| **Typical legit value** | 0 (customer uses the same device they always have) |
| **Typical fraud value** | 1 (stolen card being used from the fraudster's own device) |
| **What you enter in the UI** | Toggle: 1 = first time this account used this device |

**Background processing:**
```
For each (account_id, DeviceInfo) pair:
  is_new_device = 1 if this is the first transaction
                  from this account on this device
                = 0 if the account has used this device before
```
Done by sorting transactions by time and checking whether a (account, device) pair has appeared before in the time-ordered sequence.

**Why useful:** A legitimate customer typically uses the same phone or laptop for months. If an account that has always used "MacBook Pro / macOS 14.2" suddenly makes a transaction from "SM-G960U Build/R16NW", someone else is using that account. This is the clearest signal that account credentials were stolen.

---

#### Feature 16 — `is_new_p_email`

| | |
|---|---|
| **Input range** | 0 or 1 (binary) |
| **Typical legit value** | 0 (purchaser email is the one the account always uses) |
| **Typical fraud value** | 1 (new purchaser email — fraudster used a different contact) |
| **What you enter in the UI** | Toggle: 1 = first time this purchaser email appeared on this account |

**Background processing:** Same first-occurrence logic as `is_new_device`, applied to the (account_id, P_emaildomain) pair sorted by transaction time.

**Why useful:** A real customer doesn't usually switch email providers. If an account always purchased with a `gmail.com` purchaser email and suddenly a transaction shows `P_emaildomain = yahoo.com`, someone else may have taken over the account with their own email address. This is a classic account takeover signal.

---

#### Feature 17 — `is_new_r_email`

| | |
|---|---|
| **Input range** | 0 or 1 (binary) |
| **Typical legit value** | 0 (money going to the same recipient domain as always) |
| **Typical fraud value** | 1 (money going to a new recipient domain — possibly fraudster's account) |
| **What you enter in the UI** | Toggle: 1 = first time money sent to this recipient email domain from this account |

**Background processing:** Same first-occurrence logic on (account_id, R_emaildomain).

**Why useful:** Combined with `r_email_domain = anonymous.com`, this is devastating. If an account has always sent money to `gmail.com` recipients and suddenly sends to `anonymous.com` for the first time, that's a very strong fraud signal. The "new recipient + disposable email" combination is what the SHAP chart shows as the top driver for most high-scoring transactions.

---

#### Feature 18 — `ProductCD`

| | |
|---|---|
| **Input values** | W, H, C, S, R |
| **Highest fraud rate** | W (transfer/wallet — most fraud) |
| **Lowest fraud rate** | C, S (likely card-present or service purchases) |
| **What you enter in the UI** | Select from dropdown |

**Background processing:** Taken directly from the raw `ProductCD` column. LightGBM handles it as a categorical feature — it learns which product codes correlate with fraud during training rather than us hard-coding the mapping.

**Why useful:** `ProductCD = W` (probably wallet or wire transfers) has the highest fraud rate in the dataset. Transfers are irreversible — once the money moves, the fraudster withdraws it immediately. Card-present transactions (C) are harder to do fraudulently because the physical card is needed.

---

#### Feature 19 — `card_network`

| | |
|---|---|
| **Input values** | visa, mastercard, american express, discover |
| **What you enter in the UI** | Select from dropdown |

**Background processing:** Derived from `card4` column in the raw dataset, which Vesta encoded as the card network name. Treated as categorical by LightGBM.

**Why useful:** Different card networks have different fraud prevention systems and liability rules. The model learns which networks appear more often in fraud cases from the training data. On its own this is a weak signal, but in combination with amount, time, and email domain it contributes.

---

#### Feature 20 — `card_type`

| | |
|---|---|
| **Input values** | credit, debit, charge card |
| **What you enter in the UI** | Select from dropdown |

**Background processing:** Derived from `card6` column. Categorical feature.

**Why useful:** Credit card fraud is more common than debit fraud because credit cards often have higher limits and delayed billing (victim notices later). The model learns this pattern. Also, charge cards (no preset limit) carry different fraud dynamics.

---

#### Feature 21 — `device_type`

| | |
|---|---|
| **Input values** | desktop, mobile, Unknown |
| **What you enter in the UI** | Select from dropdown |

**Background processing:** Taken directly from the `DeviceType` column. Many transactions have `Unknown` device type (the transaction was made without a browser/app — possibly via API or automated script).

**Why useful:** `Unknown` device type is a red flag — it often means the transaction was submitted programmatically, not by a human interacting with a website. Fraudsters use automated scripts to run card-testing attacks. Also, mobile vs. desktop fraud patterns differ — mobile fraud is more common in certain product categories.

---

#### Feature 22 — `p_email_domain` and `r_email_domain`

| | |
|---|---|
| **Input values** | gmail.com, yahoo.com, anonymous.com, hotmail.com, and many others |
| **Highest fraud rate** | anonymous.com (disposable email — strongest single fraud signal in the dataset) |
| **What you enter in the UI** | Select from dropdown |

**Background processing:** Taken from `P_emaildomain` and `R_emaildomain` columns. Categorical features — LightGBM learns the fraud rate associated with each domain during training. Unknown domains not in training data fall back to a default category.

**Why useful:** `anonymous.com` is a disposable email provider — you can create a temporary email address in seconds with no identity verification. Fraudsters receive money to anonymous.com addresses and immediately move it on. In the training data, `r_email_domain = anonymous.com` is the single strongest predictor of fraud. A transaction to anonymous.com is ~8× more likely to be fraud than the baseline rate.

---

### End-to-End Flow with Real Numbers

Here's what happens from the moment you click "Score Transaction" to the result appearing:

```
User inputs 22 feature values
        │
        ▼
score_transaction(features) called in risk_model/score.py
        │
        ├── Build a 1-row DataFrame with all 22 columns
        │
        ├── Cast 6 categorical columns (ProductCD, card_network, card_type,
        │   device_type, p_email_domain, r_email_domain) to pd.CategoricalDtype
        │   with exactly the category lists from training
        │   (prevents "unknown category" errors for new values)
        │
        ├── Call model.predict_proba(X)[:, 1]
        │   → Returns probability of class 1 (fraud)
        │   → e.g. 0.9214
        │
        ├── Call shap.TreeExplainer(model).shap_values(X)
        │   → Returns a vector of 22 SHAP values, one per feature
        │   → e.g. [r_email_domain: +0.96, tx_hour: +0.65, ...]
        │
        ├── Sort SHAP values by |magnitude|, take top 5
        │
        └── Return {risk_score: 0.9214, risk_tier: "critical",
                    top_features: [...top 5 SHAP drivers...]}
```

Total time from input to output: **< 200ms** (the model is loaded once and cached in memory).

---

### What Happens During SAR Generation (Background)

```
User selects ACC_15063, clicks "Generate SAR"
        │
        ▼
Step 1 — Neo4j query (< 1 second)
  Pull: all transactions, total amount, transaction count
  Pull: devices this account uses
  Pull: other accounts sharing those devices + their fraud flags
        │
        ▼
Step 2 — LightGBM scoring (< 200ms)
  Score the highest-value transaction to get risk_score + SHAP explanation
        │
        ▼
Step 3 — ChromaDB retrieval (~3 seconds, includes model load)
  Embed the query: "suspicious activity structuring PMLA STR filing obligation"
  Search 85 regulatory chunks by cosine similarity
  Return top 5 most relevant regulation excerpts
        │
        ▼
Step 4 — Claude API call via AWS Bedrock (~20 seconds)
  Send: account data + transaction history + SHAP explanation +
        fraud ring summary + 5 regulatory excerpts
  Receive: 800-word SAR with 7 sections, citing exact regulation text
        │
        ▼
Output displayed in UI, available for download as .txt
```

**Total: ~25–35 seconds.** The bottleneck is the Bedrock API call — Claude takes time to generate 800 carefully structured words. This is intentional: the output quality (complete, cited, structured SAR) justifies the wait vs. a 2–4 hour manual effort.

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
