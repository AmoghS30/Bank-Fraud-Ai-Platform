Generate a Suspicious Activity Report (SAR) draft for a flagged case using the RAG pipeline and Claude API.

## Usage
/sar-draft <case_id or account_id>

## Steps
1. Parse $ARGUMENTS as a case ID or account ID.
2. Pull the case's transaction history from Neo4j:
```bash
python3 -c "
from neo4j import GraphDatabase
import os; from dotenv import load_dotenv; load_dotenv()
driver = GraphDatabase.driver(os.getenv('NEO4J_URI','bolt://localhost:7687'), auth=(os.getenv('NEO4J_USER','neo4j'), os.getenv('NEO4J_PASSWORD')))
with driver.session() as s:
    r = s.run('MATCH (a:Account {id: \$id})-[t:TRANSFERRED]->(b) RETURN a, t, b ORDER BY t.timestamp DESC LIMIT 50', id='$ARGUMENTS')
    for rec in r: print(dict(rec))
driver.close()
"
```
3. Run the SAR generation pipeline:
```bash
python3 compliance_assistant/generate_sar.py --case-id '$ARGUMENTS'
```
4. If `generate_sar.py` doesn't exist yet (Stage 4 not complete), tell the user and stop.
5. Present the generated SAR draft with these sections clearly labelled:
   - **Subject information** (account holder, account details)
   - **Suspicious activity description** (what happened, dates, amounts)
   - **Regulatory basis** (which PMLA / RBI circular section applies — sourced from RAG retrieval)
   - **Supporting evidence** (transaction list, graph connections)
   - **Recommended action** (freeze, file with FIU-IND, escalate)
6. Ask the user: "Does this draft look accurate? Should I adjust the regulatory citations or narrative tone?"

## Notes
- Prerequisites: Stage 1 (Neo4j populated) and Stage 4 (RAG pipeline + compliance_assistant/) complete.
- The RAG retrieval pulls from the regulatory document index in `compliance_assistant/vector_store/`. If that index is empty, remind the user to run the document ingestion script first.
- Never fabricate regulatory citations. If RAG retrieval returns nothing relevant, say so explicitly rather than inventing a citation.
