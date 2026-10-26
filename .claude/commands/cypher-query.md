Run a Cypher query against the local Neo4j instance and return results in a readable format.

## Usage
/cypher-query <your Cypher query here>

## Steps
1. If no query is provided in $ARGUMENTS, ask the user for the Cypher query they want to run.
2. Check that Neo4j is running: `docker ps | grep fraud-graph`. If it's not running, remind the user to start it with the command from CLAUDE.md.
3. Run the query using the neo4j Python driver:
```bash
python3 -c "
from neo4j import GraphDatabase
import os, json
from dotenv import load_dotenv
load_dotenv()
uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
pwd = os.getenv('NEO4J_PASSWORD', 'your_password_here')
driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as s:
    result = s.run('''$ARGUMENTS''')
    for r in result:
        print(dict(r))
driver.close()
"
```
4. If the query fails, show the error and suggest a fix.
5. Format the output as a readable table or list — not raw Python dicts.

## Notes
- Connection details are loaded from `.env` (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD).
- For read queries (MATCH) use the default database. For write queries (CREATE/MERGE), confirm with the user first.
- If the knowledge_graph/ folder has schema files, check them to suggest correct node labels and relationship types.
