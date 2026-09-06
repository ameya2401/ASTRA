# Phase 2: Tree-sitter AST Differencing & Cyclomatic Engine

**Goal:** Implement the syntax tree parser that calculates structural code disruption without relying on plain-text diffs.

---

## Instructions for the AI Agent

Act as a Senior Compilers and Static Analysis Engineer.
Write the complete implementation of `src/ast_engine/differ.py` using `tree_sitter` and `tree_sitter_python` in `e:\study\ASTRA\ast-triage-core`.

**Requirements:**

1. Create functionality to parse pre-PR code (base) and post-PR code (head).
2. Recursively calculate Cyclomatic Complexity by identifying control-flow branch points (`if_statement`, `for_statement`, `while_statement`, `except_clause`, `boolean_operator`).
3. Compute exact structural deltas:
   - `nodes_added`, `nodes_deleted`, `nodes_mutated`
   - `nesting_depth_delta` (max tree depth of conditionals)
   - `func_signatures_mod` (check if parameters or function names changed)
   - `assertions_deleted` (specifically tracking removed `assert` nodes in test functions)
4. Formulate the composite `ast_disturbance_index` (float in `[0.0, 1.0]`).
5. Include complete error handling for syntax errors in malformed diffs. 
6. Return the result as a strongly-typed Python dict containing the extracted structural features.
