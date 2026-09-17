# 5. LLMs, RAG & Compliance AI

## Why this matters for the project

This is Objective 3: "automate generation of a compliant SAR draft from
flagged cases using a RAG-grounded LLM." This is the piece most people get
wrong by skipping straight to "just call the OpenAI/Claude API with a
prompt" — which produces plausible-sounding but ungrounded, potentially
fabricated regulatory text. RAG exists specifically to fix that failure mode,
and understanding *why* it's needed (not just how to wire up LangChain) is
what will make this component defensible in a review.

## Core concepts to learn

- **How an LLM actually generates text**: at a conceptual level — next-token
  prediction conditioned on everything in its context window, with no
  built-in mechanism to "look things up." This is the root cause of
  hallucination and why an LLM asked "what does PMLA Section 12 require?"
  might confidently invent a plausible-sounding but wrong answer.
- **Context window & prompting**: how to structure a prompt with system
  instructions, retrieved context, and the specific case data, so the model
  reliably produces a structured output (this matters a lot for a SAR
  template, which has required fields).
- **Embeddings & semantic search**: how text gets converted into vectors
  such that "similar meaning" text ends up close together in vector space,
  and how a vector database (Pinecone/Weaviate, or a simpler local option —
  see Stage 4) finds the most relevant regulatory document chunks for a
  given query.
- **RAG pipeline anatomy**: document chunking → embedding → vector storage
  → similarity retrieval at query time → inserting retrieved chunks into the
  LLM's prompt → generation grounded in that retrieved text. Know each step
  and what can go wrong at each one (bad chunking splits a rule across two
  chunks; bad retrieval pulls irrelevant sections; the LLM can still ignore
  retrieved context if the prompt doesn't force it to cite sources).
- **Grounding & citation**: how to make the LLM cite which retrieved
  document/section it used for each claim — critical for something a
  regulator will read. This is a prompting/output-format technique, not
  magic — you explicitly ask for citations and verify they match what was
  retrieved.
- **Structured output**: getting an LLM to reliably produce a SAR draft with
  the right sections (customer details, transaction narrative, suspicious
  indicators, regulatory basis) — via JSON-mode / structured output features
  or careful prompt templates, not just hoping the prose stays orderly.
- **Prompt injection basics (light awareness, not deep)**: since your
  Compliance Assistant will handle real analyst questions and read
  retrieved documents, understand that content in retrieved documents or
  user input could try to override your system prompt — enough awareness to
  not build something naively exploitable.

## Recommended resources (free)

- **Anthropic's own documentation on building with Claude**:
  https://docs.anthropic.com/ — specifically the "Prompt engineering" and
  "Tool use" guides. Since the tech stack names Claude as the LLM core, this
  is the most directly relevant reference.
- **Anthropic's RAG cookbook / guide**:
  https://docs.anthropic.com/en/docs/build-with-claude/retrieval-augmented-generation-rag —
  a practical walk-through of exactly the pipeline you'll build in Stage 4.
- **LangChain's official "RAG from Scratch" tutorial series**:
  https://python.langchain.com/docs/tutorials/rag/ — the framework named in
  your tech stack; do the basic tutorial before reaching for advanced
  features you don't need yet.
- **Pinecone's "What is RAG" learning guide**:
  https://www.pinecone.io/learn/retrieval-augmented-generation/ — a clean,
  vendor-neutral-enough explainer of embeddings + retrieval + generation.
- **"Prompt Engineering Guide" (free, community-maintained)**:
  https://www.promptingguide.ai/ — skim the sections on RAG and structured
  output prompting.

## Checkpoint

> "Explain to someone why you can't just paste 'summarize RBI's SAR filing
> requirements' into an LLM and trust the output for a real compliance
> document. Then describe, step by step, what your RAG pipeline does
> differently, from the moment a case is flagged to the moment a SAR draft
> is produced."

If you can walk through the full pipeline without hand-waving any step, move
on.
