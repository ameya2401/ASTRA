"""
src/semantic_engine/embedder.py - Sentence-transformers singleton wrapper.

Manages a thread-safe singleton instance of the all-MiniLM-L6-v2
sentence transformer model for generating dense text embeddings.
"""
from __future__ import annotations

import logging
import threading
from typing import Optional, Union

import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import get_settings

logger = logging.getLogger(__name__)

# Dense embedding dimensionality for all-MiniLM-L6-v2
EMBEDDING_DIM: int = 384


class SentenceEmbedder:
    """
    Thread-safe singleton wrapper for SentenceTransformer embedding generation.

    Caches a single loaded instance of the transformer model across the application
    to prevent repeated model loads and minimize memory overhead.

    Attributes:
        model_name: Identifier for the HuggingFace model checkpoint.
        model: The underlying SentenceTransformer instance.
    """

    _instance: Optional[SentenceEmbedder] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(
        cls,
        model_name: Optional[str] = None,
    ) -> SentenceEmbedder:
        with cls._lock:
            if cls._instance is None:
                instance = super(SentenceEmbedder, cls).__new__(cls)
                settings = get_settings()
                chosen_name = model_name or getattr(settings, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
                logger.info("Initializing SentenceEmbedder singleton with model: %s", chosen_name)
                instance.model_name = chosen_name
                instance.model = SentenceTransformer(chosen_name)
                cls._instance = instance
            elif model_name is not None and model_name != cls._instance.model_name:
                logger.warning(
                    "SentenceEmbedder singleton already initialized with '%s'. "
                    "Ignoring requested model_name '%s'.",
                    cls._instance.model_name,
                    model_name,
                )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets the cached singleton instance (useful for testing)."""
        with cls._lock:
            cls._instance = None

    def get_embedding_dimension(self) -> int:
        """
        Returns the dense embedding vector dimensionality.
        For all-MiniLM-L6-v2, this is 384.
        """
        if hasattr(self.model, "get_embedding_dimension"):
            return self.model.get_embedding_dimension()
        if hasattr(self.model, "get_sentence_embedding_dimension"):
            return self.model.get_sentence_embedding_dimension()
        return 384

    def encode(
        self,
        texts: Union[str, list[str]],
        normalize_embeddings: bool = True,
        batch_size: int = 32,
        show_progress_bar: bool = False,
    ) -> np.ndarray:
        """
        Generates dense vector embeddings for input text(s).

        Args:
            texts: Single string or list of text strings to embed.
            normalize_embeddings: When True, applies L2-normalization so that
                the dot product between vectors equals cosine similarity.
            batch_size: Mini-batch size for encoding.
            show_progress_bar: Whether to display a progress bar.

        Returns:
            np.ndarray: 1D array of shape (dim,) if a single string was passed,
                        or 2D array of shape (N, dim) if a list was passed.
        """
        is_single = isinstance(texts, str)
        text_list = [texts] if is_single else list(texts)

        # Handle empty string inputs safely
        sanitized = [t if t.strip() else " " for t in text_list]

        embeddings = self.model.encode(
            sanitized,
            normalize_embeddings=normalize_embeddings,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            convert_to_numpy=True,
        )

        if is_single:
            return embeddings[0]
        return embeddings


def get_embedder(model_name: Optional[str] = None) -> SentenceEmbedder:
    """Convenience helper to obtain the SentenceEmbedder singleton."""
    return SentenceEmbedder(model_name=model_name)
