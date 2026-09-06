"""
src/ast_engine/differ.py - AST structural comparison and metric extraction.

Computes structural deltas between base (pre-PR) and head (post-PR) code:
    - Node additions, deletions, mutations
    - Cyclomatic complexity delta
    - Nesting depth changes
    - Function signature modifications
    - AST disturbance index

Implementation: Phase 2
"""
