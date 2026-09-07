# 28-D Feature Vector Taxonomy

> Master catalog of the 28 numerical features computed for each pull request.

ASTRA maps every pull request into an ordered 28-dimensional vector $X \in \mathbb{R}^{28}$. Features are grouped into four orthogonal dimensions to prevent blind spots.

---

## 1. Complete Feature Matrix

| ID | Column Name | Type | Range | Group | Brief Description |
|---|---|---|---|---|---|
| **F01** | `f01_ast_nodes_added` | INT | $[0, \infty)$ | AST Structural | New AST nodes in head not in base |
| **F02** | `f02_ast_nodes_deleted` | INT | $[0, \infty)$ | AST Structural | Base AST nodes removed from head |
| **F03** | `f03_ast_nodes_mutated` | INT | $[0, \infty)$ | AST Structural | Nodes where type was preserved but content changed |
| **F04** | `f04_cyclomatic_delta` | INT | $[-50, 50]$ | AST Structural | Change in McCabe cyclomatic complexity ($CC_{head} - CC_{base}$) |
| **F05** | `f05_max_nesting_depth_delta` | INT | $[-20, 20]$ | AST Structural | Net change in maximum block nesting depth |
| **F06** | `f06_func_signatures_modified` | INT | $[0, \infty)$ | AST Structural | Functions with changed names, parameters, or defaults |
| **F07** | `f07_classes_modified` | INT | $[0, \infty)$ | AST Structural | Class definitions added, removed, or modified |
| **F08** | `f08_return_types_altered` | INT | $[0, \infty)$ | AST Structural | Functions where return type annotations changed |
| **F09** | `f09_call_graph_fan_out_delta` | INT | $(-\infty, \infty)$| AST Structural | Net change in distinct function/method call sites |
| **F10** | `f10_ast_disturbance_index` | FLOAT | $[0.0, 1.0]$ | AST Structural | Composite structural disruption metric |
| **F11** | `f11_try_catch_blocks_added` | INT | $[0, \infty)$ | AST Structural | New try/except error-handling blocks introduced |
| **F12** | `f12_control_flow_churn_ratio` | FLOAT | $[0.0, 1.0]$ | AST Structural | Fraction of total node modifications touching control flow |
| **F13** | `f13_intent_diff_cosine_sim` | FLOAT | $[-1.0, 1.0]$| Semantic NLP | Cosine similarity between issue prompt and diff text |
| **F14** | `f14_issue_title_diff_sim` | FLOAT | $[-1.0, 1.0]$| Semantic NLP | Cosine similarity between issue title and diff text |
| **F15** | `f15_entity_drift_jaccard` | FLOAT | $[0.0, 1.0]$ | Semantic NLP | Jaccard distance between code identifiers in issue and diff |
| **F16** | `f16_docstring_to_code_ratio` | FLOAT | $[0.0, 1.0]$ | Semantic NLP | Ratio of added comments/docstrings to executable code |
| **F17** | `f17_semantic_drift_flag` | INT | $\{0, 1\}$ | Semantic NLP | Binary flag: 1 if `f13_intent_diff_cosine_sim` < 0.45 else 0 |
| **F18** | `f18_issue_token_length` | INT | $[0, \infty)$ | Semantic NLP | Total token count in the issue prompt |
| **F19** | `f19_test_files_modified` | INT | $[0, \infty)$ | Test Churn | Count of test files modified in the PR |
| **F20** | `f20_test_ast_nodes_added` | INT | $[0, \infty)$ | Test Churn | Count of AST nodes added specifically inside test files |
| **F21** | `f21_test_assertions_deleted` | INT | $[0, \infty)$ | Test Churn | Count of test assertion nodes removed |
| **F22** | `f22_test_to_logic_ratio` | FLOAT | $[0.0, 1.0]$ | Test Churn | Ratio of test node modifications to total node modifications |
| **F23** | `f23_mock_patch_count_delta` | INT | $(-\infty, \infty)$| Test Churn | Net change in `@patch` and `unittest.mock` references |
| **F24** | `f24_commit_count` | INT | $[1, \infty)$ | Process | Total commit count comprising the PR |
| **F25** | `f25_files_touched_count` | INT | $[1, \infty)$ | Process | Total number of distinct files touched |
| **F26** | `f26_file_dispersion_entropy` | FLOAT | $[0.0, \infty)$ | Process | Shannon entropy of change distribution across directory trees |
| **F27** | `f27_ci_pass_flag` | INT | $\{0, 1\}$ | Process | CI run outcome: 1 if passed or clean, 0 if failed |
| **F28** | `f28_is_known_agent_bot` | INT | $\{0, 1\}$ | Process | 1 if authored by known bot/agent, 0 if human |

---

## 2. Feature Group Justification

1. **AST Structural (F01 to F12)**: Detects when an AI bot replaces clean modular functions with massive monolithic blocks, deletes safety guards, or changes function signatures unexpectedly.
2. **Semantic NLP (F13 to F18)**: Detects hallucinations where an agent generates syntactically valid code that solves an unrelated task or touches files outside the ticket scope.
3. **Test Churn (F19 to F23)**: Detects bad agent patterns, such as deleting broken assertions to force green test suites or adding zero tests for large logic changes.
4. **Process & Provenance (F24 to F28)**: Detects high-dispersion shotgun debugging where an agent touches dozens of directories across the repository.
