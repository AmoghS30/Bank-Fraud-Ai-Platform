#!/bin/bash
set -e

DUMP_FILE="/startup/neo4j.dump"
RESTORE_FLAG="/data/.restored"

if [ ! -f "$RESTORE_FLAG" ] && [ -f "$DUMP_FILE" ]; then
    echo "=== First boot: restoring Neo4j database from dump ==="
    neo4j-admin database load neo4j --from-path=/startup/ --overwrite-destination=true
    touch "$RESTORE_FLAG"
    echo "=== Restore complete ==="
fi

exec /startup/docker-entrypoint.sh neo4j
