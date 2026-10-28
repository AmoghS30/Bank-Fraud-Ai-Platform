FROM neo4j:5

COPY neo4j_seed/neo4j.dump /startup/neo4j.dump
COPY neo4j_seed/restore-entrypoint.sh /startup/restore-entrypoint.sh
RUN chmod +x /startup/restore-entrypoint.sh

ENTRYPOINT ["/startup/restore-entrypoint.sh"]
