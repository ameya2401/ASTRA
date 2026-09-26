# ASTRA Knowledge Base

> An LLM-optimized and developer-friendly knowledge wiki for the ASTRA project (AST-Triage and Automated Risk Stratification for AI-Agent-Authored Pull Requests).

This knowledge base follows Andrej Karpathy's knowledge wiki pattern: modular, atomic markdown notes, a central Map of Content index, grounded technical mechanisms, explicit schemas, and cross-referenced hyperlinks without promotional filler.

---

## 1. Map of Content (MOC)

```
knowledge_base/
├── architecture/                   # System design, microservices, and database models
│   ├── system_overview.md          # Component boundaries, runtime environment, and tech stack
│   ├── data_flow.md                # Lifecycle of a PR from webhook ingress to comment post
│   ├── database_schema.md          # Relational entities, foreign keys, and vector storage
│   └── api_gateway.md              # FastAPI REST endpoints, schemas, lifecycle, and SLA guarantees
│
├── features/                       # 28-dimensional PR feature vector taxonomy
│   ├── feature_taxonomy.md         # Master index of features F01 through F28
│   ├── ast_structural_features.md  # Features F01 to F12: syntax tree deltas and complexity
│   ├── semantic_nlp_features.md    # Features F13 to F18: intent alignment and drift metrics
│   └── test_and_process_features.md# Features F19 to F28: test churn and author provenance
│
├── functionality/                  # Engine implementations and developer tooling
│   ├── ast_engine_differ.md        # Tree-sitter AST parsing and disturbance index computation
│   ├── semantic_drift_analyzer.md  # Sentence embeddings, cosine similarity, and entity Jaccard
│   ├── github_webhook_and_reporter.md # Webhook HMAC verification, API client, and PR comments
│   └── cli_and_runners.md          # Standalone CLI tools and local testing workflows
│
├── ml_and_scoring/                 # Machine learning, calibration, and explainability
│   ├── risk_stratification.md      # Triage policy: GREEN, YELLOW, and RED risk tiers
│   ├── model_pipeline.md           # XGBoost training, Platt calibration, and imbalance handling
│   └── explainability_shap.md      # TreeSHAP feature attributions and PR explanation generation
│
├── pipeline_and_storage/           # Persistence, async connections, and vector preparation
│   ├── storage_layer.md            # SQLAlchemy 2.0 async engine and session management
│   └── vector_assembly.md          # 28-D vector construction, normalization, and imputation
│
└── operations_and_guides/          # Engineering standards, testing, and verification
    ├── verification_gates.md       # Mandatory validation gates and testing commands
    └── developer_standards.md      # Repo conventions: error-tolerant parsing and writing style
```

---

## 2. Core Concepts at a Glance

| Concept | Description | Reference Note |
|---------|-------------|----------------|
| **AST Differencing** | Compares source code before and after a PR at the syntax tree level using Tree-sitter instead of raw line counts. | [ast_engine_differ.md](file:///e:/study/ASTRA/knowledge_base/functionality/ast_engine_differ.md) |
| **Cyclomatic Complexity** | Counts decision forks (`if`, `while`, `for`, `except`, `and`, `or`) to measure branching logic churn. | [ast_structural_features.md](file:///e:/study/ASTRA/knowledge_base/features/ast_structural_features.md) |
| **Semantic Drift** | Quantifies whether an AI agent answered the issue prompt or wandered off-topic using MiniLM embeddings and cosine distance. | [semantic_drift_analyzer.md](file:///e:/study/ASTRA/knowledge_base/functionality/semantic_drift_analyzer.md) |
| **28-D Feature Vector** | A unified numerical representation capturing code structure, semantic intent, test churn, and process provenance. | [feature_taxonomy.md](file:///e:/study/ASTRA/knowledge_base/features/feature_taxonomy.md) |
| **Platt Calibration** | Logistic sigmoid scaling fitted via cross-validation to turn raw boosting margins into true posterior probabilities. | [model_pipeline.md](file:///e:/study/ASTRA/knowledge_base/ml_and_scoring/model_pipeline.md) |
| **Local SHAP Explanations** | Computes exact marginal contributions of each feature to the final risk score so human reviewers see why a PR was flagged. | [explainability_shap.md](file:///e:/study/ASTRA/knowledge_base/ml_and_scoring/explainability_shap.md) |

---

## 3. How to Use This Knowledge Base

1. **For Agents & LLMs**: Read the relevant category sub-document directly before modifying or testing that component. Each note contains exact file paths and line ranges.
2. **For Human Developers**: Start with [system_overview.md](file:///e:/study/ASTRA/knowledge_base/architecture/system_overview.md) and [data_flow.md](file:///e:/study/ASTRA/knowledge_base/architecture/data_flow.md) to understand how components interact.
3. **For Feature Engineering**: Consult [feature_taxonomy.md](file:///e:/study/ASTRA/knowledge_base/features/feature_taxonomy.md) for standard column names, types, and mathematical formulas.
4. **For Code Standards**: Review [developer_standards.md](file:///e:/study/ASTRA/knowledge_base/operations_and_guides/developer_standards.md) to maintain repo conventions.
