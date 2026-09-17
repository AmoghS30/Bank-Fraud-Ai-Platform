# Stage 4 — Compliance Assistant (RAG + SAR Generation)

## Prerequisites from Phase A

- File 05 (LLMs, RAG & Compliance AI) — full checkpoint passed.
- File 06 (Explainable AI) — the "grounding & citation" overlap.

## Goal / deliverable

**Objective 3, fully satisfied**: given a flagged case (account + its
supporting evidence from Stages 1–2), the system retrieves relevant
regulatory text and generates a structured, cited SAR draft using Claude.

## Tasks

1. **Assemble a small regulatory document corpus.** You do not need every
   RBI circular ever published — 5–10 representative documents is enough
   for a mini-project demo:
   - PMLA 2002 (Prevention of Money Laundering Act) — key sections on
     reporting obligations.
   - RBI Master Direction on KYC (already skimmed in file 01).
   - FIU-IND's published SAR reporting format/guidance, if publicly
     available.
   - A couple of FATF typology reports (for context on smurfing/layering
     patterns, useful for the "does this qualify as X" Q&A feature).
   Save these as PDFs/text files in `compliance_assistant/documents/`, and
   cite them properly in your report (public regulatory text, not
   proprietary).

2. **Build the ingestion pipeline**:
   - Load documents (PDF/text loaders).
   - Chunk them sensibly — respect section boundaries where possible rather
     than blind fixed-size splitting, since regulatory clauses shouldn't be
     cut in half.
   - Embed each chunk (Claude doesn't have a first-party embeddings API as
     of this writing — use a solid open embeddings model, e.g. a
     `sentence-transformers` model like `all-MiniLM-L6-v2`, or another
     embeddings provider; note this substitution in `DECISIONS.md`).
   - Store embeddings in **Chroma** (recommended for a mini-project — free,
     local, no infra to manage) rather than Pinecone/Weaviate, unless you
     specifically want the cloud-hosted-vector-DB experience for your
     resume/portfolio. Note this substitution too if you make it.

3. **Build the retrieval step**: given a query (either an analyst's
   question, or an internally-constructed query like "SAR filing
   requirements for structuring/smurfing"), retrieve the top-k most relevant
   chunks.

4. **Build the generation step** with the Claude API:
   - System prompt that instructs the model to only make claims it can
     support from the retrieved context, and to cite the source document
     for each claim.
   - Insert the case's data (from Stage 1's graph + Stage 2's risk score and
     SHAP explanation) plus the retrieved regulatory chunks into the prompt.
   - Request a structured SAR draft: customer/account details, transaction
     narrative, suspicious indicators (tie back to the SHAP explanation and
     graph connections), regulatory basis (tie back to retrieved chunks),
     recommended action.
   - Use Claude's structured output support (or a strict prompt template) so
     the output reliably has these sections every time.

5. **Build the analyst Q&A feature**: a simple function/endpoint that takes
   a natural-language question ("does this qualify as smurfing under
   PMLA 2002?") and returns a grounded, cited answer using the same
   retrieval + generation pipeline.

6. **Verify grounding, don't just trust it.** For a handful of test cases,
   manually check that every citation in the generated SAR actually
   corresponds to real retrieved text (not a hallucinated section number).
   This manual verification step **is** your explainability/quality
   evidence for this component — document a few examples in your report.

## Definition of done

- [ ] A small regulatory document corpus is ingested, chunked, embedded, and
      stored in a vector database.
- [ ] Given a flagged case's data, the pipeline retrieves relevant chunks
      and generates a structured SAR draft with Claude.
- [ ] The SAR draft cites specific source documents/sections for its claims,
      and you've manually verified at least 3 generated drafts against the
      actual source text (no hallucinated citations).
- [ ] The Q&A feature answers at least 2–3 test compliance questions with
      grounded, cited responses.
- [ ] `DECISIONS.md` documents any substitutions from the original tech
      stack (embeddings model choice, Chroma vs. Pinecone/Weaviate).

## Common pitfalls

- **Trusting the LLM's citations without checking them.** LLMs can produce
  confident-looking citations to documents/sections that don't say what's
  claimed, even when retrieval worked correctly — the model can still
  misread or over-extend the retrieved text. Spot-check, always.
- **Chunking too aggressively** (e.g. fixed 200-character chunks with no
  regard for structure), splitting a single regulatory requirement across
  two chunks so neither retrieval result has the full rule.
- **Not using real regulatory text at all** and just prompting Claude from
  its training knowledge — this defeats the entire purpose of the RAG
  architecture you're being graded on. If you find yourself skipping the
  retrieval step "just to get something working," that something is not
  Objective 3.
