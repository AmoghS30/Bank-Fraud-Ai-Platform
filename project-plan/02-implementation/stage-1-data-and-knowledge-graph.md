# Stage 1 — Data & Knowledge Graph

## Prerequisites from Phase A

- File 01 (Fraud & AML Fundamentals)
- File 02 (Graphs & Knowledge Graphs) — schema design, Cypher basics
- File 07's Neo4j checkpoint

## Goal / deliverable

**Objective 1, fully satisfied**: a populated Neo4j knowledge graph linking
transaction, KYC-like, and behavioural data for a realistic set of accounts,
queryable to answer questions like "which accounts share this device or
phone number" and "what does this account's transaction network look like."

## Choosing your dataset

You will not get real bank data — use public data and be upfront about that
in your report. Recommended:

- **Primary**: **PaySim** (https://www.kaggle.com/datasets/ealaxi/paysim1)
  — synthetic mobile-money transactions explicitly designed to include
  fraud patterns, with sender/receiver account IDs. Good graph structure
  out of the box (transactions naturally form edges between accounts).
- **Secondary/supplement**: **IEEE-CIS Fraud Detection**
  (https://www.kaggle.com/c/ieee-fraud-detection/data) — has richer
  device/identity columns (`DeviceType`, `DeviceInfo`, email domains) you
  can use to construct the "shared device" and "shared identifier" edges
  that make the graph interesting. This is what makes fraud rings visible.
- You will likely need to **synthesize a light KYC layer** (phone number,
  registered address, ID document hash) yourself, since public datasets
  don't include this for privacy reasons. This is fine — document it as a
  simulated layer in your report. Keep it simple: assign each account a
  synthetic phone number and device ID, and deliberately inject a handful of
  "fraud ring" cases where multiple accounts share the same phone/device —
  this is what your graph and your demo will showcase finding.

## Graph schema (starting point — adjust as you go)

**Nodes:**
- `Account` (properties: account_id, opened_date, account_type)
- `Transaction` (properties: transaction_id, amount, timestamp, type)
- `Device` (properties: device_id, device_type)
- `PhoneNumber` (properties: phone_number)
- `Merchant` / `RecipientAccount` (if distinguishable from sender accounts)

**Relationships:**
- `(:Account)-[:SENT]->(:Transaction)-[:TO]->(:Account)`
- `(:Account)-[:USES_DEVICE]->(:Device)`
- `(:Account)-[:REGISTERED_WITH]->(:PhoneNumber)`
- `(:Account)-[:FLAGGED_AS {reason, date}]->(:FraudCase)` (optional, for
  tracking confirmed/suspected cases)

Revisit file 02's checkpoint exercise here — this schema is the answer to
that exercise, applied for real.

## Tasks

1. **Load and clean** the chosen dataset(s) with pandas: consistent account
   ID formats, parsed timestamps, dropped/flagged obviously broken rows.
2. **Design the final schema** (adjust the starting point above based on
   what your specific dataset actually has).
3. **Write a loading script** (`knowledge_graph/load_graph.py`) using the
   `neo4j` Python driver, or the Cypher `LOAD CSV` command for bulk loads
   if your dataset is large. Use `MERGE` (not `CREATE`) for entities so
   re-running the script is idempotent.
4. **Inject synthetic shared-identifier fraud rings**: pick a handful of
   otherwise-independent accounts and connect them via a shared phone number
   or device, on purpose, so you have known ground truth to demo detection
   against later.
5. **Write and save 5–10 example Cypher queries** that answer real
   investigative questions, e.g.:
   ```cypher
   // accounts sharing a device with a flagged account
   MATCH (flagged:Account {is_flagged: true})-[:USES_DEVICE]->(d:Device)<-[:USES_DEVICE]-(other:Account)
   WHERE other <> flagged
   RETURN other.account_id, d.device_id
   ```
   ```cypher
   // shortest path between two accounts
   MATCH p = shortestPath((a:Account {account_id: $id1})-[*..6]-(b:Account {account_id: $id2}))
   RETURN p
   ```
6. **Sanity-check the graph visually** in the Neo4j Browser — run a query
   that returns a small connected subgraph and confirm it renders sensibly
   (no orphan nodes that should be connected, no accidental duplicate nodes
   from inconsistent ID formatting — a very common bug).

## Definition of done

- [ ] Neo4j contains real (or realistically synthetic) Account, Transaction,
      Device, and PhoneNumber nodes with correct relationships.
- [ ] At least one deliberately-constructed "fraud ring" (shared
      phone/device across ostensibly unrelated accounts) exists and is
      findable by a Cypher query.
- [ ] A saved set of Cypher queries in `knowledge_graph/queries.cypher`
      demonstrates multi-hop traversal and shortest-path queries.
- [ ] The loading script is idempotent — running it twice does not create
      duplicate nodes (verify with a `MATCH (n) RETURN count(n)` before/after
      a second run).
- [ ] You can explain, for any node/edge type in your schema, why it's
      modeled as a node vs. a property (tie back to file 02's checkpoint).

## Common pitfalls

- **Inconsistent ID formatting** creating duplicate nodes (e.g. `"1001"`
  vs `1001` vs `"ACC-1001"`). Normalize IDs before loading, always.
- **Modeling everything as properties on Account** because it's easier —
  this defeats the entire point of a graph. If you can't write a 2-hop
  traversal query, your schema is too flat.
- **No ground-truth fraud rings to demo against.** Public datasets often
  have "is_fraud" labels but not the *reason* two accounts are linked. Build
  that in yourself (task 4) or your Stage 3/demo will have nothing
  interesting to show.
