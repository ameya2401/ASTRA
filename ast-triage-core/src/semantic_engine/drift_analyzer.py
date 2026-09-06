"""
src/semantic_engine/drift_analyzer.py - Cosine distance and entity drift calculator.

Computes semantic alignment between issue descriptions and code diffs:
    - F13: intent_diff_cosine   — Cosine similarity between issue description and diff
    - F14: title_diff_cosine    — Cosine similarity between issue title and diff
    - F15: entity_drift_jaccard — Jaccard distance between code entities in issue and diff
    - F16: docstring_code_ratio — Ratio of added comments/docstrings to added code
    - F17: semantic_drift_flag  — Binary indicator (1 if F13 < 0.45 else 0)
    - F18: issue_token_length   — Total tokens in the issue prompt

Implementation: Phase 3
"""
from __future__ import annotations

import logging
import re
from typing import Optional, Set, Tuple, TypedDict

import numpy as np

from src.semantic_engine.embedder import SentenceEmbedder, get_embedder

logger = logging.getLogger(__name__)

# Threshold below which an issue and diff are considered semantically drifted
SEMANTIC_DRIFT_THRESHOLD: float = 0.45

# Standard Python language keywords to exclude from entity sets
PYTHON_KEYWORDS: Set[str] = {
    "false", "none", "true", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
    "while", "with", "yield", "self", "cls",
}


class SemanticMetrics(TypedDict):
    """Strongly-typed dictionary for the 6 Semantic NLP features (F13–F18)."""

    # F13: Cosine similarity between issue description and diff summary in [-1.0, 1.0]
    intent_diff_cosine: float

    # F14: Cosine similarity between issue title and diff summary in [-1.0, 1.0]
    title_diff_cosine: float

    # F15: Jaccard distance between code identifier entities in [0.0, 1.0]
    entity_drift_jaccard: float

    # F16: Ratio of added docstrings/comments to added executable code
    docstring_code_ratio: float

    # F17: Binary drift flag: 1 if intent_diff_cosine < 0.45 else 0
    semantic_drift_flag: int

    # F18: Token length of the issue prompt
    issue_token_length: int


# ──────────────────────────────────────────────────────────────
#  Text Sanitization & Normalization Helpers
# ──────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """
    Sanitizes markdown and text documentation:
      - Strips HTML comments (<!-- ... -->)
      - Strips HTML tags (<...>)
      - Strips Markdown tables (| col1 | col2 | ...)
      - Strips Markdown code block delimiters (```python, ```)
      - Normalizes whitespace
    """
    if not text:
        return ""

    # Strip HTML comments
    cleaned = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)

    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)

    # Strip markdown table rows (lines starting and ending with |, or separator rows |---|)
    lines = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        if re.match(r"^\|?\s*[-:]+[-| :]*\|?$", stripped):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)

    # Strip code block fences (```python, ```)
    cleaned = re.sub(r"```[a-zA-Z0-9_-]*", " ", cleaned)
    cleaned = re.sub(r"```", " ", cleaned)

    # Collapse repeated whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_diff(raw_diff: str) -> str:
    """
    Extracts semantic content from a unified git diff:
      - Strips git metadata headers (diff --git, index, --- a/, +++ b/, @@ ... @@)
      - Retains added and deleted lines (stripping +/- prefix) and context lines
      - Collapses whitespace into a clean natural-language / code representation
    """
    if not raw_diff:
        return ""

    meaningful_lines = []
    for line in raw_diff.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Skip git patch metadata headers
        if stripped.startswith(("diff --git", "index ", "--- ", "+++ ", "new file mode", "deleted file mode", "similarity index")):
            continue
        if stripped.startswith("@@"):
            continue

        # Extract content from added, deleted, or context lines
        if stripped.startswith(("+", "-")):
            content = stripped[1:].strip()
            if content:
                meaningful_lines.append(content)
        else:
            meaningful_lines.append(stripped)

    merged = " ".join(meaningful_lines)
    return re.sub(r"\s+", " ", merged).strip()


# ──────────────────────────────────────────────────────────────
#  Entity & Identifier Extraction (F15)
# ──────────────────────────────────────────────────────────────

def extract_code_identifiers(text: str) -> Set[str]:
    """
    Extracts Python identifier tokens from text or diff:
      - snake_case (e.g., compute_alignment, delta_cc, user_id)
      - camelCase / PascalCase (e.g., SemanticDriftAnalyzer, parseTree, XGBClassifier)
      - Backtick-enclosed code tokens (`prices`, `discount_rate`)
      - Function and class definitions (def foo, class Bar)
      - Filters out standard Python keywords
    """
    if not text:
        return set()

    # Pattern for snake_case tokens with at least one underscore
    snake_case_matches = set(re.findall(r"\b[a-zA-Z0-9]+(?:_[a-zA-Z0-9]+)+\b", text))

    # Pattern for camelCase or PascalCase tokens (mixed case)
    camel_case_matches = set(re.findall(r"\b[a-z]+(?:[A-Z][a-zA-Z0-9]*)+\b|\b[A-Z][a-z0-9]+(?:[A-Z][a-zA-Z0-9]*)+\b", text))

    # Pattern for general identifier-like tokens in backticks
    backtick_matches = set(re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]*)`", text))

    # Pattern for def / class names
    def_class_matches = set(re.findall(r"\b(?:def|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)", text))

    all_entities = snake_case_matches | camel_case_matches | backtick_matches | def_class_matches

    # Filter out keywords and clean up
    filtered = {
        ent.strip("_").lower()
        for ent in all_entities
        if ent.strip("_") and ent.lower() not in PYTHON_KEYWORDS and len(ent.strip("_")) >= 3
    }
    return filtered


def compute_entity_jaccard_distance(
    issue_entities: Set[str],
    diff_entities: Set[str],
    epsilon: float = 1e-5,
) -> float:
    """
    Computes Jaccard distance between issue entities and diff entities:
        distance = 1.0 - (|A ∩ B| / |A ∪ B|)

    Returns:
        float in [0.0, 1.0]. A value of 0.0 means complete entity alignment;
        a value of 1.0 means complete entity drift (disjoint sets).
        If both sets are empty, returns 0.0 (no detected divergence).
    """
    if not issue_entities and not diff_entities:
        return 0.0

    union = issue_entities | diff_entities
    if not union:
        return 0.0

    intersection = issue_entities & diff_entities
    if not intersection:
        return 1.0

    if intersection == union:
        return 0.0

    similarity = len(intersection) / len(union)
    distance = 1.0 - similarity
    return round(float(np.clip(distance, 0.0, 1.0)), 4)


# ──────────────────────────────────────────────────────────────
#  Docstring-to-Code Ratio (F16)
# ──────────────────────────────────────────────────────────────

def compute_docstring_code_ratio(raw_diff: str, epsilon: float = 1e-5) -> float:
    """
    Computes the ratio of added docstrings/comments to added executable code:
        ratio = lines_docstring_added / (lines_executable_code_added + ε)

    Detects PRs that inflate diff size with documentation without genuine logic.
    """
    if not raw_diff:
        return 0.0

    added_docstrings = 0
    added_code = 0
    in_triple_quotes = False
    quote_char = None

    for line in raw_diff.splitlines():
        stripped = line.strip()
        # Only inspect added lines in diff, skipping file headers
        if not stripped.startswith("+") or stripped.startswith("+++"):
            continue

        content = stripped[1:].strip()
        if not content:
            continue

        # Check for multi-line docstring boundaries
        if in_triple_quotes:
            added_docstrings += 1
            if quote_char and quote_char in content:
                in_triple_quotes = False
                quote_char = None
            continue

        if '"""' in content or "'''" in content:
            delim = '"""' if '"""' in content else "'''"
            added_docstrings += 1
            # If opened and closed on different lines
            if content.count(delim) < 2:
                in_triple_quotes = True
                quote_char = delim
        elif content.startswith(("#", "/*", "*", "//")):
            added_docstrings += 1
        else:
            added_code += 1

    if added_code == 0:
        return float(added_docstrings) if added_docstrings > 0 else 0.0

    if added_docstrings == 0:
        return 0.0

    if added_docstrings == added_code:
        return 1.0

    ratio = added_docstrings / (added_code + epsilon)
    return round(float(ratio), 4)


# ──────────────────────────────────────────────────────────────
#  Issue Token Length (F18)
# ──────────────────────────────────────────────────────────────

def compute_issue_token_length(issue_description: str) -> int:
    """
    Counts total tokens (words and symbols) in the issue description.
    Controls for underspecified prompts where short issues correlate with errors.
    """
    if not issue_description or not issue_description.strip():
        return 0

    tokens = re.findall(r"\b\w+\b|[^\w\s]", issue_description)
    return len(tokens)


# ──────────────────────────────────────────────────────────────
#  Semantic Drift Analyzer Class
# ──────────────────────────────────────────────────────────────

class SemanticDriftAnalyzer:
    """
    Engine for computing semantic alignment between issue specifications
    and PR code diffs using dense embeddings and entity extraction.
    """

    _instance: Optional[SemanticDriftAnalyzer] = None

    def __new__(cls, model_name: Optional[str] = None) -> SemanticDriftAnalyzer:
        if cls._instance is None:
            cls._instance = super(SemanticDriftAnalyzer, cls).__new__(cls)
            cls._instance.embedder = SentenceEmbedder(model_name=model_name)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets the singleton instance (useful for unit testing)."""
        cls._instance = None

    def compute_alignment(
        self,
        issue_text: str,
        diff_summary: str,
    ) -> Tuple[float, int]:
        """
        Encodes issue specification and diff summary into 384-dimensional dense
        vectors and computes Cosine Similarity.

        Returns:
            cosine_similarity: float in [-1.0, 1.0]
            semantic_drift_flag: 1 if cosine_similarity < 0.45 else 0
        """
        issue_norm = normalize_text(issue_text)
        diff_norm = normalize_diff(diff_summary)

        if not issue_norm or not diff_norm:
            return 0.0, 1

        embeddings = self.embedder.encode(
            [issue_norm, diff_norm],
            normalize_embeddings=True,
        )
        e_issue, e_diff = embeddings[0], embeddings[1]

        # Dot product of L2-normalized vectors equals cosine similarity
        cosine_sim = float(np.dot(e_issue, e_diff))
        cosine_sim = float(np.clip(round(cosine_sim, 4), -1.0, 1.0))

        drift_flag = 1 if cosine_sim < SEMANTIC_DRIFT_THRESHOLD else 0
        return cosine_sim, drift_flag

    def analyze(
        self,
        issue_description: str,
        raw_diff: str,
        issue_title: str = "",
    ) -> SemanticMetrics:
        """
        Extracts all 6 Semantic Drift & NLP features (F13–F18).

        Args:
            issue_description: Full issue description or prompt text.
            raw_diff: Unified git diff string or modified code content.
            issue_title: Optional issue title or summary.

        Returns:
            SemanticMetrics: Strongly typed dictionary containing F13–F18.
        """
        norm_issue = normalize_text(issue_description)
        norm_diff = normalize_diff(raw_diff)
        norm_title = normalize_text(issue_title)

        # F18: Issue token length
        f18_token_len = compute_issue_token_length(issue_description)

        # F16: Docstring to code ratio
        f16_doc_ratio = compute_docstring_code_ratio(raw_diff)

        # F15: Entity drift Jaccard distance
        issue_entities = extract_code_identifiers(issue_description + " " + issue_title)
        diff_entities = extract_code_identifiers(raw_diff)
        f15_entity_drift = compute_entity_jaccard_distance(issue_entities, diff_entities)

        # Handle empty inputs gracefully
        if not norm_issue or not norm_diff:
            f13_cosine = 0.0
            f17_drift_flag = 1
            f14_title_sim = 0.0
            return {
                "intent_diff_cosine": f13_cosine,
                "title_diff_cosine": f14_title_sim,
                "entity_drift_jaccard": f15_entity_drift,
                "docstring_code_ratio": f16_doc_ratio,
                "semantic_drift_flag": f17_drift_flag,
                "issue_token_length": f18_token_len,
            }

        # Embed texts in a single mini-batch: [issue, diff, title (optional)]
        texts_to_embed = [norm_issue, norm_diff]
        has_title = bool(norm_title)
        if has_title:
            texts_to_embed.append(norm_title)

        embeddings = self.embedder.encode(texts_to_embed, normalize_embeddings=True)
        e_issue = embeddings[0]
        e_diff = embeddings[1]

        # F13: Intent-diff cosine similarity
        f13_cosine = float(np.dot(e_issue, e_diff))
        f13_cosine = float(np.clip(round(f13_cosine, 4), -1.0, 1.0))

        # F17: Semantic drift flag
        f17_drift_flag = 1 if f13_cosine < SEMANTIC_DRIFT_THRESHOLD else 0

        # F14: Title-diff cosine similarity
        if has_title:
            e_title = embeddings[2]
            f14_title_sim = float(np.dot(e_title, e_diff))
            f14_title_sim = float(np.clip(round(f14_title_sim, 4), -1.0, 1.0))
        else:
            # Fall back to intent cosine if title not provided
            f14_title_sim = f13_cosine

        return {
            "intent_diff_cosine": f13_cosine,
            "title_diff_cosine": f14_title_sim,
            "entity_drift_jaccard": f15_entity_drift,
            "docstring_code_ratio": f16_doc_ratio,
            "semantic_drift_flag": f17_drift_flag,
            "issue_token_length": f18_token_len,
        }


def compute_semantic_drift(
    issue_description: str,
    raw_diff: str,
    issue_title: str = "",
) -> SemanticMetrics:
    """
    Functional convenience wrapper for SemanticDriftAnalyzer.analyze().

    Usage:
        from src.semantic_engine.drift_analyzer import compute_semantic_drift
        metrics = compute_semantic_drift(issue_desc, diff, title)
    """
    analyzer = SemanticDriftAnalyzer()
    return analyzer.analyze(
        issue_description=issue_description,
        raw_diff=raw_diff,
        issue_title=issue_title,
    )
