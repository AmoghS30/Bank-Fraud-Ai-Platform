#!/bin/bash
# Run this once after cloning the repo on a new machine.
# It installs MCP servers and sets up the Python environment.

set -e

echo "=== Bank Fraud AI Platform — New Machine Setup ==="

# 1. Check prerequisites
echo ""
echo "Checking prerequisites..."
command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js not found. Install from https://nodejs.org"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: Python 3 not found."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker not found. Install from https://docker.com"; exit 1; }
command -v claude >/dev/null 2>&1 || { echo "ERROR: Claude Code CLI not found. Install from https://claude.ai/code"; exit 1; }
echo "All prerequisites found."

# 2. Copy .env template
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "Created .env from .env.example — fill in your secrets before running anything."
else
  echo ".env already exists, skipping."
fi

# 3. Python virtual environment
echo ""
echo "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
  echo "Python dependencies installed."
else
  echo "No requirements.txt yet (add packages as you build each stage)."
fi

# 4. MCP servers — installed at project scope via .claude/settings.json
# The settings.json in this repo already defines the MCP servers.
# npx will pull them on first use. But install playwright browsers now:
echo ""
echo "Installing Playwright browsers..."
npx playwright install chromium 2>/dev/null || echo "Playwright install skipped (run manually if needed: npx playwright install)"

# 5. Neo4j via Docker
echo ""
echo "Starting Neo4j..."
if docker ps | grep -q fraud-graph; then
  echo "Neo4j container already running."
elif docker ps -a | grep -q fraud-graph; then
  docker start fraud-graph
  echo "Neo4j container restarted."
else
  source .env 2>/dev/null || true
  docker run -d --name fraud-graph \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH="neo4j/${NEO4J_PASSWORD:-changeme}" \
    -v "$(pwd)/neo4j_data:/data" \
    neo4j:5
  echo "Neo4j container created and started."
fi
echo "Neo4j UI: http://localhost:7474"

echo ""
echo "=== Setup complete ==="
echo "Next: fill in .env with your API keys, then open Claude Code in this directory."
echo "Read PROGRESS.md to see where the project is at, and CLAUDE.md for full context."
