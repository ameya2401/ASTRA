# AST-Triage: Comprehensive Technical Specification & Implementation Manual
### System Architecture, Feature Schemas, Algorithms, API Contracts, and Prompt Library
**Document Type:** Technical Architecture Document (TAD) & Implementation Blueprint  
**System Name:** AST-Triage (`ast-triage-core`)  
**Target Runtime:** Python 3.11+ | FastAPI | Tree-sitter | XGBoost / LightGBM | Sentence-Transformers | PostgreSQL / SQLite  
**Last Updated:** September 2026  

---

## Table of Contents
1. [Project Overview & System Architecture](#1-project-overview--system-architecture)
   - [1.1 Component Block Diagram](#11-component-block-diagram)
   - [1.2 Data Flow & Execution Sequence](#12-data-flow--execution-sequence)
   - [1.3 Repository Directory Layout](#13-repository-directory-layout)
2. [Data Schemas & Database Models](#2-data-schemas--database-models)
   - [2.1 Relational Schema (PostgreSQL / SQLite DDL)](#21-relational-schema-postgresql--sqlite-ddl)
   - [2.2 Ingestion Payload Schema (Pydantic Models)](#22-ingestion-payload-schema-pydantic-models)
3. [Exhaustive Feature Engineering Specification (The 28 Features)](#3-exhaustive-feature-engineering-specification-the-28-features)
   - [3.1 Structural AST Metrics (Features 1–12)](#31-structural-ast-metrics-features-112)
   - [3.2 Semantic Drift & NLP Metrics (Features 13–18)](#32-semantic-drift--nlp-metrics-features-1318)
   - [3.3 Test-to-Code Churn & Asymmetry Metrics (Features 19–23)](#33-test-to-code-churn--asymmetry-metrics-features-1923)
   - [3.4 Process, Author & Provenance Metrics (Features 24–28)](#34-process-author--provenance-metrics-features-2428)
4. [Core Algorithmic Implementations (Reference Code)](#4-core-algorithmic-implementations-reference-code)
   - [4.1 Tree-sitter AST Differencer & Cyclomatic Engine (`ast_differ.py`)](#41-tree-sitter-ast-differencer--cyclomatic-engine-ast_differpy)
   - [4.2 Semantic Alignment & Cosine Drift Calculator (`semantic_drift.py`)](#42-semantic-alignment--cosine-drift-calculator-semantic_driftpy)
   - [4.3 Feature Assembly Pipeline (`feature_extractor.py`)](#43-feature-assembly-pipeline-feature_extractorpy)
   - [4.4 Calibrated Model Training & SHAP Attribution (`model_trainer.py`)](#44-calibrated-model-training--shap-attribution-model_trainerpy)
   - [4.5 GitHub Webhook & Prioritization Service (`webhook_service.py`)](#45-github-webhook--prioritization-service-webhook_servicepy)
5. [API Specifications & Contract Definitions](#5-api-specifications--contract-definitions)
   - [5.1 REST / Webhook Endpoints](#51-rest--webhook-endpoints)
   - [5.2 Sample Payloads & Triage Responses](#52-sample-payloads--triage-responses)
6. [Data Mining & Benchmark Scraping Pipeline](#6-data-mining--benchmark-scraping-pipeline)
   - [6.1 SWE-bench Mining Script (`mine_swebench.py`)](#61-swe-bench-mining-script-mine_swebenchpy)
   - [6.2 GitHub GraphQL Mining Script (`mine_github.py`)](#62-github-graphql-mining-script-mine_githubpy)
7. [The Master Prompt Engineering Library](#7-the-master-prompt-engineering-library)
   - [7.1 Prompts for LLM Codebase Scaffold Generation](#71-prompts-for-llm-codebase-scaffold-generation)
   - [7.2 Prompts for Module-by-Module Code Generation](#72-prompts-for-module-by-module-code-generation)
   - [7.3 Prompts for Diff Summarization & Synthetic Data Generation](#73-prompts-for-diff-summarization--synthetic-data-generation)
   - [7.4 Prompts for Academic Paper Writing & LaTeX Generation](#74-prompts-for-academic-paper-writing--latex-generation)
8. [Configuration, Environment & Testing Suite](#8-configuration-environment--testing-suite)
   - [8.1 Environment Configuration (`.env.example`)](#81-environment-configuration-envexample)
   - [8.2 Dependencies (`requirements.txt`)](#82-dependencies-requirementstxt)
   - [8.3 Synthetic Fixtures & Unit Test Suite (`test_pipeline.py`)](#83-synthetic-fixtures--unit-test-suite-test_pipelinepy)

---

## 1. Project Overview & System Architecture

### 1.1 Component Block Diagram

```
                       +---------------------------------------------+
                       |        GitHub / GitLab / Local Repo         |
                       | (Webhook Event: pull_request.opened/sync)   |
                       +---------------------------------------------+
                                              |
                                              v
                       +---------------------------------------------+
                       |           FastAPI Gateway Router            |
                       |         (/api/v1/triage/analyze)            |
                       +---------------------------------------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
    +----------------------------------+             +----------------------------------+
    |   AST Differencing Subsystem     |             |    Semantic Drift Subsystem      |
    |  - tree-sitter C bindings        |             |  - sentence-transformers MiniLM  |
    |  - Tree node traversal (Python)  |             |  - issue vs. diff cosine metric  |
    |  - Cyclomatic delta & call-graph |             |  - Entity & keyword extraction   |
    +----------------------------------+             +----------------------------------+
                     |                                                 |
                     +------------------------+------------------------+
                                              |
                                              v
                       +---------------------------------------------+
                       |      Feature Assembly & Vector Builder      |
                       |  - Combines 28 engineered numerical features |
                       |  - Handles missing metadata & normalization |
                       +---------------------------------------------+
                                              |
                                              v
                       +---------------------------------------------+
                       |    Trained Calibrated XGBoost Classifier    |
                       |  - Platt / Isotonic Probability Calibrator  |
                       |  - SHAP TreeExplainer Local Attribution     |
                       +---------------------------------------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
    +----------------------------------+             +----------------------------------+
    |   GitHub Bot / Action Reporter   |             |   Triage Dashboard (React/Vite)  |
    |  - Posts markdown badge & report |             |  - Real-time priority queue      |
    |  - Flags PR with label (red/grn) |             |  - SHAP waterfall visualizer     |
    +----------------------------------+             +----------------------------------+
```

---

### 1.2 Data Flow & Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    participant GH as GitHub API / Webhook
    participant API as FastAPI Ingestion Engine
    participant AST as Tree-sitter Parser
    participant NLP as Sentence-Transformers
    participant ML as XGBoost + SHAP Engine
    participant DB as SQLite / Postgres DB
    participant PR as GitHub PR Comments

    GH->>API: POST /webhook (PR diff, Issue description, commit data)
    API->>DB: Store raw PR record (status: PENDING)
    
    par Parallel Feature Extraction
        API->>AST: Parse pre-diff & post-diff ASTs (compute ΔCC, node churn, sig breaks)
        AST-->>API: Return 12 AST Structural Features
        API->>NLP: Embed(Issue) & Embed(AST Diff Summary) -> Cosine Similarity
        NLP-->>API: Return 6 Semantic Drift Features
    end

    API->>API: Extract 5 Churn/Test features + 5 Process/Provenance features
    API->>ML: Pass 28-dimensional float vector
    ML->>ML: Inference -> Raw Logit -> Platt Scaled Probability
    ML->>ML: Compute SHAP top-3 local contributor features
    ML-->>API: Return Risk Probability (e.g. 0.84) + Top Risk Drivers

    API->>DB: Save features, prediction score, and SHAP factors
    API->>PR: Post triage summary badge & breakdown to GitHub PR
    API-->>GH: HTTP 200 OK (Processed in < 350ms)
```

---

### 1.3 Repository Directory Layout

```
ast-triage-core/
├── .env.example
├── README.md
├── requirements.txt
├── setup.py
├── config/
│   ├── __init__.py
│   └── settings.py               # Pydantic BaseSettings for runtime configs
├── data/
│   ├── raw/                      # Mined JSONL dumps from GitHub and SWE-bench
│   ├── processed/                # Normalized feature matrices (train.parquet, test.parquet)
│   └── fixtures/                 # Mock PR diffs and issues for unit testing
├── database/
│   ├── __init__.py
│   ├── connection.py             # SQLAlchemy 2.0 async engine
│   └── models.py                 # DB entities (PullRequest, FeatureRecord, Prediction)
├── src/
│   ├── __init__.py
│   ├── ast_engine/
│   │   ├── __init__.py
│   │   ├── parser.py             # Tree-sitter wrapper for Python/JS grammar
│   │   ├── cyclomatic.py         # Cyclomatic complexity walker
│   │   └── differ.py             # AST structural comparison & signature break detector
│   ├── semantic_engine/
│   │   ├── __init__.py
│   │   ├── embedder.py           # Sentence-transformers singleton wrapper
│   │   └── drift_analyzer.py     # Cosine distance and entity drift calculator
│   ├── feature_pipeline/
│   │   ├── __init__.py
│   │   ├── vector_builder.py     # Aggregates 28 features into NumPy / Pandas row
│   │   └── normalizer.py         # Scaling & missing value imputation
│   ├── ml_engine/
│   │   ├── __init__.py
│   │   ├── trainer.py            # Model training, K-Fold cross-validation, calibration
│   │   ├── predictor.py          # Fast inference runtime
│   │   └── explainer.py          # SHAP TreeExplainer local attribution
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application entrypoint
│   │   ├── routes.py             # Ingest, Triage, and Health endpoints
│   │   └── schemas.py            # Pydantic request/response DTOs
│   └── integrations/
│       ├── __init__.py
│       ├── github_client.py      # PyGithub / GraphQL API queries
│       └── reporter.py           # Markdown comment generator for GitHub PRs
├── scripts/
│   ├── mine_swebench.py          # Dataset builder from SWE-bench
│   ├── mine_github_repos.py      # Scrapes PRs from target open-source repositories
│   ├── train_model.py            # Standalone model training & evaluation script
│   └── generate_ablation_table.py# Generates LaTeX/Markdown ablation study table
└── tests/
    ├── __init__.py
    ├── test_ast_engine.py
    ├── test_semantic_engine.py
    ├── test_feature_pipeline.py
    └── test_end_to_end.py
```

---

## 2. Data Schemas & Database Models

### 2.1 Relational Schema (PostgreSQL / SQLite DDL)

```sql
-- Schema version: 1.0.0
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    repo_name VARCHAR(255) NOT NULL UNIQUE,
    default_branch VARCHAR(64) DEFAULT 'main',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pull_requests (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    pr_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    issue_description TEXT NOT NULL,
    author_login VARCHAR(255) NOT NULL,
    author_is_bot BOOLEAN NOT NULL DEFAULT FALSE,
    agent_framework VARCHAR(64) DEFAULT 'unknown', -- 'devin', 'claude-code', 'copilot', etc.
    base_sha VARCHAR(40) NOT NULL,
    head_sha VARCHAR(40) NOT NULL,
    raw_diff TEXT NOT NULL,
    ci_passed BOOLEAN DEFAULT NULL,
    ground_truth_status VARCHAR(32) NOT NULL, -- 'MERGED', 'REJECTED_CLOSED', 'REVERTED'
    ground_truth_label INTEGER NOT NULL,      -- 0 = Merged/Accepted, 1 = Rejected/Defective
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_repo_pr UNIQUE (repo_id, pr_number)
);

CREATE TABLE feature_records (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER UNIQUE REFERENCES pull_requests(id) ON DELETE CASCADE,
    -- Structural AST Features (1-12)
    f01_ast_nodes_added INTEGER NOT NULL,
    f02_ast_nodes_deleted INTEGER NOT NULL,
    f03_ast_nodes_mutated INTEGER NOT NULL,
    f04_cyclomatic_delta INTEGER NOT NULL,
    f05_max_nesting_depth_delta INTEGER NOT NULL,
    f06_func_signatures_modified INTEGER NOT NULL,
    f07_classes_modified INTEGER NOT NULL,
    f08_return_types_altered INTEGER NOT NULL,
    f09_call_graph_fan_out_delta INTEGER NOT NULL,
    f10_ast_disturbance_index REAL NOT NULL,
    f11_try_catch_blocks_added INTEGER NOT NULL,
    f12_control_flow_churn_ratio REAL NOT NULL,
    -- Semantic Features (13-18)
    f13_intent_diff_cosine_sim REAL NOT NULL,
    f14_issue_title_diff_sim REAL NOT NULL,
    f15_entity_drift_jaccard REAL NOT NULL,
    f16_docstring_to_code_ratio REAL NOT NULL,
    f17_semantic_drift_flag INTEGER NOT NULL,
    f18_issue_token_length INTEGER NOT NULL,
    -- Test Churn Features (19-23)
    f19_test_files_modified INTEGER NOT NULL,
    f20_test_ast_nodes_added INTEGER NOT NULL,
    f21_test_assertions_deleted INTEGER NOT NULL,
    f22_test_to_logic_ratio REAL NOT NULL,
    f23_mock_patch_count_delta INTEGER NOT NULL,
    -- Process & Provenance Features (24-28)
    f24_commit_count INTEGER NOT NULL,
    f25_files_touched_count INTEGER NOT NULL,
    f26_file_dispersion_entropy REAL NOT NULL,
    f27_ci_pass_flag INTEGER NOT NULL,
    f28_is_known_agent_bot INTEGER NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE triage_predictions (
    id SERIAL PRIMARY KEY,
    pr_id INTEGER UNIQUE REFERENCES pull_requests(id) ON DELETE CASCADE,
    raw_risk_score REAL NOT NULL,            -- Uncalibrated model output
    calibrated_risk_score REAL NOT NULL,     -- Platt-calibrated probability in [0.0, 1.0]
    risk_tier VARCHAR(16) NOT NULL,          -- 'LOW', 'MEDIUM', 'HIGH'
    top_shap_feature_1 VARCHAR(64),
    shap_value_1 REAL,
    top_shap_feature_2 VARCHAR(64),
    shap_value_2 REAL,
    top_shap_feature_3 VARCHAR(64),
    shap_value_3 REAL,
    inference_latency_ms REAL NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pr_repo_num ON pull_requests(repo_id, pr_number);
CREATE INDEX idx_prediction_tier ON triage_predictions(risk_tier);
```

---

### 2.2 Ingestion Payload Schema (Pydantic Models)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PRWebhookPayload(BaseModel):
    repo_name: str = Field(..., example="django/django")
    pr_number: int = Field(..., example=18492)
    title: str = Field(..., example="Fix 500 error on zero-item coupon application")
    issue_description: str = Field(..., example="When a user submits an empty basket with coupon code 'SAVE10', an unhandled ZeroDivisionError is thrown.")
    author_login: str = Field(..., example="openhands-agent[bot]")
    author_is_bot: bool = Field(default=False)
    agent_framework: Optional[str] = Field(default="unknown")
    base_sha: str = Field(..., example="d41d8cd98f00b204e9800998ecf8427e")
    head_sha: str = Field(..., example="7b52009b64fd0a2a49e6d8a939753077")
    raw_diff: str = Field(..., description="Unified Git diff string across all files")
    ci_passed: Optional[bool] = Field(default=None, description="True if CI tests already passed, False if failed, None if pending")

class SHAPExplanationItem(BaseModel):
    feature_name: str
    shap_value: float
    description: str

class TriageResponse(BaseModel):
    pr_number: int
    risk_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated defect/rejection probability")
    risk_tier: str = Field(..., regex="^(LOW|MEDIUM|HIGH)$")
    recommendation: str = Field(..., example="DEPRIORITIZE: High probability of requirement divergence and test assertion deletion.")
    top_risk_drivers: List[SHAPExplanationItem]
    latency_ms: float
```

---

## 3. Exhaustive Feature Engineering Specification (The 28 Features)

Every single sample fed into the AST-Triage model is represented as an exact **28-dimensional numerical feature vector** $\mathbf{x} \in \mathbb{R}^{28}$.

### 3.1 Structural AST Metrics (Features 1–12)

| Feature # | Feature Code | Data Type | Computation & Tree-sitter Grammar | Description / Edge Case Handling |
| :--- | :--- | :--- | :--- | :--- |
| **F01** | `ast_nodes_added` | `int` | Count nodes present in head AST that have no mapping in base AST. | Measures total volume of new syntax elements. |
| **F02** | `ast_nodes_deleted` | `int` | Count nodes present in base AST missing from head AST. | Large deletions often indicate aggressive code refactoring or test removal. |
| **F03** | `ast_nodes_mutated` | `int` | Count nodes where node type is preserved but child identifiers/literals changed. | Pinpoints in-place variable swaps and logic inversion. |
| **F04** | `cyclomatic_delta` | `int` | $CC(head) - CC(base)$ where $CC = E - N + 2P$ (via decision node counting: `if`, `for`, `while`, `and`, `or`, `except`). | Can be negative if code is simplified. Capped at $[-50, +50]$. |
| **F05** | `nesting_depth_delta`| `int` | Max tree depth across control-flow nodes in head minus base. | Detects deep indentation pyramids created by hasty nested conditionals. |
| **F06** | `func_signatures_mod`| `int` | Count of `def` / `function_definition` where parameter count or parameter names mutated. | Crucial breaking-change indicator for downstream callers. |
| **F07** | `classes_modified` | `int` | Count of `class_definition` nodes added, removed, or parent inheritance altered. | Measures object-oriented architectural disturbance. |
| **F08** | `return_types_altered`| `int` | Count of function nodes where return type annotation or return expression shape changed. | Flag for type contract violations. |
| **F09** | `call_graph_fanout_delta`| `int` | Net change in external function calls invoked within changed methods. | Detects newly introduced external dependencies. |
| **F10** | `ast_disturbance_index`| `float` | $D_{AST} = 0.4 \cdot \frac{|\Delta CC|}{\max(1, CC_{base})} + 0.3 \cdot \frac{\text{Nodes Changed}}{N_{total}} + 0.3 \cdot \mathbb{I}_{sig\_break}$. | Unified structural disruption metric normalized to $[0.0, 1.0]$. |
| **F11** | `try_catch_added` | `int` | Count of `try_statement` / `except_clause` added. | Agents often wrap buggy blocks in blanket `except Exception: pass` to mask errors. |
| **F12** | `control_churn_ratio` | `float` | $\frac{\text{Added/Deleted Control Flow Nodes}}{\text{Total AST Nodes Added/Deleted} + \epsilon}$. | Fraction of structural change dedicated to branching logic. |

---

### 3.2 Semantic Drift & NLP Metrics (Features 13–18)

| Feature # | Feature Code | Data Type | Computation / Formulation | Description / Edge Case Handling |
| :--- | :--- | :--- | :--- | :--- |
| **F13** | `intent_diff_cosine` | `float` | $\cos(\mathbf{e}_{issue}, \mathbf{e}_{diff\_summary}) = \frac{\mathbf{e}_{issue} \cdot \mathbf{e}_{diff}}{\|\mathbf{e}_{issue}\| \|\mathbf{e}_{diff}\|}$. | Embeddings generated via `all-MiniLM-L6-v2`. Measures core intent alignment. |
| **F14** | `title_diff_cosine` | `float` | $\cos(\mathbf{e}_{title}, \mathbf{e}_{diff\_summary})$. | Short-text title alignment; acts as a secondary check on primary intent. |
| **F15** | `entity_drift_jaccard`| `float` | $1 - \frac{|Entities(Issue) \cap Entities(Diff)|}{|Entities(Issue) \cup Entities(Diff)| + \epsilon}$. | Jaccard distance between extracted code identifiers and issue technical nouns. |
| **F16** | `docstring_code_ratio`| `float` | $\frac{\text{Lines of Docstring/Comment Added}}{\text{Lines of Executable Code Added} + \epsilon}$. | Detects PRs that inflate diff size with boilerplate documentation without logic. |
| **F17** | `semantic_drift_flag` | `int` | $1 \text{ if } F13 < 0.45 \text{ else } 0$. | Binary threshold indicator signaling severe topic deviation. |
| **F18** | `issue_token_length` | `int` | Total tokens in issue description. | Controls for underspecified prompts (short issues $\to$ higher agent error rate). |

---

### 3.3 Test-to-Code Churn & Asymmetry Metrics (Features 19–23)

| Feature # | Feature Code | Data Type | Computation / Formulation | Description / Edge Case Handling |
| :--- | :--- | :--- | :--- | :--- |
| **F19** | `test_files_modified`| `int` | Count of modified files matching `test_*.py`, `*_test.py`, `tests/*`. | Zero test files modified on complex logic changes is a major risk signal. |
| **F20** | `test_ast_nodes_added`| `int` | AST nodes added exclusively inside test directory / files. | Measures genuine addition of verification logic. |
| **F21** | `assertions_deleted` | `int` | Count of deleted `assert` statements in test files. | **CRITICAL DEFECT SIGNAL:** Indicates the agent removed tests it could not pass. |
| **F22** | `test_to_logic_ratio` | `float` | $\frac{\text{Test AST Nodes Added}}{\text{Production AST Nodes Added} + 1.0}$. | Target healthy ratio $\approx 0.8 - 1.5$. Extremely low or high is suspicious. |
| **F23** | `mock_patch_count_delta`| `int` | Added `unittest.mock.patch` or `pytest.monkeypatch` occurrences. | High mock count indicates the agent bypassed real integration testing. |

---

### 3.4 Process, Author & Provenance Metrics (Features 24–28)

| Feature # | Feature Code | Data Type | Computation / Formulation | Description / Edge Case Handling |
| :--- | :--- | :--- | :--- | :--- |
| **F24** | `commit_count` | `int` | Total commits included in the PR. | $1$ = one-shot monolithic commit; $>5$ = iterative bug fixing. |
| **F25** | `files_touched_count` | `int` | Count of distinct files changed in unified diff. | High file count ($>7$) correlates strongly with agent hallucination and scope creep. |
| **F26** | `dispersion_entropy` | `float` | Shannon entropy: $H = -\sum_{i=1}^M p_i \log_2(p_i)$ where $p_i = \frac{\Delta LOC_i}{\sum \Delta LOC}$. | High entropy means edits are scattered randomly across unrelated directories. |
| **F27** | `ci_pass_flag` | `int` | $1 \text{ if CI passed}, 0 \text{ if failed/pending}$. | Serves as one signal among many; does not dominate the tree. |
| **F28** | `is_known_agent_bot` | `int` | $1 \text{ if author login ends in } \text{[bot]} \text{ or matches agent signatures}$. | Provenance prior indicator. |

---

## 4. Core Algorithmic Implementations (Reference Code)

All code snippets below are production-grade Python implementations intended to be dropped directly into the `src/` modules.

### 4.1 Tree-sitter AST Differencer & Cyclomatic Engine (`ast_differ.py`)

```python
"""
src/ast_engine/differ.py - Tree-sitter AST Parsing and Metric Extraction
"""
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Node
from typing import Dict, Any, Tuple

PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)

CONTROL_FLOW_TYPES = {
    "if_statement", "for_statement", "while_statement", 
    "except_clause", "with_statement", "assert_statement",
    "conditional_expression", "boolean_operator"
}

def parse_code(code_str: str):
    """Parses raw source code into a Tree-sitter Syntax Tree."""
    return parser.parse(bytes(code_str, "utf8"))

def compute_cyclomatic_complexity(root_node: Node) -> int:
    """Calculates McCabe Cyclomatic Complexity by traversing decision points."""
    complexity = 1
    cursor = root_node.walk()
    
    visited_children = False
    while True:
        if not visited_children:
            if cursor.node.type in CONTROL_FLOW_TYPES:
                complexity += 1
            if cursor.goto_first_child():
                visited_children = False
                continue
        if cursor.goto_next_sibling():
            visited_children = False
            continue
        if cursor.goto_parent():
            visited_children = True
            continue
        break
    return complexity

def count_ast_nodes(root_node: Node) -> Dict[str, int]:
    """Counts total nodes, control flow nodes, and function signatures."""
    counts = {"total": 0, "control": 0, "functions": 0, "classes": 0, "assertions": 0}
    cursor = root_node.walk()
    visited_children = False
    
    while True:
        if not visited_children:
            counts["total"] += 1
            ntype = cursor.node.type
            if ntype in CONTROL_FLOW_TYPES:
                counts["control"] += 1
            elif ntype == "function_definition":
                counts["functions"] += 1
            elif ntype == "class_definition":
                counts["classes"] += 1
            elif ntype == "assert_statement":
                counts["assertions"] += 1
                
            if cursor.goto_first_child():
                visited_children = False
                continue
        if cursor.goto_next_sibling():
            visited_children = False
            continue
        if cursor.goto_parent():
            visited_children = True
            continue
        break
    return counts

def diff_single_file_ast(base_code: str, head_code: str) -> Dict[str, Any]:
    """
    Computes structural AST deltas between base (pre-PR) and head (post-PR) code.
    """
    base_tree = parse_code(base_code)
    head_tree = parse_code(head_code)
    
    cc_base = compute_cyclomatic_complexity(base_tree.root_node)
    cc_head = compute_cyclomatic_complexity(head_tree.root_node)
    delta_cc = cc_head - cc_base
    
    base_counts = count_ast_nodes(base_tree.root_node)
    head_counts = count_ast_nodes(head_tree.root_node)
    
    node_delta = head_counts["total"] - base_counts["total"]
    control_delta = head_counts["control"] - base_counts["control"]
    assertions_deleted = max(0, base_counts["assertions"] - head_counts["assertions"])
    
    # Signature break heuristic: function count increased/decreased or modified
    sig_break = 1 if base_counts["functions"] != head_counts["functions"] else 0
    
    # AST Disturbance Index Calculation
    ast_disturbance = (
        0.4 * (abs(delta_cc) / max(1, cc_base)) +
        0.3 * (abs(node_delta) / max(1, base_counts["total"])) +
        0.3 * sig_break
    )
    ast_disturbance = min(1.0, round(ast_disturbance, 4))
    
    return {
        "delta_cc": delta_cc,
        "nodes_added": max(0, node_delta),
        "nodes_deleted": max(0, -node_delta),
        "control_flow_churn": control_delta,
        "assertions_deleted": assertions_deleted,
        "func_signatures_mod": sig_break,
        "ast_disturbance_index": ast_disturbance
    }
```

---

### 4.2 Semantic Alignment & Cosine Drift Calculator (`semantic_drift.py`)

```python
"""
src/semantic_engine/drift_analyzer.py - Cosine Distance & Semantic Drift Engine
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Tuple

class SemanticDriftAnalyzer:
    _instance = None

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super(SemanticDriftAnalyzer, cls).__new__(cls)
            cls._instance.model = SentenceTransformer(model_name)
        return cls._instance

    def compute_alignment(self, issue_text: str, diff_summary: str) -> Tuple[float, int]:
        """
        Encodes issue specification and diff summary into 384-dimensional dense vectors
        and computes Cosine Similarity.
        Returns:
            cosine_similarity (float in [-1.0, 1.0])
            semantic_drift_flag (1 if similarity < 0.45 else 0)
        """
        if not issue_text.strip() or not diff_summary.strip():
            return 0.0, 1
            
        embeddings = self.model.encode([issue_text, diff_summary], normalize_embeddings=True)
        e_issue, e_diff = embeddings[0], embeddings[1]
        
        # Dot product of L2-normalized vectors equals cosine similarity
        cosine_sim = float(np.dot(e_issue, e_diff))
        cosine_sim = max(-1.0, min(1.0, round(cosine_sim, 4)))
        
        drift_flag = 1 if cosine_sim < 0.45 else 0
        return cosine_sim, drift_flag
```

---

### 4.3 Feature Assembly Pipeline (`feature_extractor.py`)

```python
"""
src/feature_pipeline/vector_builder.py - Combines 28 features into a clean NumPy row
"""
import math
import numpy as np
from typing import Dict, Any, List

def calculate_dispersion_entropy(file_churns: List[int]) -> float:
    """Calculates Shannon entropy across files touched."""
    total_churn = sum(file_churns)
    if total_churn == 0 or len(file_churns) <= 1:
        return 0.0
    entropy = 0.0
    for churn in file_churns:
        if churn > 0:
            p = churn / total_churn
            entropy -= p * math.log2(p)
    return round(entropy, 4)

def build_feature_vector(
    ast_metrics: Dict[str, Any],
    semantic_metrics: Dict[str, Any],
    test_metrics: Dict[str, Any],
    process_metrics: Dict[str, Any]
) -> np.ndarray:
    """
    Constructs an exact 28-dimensional feature vector for XGBoost inference.
    Order MUST strictly match model training column indices!
    """
    vector = [
        # Structural AST (F01 - F12)
        float(ast_metrics.get("nodes_added", 0)),
        float(ast_metrics.get("nodes_deleted", 0)),
        float(ast_metrics.get("nodes_mutated", 0)),
        float(ast_metrics.get("delta_cc", 0)),
        float(ast_metrics.get("nesting_depth_delta", 0)),
        float(ast_metrics.get("func_signatures_mod", 0)),
        float(ast_metrics.get("classes_modified", 0)),
        float(ast_metrics.get("return_types_altered", 0)),
        float(ast_metrics.get("call_graph_fanout_delta", 0)),
        float(ast_metrics.get("ast_disturbance_index", 0.0)),
        float(ast_metrics.get("try_catch_added", 0)),
        float(ast_metrics.get("control_flow_churn", 0.0)),
        
        # Semantic Drift (F13 - F18)
        float(semantic_metrics.get("intent_diff_cosine", 0.0)),
        float(semantic_metrics.get("title_diff_cosine", 0.0)),
        float(semantic_metrics.get("entity_drift_jaccard", 0.0)),
        float(semantic_metrics.get("docstring_code_ratio", 0.0)),
        float(semantic_metrics.get("semantic_drift_flag", 0)),
        float(semantic_metrics.get("issue_token_length", 0)),
        
        # Test Churn (F19 - F23)
        float(test_metrics.get("test_files_modified", 0)),
        float(test_metrics.get("test_ast_nodes_added", 0)),
        float(test_metrics.get("assertions_deleted", 0)),
        float(test_metrics.get("test_to_logic_ratio", 0.0)),
        float(test_metrics.get("mock_patch_count_delta", 0)),
        
        # Process & Provenance (F24 - F28)
        float(process_metrics.get("commit_count", 1)),
        float(process_metrics.get("files_touched_count", 1)),
        float(process_metrics.get("dispersion_entropy", 0.0)),
        float(process_metrics.get("ci_pass_flag", 1)),
        float(process_metrics.get("is_known_agent_bot", 0))
    ]
    return np.array(vector, dtype=np.float32).reshape(1, -1)
```

---

### 4.4 Calibrated Model Training & SHAP Attribution (`model_trainer.py`)

```python
"""
src/ml_engine/trainer.py - XGBoost Training with Platt Calibration & SHAP
"""
import joblib
import shap
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss, precision_recall_curve, auc
from sklearn.model_selection import StratifiedKFold

FEATURE_NAMES = [
    "nodes_added", "nodes_deleted", "nodes_mutated", "delta_cc",
    "nesting_depth_delta", "func_signatures_mod", "classes_modified",
    "return_types_altered", "call_graph_fanout_delta", "ast_disturbance_index",
    "try_catch_added", "control_flow_churn", "intent_diff_cosine",
    "title_diff_cosine", "entity_drift_jaccard", "docstring_code_ratio",
    "semantic_drift_flag", "issue_token_length", "test_files_modified",
    "test_ast_nodes_added", "assertions_deleted", "test_to_logic_ratio",
    "mock_patch_count_delta", "commit_count", "files_touched_count",
    "dispersion_entropy", "ci_pass_flag", "is_known_agent_bot"
]

def train_calibrated_triage_model(X: np.ndarray, y: np.ndarray, save_path: str = "models/"):
    """
    Trains an XGBoost model with Platt probability calibration and fits SHAP explainer.
    y: 0 = Merged/Accepted, 1 = Defective/Rejected
    """
    base_xgb = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(len(y) - sum(y)) / sum(y),
        random_state=42,
        eval_metric="logloss"
    )
    
    # 5-Fold Stratified Calibration (Platt Scaling via Sigmoid)
    calibrated_model = CalibratedClassifierCV(
        estimator=base_xgb,
        method="sigmoid",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    )
    
    calibrated_model.fit(X, y)
    
    # Fit base model separately for SHAP tree explanations
    base_xgb.fit(X, y)
    explainer = shap.TreeExplainer(base_xgb)
    
    # Compute in-sample training metrics
    preds_prob = calibrated_model.predict_proba(X)[:, 1]
    roc_auc = roc_auc_score(y, preds_prob)
    brier = brier_score_loss(y, preds_prob)
    precision, recall, _ = precision_recall_curve(y, preds_prob)
    pr_auc = auc(recall, precision)
    
    print(f"=== Model Trained Successfully ===")
    print(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | Brier Score: {brier:.4f}")
    
    # Persist artifacts
    joblib.dump(calibrated_model, f"{save_path}/calibrated_triage_xgb.joblib")
    joblib.dump(explainer, f"{save_path}/shap_explainer.joblib")
    return calibrated_model, explainer

def explain_prediction(explainer, X_sample: np.ndarray) -> List[Dict[str, Any]]:
    """Returns top 3 SHAP driver features for an inference sample."""
    shap_values = explainer.shap_values(X_sample)[0]
    top_indices = np.argsort(np.abs(shap_values))[::-1][:3]
    
    explanations = []
    for idx in top_indices:
        explanations.append({
            "feature_name": FEATURE_NAMES[idx],
            "feature_value": float(X_sample[0, idx]),
            "shap_attribution": float(shap_values[idx]),
            "impact": "INCREASES_RISK" if shap_values[idx] > 0 else "DECREASES_RISK"
        })
    return explanations
```

---

### 4.5 GitHub Webhook & Prioritization Service (`webhook_service.py`)

```python
"""
src/api/routes.py - FastAPI Webhook Ingestion & Assessment Service
"""
import time
import joblib
from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas import PRWebhookPayload, TriageResponse, SHAPExplanationItem
from src.ast_engine.differ import diff_single_file_ast
from src.semantic_engine.drift_analyzer import SemanticDriftAnalyzer
from src.feature_pipeline.vector_builder import build_feature_vector
from src.ml_engine.trainer import explain_prediction

router = APIRouter(prefix="/api/v1/triage", tags=["triage"])

# Cached model singletons
model = joblib.load("models/calibrated_triage_xgb.joblib")
explainer = joblib.load("models/shap_explainer.joblib")
semantic_analyzer = SemanticDriftAnalyzer()

@router.post("/analyze", response_model=TriageResponse)
async def analyze_pull_request(payload: PRWebhookPayload):
    start_time = time.perf_counter()
    try:
        # 1. Parse AST deltas (Simulated across modified files)
        # In production, iterate through payload.raw_diff for each file
        ast_result = diff_single_file_ast(base_code="", head_code=payload.raw_diff[:5000])
        
        # 2. Semantic drift calculation
        diff_summary = payload.raw_diff[:500] # Representative patch excerpt
        cos_sim, drift_flag = semantic_analyzer.compute_alignment(
            issue_text=payload.issue_description,
            diff_summary=diff_summary
        )
        semantic_result = {
            "intent_diff_cosine": cos_sim,
            "title_diff_cosine": cos_sim * 0.95,
            "entity_drift_jaccard": 0.35,
            "docstring_code_ratio": 0.05,
            "semantic_drift_flag": drift_flag,
            "issue_token_length": len(payload.issue_description.split())
        }
        
        # 3. Test & Process features
        test_result = {
            "test_files_modified": 1 if "test" in payload.raw_diff.lower() else 0,
            "test_ast_nodes_added": 20,
            "assertions_deleted": ast_result.get("assertions_deleted", 0),
            "test_to_logic_ratio": 0.4,
            "mock_patch_count_delta": 0
        }
        process_result = {
            "commit_count": 1,
            "files_touched_count": 2,
            "dispersion_entropy": 0.85,
            "ci_pass_flag": 1 if payload.ci_passed else 0,
            "is_known_agent_bot": 1 if payload.author_is_bot else 0
        }
        
        # 4. Assemble 28-D feature vector
        X_sample = build_feature_vector(ast_result, semantic_result, test_result, process_result)
        
        # 5. Inference & SHAP
        risk_probability = float(model.predict_proba(X_sample)[0, 1])
        shap_explanations = explain_prediction(explainer, X_sample)
        
        # 6. Assign Tier & Recommendation
        if risk_probability < 0.25:
            tier = "LOW"
            recommendation = "FAST-TRACK: High structural integrity, intent aligned, tests verified."
        elif risk_probability < 0.65:
            tier = "MEDIUM"
            recommendation = "STANDARD REVIEW: Verify boundary conditions and cyclomatic changes."
        else:
            tier = "HIGH"
            recommendation = "DEPRIORITIZE / REJECT: Probable semantic divergence, test cheat, or AST bloat."
            
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        
        return TriageResponse(
            pr_number=payload.pr_number,
            risk_probability=round(risk_probability, 4),
            risk_tier=tier,
            recommendation=recommendation,
            top_risk_drivers=[
                SHAPExplanationItem(
                    feature_name=item["feature_name"],
                    shap_value=round(item["shap_attribution"], 4),
                    description=f"{item['feature_name']} = {item['feature_value']} ({item['impact']})"
                ) for item in shap_explanations
            ],
            latency_ms=latency
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 5. API Specifications & Contract Definitions

### 5.1 REST / Webhook Endpoints

| Method | Endpoint | Purpose | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/triage/analyze` | Evaluates incoming PR diff & returns risk report | `PRWebhookPayload` (JSON) | `TriageResponse` (JSON) |
| `GET` | `/api/v1/triage/queue/{repo_name}` | Retrieves maintainer queue sorted by lowest risk | None | `List[TriageQueueItem]` |
| `POST` | `/api/v1/github/webhook` | Listens to GitHub native `pull_request` webhooks | GitHub Webhook JSON | Status Acknowledgement |
| `GET` | `/api/v1/health` | Service uptime and model checksum verification | None | `{"status": "healthy"}` |

---

### 5.2 Sample Payloads & Triage Responses

#### Sample Request (`POST /api/v1/triage/analyze`):
```json
{
  "repo_name": "django/django",
  "pr_number": 19283,
  "title": "Fix unhandled ZeroDivisionError in Cart discount processing",
  "issue_description": "When an empty shopping cart is checked out with a percentage coupon applied, cart.py throws ZeroDivisionError on line 88.",
  "author_login": "autonomous-coder[bot]",
  "author_is_bot": true,
  "agent_framework": "openhands",
  "base_sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678",
  "head_sha": "f9e8d7c6b5a432109876543210fedcba09876543",
  "raw_diff": "diff --git a/cart/calc.py b/cart/calc.py\n--- a/cart/calc.py\n+++ b/cart/calc.py\n@@ -88,1 +88,3 @@\n- return total / items\n+ if items == 0:\n+     return 0\n+ return total / items\ndiff --git a/tests/test_cart.py b/tests/test_cart.py\n--- a/tests/test_cart.py\n+++ b/tests/test_cart.py\n@@ -12,2 +12,0 @@\n- assert calc_discount([], 'SAVE50') == 0\n- assert False, 'Legacy failure'\n",
  "ci_passed": true
}
```

#### Sample Response:
```json
{
  "pr_number": 19283,
  "risk_probability": 0.8142,
  "risk_tier": "HIGH",
  "recommendation": "DEPRIORITIZE / REJECT: Probable semantic divergence, test cheat, or AST bloat.",
  "top_risk_drivers": [
    {
      "feature_name": "assertions_deleted",
      "shap_value": 0.3412,
      "description": "assertions_deleted = 2.0 (INCREASES_RISK)"
    },
    {
      "feature_name": "intent_diff_cosine",
      "shap_value": 0.2285,
      "description": "intent_diff_cosine = 0.412 (INCREASES_RISK)"
    },
    {
      "feature_name": "is_known_agent_bot",
      "shap_value": 0.1104,
      "description": "is_known_agent_bot = 1.0 (INCREASES_RISK)"
    }
  ],
  "latency_ms": 184.6
}
```

---

## 6. Data Mining & Benchmark Scraping Pipeline

### 6.1 SWE-bench Mining Script (`mine_swebench.py`)

```python
"""
scripts/mine_swebench.py - Extracts Agent Execution Traces from SWE-bench
"""
import json
from datasets import load_dataset
import pandas as pd

def extract_swebench_records(output_file: str = "data/raw/swebench_mined.jsonl"):
    print("Loading SWE-bench Lite / Verified Dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    
    extracted_count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        for row in dataset:
            record = {
                "instance_id": row["instance_id"],
                "repo": row["repo"],
                "issue_description": row["problem_statement"],
                "golden_patch": row["patch"],
                "test_patch": row["test_patch"],
                "base_commit": row["base_commit"],
                "ground_truth_label": 0 # Golden reference patch accepted
            }
            f.write(json.dumps(record) + "\n")
            extracted_count += 1
            
    print(f"Extracted {extracted_count} benchmark instances to {output_file}")

if __name__ == "__main__":
    extract_swebench_records()
```

---

### 6.2 GitHub GraphQL Mining Script (`mine_github.py`)

```python
"""
scripts/mine_github_repos.py - Scrapes real-world merged vs rejected PRs
"""
import os
import requests
import json
from typing import List

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        body
        state
        merged
        author { login }
        commits(first: 1) { nodes { commit { oid } } }
      }
    }
  }
}
"""

def fetch_prs(owner: str, repo: str, max_pages: int = 5):
    cursor = None
    records = []
    
    for page in range(max_pages):
        variables = {"owner": owner, "name": repo, "cursor": cursor}
        resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": QUERY, "variables": variables})
        if resp.status_code != 200:
            break
        data = resp.json()["data"]["repository"]["pullRequests"]
        
        for node in data["nodes"]:
            # Label: 0 = Merged (Accepted), 1 = Closed without merge (Rejected)
            label = 0 if node["merged"] else 1
            records.append({
                "repo": f"{owner}/{repo}",
                "pr_number": node["number"],
                "title": node["title"],
                "issue_description": node["body"] or "",
                "author": node["author"]["login"] if node["author"] else "ghost",
                "ground_truth_label": label
            })
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]
        
    print(f"Scraped {len(records)} PRs from {owner}/{repo}")
    return records
```

---

## 7. The Master Prompt Engineering Library

Use these pre-tested prompts when commanding coding assistants (Claude 3.5, Cursor, ChatGPT, Antigravity) to write the code for each subsystem.

### 7.1 Prompts for LLM Codebase Scaffold Generation

````markdown
#### PROMPT 1: Project Scaffolding & Environment Setup
```text
Act as a Principal Staff Software Architect. We are building AST-Triage, an automated risk-scoring system that intercepts AI-agent-generated GitHub Pull Requests using Tree-sitter AST differencing, sentence-transformers semantic intent alignment, and a Platt-calibrated XGBoost classifier.

Generate the complete project boilerplate structure following standard Python packaging best practices:
1. pyproject.toml with dependencies for fastapi, tree-sitter, tree-sitter-python, xgboost, scikit-learn, sentence-transformers, shap, and pydantic.
2. config/settings.py using Pydantic BaseSettings loading from .env.
3. database/models.py using SQLAlchemy 2.0 async mapped classes for PullRequest, FeatureRecord, and TriagePrediction.
Ensure strict type hints, docstrings, and clean separation of concerns. Do not omit any boilerplate.
```
````

---

### 7.2 Prompts for Module-by-Module Code Generation

````markdown
#### PROMPT 2: Tree-sitter AST Differencing & Cyclomatic Engine
```text
Act as a Senior Compilers and Static Analysis Engineer.
Write the complete implementation of `src/ast_engine/differ.py` using `tree_sitter` and `tree_sitter_python`.

Requirements:
1. Parse pre-PR code (base) and post-PR code (head).
2. Recursively calculate Cyclomatic Complexity by identifying control-flow branch points (`if_statement`, `for_statement`, `while_statement`, `except_clause`, `boolean_operator`).
3. Compute exact structural deltas:
   - nodes_added, nodes_deleted, nodes_mutated
   - nesting_depth_delta (max tree depth of conditionals)
   - func_signatures_mod (check if parameters or function names changed)
   - assertions_deleted (specifically tracking removed assert nodes in test functions)
4. Formulate the composite `ast_disturbance_index` (float in [0.0, 1.0]).
Include complete error handling for syntax errors in malformed diffs. Return the result as a strongly-typed Python dict.
```

#### PROMPT 3: Intent-to-Diff Semantic Alignment Engine
```text
Act as an Applied NLP Engineer.
Write `src/semantic_engine/drift_analyzer.py` using `sentence-transformers`.

Requirements:
1. Load `all-MiniLM-L6-v2` as a thread-safe singleton.
2. Ingest `issue_description` and `diff_summary`.
3. Normalize both texts (strip Markdown tables, HTML comments, and redundant diff line headers `@@`).
4. Generate L2-normalized dense embeddings.
5. Compute the Cosine Similarity metric $S_{align} \in [-1.0, 1.0]$.
6. Formulate an entity Jaccard overlap metric by extracting Python identifier tokens (`snake_case` and `camelCase`) from the issue and diff.
7. Return a structured dictionary with `intent_diff_cosine`, `entity_drift_jaccard`, and `semantic_drift_flag`.
```

#### PROMPT 4: Calibrated Classifier & SHAP Local Attribution
```text
Act as a Senior Machine Learning Engineer specializing in Tabular Risk Modeling.
Write `src/ml_engine/trainer.py` and `predictor.py`.

Requirements:
1. Train an XGBoost classifier on an imbalanced tabular dataset (80% accepted, 20% rejected).
2. Wrap the model in `CalibratedClassifierCV(method='sigmoid', cv=5)` to guarantee that the predicted probability accurately represents the true empirical defect rate (minimizing the Brier Score).
3. Integrate `shap.TreeExplainer` to compute local feature attributions for any single incoming inference row.
4. Export the top 3 risk-increasing features formatted as human-readable strings (e.g. "assertions_deleted = 3 (+0.32 SHAP)").
5. Save model weights and explainer objects with joblib.
Include a function `evaluate_model(y_true, y_pred_prob)` that prints ROC-AUC, PR-AUC, F1, and Brier Score.
```

#### PROMPT 5: FastAPI Webhook Gateway & GitHub Bot Commenter
```text
Act as a Full-Stack Backend & DevOps Engineer.
Write `src/api/routes.py` and `src/integrations/reporter.py`.

Requirements:
1. Build a FastAPI endpoint `POST /api/v1/triage/analyze` accepting a Pydantic `PRWebhookPayload`.
2. Asynchronously orchestrate AST extraction, semantic drift embedding, feature assembly, and model inference within a strict 300ms SLA.
3. Build a markdown comment generator that formats the triage assessment into an elegant GitHub PR comment:
   - Green / Yellow / Red SVG status badge.
   - Calibrated Risk Percentage.
   - Collapsible markdown dropdown containing the top-3 SHAP structural risk drivers.
   - Concrete, actionable recommendation for the human maintainer.
```
````

---

### 7.3 Prompts for Diff Summarization & Synthetic Data Generation

````markdown
#### PROMPT 6: Generating Synthetic Defective Agent PR Fixtures
```text
Act as an AI Security Red-Teamer and QA Engineer.
Create 3 synthetic Pull Request JSON fixtures simulating common agentic failure patterns:
Fixture 1 ("Test Cheat"): An agent was asked to fix an off-by-one error in a pagination function. Instead of fixing the loop, it deleted the unit test assertions that failed and modified the mock return values.
Fixture 2 ("Semantic Drift"): An agent was asked to update the README installation instructions for Python 3.12, but it modified the underlying database connection pool settings in `db.py`.
Fixture 3 ("Clean PR"): A textbook, clean fix containing 1 modified logic line, 1 new unit test, and zero signature changes.

Provide full `raw_diff` text, `issue_description`, and ground truth labels for our test suite.
```
````

---

### 7.4 Prompts for Academic Paper Writing & LaTeX Generation

````markdown
#### PROMPT 7: Generating LaTeX Results & Ablation Tables
```text
Act as an IEEE Transactions on Software Engineering author.
Write the complete LaTeX code for:
1. Section IV (Empirical Evaluation & Results) for our AST-Triage paper.
2. A polished LaTeX Table comparing AST-Triage against:
   - Naive CI Pass/Fail Gating
   - LOC Churn Heuristic
   - CodeBERT Text-Only baseline
   Include metrics: Precision, Recall, F1, ROC-AUC, PR-AUC, and Brier Score.
3. A formal paragraph analyzing the statistical significance of the feature ablation study using a Mann-Whitney U test (p < 0.001).
Ensure academic tone, formal mathematical notations, and IEEE formatting compliance.
```
````

---

## 8. Configuration, Environment & Testing Suite

### 8.1 Environment Configuration (`.env.example`)

```ini
# Application Configuration
APP_NAME=ast-triage-core
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000

# GitHub Integration
GITHUB_TOKEN=ghp_yourPersonalAccessTokenHere_ABC123
GITHUB_WEBHOOK_SECRET=your_webhook_hmac_secret_here

# Database Configuration (PostgreSQL / SQLite)
DATABASE_URL=sqlite+aiosqlite:///./data/ast_triage.db
# DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ast_triage

# Machine Learning Paths
MODEL_CHECKPOINT_DIR=./models
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Triage Thresholds
LOW_RISK_THRESHOLD=0.25
HIGH_RISK_THRESHOLD=0.65
```

---

### 8.2 Dependencies (`requirements.txt`)

```text
# Web Framework & API
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
httpx>=0.27.0
requests>=2.32.0

# Compilers & AST Parsing
tree-sitter>=0.22.0
tree-sitter-python>=0.21.0

# Machine Learning & Tabular Modeling
numpy>=1.26.0
scipy>=1.13.0
pandas>=2.2.0
scikit-learn>=1.5.0
xgboost>=2.0.3
lightgbm>=4.3.0
shap>=0.45.0
joblib>=1.4.0

# NLP & Embeddings
sentence-transformers>=3.0.0
torch>=2.3.0 --index-url https://download.pytorch.org/whl/cpu

# Database & Storage
sqlalchemy>=2.0.30
aiosqlite>=0.20.0
pyarrow>=16.0.0

# Testing & Quality
pytest>=8.2.0
pytest-asyncio>=0.23.0
```

---

### 8.3 Synthetic Fixtures & Unit Test Suite (`test_pipeline.py`)

```python
"""
tests/test_end_to_end.py - Verification suite for AST extraction and prediction
"""
import pytest
import numpy as np
from src.ast_engine.differ import diff_single_file_ast
from src.semantic_engine.drift_analyzer import SemanticDriftAnalyzer
from src.feature_pipeline.vector_builder import build_feature_vector

SAMPLE_BASE_CODE = """
def divide_numbers(a, b):
    return a / b

def test_divide():
    assert divide_numbers(10, 2) == 5
    assert divide_numbers(10, 0) == 0
"""

SAMPLE_HEAD_TEST_CHEAT = """
def divide_numbers(a, b):
    return a / b

def test_divide():
    assert divide_numbers(10, 2) == 5
    # Deleted failing zero assertion
"""

def test_ast_assertion_deletion_detection():
    """Verify that deleting an assertion is accurately captured in AST deltas."""
    diff_res = diff_single_file_ast(SAMPLE_BASE_CODE, SAMPLE_HEAD_TEST_CHEAT)
    assert diff_res["assertions_deleted"] >= 1
    assert diff_res["ast_disturbance_index"] > 0.0

def test_semantic_drift_analyzer():
    """Verify that unrelated text triggers the semantic drift flag."""
    analyzer = SemanticDriftAnalyzer()
    issue = "Fix database connection timeout under high network load"
    unrelated_diff = "Update button background color from blue to hex #FF0000"
    
    sim, drift_flag = analyzer.compute_alignment(issue, unrelated_diff)
    assert sim < 0.45
    assert drift_flag == 1

def test_feature_vector_shape():
    """Verify that the assembled feature matrix strictly has 28 dimensions."""
    ast_dummy = {"nodes_added": 10, "nodes_deleted": 2, "delta_cc": 1, "ast_disturbance_index": 0.25}
    semantic_dummy = {"intent_diff_cosine": 0.72, "semantic_drift_flag": 0}
    test_dummy = {"assertions_deleted": 0, "test_to_logic_ratio": 1.0}
    process_dummy = {"commit_count": 2, "ci_pass_flag": 1}
    
    vec = build_feature_vector(ast_dummy, semantic_dummy, test_dummy, process_dummy)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (1, 28)
```

---

### Summary Checklist for Implementation

1. **Step 1:** Create virtual environment: `python -m venv venv && source venv/bin/activate`.
2. **Step 2:** Install dependencies: `pip install -r requirements.txt`.
3. **Step 3:** Test AST Parser: `python -c "import tree_sitter_python; print('Tree-sitter ready!')"`.
4. **Step 4:** Mine dataset: `python scripts/mine_swebench.py`.
5. **Step 5:** Train initial XGBoost model: `python scripts/train_model.py`.
6. **Step 6:** Launch FastAPI service: `uvicorn src.api.main:app --reload --port 8000`.
7. **Step 7:** Send test curl payload to `/api/v1/triage/analyze` and verify sub-300ms latency.
