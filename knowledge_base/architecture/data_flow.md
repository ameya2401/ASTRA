# Data Flow & Pipeline Architecture

> Traces the complete lifecycle of a Pull Request moving through the ASTRA triage pipeline.

---

## 1. End-to-End Pipeline Diagram

```
[GitHub Webhook / CLI Input]
              │
              ▼
    1. INGESTION & PARSING
       ├── Extract Issue Title, Issue Body, Author, Base SHA, Head SHA
       └── Extract File Patches & Unified Diff
              │
              ├────────────────────────────────────────┐
              ▼                                        ▼
    2. AST STRUCTURAL ENGINE              3. SEMANTIC DRIFT ENGINE
       ├── Parse base & head files via Tree-sitter  ├── Load MiniLM singleton embedder
       ├── Compute McCabe Cyclomatic Complexity     ├── Strip unified diff formatting
       ├── Measure nesting depth & fan-out delta   ├── Compute cosine distance (intent vs diff)
       └── Calculate Disturbance Index (0.0 - 1.0) ├── Calculate Entity Jaccard Distance
              │                                        └── Compute docstring-to-code ratio
              │                                                │
              └────────────────────┬───────────────────────────┘
                                   │
                                   ▼
                        4. 28-D VECTOR ASSEMBLY
                           ├── F01-F12: AST Structural Metrics
                           ├── F13-F18: Semantic Drift Metrics
                           ├── F19-F23: Test Churn & Asymmetry Metrics
                           └── F24-F28: Process & Provenance Metrics
                                   │
                                   ▼
                        5. ML SCORING & CALIBRATION
                           ├── Feed vector into XGBoost Classifier
                           ├── Apply Platt Scaling (CalibratedClassifierCV)
                           └── Output Calibrated Risk Score in [0.0, 1.0]
                                   │
                                   ▼
                        6. EXPLAINABILITY & TRIAGE
                           ├── TreeSHAP computes feature attributions
                           ├── Identify Top 3 Risk Factors & Top 3 Mitigating Factors
                           └── Assign Risk Tier: GREEN (<0.35), YELLOW (0.35-0.70), RED (>0.70)
                                   │
                                   ▼
                        7. PERSISTENCE & RESPONSE
                           ├── Save PullRequest & FeatureRecord & TriagePrediction to DB
                           └── Post Markdown Review Summary to GitHub PR Webhook
```

---

## 2. Stage Breakdown

### Stage 1: Ingestion
- In live operation, GitHub fires a `pull_request.opened` or `pull_request.synchronize` webhook event to `POST /api/v1/webhook`.
- [src/api/schemas.py](file:///e:/study/ASTRA/ast-triage-core/src/api/schemas.py) parses the payload into structured models, extracting the issue prompt, base and head commit SHAs, author identity, and raw unified diff.

### Stage 2: Dual Feature Extraction
The incoming PR triggers parallel static analysis:
- **Structural Analysis**: [src/ast_engine/differ.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py) processes modified source files. It parses AST representations for base and head revisions, computes cyclomatic complexity change, measures fan-out delta, and calculates the disturbance index.
- **Semantic Analysis**: [src/semantic_engine/drift_analyzer.py](file:///e:/study/ASTRA/ast-triage-core/src/semantic_engine/drift_analyzer.py) cleans the raw diff text, computes 384-dimensional embeddings of the issue prompt and diff summary, and assesses whether the agent stayed on task. If cosine similarity drops below 0.45, `f17_semantic_drift_flag` is set to 1.

### Stage 3: Vector Normalization
- [src/feature_pipeline/vector_builder.py](file:///e:/study/ASTRA/ast-triage-core/src/feature_pipeline/vector_builder.py) merges the structural, semantic, test churn, and process features into an ordered 28-dimensional floating point vector.
- [src/feature_pipeline/normalizer.py](file:///e:/study/ASTRA/ast-triage-core/src/feature_pipeline/normalizer.py) validates bounds, imputes missing optional signals (such as CI status before test runs complete), and applies standard scaling.

### Stage 4: Inference and Attribution
- [src/ml_engine/predictor.py](file:///e:/study/ASTRA/ast-triage-core/src/ml_engine/predictor.py) passes the 28-D vector to the trained XGBoost model. Platt calibration converts the raw decision margin into a true posterior probability of defect.
- [src/ml_engine/explainer.py](file:///e:/study/ASTRA/ast-triage-core/src/ml_engine/explainer.py) runs TreeSHAP to assign exact additive importance values to each of the 28 features, highlighting which metrics pushed the PR into a higher risk band.

### Stage 5: Storage and Action
- [database/connection.py](file:///e:/study/ASTRA/ast-triage-core/database/connection.py) persists the full record ([PullRequest](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L71-L136), [FeatureRecord](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L138-L245), and [TriagePrediction](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L248-L306)).
- If integrated with GitHub, [src/integrations/reporter.py](file:///e:/study/ASTRA/ast-triage-core/src/integrations/reporter.py) generates a clear markdown comment detailing the risk score, risk band, and top SHAP explanations.
