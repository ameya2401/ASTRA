# AST Structural Features (F01 to F12)

> Implemented in [src/ast_engine/differ.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py) and [src/ast_engine/cyclomatic.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/cyclomatic.py).

The structural AST features capture syntactic changes between the base version and the PR head version of each modified Python file.

---

## 1. Feature Specifications

### F01: `nodes_added`
- **Definition**: Number of AST syntax nodes present in the head file that have no direct match in the base file.
- **Code reference**: [src/ast_engine/differ.py:L268-L330](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L268-L330).

### F02: `nodes_deleted`
- **Definition**: Number of AST syntax nodes present in the base file that are removed in the head file.
- **Code reference**: [src/ast_engine/differ.py:L268-L330](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L268-L330).

### F03: `nodes_mutated`
- **Definition**: Number of AST nodes where node type is preserved (e.g. `assignment` or `call`) but identifier, operator, or literal values changed.
- **Code reference**: [src/ast_engine/differ.py:L310-L345](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L310-L345).

### F04: `delta_cc` (Cyclomatic Complexity Delta)
- **Definition**: Net change in McCabe Cyclomatic Complexity:
  $$CC = 1 + \sum (\text{decision nodes})$$
  Decision node types include `if_statement`, `for_statement`, `while_statement`, `except_clause`, `with_statement`, `conditional_expression`, and `boolean_operator` (`and`, `or`).
- **Cap**: Clamped to the range `[-50, +50]`.
- **Code reference**: [src/ast_engine/cyclomatic.py:L35-L66](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/cyclomatic.py#L35-L66).

### F05: `nesting_depth_delta`
- **Definition**: Change in the maximum block nesting depth between head and base. Construct nodes that increment depth include `if`, `for`, `while`, `try`, `except`, `with`, and `elif`.
- **Code reference**: [src/ast_engine/cyclomatic.py:L69-L95](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/cyclomatic.py#L69-L95).

### F06: `func_signatures_mod`
- **Definition**: Count of function definitions where parameter names, default arguments, parameter counts, or positional/keyword constraints changed.
- **Code reference**: [src/ast_engine/differ.py:L360-L400](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L360-L400).

### F07: `classes_modified`
- **Definition**: Count of class definitions added, removed, or with modified inheritance bases.
- **Code reference**: [src/ast_engine/differ.py:L405-L435](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L405-L435).

### F08: `return_types_altered`
- **Definition**: Count of functions where explicit return type annotations were added, deleted, or modified.
- **Code reference**: [src/ast_engine/differ.py:L440-L470](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L440-L470).

### F09: `call_graph_fanout_delta`
- **Definition**: Net change in the number of distinct external function/method call sites:
  $$\Delta Fanout = |Calls_{head}| - |Calls_{base}|$$
- **Code reference**: [src/ast_engine/differ.py:L475-L510](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L475-L510).

### F10: `ast_disturbance_index`
- **Definition**: Composite disruption metric normalized between `0.0` and `1.0`. Combines relative node churn, control flow changes, and depth fluctuations:
  $$\text{Disturbance} = \min\left(1.0, \frac{\text{added} + \text{deleted} + 2 \times \text{mutated}}{\max(1, \text{base nodes})} \times 0.5 + \frac{|\Delta CC|}{10} \times 0.3 + \frac{|\Delta Nesting|}{5} \times 0.2\right)$$
- **Code reference**: [src/ast_engine/differ.py:L520-L555](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L520-L555).

### F11: `try_catch_added`
- **Definition**: Total count of new `try_statement` blocks introduced. AI agents frequently wrap failing statements in bare try-except blocks to pass tests silently.
- **Code reference**: [src/ast_engine/differ.py:L560-L575](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L560-L575).

### F12: `control_churn_ratio`
- **Definition**: Fraction of all node edits that specifically targeted control flow structures:
  $$\text{Control Churn Ratio} = \frac{\text{control nodes added} + \text{control nodes deleted}}{\max(1, \text{total nodes added} + \text{total nodes deleted})}$$
- **Code reference**: [src/ast_engine/differ.py:L580-L593](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py#L580-L593).
