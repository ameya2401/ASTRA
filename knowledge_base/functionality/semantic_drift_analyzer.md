# Semantic Drift Analyzer

> Implementation: [src/semantic_engine/](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/)  
> Key modules: [embedder.py](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/embedder.py), [drift_analyzer.py](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/drift_analyzer.py)

The semantic engine measures whether an agent pull request adheres to the intent stated in the issue prompt or drifts into off-topic code modifications.

---

## 1. Sentence Embedder Singleton

Located in [src/semantic_engine/embedder.py](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/embedder.py):

- **Model Selection**: Uses `all-MiniLM-L6-v2` from HuggingFace via `sentence-transformers`. It outputs dense 384-dimensional vectors.
- **Thread-Safe Singleton**:
  ```python
  class SentenceEmbedder:
      _instance: Optional[SentenceEmbedder] = None
      _lock: threading.Lock = threading.Lock()

      def __new__(cls, model_name=None):
          with cls._lock:
              if cls._instance is None:
                  instance = super().__new__(cls)
                  instance.model = SentenceTransformer("all-MiniLM-L6-v2")
                  cls._instance = instance
          return cls._instance
  ```
  This pattern guarantees that heavy transformer weights are loaded only once in memory across worker threads.

---

## 2. Text Sanitization and Cosine Similarity

Located in [src/semantic_engine/drift_analyzer.py](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/drift_analyzer.py):

1. **Diff Sanitization (`clean_diff_for_embedding`)**:
   - Strips unified diff prefixes (`+++`, `---`, `@@ -1,4 +1,5 @@`, `diff --git`).
   - Retains added lines (prefixed with `+`), comments, and variable assignments while dropping pure noise tokens.
2. **Cosine Similarity**:
   - Projects both the issue prompt string and the sanitized diff summary into 384-dimensional space.
   - Computes standard dot product divided by Euclidean norms:
     $$\cos(\theta) = \frac{u \cdot v}{\|u\|_2 \|v\|_2}$$
   - Produces `f13_intent_diff_cosine_sim` and `f14_issue_title_diff_sim`.

---

## 3. Entity Drift and Jaccard Distance

Located in [src/semantic_engine/drift_analyzer.py:L142-L195](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/drift_analyzer.py#L142-L195):

1. **Identifier Extraction (`extract_code_entities`)**:
   - Uses regex pattern `\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b` to locate identifier tokens in both the issue text and the diff.
   - Filters out standard Python language keywords (`if`, `while`, `def`, `class`, `self`, `return`, `import`, etc.).
2. **Jaccard Distance**:
   $$J_{dist} = 1.0 - \frac{|E_{issue} \cap E_{diff}|}{|E_{issue} \cup E_{diff}|}$$
   - A Jaccard distance near `1.0` means the diff touches variables and functions never cited in the issue prompt, signaling scope creep or hallucination.

---

## 4. Drift Decision Policy

- Threshold constant: `SEMANTIC_DRIFT_THRESHOLD = 0.45`.
- If `intent_diff_cosine < 0.45`, `f17_semantic_drift_flag` is set to `1`.
- The triage classifier treats this flag as an overriding risk amplifier, preventing drifted agent submissions from receiving green approval.
