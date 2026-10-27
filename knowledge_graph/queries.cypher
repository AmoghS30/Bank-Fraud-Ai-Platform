// ============================================================
// Stage 1 — Investigative Cypher Queries
// Run these in the Neo4j Browser (http://localhost:7474)
// or via /cypher-query skill
// ============================================================


// --- 1. Accounts sharing a device with a flagged account ---
// Core fraud ring detection query.
// Finds accounts that used the same physical device as a known fraud account.
MATCH (fraud:Account)-[:MADE]->(t:Transaction {is_fraud: true})
MATCH (fraud)-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other:Account)
WHERE other <> fraud
RETURN fraud.account_id AS fraud_account,
       d.device_info    AS shared_device,
       other.account_id AS linked_account
LIMIT 50;


// --- 2. Devices used by more than one account ---
// High-value fraud signal: one device fingerprint → multiple accounts = probable fraud ring.
MATCH (d:Device)<-[:USES_DEVICE]-(a:Account)
WITH d, count(a) AS account_count, collect(a.account_id) AS accounts
WHERE account_count > 1
RETURN d.device_info  AS device,
       account_count,
       accounts
ORDER BY account_count DESC
LIMIT 20;


// --- 3. Shortest path between two accounts ---
// Useful during investigation to see how two suspects are connected.
// Replace $id1 and $id2 with actual account IDs.
MATCH p = shortestPath(
  (a:Account {account_id: $id1})-[*..6]-(b:Account {account_id: $id2})
)
RETURN p;


// --- 4. Full subgraph around a flagged account (2 hops) ---
// Used by /graph-explain skill and the dashboard network view.
MATCH (a:Account {account_id: $account_id})-[r1]-(n1)-[r2]-(n2)
RETURN a, r1, n1, r2, n2
LIMIT 100;


// --- 5. Accounts sending to the same recipient email domain ---
// Layering pattern: multiple accounts funnelling funds to the same destination domain.
MATCH (a:Account)-[:MADE]->(t:Transaction)-[:TO_EMAIL]->(e:EmailDomain)
WITH e, count(DISTINCT a) AS sender_count, collect(DISTINCT a.account_id) AS senders
WHERE sender_count > 3
RETURN e.domain    AS recipient_domain,
       sender_count,
       senders
ORDER BY sender_count DESC
LIMIT 20;


// --- 6. Fraud transactions with their account and device context ---
// Quick overview of confirmed fraud cases with full context.
MATCH (a:Account)-[:MADE]->(t:Transaction {is_fraud: true})
OPTIONAL MATCH (a)-[:USES_DEVICE]->(d:Device)
OPTIONAL MATCH (t)-[:TO_EMAIL]->(e:EmailDomain)
RETURN a.account_id  AS account,
       t.tx_id        AS transaction_id,
       t.amount       AS amount,
       t.dt           AS timestamp,
       d.device_info  AS device,
       e.domain       AS recipient_domain
ORDER BY t.amount DESC
LIMIT 25;


// --- 7. Accounts with the most fraud transactions ---
// Identifies highest-risk accounts for investigation prioritisation.
MATCH (a:Account)-[:MADE]->(t:Transaction {is_fraud: true})
WITH a, count(t) AS fraud_tx_count, sum(t.amount) AS total_fraud_amount
RETURN a.account_id   AS account,
       fraud_tx_count,
       total_fraud_amount
ORDER BY fraud_tx_count DESC
LIMIT 20;


// --- 8. Node and relationship counts (sanity check / idempotency verification) ---
MATCH (a:Account) WITH count(a) AS accounts
MATCH (t:Transaction) WITH accounts, count(t) AS transactions
MATCH (d:Device) WITH accounts, transactions, count(d) AS devices
MATCH (e:EmailDomain) WITH accounts, transactions, devices, count(e) AS email_domains
RETURN accounts, transactions, devices, email_domains;
