# Phase 3: Intent-to-Diff Semantic Alignment Engine

**Goal:** Implement the NLP module that compares the user's issue text against the AI's actual code changes to detect semantic drift.

---

## Instructions for the AI Agent

Act as an Applied NLP Engineer.
Write `src/semantic_engine/drift_analyzer.py` using `sentence-transformers` in `e:\study\ASTRA\ast-triage-core`.

**Requirements:**

1. Load `all-MiniLM-L6-v2` as a thread-safe singleton.
2. Create a method to ingest `issue_description` and `diff_summary`.
3. Normalize both texts (strip Markdown tables, HTML comments, and redundant diff line headers `@@`).
4. Generate L2-normalized dense embeddings.
5. Compute the Cosine Similarity metric $S_{align} \in [-1.0, 1.0]$.
6. Formulate an entity Jaccard overlap metric by extracting Python identifier tokens (`snake_case` and `camelCase`) from the issue and diff.
7. Return a structured dictionary with `intent_diff_cosine`, `entity_drift_jaccard`, and `semantic_drift_flag` (1 if cosine similarity < 0.45).
