# Design Decisions Log

One line per decision. Format: `[Stage N] Decision — Reason`.

---

<!-- Add entries below as you make decisions during implementation -->

[Stage 0] Using AWS Bedrock bearer token auth (AWS_BEARER_TOKEN_BEDROCK) instead of IAM access key + secret — simpler single-key auth launched July 2025, long-term key generated from AWS Bedrock console
[Stage 0] Using boto3 converse API for Bedrock calls instead of AnthropicBedrock SDK — AnthropicBedrock uses SigV4 signing and does not support bearer token auth; boto3 picks up AWS_BEARER_TOKEN_BEDROCK automatically
[Stage 0] AWS region: ap-south-1 (Mumbai) — user's Bedrock account region; using in.anthropic.claude-sonnet-5 inference profile
[Stage 0] Neo4j running as Docker named volume (fraud-graph-data) instead of bind mount — macOS Docker Desktop permission issue prevents host directory bind mounts
[Stage 1] Primary dataset: IEEE-CIS Fraud Detection (Kaggle) — 590,540 real transactions, 3.5% fraud rate, device + identity layer; PaySim reserved for Stage 2 risk model training only
[Stage 1] Account proxy: card1 (card sub-bin) prefixed as ACC_{card1} — best single-column cardholder proxy in IEEE-CIS; imperfect but standard practice for this dataset
[Stage 1] DeviceInfo filter: only keep strings containing "Build/" — these are specific Android hardware fingerprints (e.g. "SM-G950U Build/NRD90M"); generic strings like "Windows", "MacOS", "iOS Device" are shared by thousands of accounts and produce meaningless fraud-ring connections; 975 specific devices remain
[Stage 1] Batch size 500 for Neo4j loading — balances memory and throughput; email domain edges in separate Cypher query to avoid WITH clause complexity with optional matches

