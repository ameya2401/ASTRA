# Test & Process Features (F19 to F28)

> Defined in [database/models.py:L182-L195](file:///e:/study/ASTRA/ast-triage-core/database/models.py#L182-L195) and assembled in [src/feature_pipeline/vector_builder.py](file:///e:/study/ASTRA/ast-triage-core/src/feature_pipeline/vector_builder.py).

Test churn and process provenance features capture software engineering hygiene and authorship patterns.

---

## 1. Test Churn Features (F19 to F23)

Autonomous agents frequently struggle with test maintenance. They often alter existing assertions to fit buggy implementations or skip tests entirely.

### F19: `test_files_modified`
- **Definition**: Number of files matching test path heuristics (such as `tests/`, `test_*.py`, `*_test.py`) modified in the PR.
- **Risk Indicator**: Logic-heavy changes with zero test files modified suggest an unverified PR.

### F20: `test_ast_nodes_added`
- **Definition**: Count of new AST nodes added exclusively inside identified test files. Measures the actual volume of new test logic introduced.

### F21: `test_assertions_deleted`
- **Definition**: Count of `assert` statements and `self.assert*` calls removed from test files.
- **Risk Indicator**: Agents frequently delete failing test cases rather than fixing underlying code defects. A high value is a strong defect signal.

### F22: `test_to_logic_ratio`
- **Definition**: Fraction of total AST modifications that occurred in test files versus production source code:
  $$\text{Ratio} = \frac{\Delta \text{Test Nodes}}{\Delta \text{Test Nodes} + \Delta \text{Production Nodes}}$$
  Bounded in $[0.0, 1.0]$. A value of `0.0` represents zero test changes.

### F23: `mock_patch_count_delta`
- **Definition**: Net change in mock decorator or context manager instances (`unittest.mock.patch`, `mocker.patch`, `@patch`).
- **Risk Indicator**: Rapid increases in mocks can indicate over-mocking where real behavior is bypassed to force tests green.

---

## 2. Process & Provenance Features (F24 to F28)

Process features track the git interaction history, directory sprawl, and author identity.

### F24: `commit_count`
- **Definition**: Total number of git commits included in the PR branch.
- **Risk Indicator**: Agent PRs with 20+ micro-commits often reflect wandering trial-and-error loops.

### F25: `files_touched_count`
- **Definition**: Total number of distinct repository files touched by the diff across all file types.

### F26: `file_dispersion_entropy`
- **Definition**: Shannon entropy of file modifications distributed across root directories:
  $$H = -\sum_{i=1}^{K} p_i \log_2(p_i)$$
  where $p_i$ is the proportion of edits occurring in top-level directory $i$.
- **Interpretation**: A change concentrated in `src/ast_engine/` has low entropy (localized). A change scattering edits across `src/`, `docs/`, `config/`, and `database/` has high entropy (shotgun modification).

### F27: `ci_pass_flag`
- **Definition**: Binary flag reflecting continuous integration status. `1` if all checks passed, `0` if checks failed or were skipped.

### F28: `is_known_agent_bot`
- **Definition**: Binary indicator set to `1` if the PR author is an identified autonomous bot account (e.g. usernames containing `[bot]`, `devin-ai`, `claude-code`, `copilot`), otherwise `0` for human contributors.
