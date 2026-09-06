"""
tests/test_semantic_engine.py - Tests for the semantic drift analyzer.

Validates:
    - Text sanitization (HTML comments, tags, markdown tables, code fences)
    - Unified diff normalization (header stripping, hunk cleaning, line retention)
    - Code identifier extraction (snake_case, camelCase, backticks, keywords filtered)
    - Jaccard entity distance computation (identical, disjoint, partial, empty)
    - Docstring-to-code ratio calculation (comments, multiline docstrings, pure code)
    - Issue prompt token counting
    - SentenceEmbedder singleton pattern, thread safety, dimension, and L2-norm
    - SemanticDriftAnalyzer.compute_alignment() (cosine similarity & drift flag)
    - SemanticDriftAnalyzer.analyze() & compute_semantic_drift() (all 6 features F13–F18)
    - Aligned vs drifted PR test cases
    - Edge cases: empty text, whitespace-only, missing title
"""
import concurrent.futures
import numpy as np
import pytest

from src.semantic_engine.drift_analyzer import (
    SEMANTIC_DRIFT_THRESHOLD,
    SemanticDriftAnalyzer,
    compute_docstring_code_ratio,
    compute_entity_jaccard_distance,
    compute_issue_token_length,
    compute_semantic_drift,
    extract_code_identifiers,
    normalize_diff,
    normalize_text,
)
from src.semantic_engine.embedder import (
    EMBEDDING_DIM,
    SentenceEmbedder,
    get_embedder,
)


# ==============================================================================
# 1. Text Normalization & Sanitization Tests
# ==============================================================================

class TestNormalizeText:
    """Validates markdown, HTML, and comment sanitization."""

    def test_strip_html_comments(self):
        raw = "Feature description. <!-- TODO: remove before PR --> All done."
        cleaned = normalize_text(raw)
        assert "TODO: remove before PR" not in cleaned
        assert "Feature description." in cleaned
        assert "All done." in cleaned

    def test_strip_html_tags(self):
        raw = "<h3>Bug Report</h3><p>Fix the <code>timeout</code> issue.</p>"
        cleaned = normalize_text(raw)
        assert "<p>" not in cleaned
        assert "<h3>" not in cleaned
        assert "Bug Report" in cleaned
        assert "Fix the timeout issue." in cleaned

    def test_strip_markdown_tables(self):
        raw = (
            "Here is the issue description:\n\n"
            "| Column 1 | Column 2 |\n"
            "| --- | --- |\n"
            "| Item A | Value 1 |\n"
            "| Item B | Value 2 |\n\n"
            "Please fix calculate_total."
        )
        cleaned = normalize_text(raw)
        assert "Column 1" not in cleaned
        assert "Item A" not in cleaned
        assert "Here is the issue description:" in cleaned
        assert "Please fix calculate_total." in cleaned

    def test_strip_markdown_code_fences(self):
        raw = "Check this snippet:\n```python\nprint('hello')\n```\nDone."
        cleaned = normalize_text(raw)
        assert "```python" not in cleaned
        assert "```" not in cleaned
        assert "print('hello')" in cleaned

    def test_normalize_empty_and_whitespace(self):
        assert normalize_text("") == ""
        assert normalize_text("   \n\n\t  ") == ""


class TestNormalizeDiff:
    """Validates unified git diff cleaning."""

    def test_strip_git_headers(self):
        diff = (
            "diff --git a/calc.py b/calc.py\n"
            "index 1234abc..5678def 100644\n"
            "--- a/calc.py\n"
            "+++ b/calc.py\n"
            "@@ -10,5 +10,8 @@ def calculate_total(prices):\n"
            "+    if discount_rate < 0:\n"
            "+        raise ValueError\n"
            "-    total = 0\n"
        )
        cleaned = normalize_diff(diff)
        assert "diff --git" not in cleaned
        assert "@@" not in cleaned
        assert "---" not in cleaned
        assert "+++" not in cleaned
        assert "if discount_rate < 0:" in cleaned
        assert "raise ValueError" in cleaned
        assert "total = 0" in cleaned

    def test_normalize_empty_diff(self):
        assert normalize_diff("") == ""
        assert normalize_diff("   \n\n\t  ") == ""


# ==============================================================================
# 2. Entity & Identifier Extraction Tests
# ==============================================================================

class TestEntityExtraction:
    """Validates extraction of Python identifiers (snake_case, camelCase, etc.)."""

    def test_extract_snake_case(self):
        text = "Please update calculate_total and discount_rate in order_processor."
        entities = extract_code_identifiers(text)
        assert "calculate_total" in entities
        assert "discount_rate" in entities
        assert "order_processor" in entities

    def test_extract_camel_case(self):
        text = "Should raise ValueError or InvalidRateException on bad inputs."
        entities = extract_code_identifiers(text)
        assert "valueerror" in entities
        assert "invalidrateexception" in entities

    def test_extract_backticked_identifiers(self):
        text = "Ensure `prices` and `total` are validated in `calculate_total`."
        entities = extract_code_identifiers(text)
        assert "prices" in entities
        assert "total" in entities
        assert "calculate_total" in entities

    def test_keywords_filtered_out(self):
        text = "def return_total(prices):\n    for price in prices:\n        if True: return price"
        entities = extract_code_identifiers(text)
        assert "def" not in entities
        assert "for" not in entities
        assert "if" not in entities
        assert "return" not in entities
        assert "true" not in entities
        assert "return_total" in entities

    def test_extract_empty_string(self):
        assert extract_code_identifiers("") == set()
        assert extract_code_identifiers("no code here at all") == set()


# ==============================================================================
# 3. Entity Jaccard Distance Tests
# ==============================================================================

class TestEntityJaccardDistance:
    """Validates F15 entity Jaccard distance formula."""

    def test_identical_entities_zero_distance(self):
        entities = {"calculate_total", "discount_rate"}
        distance = compute_entity_jaccard_distance(entities, entities)
        assert distance == 0.0

    def test_completely_disjoint_entities_max_distance(self):
        issue_entities = {"database_pool", "connection_timeout"}
        diff_entities = {"button_style", "css_padding"}
        distance = compute_entity_jaccard_distance(issue_entities, diff_entities)
        assert distance == 1.0

    def test_partial_overlap_distance(self):
        issue_entities = {"calculate_total", "discount_rate"}
        diff_entities = {"calculate_total", "prices"}
        distance = compute_entity_jaccard_distance(issue_entities, diff_entities)
        # Intersection = 1, Union = 3, similarity = 1/3 = 0.3333, distance = 0.6667
        assert pytest.approx(distance, 0.001) == 0.6667

    def test_both_empty_entities_zero_distance(self):
        distance = compute_entity_jaccard_distance(set(), set())
        assert distance == 0.0


# ==============================================================================
# 4. Docstring-to-Code Ratio & Token Length Tests
# ==============================================================================

class TestDocstringRatioAndTokens:
    """Validates F16 docstring-to-code ratio and F18 token length."""

    def test_code_with_comments_and_docstrings(self):
        diff = (
            "+# Validates the discount rate\n"
            '+"""Check range [0, 1]"""\n'
            "+if discount_rate < 0.0:\n"
            "+    raise ValueError\n"
        )
        ratio = compute_docstring_code_ratio(diff)
        assert pytest.approx(ratio, 0.01) == 1.0

    def test_code_without_comments(self):
        diff = (
            "+total = 0.0\n"
            "+for p in prices:\n"
            "+    total += p\n"
        )
        ratio = compute_docstring_code_ratio(diff)
        assert ratio == 0.0

    def test_empty_diff_docstring_ratio(self):
        assert compute_docstring_code_ratio("") == 0.0

    def test_issue_token_length(self):
        prompt = "Add discount_rate validation to calculate_total."
        count = compute_issue_token_length(prompt)
        assert count > 0
        assert compute_issue_token_length("") == 0


# ==============================================================================
# 5. SentenceEmbedder Singleton & Encoding Tests
# ==============================================================================

class TestSentenceEmbedder:
    """Validates singleton pattern, thread safety, and vector properties."""

    def test_singleton_identity(self):
        embedder1 = get_embedder()
        embedder2 = SentenceEmbedder()
        assert embedder1 is embedder2

    def test_embedding_dimension(self):
        embedder = get_embedder()
        dim = embedder.get_embedding_dimension()
        assert dim == EMBEDDING_DIM
        assert dim == 384

    def test_thread_safe_singleton(self):
        instances = []

        def acquire():
            return SentenceEmbedder()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(acquire) for _ in range(10)]
            for f in concurrent.futures.as_completed(futures):
                instances.append(f.result())

        for inst in instances:
            assert inst is instances[0]

    def test_single_encoding_shape_and_norm(self):
        embedder = get_embedder()
        text = "Add validation for discount rate parameter in calculate_total."
        vec = embedder.encode(text, normalize_embeddings=True)
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (EMBEDDING_DIM,)
        # L2 norm of normalized vector should be approx 1.0
        norm = np.linalg.norm(vec)
        assert pytest.approx(norm, 0.01) == 1.0

    def test_batch_encoding_shape(self):
        embedder = get_embedder()
        texts = [
            "Issue: Fix calculate_total discount calculation.",
            "Diff: Add discount rate validation logic.",
        ]
        matrix = embedder.encode(texts, normalize_embeddings=True)
        assert isinstance(matrix, np.ndarray)
        assert matrix.shape == (2, EMBEDDING_DIM)

    def test_empty_input_handled_safely(self):
        embedder = get_embedder()
        vec = embedder.encode("", normalize_embeddings=True)
        assert isinstance(vec, np.ndarray)
        assert vec.shape == (EMBEDDING_DIM,)


# ==============================================================================
# 6. SemanticDriftAnalyzer Integration Tests
# ==============================================================================

class TestSemanticDriftAnalyzer:
    """Validates end-to-end semantic alignment and drift classification."""

    @pytest.fixture(autouse=True)
    def setup_analyzer(self):
        self.analyzer = SemanticDriftAnalyzer()

    def test_compute_alignment_aligned(self):
        """Validates the 2-tuple compute_alignment contract from TAD 4.2."""
        issue = "Add discount rate validation to calculate_total."
        diff = (
            "+def calculate_total(prices, discount_rate=0.0):\n"
            "+    if discount_rate < 0 or discount_rate > 1:\n"
            "+        raise ValueError('Invalid discount rate')\n"
        )
        cosine_sim, drift_flag = self.analyzer.compute_alignment(issue, diff)
        assert cosine_sim >= SEMANTIC_DRIFT_THRESHOLD
        assert drift_flag == 0

    def test_compute_alignment_drifted(self):
        """Unrelated issue and diff must trigger drift_flag = 1."""
        issue = "Optimize PostgreSQL connection pooling settings."
        diff = "+body { background-color: #f0f0f0; margin: 0; }"
        cosine_sim, drift_flag = self.analyzer.compute_alignment(issue, diff)
        assert cosine_sim < SEMANTIC_DRIFT_THRESHOLD
        assert drift_flag == 1

    def test_aligned_issue_and_diff_full_features(self):
        """When issue and diff describe the same functionality, F13 is high and F17 is 0."""
        issue_title = "Add discount rate validation to calculate_total"
        issue_desc = (
            "We need to validate discount_rate in calculate_total. "
            "If discount_rate is outside [0.0, 1.0], raise ValueError. "
            "Also apply the discount to the returned total."
        )
        raw_diff = (
            "@@ -1,5 +1,10 @@\n"
            " def calculate_total(prices: list[float], discount_rate: float = 0.0) -> float:\n"
            "+    '''Calculates subtotal with discount rate validation.'''\n"
            "+    if discount_rate < 0.0 or discount_rate > 1.0:\n"
            "+        raise ValueError('discount_rate must be between 0.0 and 1.0')\n"
            "     total = 0.0\n"
            "     for price in prices:\n"
            "-        total += price\n"
            "+        if price > 0:\n"
            "+            total += price\n"
            "+    return total * (1.0 - discount_rate)\n"
        )

        metrics = self.analyzer.analyze(
            issue_description=issue_desc,
            raw_diff=raw_diff,
            issue_title=issue_title,
        )

        assert metrics["intent_diff_cosine"] >= SEMANTIC_DRIFT_THRESHOLD
        assert metrics["semantic_drift_flag"] == 0
        assert metrics["title_diff_cosine"] >= SEMANTIC_DRIFT_THRESHOLD
        assert metrics["entity_drift_jaccard"] < 0.7
        assert metrics["issue_token_length"] > 0
        assert metrics["docstring_code_ratio"] >= 0.0

    def test_drifted_issue_and_diff_full_features(self):
        """When issue asks for database pooling and diff changes UI CSS, flag drift."""
        issue_title = "Fix connection leak in PostgreSQL connection pool"
        issue_desc = (
            "Database connections in async pool are not being released on error. "
            "Need to ensure session.close() is called in finally block."
        )
        raw_diff = (
            "@@ -10,3 +10,8 @@\n"
            "+/* Add glowing button styling for dashboard submit button */\n"
            "+.submit-button {\n"
            "+    background: linear-gradient(135deg, #6366f1, #a855f7);\n"
            "+    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);\n"
            "+    border-radius: 8px;\n"
            "+}\n"
        )

        metrics = compute_semantic_drift(
            issue_description=issue_desc,
            raw_diff=raw_diff,
            issue_title=issue_title,
        )

        assert metrics["intent_diff_cosine"] < SEMANTIC_DRIFT_THRESHOLD
        assert metrics["semantic_drift_flag"] == 1
        assert metrics["entity_drift_jaccard"] == 1.0

    def test_empty_issue_triggers_drift_flag(self):
        """Empty issue description must trigger semantic_drift_flag = 1."""
        metrics = self.analyzer.analyze(
            issue_description="",
            raw_diff="def foo(): pass",
            issue_title="",
        )
        assert metrics["intent_diff_cosine"] == 0.0
        assert metrics["semantic_drift_flag"] == 1
        assert metrics["issue_token_length"] == 0

    def test_empty_diff_triggers_drift_flag(self):
        """Empty diff must trigger semantic_drift_flag = 1."""
        metrics = self.analyzer.analyze(
            issue_description="Please fix the bug in calculate_total.",
            raw_diff="",
        )
        assert metrics["intent_diff_cosine"] == 0.0
        assert metrics["semantic_drift_flag"] == 1

    def test_missing_title_falls_back_to_intent_cosine(self):
        """If issue_title is omitted, title_diff_cosine matches intent_diff_cosine."""
        issue_desc = "Add discount rate validation in calculate_total."
        diff = "def calculate_total(prices, discount_rate=0.0): pass"
        metrics = self.analyzer.analyze(
            issue_description=issue_desc,
            raw_diff=diff,
            issue_title="",
        )
        assert metrics["title_diff_cosine"] == metrics["intent_diff_cosine"]

    def test_all_f13_to_f18_features_present(self):
        """Validates that all required feature keys are present in output dictionary."""
        metrics = self.analyzer.analyze(
            issue_description="Sample issue",
            raw_diff="Sample diff",
        )
        required_keys = {
            "intent_diff_cosine",
            "title_diff_cosine",
            "entity_drift_jaccard",
            "docstring_code_ratio",
            "semantic_drift_flag",
            "issue_token_length",
        }
        assert required_keys.issubset(metrics.keys())
