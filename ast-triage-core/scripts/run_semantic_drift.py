"""
scripts/run_semantic_drift.py - CLI tool to run Semantic Drift Analysis.

Computes the 6 Semantic NLP features (F13–F18) including:
- F13: Intent-to-diff cosine similarity (sentence-transformers MiniLM)
- F14: Issue title-to-diff cosine similarity
- F15: Entity drift Jaccard distance (extracted identifier overlap)
- F16: Docstring-to-code ratio in diff
- F17: Semantic drift flag (1 if cosine < 0.45 else 0)
- F18: Issue token length

Usage:
    # Run built-in demo (aligned vs drifted comparison)
    python scripts/run_semantic_drift.py

    # Analyze custom files
    python scripts/run_semantic_drift.py --issue path/to/issue.md --diff path/to/pr.patch --title "Fix db timeout"

    # Output pure JSON
    python scripts/run_semantic_drift.py --json

    # Save reports locally
    python scripts/run_semantic_drift.py --save
"""
import argparse
import json
import sys
from pathlib import Path

# Ensure root package is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.semantic_engine import SemanticDriftAnalyzer, compute_semantic_drift

# Aligned PR Scenario: Issue and diff solve the same problem
DEMO_ALIGNED_TITLE = "Fix SQLite database connection pool timeout under high load"
DEMO_ALIGNED_ISSUE = """
Under concurrent worker load, SQLite connections are timing out because
the default timeout is 5.0 seconds and connection pooling is unconfigured.
We need to increase the default connection timeout parameter to 30 seconds
and configure pool recycling to prevent stale file descriptor errors.
"""
DEMO_ALIGNED_DIFF = """
diff --git a/database/connection.py b/database/connection.py
index a1b2c3d..e4f5g6h 100644
--- a/database/connection.py
+++ b/database/connection.py
@@ -10,7 +10,12 @@ def get_engine(db_url: str):
-    return create_async_engine(db_url, timeout=5.0)
+    # Increase timeout to prevent concurrent worker pool exhaustion
+    return create_async_engine(
+        db_url,
+        timeout=30.0,
+        pool_recycle=1800,
+        pool_pre_ping=True,
+    )
"""

# Drifted PR Scenario: Agent asked for documentation update, but hacked database logic
DEMO_DRIFTED_TITLE = "Update documentation installation instructions for Python 3.12"
DEMO_DRIFTED_ISSUE = """
Please update the README.md installation section to state that Python 3.12
is now supported and provide instructions for installing via pip in a virtualenv.
Add notes regarding macOS Homebrew python versions.
"""
DEMO_DRIFTED_DIFF = """
diff --git a/database/connection.py b/database/connection.py
index a1b2c3d..e4f5g6h 100644
--- a/database/connection.py
+++ b/database/connection.py
@@ -10,7 +10,12 @@ def get_engine(db_url: str):
-    return create_async_engine(db_url, timeout=5.0)
+    # Hardcoded bypass for query timeout
+    import os
+    os.environ["SQLITE_BUSY_TIMEOUT"] = "999999"
+    return create_async_engine(db_url, echo=True)
"""


# Ensure stdout supports UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def format_table(title: str, metrics: dict, label: str = "") -> str:
    """Formats metrics dictionary into a readable CLI summary."""
    status_icon = "[!] DRIFT DETECTED" if metrics["semantic_drift_flag"] == 1 else "[OK] ALIGNED"
    lines = [
        "================================================================",
        f"       AST-Triage Semantic Drift Report {label}",
        "================================================================",
        f"  * Case:                         {title}",
        f"  * Status:                       {status_icon} (Flag: {metrics['semantic_drift_flag']})",
        "----------------------------------------------------------------",
        "  Vector Semantic Alignment:",
        f"    - Intent-Diff Cosine (F13):   {metrics['intent_diff_cosine']:.4f}  (Threshold: 0.45)",
        f"    - Title-Diff Cosine (F14):    {metrics['title_diff_cosine']:.4f}",
        "----------------------------------------------------------------",
        "  Entity & Code Overlap:",
        f"    - Entity Drift Jaccard (F15): {metrics['entity_drift_jaccard']:.4f}  (0.0 = aligned, 1.0 = disjoint)",
        f"    - Docstring/Code Ratio (F16): {metrics['docstring_code_ratio']:.4f}",
        f"    - Issue Token Length (F18):   {metrics['issue_token_length']} tokens",
        "================================================================",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="AST-Triage: Intent-to-Diff Semantic Alignment CLI")
    parser.add_argument("--issue", "-i", type=str, help="Path to issue description file or raw text")
    parser.add_argument("--diff", "-d", type=str, help="Path to diff/patch file or raw diff text")
    parser.add_argument("--title", "-t", type=str, default="", help="Issue title")
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    parser.add_argument(
        "--save",
        "-s",
        nargs="?",
        const="test_reports/semantic_drift_report.json",
        default=None,
        help="Save test results locally (default: test_reports/semantic_drift_report.json)",
    )

    args = parser.parse_args()
    analyzer = SemanticDriftAnalyzer()

    if args.issue and args.diff:
        issue_path = Path(args.issue)
        diff_path = Path(args.diff)

        issue_text = issue_path.read_text(encoding="utf-8") if issue_path.exists() else args.issue
        diff_text = diff_path.read_text(encoding="utf-8") if diff_path.exists() else args.diff

        metrics = analyzer.analyze(issue_text, diff_text, issue_title=args.title)
        title_str = args.title or "Custom Evaluation"

        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(format_table(title_str, metrics))

        results_to_save = {"title": title_str, "metrics": metrics}
    else:
        print("No files specified. Running demonstration with Aligned vs. Drifted PR cases:\n")

        # Case 1: Aligned
        aligned_metrics = analyzer.analyze(DEMO_ALIGNED_ISSUE, DEMO_ALIGNED_DIFF, issue_title=DEMO_ALIGNED_TITLE)
        aligned_table = format_table(DEMO_ALIGNED_TITLE, aligned_metrics, label="[Scenario 1: Aligned PR]")

        # Case 2: Drifted
        drifted_metrics = analyzer.analyze(DEMO_DRIFTED_ISSUE, DEMO_DRIFTED_DIFF, issue_title=DEMO_DRIFTED_TITLE)
        drifted_table = format_table(DEMO_DRIFTED_TITLE, drifted_metrics, label="[Scenario 2: Semantic Drift]")

        if args.json:
            combined = {
                "aligned_scenario": {"title": DEMO_ALIGNED_TITLE, "metrics": aligned_metrics},
                "drifted_scenario": {"title": DEMO_DRIFTED_TITLE, "metrics": drifted_metrics},
            }
            print(json.dumps(combined, indent=2))
            results_to_save = combined
        else:
            print(aligned_table)
            print()
            print(drifted_table)
            results_to_save = {
                "aligned": {"title": DEMO_ALIGNED_TITLE, "metrics": aligned_metrics},
                "drifted": {"title": DEMO_DRIFTED_TITLE, "metrics": drifted_metrics},
            }

    # Save report locally if requested
    if args.save:
        save_path = Path(args.save)
        if not save_path.is_absolute():
            save_path = BASE_DIR / save_path

        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON data
        save_path.write_text(json.dumps(results_to_save, indent=2), encoding="utf-8")
        print(f"\n[Saved Local Report (Ignored by Git)] -> {save_path}")

        # Also write readable summary alongside
        txt_path = save_path.with_suffix(".txt")
        if "aligned" in results_to_save:
            summary_txt = (
                format_table(DEMO_ALIGNED_TITLE, results_to_save["aligned"]["metrics"], "[Scenario 1: Aligned PR]")
                + "\n\n"
                + format_table(DEMO_DRIFTED_TITLE, results_to_save["drifted"]["metrics"], "[Scenario 2: Semantic Drift]")
            )
        else:
            summary_txt = format_table(results_to_save["title"], results_to_save["metrics"])

        txt_path.write_text(summary_txt, encoding="utf-8")
        print(f"[Saved Human-Readable Summary]     -> {txt_path}")


if __name__ == "__main__":
    main()
