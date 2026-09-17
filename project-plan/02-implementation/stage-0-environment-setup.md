# Stage 0 — Environment Setup

## Prerequisites from Phase A

- File 07 (Systems & Tech Stack) checkpoint passed: Docker, Python, and Neo4j
  access confirmed working.

## Goal / deliverable

A reproducible development environment, a real git repository with a sane
structure, and the raw datasets downloaded and sitting on disk — so every
later stage starts from a known-good baseline instead of "works on my
machine, sort of."

## Tasks

1. **Initialize git**, if this project isn't already tracked:
   ```bash
   git init
   ```
   Add a `.gitignore` covering at least: `data/raw/`, `data/processed/`,
   `*.pyc`, `__pycache__/`, `.env`, `venv/` or `.venv/`, `node_modules/`,
   any local Neo4j data directories, and model checkpoint files over a few
   MB (use Git LFS or just don't commit large binaries).

2. **Create the folder structure** listed in `02-implementation/README.md`.

3. **Set up a Python environment**. Use a virtual environment
   (`python -m venv .venv`) or `conda`/`uv` — whichever you're already
   comfortable with. Pin a `requirements.txt` (or `pyproject.toml`) as you
   add dependencies stage by stage, rather than installing everything
   up front — you'll actually know why each package is there.

4. **Get Neo4j running.** Two options:
   - **Neo4j Desktop** (easiest to start, GUI-based): download from
     https://neo4j.com/download/, create a local DBMS, start it.
   - **Docker** (better for reproducibility, recommended once comfortable):
     ```bash
     docker run -d --name fraud-graph \
       -p 7474:7474 -p 7687:7687 \
       -e NEO4J_AUTH=neo4j/your_password_here \
       -v $(pwd)/neo4j_data:/data \
       neo4j:5
     ```
   Confirm you can open `http://localhost:7474` and log in.

5. **Get an Anthropic API key** (console.anthropic.com) for Stage 4 later.
   Store it in a `.env` file (never commit this — confirm it's in
   `.gitignore`), load via `python-dotenv`.

6. **Download the datasets** you'll use in Stage 1/2 (see that stage for
   exact choices) into `data/raw/`. Don't process anything yet — just get
   the files onto disk so Stage 1 isn't blocked on a slow download.

7. **Start a `DECISIONS.md` file** at the repo root (or in `project-plan/`)
   — a running log of design decisions. First entry: why you picked the
   datasets you picked, and any tool substitutions from the original tech
   stack (e.g. "using Chroma instead of Pinecone/Weaviate — free, local,
   sufficient for a mini-project's data volume").

## Definition of done

- [ ] `git log` shows at least one commit with the initial repo structure.
- [ ] `docker ps` (or Neo4j Desktop) shows Neo4j running and reachable at
      `localhost:7474`, and you can log in.
- [ ] A Python virtual environment exists and activates cleanly.
- [ ] `.env` holds your Anthropic API key and is gitignored (verify with
      `git status` — it should not appear as trackable).
- [ ] Raw dataset files are present under `data/raw/`.
- [ ] `DECISIONS.md` exists with at least one real entry.

## Common pitfalls

- **Committing secrets.** Double-check `.env` is actually ignored before
  your first commit that touches it — `git status` before every commit,
  always, not just here.
- **Skipping the virtual environment** "just for now" and then fighting
  dependency conflicts three stages later. Do it now, it's five minutes.
- **Downloading a dataset and immediately starting to clean/transform it
  in Stage 0.** Keep this stage boring and infrastructural — data work
  belongs in Stage 1.
