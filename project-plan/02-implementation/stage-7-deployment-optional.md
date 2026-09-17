# Stage 7 — Deployment (Optional / Stretch)

## Prerequisites

- Stages 0–6 complete. Do not start this unless everything above is solid —
  deployment polish on a shaky core is wasted effort for a mini-project
  review, where what matters is the working demo and the results, not
  whether it's technically "in the cloud."

## Goal / deliverable

A containerized version of the system that runs with a single command,
demonstrating the "Docker + Kubernetes" line item from your tech-stack
slide — at a scope appropriate to a mini-project (Docker Compose is
sufficient; full Kubernetes is almost certainly overkill unless you have
specific reasons to want that experience).

## Tasks (if you proceed)

1. **Write a `docker-compose.yml`** that brings up:
   - Neo4j (with a volume for persistence)
   - Chroma (or your chosen vector DB)
   - The FastAPI backend
   - The React frontend (served as a static build, or via its dev server for
     simplicity)
2. **Externalize configuration** (API keys, DB URLs) via environment
   variables / a `.env` file read by Compose, not hardcoded.
3. **Confirm a clean `docker compose up` brings the whole system to a
   working state** from nothing (empty volumes) through your seed/loading
   scripts.
4. **(Only if genuinely useful for you)** experiment with a basic
   Kubernetes manifest or Helm chart translating the same services — but
   treat this as personal skill-building, not a project requirement. It adds
   real value to a portfolio; it adds close to zero value to a mini-project
   grade beyond what Docker Compose already demonstrates.

## Definition of done

- [ ] `docker compose up` (from a clean state) brings up all services.
- [ ] Environment variables are used for all secrets/config — no hardcoded
      API keys or passwords in the compose file or code.
- [ ] A short `DEPLOYMENT.md` explains how to run the whole stack from
      scratch, for anyone (a reviewer, a teammate) to reproduce.

## Common pitfalls

- **Spending review-week time on Kubernetes manifests instead of on Stage 6
  validation.** Prioritize correctly — this stage is explicitly the last
  and most skippable one for a reason.
- **Hardcoding secrets into the compose file** "temporarily" and then
  forgetting before a commit — check `git status` before every commit, as
  always.
