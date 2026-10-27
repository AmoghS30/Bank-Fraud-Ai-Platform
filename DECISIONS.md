# Design Decisions Log

One line per decision. Format: `[Stage N] Decision — Reason`.

---

<!-- Add entries below as you make decisions during implementation -->

[Stage 0] Using AWS Bedrock bearer token auth (AWS_BEARER_TOKEN_BEDROCK) instead of IAM access key + secret — simpler single-key auth launched July 2025, long-term key generated from AWS Bedrock console
[Stage 0] Using boto3 converse API for Bedrock calls instead of AnthropicBedrock SDK — AnthropicBedrock uses SigV4 signing and does not support bearer token auth; boto3 picks up AWS_BEARER_TOKEN_BEDROCK automatically
[Stage 0] AWS region: ap-south-1 (Mumbai) — user's Bedrock account region; using in.anthropic.claude-sonnet-5 inference profile
[Stage 0] Neo4j running as Docker named volume (fraud-graph-data) instead of bind mount — macOS Docker Desktop permission issue prevents host directory bind mounts

