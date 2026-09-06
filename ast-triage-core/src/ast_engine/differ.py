"""
src/ast_engine/differ.py - Tree-sitter AST structural comparison and metric extraction.

Computes the 12 Structural AST Features (F01–F12) by comparing
pre-PR (base) and post-PR (head) source code at the syntax tree level.

Features computed:
    F01: ast_nodes_added        — New nodes in head not in base
    F02: ast_nodes_deleted      — Nodes in base missing from head
    F03: ast_nodes_mutated      — Nodes where type preserved but content changed
    F04: cyclomatic_delta       — CC(head) - CC(base), capped at [-50, +50]
    F05: nesting_depth_delta    — Max nesting depth change
    F06: func_signatures_mod    — Functions with changed parameters/names
    F07: classes_modified       — Class definitions added/removed/altered
    F08: return_types_altered   — Functions with changed return type annotations
    F09: call_graph_fanout_delta— Net change in external function calls
    F10: ast_disturbance_index  — Composite disruption metric in [0.0, 1.0]
    F11: try_catch_added        — New try/except blocks
    F12: control_churn_ratio    — Fraction of changes in control-flow nodes

Usage:
    from src.ast_engine.differ import diff_single_file_ast, diff_multi_file

    result = diff_single_file_ast(base_code, head_code)
    print(result["ast_disturbance_index"])  # 0.72
"""
import logging
from typing import Any, TypedDict

from tree_sitter import Node

from src.ast_engine.parser import (
    CALL_TYPES,
    CONTROL_FLOW_TYPES,
    EXCEPTION_HANDLING_TYPES,
    get_node_text,
    parse_code,
)
from src.ast_engine.cyclomatic import (
    compute_cyclomatic_complexity,
    compute_max_nesting_depth,
)

logger = logging.getLogger(__name__)


class ASTMetrics(TypedDict):
    """Strongly-typed dictionary for the 12 structural AST features (F01–F12)."""

    # F01–F03: Node volume changes
    nodes_added: int
    nodes_deleted: int
    nodes_mutated: int

    # F04–F05: Complexity changes
    delta_cc: int
    nesting_depth_delta: int

    # F06–F08: Signature & type changes
    func_signatures_mod: int
    classes_modified: int
    return_types_altered: int

    # F09: Dependency changes
    call_graph_fanout_delta: int

    # F10: Composite metric
    ast_disturbance_index: float

    # F11–F12: Exception handling & control flow
    try_catch_added: int
    control_flow_churn_ratio: float


# ──────────────────────────────────────────────────────────────
#  Node Counting & Analysis Helpers
# ──────────────────────────────────────────────────────────────

def _count_nodes(root_node: Node) -> dict[str, int]:
    """
    Counts total nodes, control-flow nodes, functions, classes,
    assertions, try/except blocks, and function calls in a tree.

    Uses cursor-based traversal (no recursion, no stack allocation)
    for optimal performance on large files.
    """
    counts = {
        "total": 0,
        "control": 0,
        "functions": 0,
        "classes": 0,
        "assertions": 0,
        "try_except": 0,
        "calls": 0,
    }
    cursor = root_node.walk()
    visited_children: bool = False

    while True:
        if not visited_children:
            counts["total"] += 1
            ntype = cursor.node.type

            if ntype in CONTROL_FLOW_TYPES:
                counts["control"] += 1
            if ntype == "function_definition":
                counts["functions"] += 1
            elif ntype == "class_definition":
                counts["classes"] += 1
            elif ntype == "assert_statement":
                counts["assertions"] += 1
            if ntype in EXCEPTION_HANDLING_TYPES:
                counts["try_except"] += 1
            if ntype in CALL_TYPES:
                counts["calls"] += 1

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

    return counts


def _extract_function_signatures(
    root_node: Node, source_bytes: bytes
) -> dict[str, dict[str, Any]]:
    """
    Extracts function signatures from the AST.

    For each function_definition node, captures:
        - name: function name identifier
        - params: list of parameter names (from the parameters node)
        - return_type: return type annotation text (if present)

    Returns:
        Dict mapping function name to its signature details.
        If duplicate function names exist, the last definition wins.
    """
    signatures: dict[str, dict[str, Any]] = {}

    def _walk(node: Node) -> None:
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            params_node = node.child_by_field_name("parameters")
            return_type_node = node.child_by_field_name("return_type")

            func_name = get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

            # Extract parameter names
            param_names: list[str] = []
            if params_node:
                for child in params_node.children:
                    if child.type in ("identifier", "typed_parameter",
                                      "default_parameter", "typed_default_parameter",
                                      "list_splat_pattern", "dictionary_splat_pattern"):
                        # For typed/default params, get the identifier child
                        if child.type == "identifier":
                            param_names.append(get_node_text(child, source_bytes))
                        elif child.type in ("typed_parameter", "default_parameter",
                                            "typed_default_parameter"):
                            id_child = child.child_by_field_name("name")
                            if id_child:
                                param_names.append(get_node_text(id_child, source_bytes))
                            else:
                                # Fallback: use first identifier child
                                for sub in child.children:
                                    if sub.type == "identifier":
                                        param_names.append(get_node_text(sub, source_bytes))
                                        break
                        elif child.type in ("list_splat_pattern", "dictionary_splat_pattern"):
                            # *args / **kwargs
                            for sub in child.children:
                                if sub.type == "identifier":
                                    param_names.append("*" + get_node_text(sub, source_bytes))
                                    break

            # Extract return type annotation
            return_type: str | None = None
            if return_type_node:
                return_type = get_node_text(return_type_node, source_bytes)

            signatures[func_name] = {
                "params": param_names,
                "return_type": return_type,
                "param_count": len(param_names),
            }

        # Recurse into children (functions can be nested)
        for child in node.children:
            _walk(child)

    _walk(root_node)
    return signatures


def _extract_class_info(
    root_node: Node, source_bytes: bytes
) -> dict[str, dict[str, Any]]:
    """
    Extracts class definitions and their inheritance info.

    Returns:
        Dict mapping class name to its metadata (bases, method count).
    """
    classes: dict[str, dict[str, Any]] = {}

    def _walk(node: Node) -> None:
        if node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            class_name = get_node_text(name_node, source_bytes) if name_node else "<anonymous>"

            # Extract base classes from argument_list
            bases: list[str] = []
            superclasses_node = node.child_by_field_name("superclasses")
            if superclasses_node:
                for child in superclasses_node.children:
                    if child.type not in ("(", ")", ","):
                        bases.append(get_node_text(child, source_bytes))

            # Count methods inside the class body
            method_count = 0
            body_node = node.child_by_field_name("body")
            if body_node:
                for child in body_node.children:
                    if child.type == "function_definition":
                        method_count += 1

            classes[class_name] = {
                "bases": bases,
                "method_count": method_count,
            }

        for child in node.children:
            _walk(child)

    _walk(root_node)
    return classes


def _build_node_fingerprint_map(
    root_node: Node, source_bytes: bytes
) -> dict[str, list[str]]:
    """
    Builds a mapping of (node_type, start_position) -> content_hash
    for mutation detection.

    Groups nodes by type and captures their text content for comparison.
    Only leaf and near-leaf nodes are included (depth ≤ 3 from leaves)
    to avoid counting container nodes that change when children change.

    Returns:
        Dict mapping node_type to a sorted list of content strings.
    """
    fingerprints: dict[str, list[str]] = {}

    def _walk(node: Node, depth: int = 0) -> int:
        """Returns the max depth below this node."""
        if not node.children:
            # Leaf node
            ntype = node.type
            text = get_node_text(node, source_bytes)
            fingerprints.setdefault(ntype, []).append(text)
            return 0

        max_child_depth = 0
        for child in node.children:
            child_depth = _walk(child, depth + 1)
            max_child_depth = max(max_child_depth, child_depth)

        # Include near-leaf nodes (within 2 levels of leaves)
        if max_child_depth <= 2:
            ntype = node.type
            text = get_node_text(node, source_bytes)
            fingerprints.setdefault(ntype, []).append(text)

        return max_child_depth + 1

    _walk(root_node)

    # Sort for consistent comparison
    for key in fingerprints:
        fingerprints[key].sort()

    return fingerprints


def _count_mutations(
    base_fingerprints: dict[str, list[str]],
    head_fingerprints: dict[str, list[str]],
) -> int:
    """
    Counts nodes where the type is preserved but the content changed.

    A mutation occurs when a node_type exists in both trees but
    the set of content strings differs. We count the symmetric difference
    between content lists for shared node types.

    Returns:
        Number of mutated node instances.
    """
    mutations: int = 0
    all_types = set(base_fingerprints.keys()) & set(head_fingerprints.keys())

    for ntype in all_types:
        base_contents = base_fingerprints[ntype]
        head_contents = head_fingerprints[ntype]

        # Only count as mutations if the type exists in both but content differs
        if base_contents != head_contents:
            # Use multiset difference to count actual mutations
            # (not just additions/deletions which are captured by F01/F02)
            base_copy = list(base_contents)
            matched = 0
            for item in head_contents:
                if item in base_copy:
                    base_copy.remove(item)
                    matched += 1

            # Mutations = nodes of this type that exist in both but changed
            min_count = min(len(base_contents), len(head_contents))
            unmatched = min_count - matched
            mutations += max(0, unmatched)

    return mutations


# ──────────────────────────────────────────────────────────────
#  Core Public API
# ──────────────────────────────────────────────────────────────

def diff_single_file_ast(base_code: str, head_code: str) -> ASTMetrics:
    """
    Computes all 12 structural AST deltas between base and head code.

    This is the primary entry point for single-file AST analysis.
    It parses both versions, extracts metrics, and computes the
    composite AST disturbance index.

    Args:
        base_code: Pre-PR Python source code (can be empty for new files).
        head_code: Post-PR Python source code (can be empty for deleted files).

    Returns:
        ASTMetrics TypedDict with all 12 structural features.

    Raises:
        No exceptions — malformed code is handled gracefully by Tree-sitter's
        error-tolerant parser. Parse errors are logged as warnings.
    """
    # Parse both versions
    base_bytes = bytes(base_code, "utf8")
    head_bytes = bytes(head_code, "utf8")

    base_tree = parse_code(base_code)
    head_tree = parse_code(head_code)

    # Log parse errors (Tree-sitter still produces a valid tree)
    if base_tree.root_node.has_error:
        logger.warning("Parse errors detected in base code (error-tolerant parsing continues)")
    if head_tree.root_node.has_error:
        logger.warning("Parse errors detected in head code (error-tolerant parsing continues)")

    # ── F04: Cyclomatic Complexity Delta ──
    cc_base = compute_cyclomatic_complexity(base_tree.root_node)
    cc_head = compute_cyclomatic_complexity(head_tree.root_node)
    delta_cc = max(-50, min(50, cc_head - cc_base))  # Capped at [-50, +50]

    # ── F05: Nesting Depth Delta ──
    depth_base = compute_max_nesting_depth(base_tree.root_node)
    depth_head = compute_max_nesting_depth(head_tree.root_node)
    nesting_depth_delta = depth_head - depth_base

    # ── Node counts ──
    base_counts = _count_nodes(base_tree.root_node)
    head_counts = _count_nodes(head_tree.root_node)

    # ── F01: Nodes Added ──
    node_delta = head_counts["total"] - base_counts["total"]
    nodes_added = max(0, node_delta)

    # ── F02: Nodes Deleted ──
    nodes_deleted = max(0, -node_delta)

    # ── F03: Nodes Mutated ──
    base_fingerprints = _build_node_fingerprint_map(base_tree.root_node, base_bytes)
    head_fingerprints = _build_node_fingerprint_map(head_tree.root_node, head_bytes)
    nodes_mutated = _count_mutations(base_fingerprints, head_fingerprints)

    # ── F06: Function Signatures Modified ──
    base_sigs = _extract_function_signatures(base_tree.root_node, base_bytes)
    head_sigs = _extract_function_signatures(head_tree.root_node, head_bytes)
    func_signatures_mod = _count_signature_changes(base_sigs, head_sigs)

    # ── F07: Classes Modified ──
    base_classes = _extract_class_info(base_tree.root_node, base_bytes)
    head_classes = _extract_class_info(head_tree.root_node, head_bytes)
    classes_modified = _count_class_changes(base_classes, head_classes)

    # ── F08: Return Types Altered ──
    return_types_altered = _count_return_type_changes(base_sigs, head_sigs)

    # ── F09: Call Graph Fan-out Delta ──
    call_graph_fanout_delta = head_counts["calls"] - base_counts["calls"]

    # ── F11: Try/Catch Blocks Added ──
    try_catch_added = max(0, head_counts["try_except"] - base_counts["try_except"])

    # ── F12: Control Flow Churn Ratio ──
    control_delta = abs(head_counts["control"] - base_counts["control"])
    total_node_churn = abs(node_delta) + 1e-8  # epsilon to avoid division by zero
    control_flow_churn_ratio = round(control_delta / total_node_churn, 4)
    control_flow_churn_ratio = min(1.0, control_flow_churn_ratio)

    # ── F10: AST Disturbance Index ──
    # D_AST = 0.4 * |ΔCC|/max(1,CC_base) + 0.3 * NodesChanged/N_total + 0.3 * I_sig_break
    sig_break = 1 if func_signatures_mod > 0 else 0
    nodes_changed = nodes_added + nodes_deleted + nodes_mutated
    ast_disturbance = (
        0.4 * (abs(delta_cc) / max(1, cc_base))
        + 0.3 * (nodes_changed / max(1, base_counts["total"]))
        + 0.3 * sig_break
    )
    ast_disturbance_index = min(1.0, round(ast_disturbance, 4))

    return ASTMetrics(
        nodes_added=nodes_added,
        nodes_deleted=nodes_deleted,
        nodes_mutated=nodes_mutated,
        delta_cc=delta_cc,
        nesting_depth_delta=nesting_depth_delta,
        func_signatures_mod=func_signatures_mod,
        classes_modified=classes_modified,
        return_types_altered=return_types_altered,
        call_graph_fanout_delta=call_graph_fanout_delta,
        ast_disturbance_index=ast_disturbance_index,
        try_catch_added=try_catch_added,
        control_flow_churn_ratio=control_flow_churn_ratio,
    )


def diff_multi_file(
    file_diffs: list[dict[str, str]],
) -> ASTMetrics:
    """
    Aggregates AST metrics across multiple file diffs.

    Args:
        file_diffs: List of dicts, each with 'base_code' and 'head_code' keys.
                    For new files, base_code should be "".
                    For deleted files, head_code should be "".

    Returns:
        Aggregated ASTMetrics across all files. Integer fields are summed,
        float fields are averaged, delta_cc is summed, and
        ast_disturbance_index is recomputed from aggregated values.
    """
    if not file_diffs:
        return _empty_metrics()

    # Accumulate metrics from all files
    totals: dict[str, float] = {key: 0 for key in ASTMetrics.__annotations__}
    file_count = 0

    for file_diff in file_diffs:
        try:
            base_code = file_diff.get("base_code", "")
            head_code = file_diff.get("head_code", "")
            metrics = diff_single_file_ast(base_code, head_code)

            for key in metrics:
                totals[key] += metrics[key]  # type: ignore[operator]

            file_count += 1
        except Exception as e:
            logger.error(f"Error processing file diff: {e}", exc_info=True)
            continue

    if file_count == 0:
        return _empty_metrics()

    # Average the float metrics, keep int sums
    result = ASTMetrics(
        nodes_added=int(totals["nodes_added"]),
        nodes_deleted=int(totals["nodes_deleted"]),
        nodes_mutated=int(totals["nodes_mutated"]),
        delta_cc=max(-50, min(50, int(totals["delta_cc"]))),
        nesting_depth_delta=int(totals["nesting_depth_delta"]),
        func_signatures_mod=int(totals["func_signatures_mod"]),
        classes_modified=int(totals["classes_modified"]),
        return_types_altered=int(totals["return_types_altered"]),
        call_graph_fanout_delta=int(totals["call_graph_fanout_delta"]),
        ast_disturbance_index=min(1.0, round(totals["ast_disturbance_index"] / file_count, 4)),
        try_catch_added=int(totals["try_catch_added"]),
        control_flow_churn_ratio=min(1.0, round(totals["control_flow_churn_ratio"] / file_count, 4)),
    )
    return result


# ──────────────────────────────────────────────────────────────
#  Internal Comparison Helpers
# ──────────────────────────────────────────────────────────────

def _count_signature_changes(
    base_sigs: dict[str, dict[str, Any]],
    head_sigs: dict[str, dict[str, Any]],
) -> int:
    """
    Counts function signatures that were modified between base and head.

    A modification is detected when a function exists in both versions
    but its parameter list (names or count) has changed.
    Functions that are entirely added or removed are also counted.
    """
    modified = 0
    all_func_names = set(base_sigs.keys()) | set(head_sigs.keys())

    for name in all_func_names:
        if name not in base_sigs or name not in head_sigs:
            # Function added or removed entirely
            modified += 1
        else:
            base_params = base_sigs[name]["params"]
            head_params = head_sigs[name]["params"]
            if base_params != head_params:
                modified += 1

    return modified


def _count_class_changes(
    base_classes: dict[str, dict[str, Any]],
    head_classes: dict[str, dict[str, Any]],
) -> int:
    """
    Counts classes that were added, removed, or had inheritance altered.
    """
    modified = 0
    all_class_names = set(base_classes.keys()) | set(head_classes.keys())

    for name in all_class_names:
        if name not in base_classes or name not in head_classes:
            # Class added or removed
            modified += 1
        else:
            # Check if inheritance chain changed
            if base_classes[name]["bases"] != head_classes[name]["bases"]:
                modified += 1

    return modified


def _count_return_type_changes(
    base_sigs: dict[str, dict[str, Any]],
    head_sigs: dict[str, dict[str, Any]],
) -> int:
    """
    Counts functions where return type annotation changed.
    """
    changed = 0
    common_funcs = set(base_sigs.keys()) & set(head_sigs.keys())

    for name in common_funcs:
        base_rt = base_sigs[name].get("return_type")
        head_rt = head_sigs[name].get("return_type")
        if base_rt != head_rt:
            changed += 1

    return changed


def _empty_metrics() -> ASTMetrics:
    """Returns a zeroed-out ASTMetrics dict for edge cases."""
    return ASTMetrics(
        nodes_added=0,
        nodes_deleted=0,
        nodes_mutated=0,
        delta_cc=0,
        nesting_depth_delta=0,
        func_signatures_mod=0,
        classes_modified=0,
        return_types_altered=0,
        call_graph_fanout_delta=0,
        ast_disturbance_index=0.0,
        try_catch_added=0,
        control_flow_churn_ratio=0.0,
    )
