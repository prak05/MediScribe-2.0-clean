"""Transformers, Tokenization, and Context Window Utilities.
Fundamentals Layer.
"""

from typing import List
import math
import re

class TransformerTokenizer:
    """Tokenizer and attention token management utility for transformer context windows."""

    def __init__(self, avg_chars_per_token: float = 4.0):
        self.avg_chars_per_token = avg_chars_per_token

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for prompt budget management."""
        if not text:
            return 0
        return max(1, int(len(text) / self.avg_chars_per_token))

    def truncate_to_context_budget(self, text: str, max_tokens: int = 8000) -> str:
        """Trim text if it exceeds maximum token budget."""
        max_chars = int(max_tokens * self.avg_chars_per_token)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "... [TRUNCATED DUE TO CONTEXT LIMIT]"

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Standard cosine similarity for transformer vector embeddings."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 <= 0 or n2 <= 0:
            return 0.0
        return dot / (n1 * n2)
