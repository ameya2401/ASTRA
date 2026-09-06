"""
src/ast_engine/parser.py - Tree-sitter wrapper for Python grammar initialization.

Provides a pre-configured Tree-sitter parser for Python source code.
Handles grammar loading and provides a clean interface for parsing
raw source strings into syntax trees.

Usage:
    from src.ast_engine.parser import parse_code, PY_LANGUAGE

    tree = parse_code("def foo(): return 42")
    print(tree.root_node.type)  # "module"
"""
import tree_sitter_python as tspython
from tree_sitter import Language, Parser, Tree, Node

# Initialize the Python language binding once at module load time.
# tree-sitter-python provides pre-compiled grammar via tspython.language().
PY_LANGUAGE: Language = Language(tspython.language())

# Module-level parser instance, pre-configured for Python.
_parser: Parser = Parser(PY_LANGUAGE)

# ----- Node type sets used across the AST engine -----

# Decision points that contribute to McCabe Cyclomatic Complexity.
# Includes control-flow statements AND boolean operators (short-circuit branching).
CONTROL_FLOW_TYPES: set[str] = {
    "if_statement",
    "for_statement",
    "while_statement",
    "except_clause",
    "with_statement",
    "conditional_expression",   # ternary: x if cond else y
    "boolean_operator",         # `and` / `or` (short-circuit branch)
}

# Node types used for nesting depth analysis (block-creating constructs).
NESTING_TYPES: set[str] = {
    "if_statement",
    "for_statement",
    "while_statement",
    "except_clause",
    "with_statement",
    "try_statement",
    "elif_clause",
}

# Exception-handling node types.
EXCEPTION_HANDLING_TYPES: set[str] = {
    "try_statement",
    "except_clause",
}

# Nodes that represent function/method calls.
CALL_TYPES: set[str] = {
    "call",
}


def parse_code(code_str: str) -> Tree:
    """
    Parses raw Python source code into a Tree-sitter syntax tree.

    Args:
        code_str: Python source code as a string.

    Returns:
        A Tree-sitter Tree object. The root node is accessible via tree.root_node.

    Note:
        Tree-sitter is error-tolerant — it always produces a valid tree,
        even for syntactically broken code. Check root_node.has_error to
        detect parse errors.
    """
    return _parser.parse(bytes(code_str, "utf8"))


def get_node_text(node: Node, source_bytes: bytes) -> str:
    """
    Extracts the source text corresponding to a Tree-sitter node.

    Args:
        node: A Tree-sitter Node object.
        source_bytes: The original source code as bytes.

    Returns:
        The text content of the node as a string.
    """
    return source_bytes[node.start_byte:node.end_byte].decode("utf8")
