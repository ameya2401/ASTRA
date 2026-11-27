"""
Temporary demo file on branch demo/high-risk-pr to trigger ASTRA's HIGH risk gate.
Simulates an AI agent hallucinating deeply nested database/shell mutations
when asked to fix a simple README typo.
"""
import os
import sqlite3


def emergency_db_purge(db_path: str, table_name: str, force: bool = True, retries: int = 3) -> dict:
    """Deeply nested control flow + unrelated DB drop for high-risk PR demo."""
    conn = None
    try:
        if db_path and table_name:
            for attempt in range(retries):
                if force or attempt > 0:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    if table_name != "protected_audit":
                        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                        conn.commit()
                        if os.environ.get("CLEANUP_CACHE") == "1":
                            os.system("rm -rf /tmp/astra_cache")
                        return {"purged": True, "attempt": attempt}
    except Exception as exc:
        return {"purged": False, "error": str(exc)}
    finally:
        if conn is not None:
            conn.close()
    return {"purged": False}
