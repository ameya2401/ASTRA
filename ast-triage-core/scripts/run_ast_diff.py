"""
scripts/run_ast_diff.py - CLI tool to run AST Differencing between Python files.

Computes the 12 structural AST features (F01–F12) including:
- Cyclomatic complexity change (McCabe)
- AST disturbance index (0.0 to 1.0)
- Node additions, deletions, mutations
- Nesting depth delta
- Function signature & return type modifications

Usage:
    # Run built-in demo
    python scripts/run_ast_diff.py

    # Compare two files
    python scripts/run_ast_diff.py --base path/to/base.py --head path/to/head.py

    # Output pure JSON
    python scripts/run_ast_diff.py --base path/to/base.py --head path/to/head.py --json
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure root package is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.ast_engine.differ import diff_single_file_ast

DEMO_BASE = '''
def process_data(items: list[int]) -> int:
    total = 0
    for item in items:
        total += item
    return total
'''

DEMO_HEAD = '''
def process_data(items: list[int], filter_negative: bool = True) -> int:
    total = 0
    for item in items:
        if filter_negative and item < 0:
            continue
        try:
            total += item
        except Exception:
            pass
    return total
'''


def format_table(metrics: dict) -> str:
    """Formats metrics dictionary into a readable CLI summary."""
    lines = [
        "================================================================",
        "          AST-Triage Structural Differencing Report",
        "================================================================",
        f"  * AST Disturbance Index (F10):  {metrics['ast_disturbance_index']:.4f}  (0.0 = low, 1.0 = extreme)",
        f"  * Cyclomatic Complexity Delta:  {metrics['delta_cc']:+d}",
        f"  * Nesting Depth Delta:          {metrics['nesting_depth_delta']:+d}",
        "----------------------------------------------------------------",
        "  Node Modifications:",
        f"    - Nodes Added (F01):          {metrics['nodes_added']}",
        f"    - Nodes Deleted (F02):        {metrics['nodes_deleted']}",
        f"    - Nodes Mutated (F03):        {metrics['nodes_mutated']}",
        "----------------------------------------------------------------",
        "  Code Architecture & Signatures:",
        f"    - Function Signatures Mod:    {metrics['func_signatures_mod']}",
        f"    - Return Types Altered:       {metrics['return_types_altered']}",
        f"    - Classes Modified:           {metrics['classes_modified']}",
        f"    - Call Graph Fan-out Delta:   {metrics['call_graph_fanout_delta']:+d}",
        "----------------------------------------------------------------",
        "  Robustness & Flow:",
        f"    - Try/Catch Blocks Added:     {metrics['try_catch_added']}",
        f"    - Control Flow Churn Ratio:   {metrics['control_flow_churn_ratio']:.4f}",
        "================================================================",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="AST-Triage: Structural AST Differencing CLI")
    parser.add_argument("--base", "-b", type=str, help="Path to pre-PR (base) Python file")
    parser.add_argument("--head", "-H", type=str, help="Path to post-PR (head) Python file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    parser.add_argument(
        "--save",
        "-s",
        nargs="?",
        const="test_reports/ast_diff_report.json",
        default=None,
        help="Save test results locally (default: test_reports/ast_diff_report.json)",
    )

    args = parser.parse_args()

    if args.base and args.head:
        base_path = Path(args.base)
        head_path = Path(args.head)

        if not base_path.exists():
            print(f"Error: Base file not found at '{base_path}'", file=sys.stderr)
            sys.exit(1)
        if not head_path.exists():
            print(f"Error: Head file not found at '{head_path}'", file=sys.stderr)
            sys.exit(1)

        base_code = base_path.read_text(encoding="utf-8")
        head_code = head_path.read_text(encoding="utf-8")
        print(f"Comparing base: {base_path} -> head: {head_path}\n")
    else:
        print("No files specified. Running demonstration with sample functions:\n")
        print("--- [Base Code] ---" + DEMO_BASE)
        print("--- [Head Code] ---" + DEMO_HEAD)
        base_code = DEMO_BASE
        head_code = DEMO_HEAD

    metrics = diff_single_file_ast(base_code, head_code)

    if args.json:
        output_str = json.dumps(metrics, indent=2)
        print(output_str)
    else:
        output_str = format_table(metrics)
        print(output_str)

    # Save report locally if requested
    if args.save:
        save_path = Path(args.save)
        if not save_path.is_absolute():
            save_path = BASE_DIR / save_path

        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON data
        save_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"\n[Saved Local Report (Ignored by Git)] -> {save_path}")

        # Also write readable summary alongside
        txt_path = save_path.with_suffix(".txt")
        txt_path.write_text(format_table(metrics), encoding="utf-8")
        print(f"[Saved Human-Readable Summary]     -> {txt_path}")


if __name__ == "__main__":
    main()

