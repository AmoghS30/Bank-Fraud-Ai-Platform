FROM neo4j:5

# Load the database dump at build time — no shell script needed at runtime.
# neo4j-admin runs fine here because no Neo4j process is running during build.
COPY neo4j_seed/neo4j.dump /tmp/neo4j.dump
RUN neo4j-admin database load neo4j --from-path=/tmp/ --overwrite-destination=true \
    && rm /tmp/neo4j.dump
