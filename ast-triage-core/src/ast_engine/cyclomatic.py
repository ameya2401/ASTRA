"""
src/ast_engine/cyclomatic.py - McCabe Cyclomatic Complexity calculator.

Traverses Tree-sitter syntax trees to count decision points
(if, for, while, except, boolean operators) and compute
cyclomatic complexity scores.

McCabe's formula:  CC = 1 + (number of decision points)

This simplified counting approach is equivalent to M = E − N + 2P
for single-function analysis, where each decision point adds one edge.

Usage:
    from src.ast_engine.parser import parse_code
    from src.ast_engine.cyclomatic import compute_cyclomatic_complexity

    tree = parse_code("if x: pass\\nfor i in r: pass")
    cc = compute_cyclomatic_complexity(tree.root_node)
    print(cc)  # 3 (base 1 + if + for)
"""
from tree_sitter import Node

from src.ast_engine.parser import CONTROL_FLOW_TYPES, NESTING_TYPES


def compute_cyclomatic_complexity(root_node: Node) -> int:
    """
    Calculates McCabe Cyclomatic Complexity by counting decision points.

    Traverses the entire syntax tree using a TreeCursor (stack-free iteration)
    and counts nodes whose type is in CONTROL_FLOW_TYPES.

    Args:
        root_node: The root node of a Tree-sitter parse tree.

    Returns:
        Integer cyclomatic complexity score (minimum 1 for any code).
    """
    complexity: int = 1
    cursor = root_node.walk()
    visited_children: bool = False

    while True:
        if not visited_children:
            if cursor.node.type in CONTROL_FLOW_TYPES:
                complexity += 1
            if cursor.goto_first_child():
                visited_children = False
                continue
        if cursor.goto_next_sibling():
            visited_children = False
            continue
        if cursor.goto_parent():
            visited_children = True
            continue
        break

    return complexity


def compute_max_nesting_depth(root_node: Node) -> int:
    """
    Computes the maximum nesting depth of control-flow constructs.

    Walks the tree recursively, tracking the current nesting level.
    Only NESTING_TYPES nodes increment the depth counter.

    Args:
        root_node: The root node of a Tree-sitter parse tree.

    Returns:
        The deepest nesting level found (0 if no nesting constructs).
    """
    max_depth: int = 0

    def _walk(node: Node, current_depth: int) -> None:
        nonlocal max_depth

        depth_increment = 1 if node.type in NESTING_TYPES else 0
        new_depth = current_depth + depth_increment

        if new_depth > max_depth:
            max_depth = new_depth

        for child in node.children:
            _walk(child, new_depth)

    _walk(root_node, 0)
    return max_depth
