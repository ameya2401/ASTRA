"""
tests/test_ast_engine.py - Tests for the Tree-sitter AST differencing engine.

Validates:
    - Correct parsing of Python source code
    - Cyclomatic complexity computation
    - Max nesting depth calculation
    - Structural delta calculations (all 12 features F01-F12)
    - Function signature modification detection
    - Class modification detection
    - Return type annotation change detection
    - AST disturbance index normalization
    - Multi-file aggregation
    - Error handling for malformed / empty code
"""
import pytest
from src.ast_engine.parser import parse_code, CONTROL_FLOW_TYPES
from src.ast_engine.cyclomatic import compute_cyclomatic_complexity, compute_max_nesting_depth
from src.ast_engine.differ import diff_single_file_ast, diff_multi_file


# ──────────────────────────────────────────────────────────────
#  Parser Tests
# ──────────────────────────────────────────────────────────────

class TestParser:
    """Tests for the Tree-sitter Python parser wrapper."""

    def test_parse_simple_code(self) -> None:
        """Parser produces a valid tree for simple Python code."""
        tree = parse_code("x = 42")
        assert tree.root_node.type == "module"
        assert not tree.root_node.has_error

    def test_parse_function_definition(self) -> None:
        """Parser correctly identifies function_definition nodes."""
        code = "def greet(name: str) -> str:\n    return f'Hello, {name}'"
        tree = parse_code(code)
        root = tree.root_node
        assert root.children[0].type == "function_definition"

    def test_parse_empty_string(self) -> None:
        """Parser handles empty input gracefully."""
        tree = parse_code("")
        assert tree.root_node.type == "module"
        assert tree.root_node.child_count == 0

    def test_parse_malformed_code(self) -> None:
        """Parser is error-tolerant — produces a tree even for broken syntax."""
        tree = parse_code("def foo(:\n    return")
        assert tree.root_node.type == "module"
        assert tree.root_node.has_error  # Errors are flagged but tree is valid


# ──────────────────────────────────────────────────────────────
#  Cyclomatic Complexity Tests
# ──────────────────────────────────────────────────────────────

class TestCyclomaticComplexity:
    """Tests for McCabe Cyclomatic Complexity calculation."""

    def test_empty_code_has_complexity_one(self) -> None:
        """Empty/trivial code has base complexity of 1."""
        tree = parse_code("")
        assert compute_cyclomatic_complexity(tree.root_node) == 1

    def test_linear_code(self) -> None:
        """Code with no branches has complexity 1."""
        code = "x = 1\ny = 2\nz = x + y"
        tree = parse_code(code)
        assert compute_cyclomatic_complexity(tree.root_node) == 1

    def test_single_if(self) -> None:
        """Single if statement adds 1 to complexity."""
        code = "if x > 0:\n    pass"
        tree = parse_code(code)
        assert compute_cyclomatic_complexity(tree.root_node) == 2

    def test_if_elif_else(self) -> None:
        """If/elif chain: each branch point counts."""
        code = "if x > 0:\n    pass\nelif x < 0:\n    pass\nelse:\n    pass"
        tree = parse_code(code)
        # if_statement counts once, elif is another if_statement inside
        cc = compute_cyclomatic_complexity(tree.root_node)
        assert cc >= 2  # At minimum if + elif

    def test_for_loop(self) -> None:
        """For loop adds 1 to complexity."""
        code = "for i in range(10):\n    print(i)"
        tree = parse_code(code)
        assert compute_cyclomatic_complexity(tree.root_node) == 2

    def test_while_loop(self) -> None:
        """While loop adds 1 to complexity."""
        code = "while True:\n    break"
        tree = parse_code(code)
        assert compute_cyclomatic_complexity(tree.root_node) == 2

    def test_boolean_operators(self) -> None:
        """Boolean operators (and, or) each add 1 to complexity."""
        code = "if x > 0 and y > 0:\n    pass"
        tree = parse_code(code)
        # if_statement + boolean_operator (and)
        assert compute_cyclomatic_complexity(tree.root_node) >= 3

    def test_try_except(self) -> None:
        """Except clause adds to complexity."""
        code = "try:\n    pass\nexcept ValueError:\n    pass"
        tree = parse_code(code)
        assert compute_cyclomatic_complexity(tree.root_node) >= 2

    def test_complex_function(self) -> None:
        """Complex function with multiple branch points."""
        code = """
def process(data):
    if not data:
        return None
    for item in data:
        if item > 0:
            while item > 10:
                item -= 1
        elif item < 0:
            pass
    return data
"""
        tree = parse_code(code)
        cc = compute_cyclomatic_complexity(tree.root_node)
        assert cc >= 5  # Multiple decision points


# ──────────────────────────────────────────────────────────────
#  Nesting Depth Tests
# ──────────────────────────────────────────────────────────────

class TestNestingDepth:
    """Tests for max nesting depth calculation."""

    def test_no_nesting(self) -> None:
        """Flat code has nesting depth 0."""
        tree = parse_code("x = 1")
        assert compute_max_nesting_depth(tree.root_node) == 0

    def test_single_level(self) -> None:
        """Single if block has depth 1."""
        tree = parse_code("if True:\n    pass")
        assert compute_max_nesting_depth(tree.root_node) == 1

    def test_nested_blocks(self) -> None:
        """Nested control flow increases depth."""
        code = "if True:\n    for i in range(10):\n        while True:\n            break"
        tree = parse_code(code)
        assert compute_max_nesting_depth(tree.root_node) == 3

    def test_deep_nesting(self) -> None:
        """Deeply nested conditionals."""
        code = """
if a:
    if b:
        if c:
            if d:
                pass
"""
        tree = parse_code(code)
        assert compute_max_nesting_depth(tree.root_node) >= 4


# ──────────────────────────────────────────────────────────────
#  AST Differ Tests — Full Feature Vector
# ──────────────────────────────────────────────────────────────

class TestDiffSingleFileAST:
    """Tests for the complete AST differencing engine."""

    def test_identical_code_produces_zero_deltas(self) -> None:
        """No changes when base and head are identical."""
        code = "def foo():\n    return 42"
        result = diff_single_file_ast(code, code)

        assert result["nodes_added"] == 0
        assert result["nodes_deleted"] == 0
        assert result["delta_cc"] == 0
        assert result["nesting_depth_delta"] == 0
        assert result["func_signatures_mod"] == 0
        assert result["classes_modified"] == 0
        assert result["return_types_altered"] == 0
        assert result["try_catch_added"] == 0
        assert result["ast_disturbance_index"] == 0.0

    def test_new_file(self) -> None:
        """Empty base, non-empty head: all additions."""
        head_code = "def hello():\n    print('hello')"
        result = diff_single_file_ast("", head_code)

        assert result["nodes_added"] > 0
        assert result["nodes_deleted"] == 0
        assert result["func_signatures_mod"] > 0  # New function

    def test_deleted_file(self) -> None:
        """Non-empty base, empty head: all deletions."""
        base_code = "def hello():\n    print('hello')"
        result = diff_single_file_ast(base_code, "")

        assert result["nodes_deleted"] > 0
        assert result["nodes_added"] == 0

    def test_added_if_increases_complexity(self) -> None:
        """Adding an if statement increases cyclomatic delta."""
        base = "def f():\n    return 1"
        head = "def f():\n    if True:\n        return 1\n    return 0"
        result = diff_single_file_ast(base, head)

        assert result["delta_cc"] > 0
        assert result["nesting_depth_delta"] >= 0

    def test_function_signature_change_detected(self) -> None:
        """Changing function parameters is detected."""
        base = "def greet(name):\n    return name"
        head = "def greet(name, greeting):\n    return f'{greeting} {name}'"
        result = diff_single_file_ast(base, head)

        assert result["func_signatures_mod"] >= 1

    def test_new_function_counted_as_signature_mod(self) -> None:
        """Adding a new function counts as a signature modification."""
        base = "x = 1"
        head = "x = 1\ndef new_func():\n    pass"
        result = diff_single_file_ast(base, head)

        assert result["func_signatures_mod"] >= 1

    def test_class_modification_detected(self) -> None:
        """Changing class inheritance is detected."""
        base = "class Foo:\n    pass"
        head = "class Foo(Bar):\n    pass"
        result = diff_single_file_ast(base, head)

        assert result["classes_modified"] >= 1

    def test_new_class_detected(self) -> None:
        """Adding a new class is counted."""
        base = "x = 1"
        head = "x = 1\nclass NewClass:\n    pass"
        result = diff_single_file_ast(base, head)

        assert result["classes_modified"] >= 1

    def test_return_type_change_detected(self) -> None:
        """Changing return type annotation is detected."""
        base = "def foo() -> int:\n    return 42"
        head = "def foo() -> str:\n    return '42'"
        result = diff_single_file_ast(base, head)

        assert result["return_types_altered"] >= 1

    def test_try_catch_addition(self) -> None:
        """Adding try/except blocks is tracked."""
        base = "x = int(input())"
        head = "try:\n    x = int(input())\nexcept ValueError:\n    x = 0"
        result = diff_single_file_ast(base, head)

        assert result["try_catch_added"] >= 1

    def test_assertions_tracked_via_node_counts(self) -> None:
        """Assertions in base code are part of the node counting."""
        base = "assert True\nassert 1 == 1"
        head = "assert True"
        result = diff_single_file_ast(base, head)

        # At least some nodes were deleted
        assert result["nodes_deleted"] > 0

    def test_call_graph_fanout_increase(self) -> None:
        """Adding function calls increases fan-out delta."""
        base = "x = 1"
        head = "x = foo()\ny = bar()\nz = baz()"
        result = diff_single_file_ast(base, head)

        assert result["call_graph_fanout_delta"] > 0

    def test_ast_disturbance_index_range(self) -> None:
        """Disturbance index is always in [0.0, 1.0]."""
        # Drastic change
        base = "x = 1"
        head = """
def complex_func(a, b, c):
    if a > 0:
        for i in range(b):
            while c > 0:
                try:
                    result = a / c
                except ZeroDivisionError:
                    result = 0
                c -= 1
    return result
"""
        result = diff_single_file_ast(base, head)

        assert 0.0 <= result["ast_disturbance_index"] <= 1.0

    def test_control_flow_churn_ratio_range(self) -> None:
        """Control flow churn ratio is always in [0.0, 1.0]."""
        base = "x = 1"
        head = "if x > 0:\n    pass\nfor i in range(10):\n    pass"
        result = diff_single_file_ast(base, head)

        assert 0.0 <= result["control_flow_churn_ratio"] <= 1.0

    def test_malformed_code_handled(self) -> None:
        """Malformed code doesn't crash — metrics are still computed."""
        base = "def foo(:\n    return"
        head = "def foo():\n    return 42"
        result = diff_single_file_ast(base, head)

        # Should produce some result without crashing
        assert isinstance(result["nodes_added"], int)
        assert isinstance(result["ast_disturbance_index"], float)

    def test_cyclomatic_delta_capped(self) -> None:
        """Delta CC is capped at [-50, +50] per spec."""
        # Create extreme complexity difference
        base = "x = 1"
        # Generate code with many branches
        lines = ["def f():"]
        for i in range(60):
            lines.append(f"    if x{i}: pass")
        head = "\n".join(lines)

        result = diff_single_file_ast(base, head)
        assert -50 <= result["delta_cc"] <= 50

    def test_result_has_all_12_keys(self) -> None:
        """Result dict contains all 12 required feature keys."""
        result = diff_single_file_ast("x = 1", "y = 2")
        expected_keys = {
            "nodes_added", "nodes_deleted", "nodes_mutated",
            "delta_cc", "nesting_depth_delta",
            "func_signatures_mod", "classes_modified", "return_types_altered",
            "call_graph_fanout_delta",
            "ast_disturbance_index",
            "try_catch_added", "control_flow_churn_ratio",
        }
        assert set(result.keys()) == expected_keys


# ──────────────────────────────────────────────────────────────
#  Multi-File Aggregation Tests
# ──────────────────────────────────────────────────────────────

class TestDiffMultiFile:
    """Tests for multi-file AST metric aggregation."""

    def test_empty_list(self) -> None:
        """Empty file list returns zeroed metrics."""
        result = diff_multi_file([])
        assert result["nodes_added"] == 0
        assert result["ast_disturbance_index"] == 0.0

    def test_single_file_matches_direct(self) -> None:
        """Single-file aggregation matches direct diff."""
        base = "x = 1"
        head = "def foo():\n    return 42"

        direct = diff_single_file_ast(base, head)
        aggregated = diff_multi_file([{"base_code": base, "head_code": head}])

        assert direct["nodes_added"] == aggregated["nodes_added"]
        assert direct["delta_cc"] == aggregated["delta_cc"]

    def test_two_files_sum_nodes(self) -> None:
        """Multiple files aggregate node counts."""
        files = [
            {"base_code": "", "head_code": "x = 1"},
            {"base_code": "", "head_code": "y = 2"},
        ]
        result = diff_multi_file(files)
        assert result["nodes_added"] > 0

    def test_error_in_one_file_doesnt_crash(self) -> None:
        """Malformed diffs are skipped gracefully."""
        files = [
            {"base_code": "def broken(:", "head_code": "def fixed(): pass"},
            {"base_code": "a = 1", "head_code": "b = 2"},
        ]
        result = diff_multi_file(files)
        assert isinstance(result["ast_disturbance_index"], float)
