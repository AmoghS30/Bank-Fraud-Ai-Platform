Pull an account's subgraph from Neo4j and explain all connections in plain English — useful for understanding why an account was flagged.

## Usage
/graph-explain <account_id>

## Steps
1. Parse $ARGUMENTS as an account ID.
2. Query the local subgraph (2 hops) from Neo4j:
```bash
python3 -c "
from neo4j import GraphDatabase
import os, json; from dotenv import load_dotenv; load_dotenv()
driver = GraphDatabase.driver(os.getenv('NEO4J_URI','bolt://localhost:7687'), auth=(os.getenv('NEO4J_USER','neo4j'), os.getenv('NEO4J_PASSWORD')))
with driver.session() as s:
    r = s.run('''
        MATCH (a:Account {id: \$id})-[r1]-(n1)-[r2]-(n2)
        RETURN a, r1, n1, r2, n2
        LIMIT 100
    ''', id='$ARGUMENTS')
    rows = [{'r1': dict(rec['r1']), 'n1': dict(rec['n1']), 'r2': dict(rec['r2']), 'n2': dict(rec['n2'])} for rec in r]
    print(json.dumps(rows, indent=2, default=str))
driver.close()
"
```
3. Also pull any fraud flags on connected nodes:
```bash
python3 -c "
from neo4j import GraphDatabase
import os; from dotenv import load_dotenv; load_dotenv()
driver = GraphDatabase.driver(os.getenv('NEO4J_URI','bolt://localhost:7687'), auth=(os.getenv('NEO4J_USER','neo4j'), os.getenv('NEO4J_PASSWORD')))
with driver.session() as s:
    r = s.run('''
        MATCH (a:Account {id: \$id})-[*1..2]-(connected)
        WHERE connected.flagged = true OR connected.confirmed_fraud = true
        RETURN connected
    ''', id='$ARGUMENTS')
    for rec in r: print(dict(rec['connected']))
driver.close()
"
```
4. Synthesise the graph data into a plain English explanation covering:
   - **What is this account directly connected to?** (shared phone numbers, devices, IP addresses, recipients)
   - **What are those connections connected to?** (second-hop suspicious nodes)
   - **How many previously flagged or confirmed fraud nodes are within 2 hops?**
   - **Does this match a known fraud pattern?** (smurfing network, money mule cluster, account takeover indicators)
5. End with a one-line verdict: **Low / Medium / High / Critical network-level risk** and the single strongest reason.

## Notes
- Prerequisites: Stage 1 (Neo4j populated with relationships) complete.
- If the account ID doesn't exist in the graph, say so — don't return empty results silently.
- For large networks (100+ nodes), summarise by cluster rather than listing every node individually.
- If the GNN model exists (Stage 3 complete), also run: `python3 gnn_model/predict.py --account '$ARGUMENTS'` and include the GNN risk score alongside the plain English explanation.
