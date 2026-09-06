"""
src/ast_engine/cyclomatic.py - McCabe Cyclomatic Complexity calculator.

Traverses Tree-sitter syntax trees to count decision points
(if, for, while, except, boolean operators) and compute
cyclomatic complexity scores for pre/post PR code.

Implementation: Phase 2
"""
