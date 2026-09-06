"""
src.ast_engine - Tree-sitter AST parsing and structural code analysis.

Provides structural AST comparison between pre-PR and post-PR code
to compute the 12 structural features (F01–F12) used by the
AST-Triage risk scoring model.

Modules:
    parser:     Tree-sitter Python grammar wrapper and node type constants
    cyclomatic: McCabe Cyclomatic Complexity and nesting depth calculators
    differ:     Full structural AST comparison engine (primary entry point)

Quick Usage:
    from src.ast_engine.differ import diff_single_file_ast

    result = diff_single_file_ast(base_code, head_code)
    print(result["ast_disturbance_index"])
"""
from src.ast_engine.differ import diff_single_file_ast, diff_multi_file, ASTMetrics
from src.ast_engine.cyclomatic import compute_cyclomatic_complexity, compute_max_nesting_depth
from src.ast_engine.parser import parse_code

__all__ = [
    "diff_single_file_ast",
    "diff_multi_file",
    "ASTMetrics",
    "compute_cyclomatic_complexity",
    "compute_max_nesting_depth",
    "parse_code",
]
