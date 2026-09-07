# CLI & Standalone Runners

> Standalone command-line tools for running AST differencing and semantic drift analysis locally.

ASTRA provides dedicated CLI runners under [ast-triage-core/scripts/](file:///e:/study/ASTRA/ast-triage-core/scripts/) that allow testing the engines without running the full API server.

---

## 1. AST Differ CLI (`run_ast_diff.py`)

Implementation: [scripts/run_ast_diff.py](file:///e:/study/ASTRA/ast-triage-core/scripts/run_ast_diff.py)

### Usage Modes

1. **Built-in Demo**:
   Compares a simple integer sum loop with an updated version containing optional filtering and a try-catch block:
   ```powershell
   python scripts/run_ast_diff.py
   ```
2. **Comparing Two Local Files**:
   ```powershell
   python scripts/run_ast_diff.py --base path/to/base.py --head path/to/head.py
   ```
3. **Structured JSON Output**:
   ```powershell
   python scripts/run_ast_diff.py --base path/to/base.py --head path/to/head.py --json
   ```

### Sample Output Format

```text
================================================================
          AST-Triage Structural Differencing Report
================================================================
  Nodes Added:                 14
  Nodes Deleted:               0
  Nodes Mutated:               2
  Cyclomatic Complexity Delta: +2
  Nesting Depth Delta:         +1
  Function Signatures Mod:     1
  Classes Modified:            0
  Return Types Altered:        0
  Call Graph Fan-out Delta:    0
  AST Disturbance Index:       0.4286
  Try/Catch Blocks Added:      1
  Control Flow Churn Ratio:    0.3333
================================================================
```

---

## 2. Semantic Drift CLI (`run_semantic_drift.py`)

Implementation: [scripts/run_semantic_drift.py](file:///e:/study/ASTRA/ast-triage-core/scripts/run_semantic_drift.py)

### Usage Modes

1. **Built-in Comparison Demo**:
   Evaluates an aligned scenario (database timeout bug vs connection pool patch) and a drifted scenario (database timeout bug vs unrequested markdown docs rewrite):
   ```powershell
   python scripts/run_semantic_drift.py
   ```
2. **Custom Issue & Diff Files**:
   ```powershell
   python scripts/run_semantic_drift.py --issue path/to/issue.md --diff path/to/patch.diff --title "Fix db timeout"
   ```
3. **JSON Output**:
   ```powershell
   python scripts/run_semantic_drift.py --json
   ```
4. **Save Inspection Reports Locally**:
   ```powershell
   python scripts/run_semantic_drift.py --save
   ```
   Writes formatted reports to `test_reports/` (git-ignored).

### Sample Output Format

```text
================================================================
         AST-Triage Semantic Drift Analysis Report
================================================================
  Scenario:                    Aligned PR Demo
  Issue Title:                 Fix SQLite connection timeout under load
  Intent-Diff Cosine Sim:      0.7342 (ALIGNED)
  Title-Diff Cosine Sim:       0.6891
  Entity Drift Jaccard:        0.2500
  Docstring-to-Code Ratio:     0.1875
  Semantic Drift Flag:         0 (PASS)
  Issue Token Length:          45 tokens
================================================================
```
