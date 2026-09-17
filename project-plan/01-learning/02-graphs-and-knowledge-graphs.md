# 2. Graphs & Knowledge Graphs

## Why this matters for the project

Objective 1 of the mini-project is literally "build a unified knowledge graph
that links transaction, KYC and behavioural data." This is the foundational
data structure everything else sits on — the risk-scoring model (Stage 2)
queries it for context, and the compliance assistant (Stage 4) cites entities
from it. If you don't understand graph modelling, you'll build a knowledge
graph that's really just a relational database with extra steps, and it
won't reveal the hidden fraud-ring connections that are the whole point.

## Core concepts to learn

- **Nodes, edges, properties, labels**: the basic vocabulary of a property
  graph (as opposed to a relational table or a plain triple-store RDF graph).
- **Why graphs beat tables for this problem**: understand *concretely* why
  "find all accounts within 2 hops of a flagged phone number" is a slow,
  ugly multi-JOIN in SQL but a trivial traversal in a graph database. Try
  writing the SQL query for that yourself once — the pain is the lesson.
- **Graph traversal & pathfinding**: breadth-first search, shortest path,
  and why these map directly to "how many accounts share this device
  fingerprint" or "is there a path connecting these two flagged accounts."
- **Graph schema design for this domain**: what should be a node vs. an edge
  vs. a property? (e.g. is "phone number" a node, or a property on Account?
  For this project it should almost always be a **node**, because you need
  to query "which other accounts share this phone number" — if it's just a
  property, you can't traverse it efficiently.)
- **Cypher query language** (Neo4j's query language): enough to write basic
  `MATCH`, `CREATE`, `WHERE`, and multi-hop pattern queries.
- **Centrality and community detection basics**: degree centrality (which
  nodes have unusually many connections — a red flag for a hub account in a
  fraud ring) and simple community detection (clustering accounts that are
  more connected to each other than to the rest of the graph — this is
  literally how you'll surface a "fraud ring" for Stage 3/stretch work).

## Recommended resources (free)

- **Neo4j GraphAcademy — "Neo4j Fundamentals" course**:
  https://graphacademy.neo4j.com/courses/neo4j-fundamentals/ — free,
  interactive, and directly teaches the tool you'll use in Stage 1. Do this
  one in full; it's short (~2 hours) and hands-on.
- **Neo4j GraphAcademy — "Cypher Fundamentals"**:
  https://graphacademy.neo4j.com/courses/cypher-fundamentals/ — do this
  right after. You'll be writing real Cypher queries within a day.
- **Neo4j's own fraud-detection use-case guide**:
  https://neo4j.com/use-cases/fraud-detection/ — short, practical, and
  aligned almost exactly with what you're building (shared identifiers,
  fraud rings, first-party vs. third-party fraud patterns).
- **"Graph Algorithms" (free O'Reilly ebook by Needham & Hodler, sponsored by
  Neo4j)**: https://neo4j.com/graph-algorithms-book/ — read chapters on
  pathfinding and community detection only; skip the rest for now.

## Checkpoint

> "Design a graph schema (nodes, edges, key properties) for: an Account, a
> Transaction, a Device, a Phone Number, and a KYC Document. Explain which of
> these you'd model as nodes vs. properties, and why."

If you can sketch that on paper and justify each choice, move to GNNs.
