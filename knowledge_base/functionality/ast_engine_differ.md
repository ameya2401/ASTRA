# AST Differencing Engine

> Implementation: [src/ast_engine/](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/)  
> Key modules: [parser.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/parser.py), [cyclomatic.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/cyclomatic.py), [differ.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py)

The AST differencing engine compares two Python source states (base and head) at the syntax tree level. It computes features F01 through F12.

---

## 1. Tree-Sitter Parser Wrapper

Located in [src/ast_engine/parser.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/parser.py):

- **Grammar Initialization**: Loads the pre-compiled C-binding grammar for Python once at module import:
  ```python
  import tree_sitter_python as tspython
  from tree_sitter import Language, Parser

  PY_LANGUAGE: Language = Language(tspython.language())
  _parser: Parser = Parser(PY_LANGUAGE)
  ```
- **Error Tolerance**: When an incoming agent PR contains invalid syntax, Tree-sitter builds an error-tolerant tree where erroneous tokens become `ERROR` nodes without throwing exceptions. The parser checks `tree.root_node.has_error` and logs warnings while continuing extraction.

---

## 2. Cyclomatic Complexity and Nesting Depth

Located in [src/ast_engine/cyclomatic.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/cyclomatic.py):

- **Decision Points**: Walks the syntax tree using iterative stack traversal to count branching nodes:
  - `if_statement`
  - `for_statement`
  - `while_statement`
  - `except_clause`
  - `with_statement`
  - `conditional_expression` (ternary operator)
  - `boolean_operator` (`and`, `or` short-circuit branches)
- **Complexity Formula**:
  $$\text{Complexity} = 1 + \sum \text{decision nodes}$$
- **Nesting Depth**: Tracks current depth by pushing to an explicit stack whenever entering block constructs (`if`, `for`, `while`, `try`, `except`, `with`, `elif`) and records the peak depth reached in the file.

---

## 3. Differencing Algorithm

Located in [src/ast_engine/differ.py](file:///e:/study/ASTRA/ast-triage-core/src/ast_engine/differ.py):

```
Base Source Code ──> parse_code() ──> Base AST Root
                                           │
                                           ├──> Node Matching & Churn Counter
                                           │    (Type, Named Children, Text Hash)
                                           │
Head Source Code ──> parse_code() ──> Head AST Root
                                           │
                                           ▼
                                    ASTMetrics Dictionary
                                    (F01 - F12)
```

1. **Multi-File Aggregation**:
   - `diff_multi_file(file_pairs)` accepts pairs of `(file_path, base_code, head_code)`.
   - Structural counts (`nodes_added`, `func_signatures_mod`) are summed across all files.
   - Fractional and bounded metrics (`delta_cc`, `ast_disturbance_index`, `control_churn_ratio`) are weighted by the relative churn of each file.
2. **Signature Delta Extraction**:
   - Compares parameters of matching function names between base and head.
   - Flags changes when parameter count, parameter names, or type hints differ.
3. **Disturbance Index Calculation**:
   - Integrates relative node modifications, cyclomatic jump, and nesting change into a single normalized index in `[0.0, 1.0]`.
