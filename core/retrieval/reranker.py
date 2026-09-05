"""Intelligent Re-ranking & Filtering Module for MediScribe.
Commandment 8: Choice of Retrieval Interface (Query Re-ranking & Cross-Scoring).
"""

from typing import List, Optional
import math
import re

from core.config import settings
from .retriever import RetrievedChunk

class ReRanker:
    """Multi-signal re-ranking engine combining dense similarity, lexical overlap, and medical keyword boost."""

    def __init__(
        self,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ):
        self.top_k = top_k or settings.retrieval.rerank_top_k
        self.threshold = threshold or settings.retrieval.similarity_threshold

    @staticmethod
    def _extract_keywords(text: str) -> set:
        """Extract clean lowercased tokens longer than 2 characters."""
        words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
        # Filter common stopwords
        stopwords = {
            "the", "and", "for", "with", "this", "that", "from", "are", "was",
            "were", "been", "have", "has", "had", "what", "which", "when", "where",
            "who", "how", "why", "about", "can", "will", "would", "should", "does"
        }
        return {w for w in words if w not in stopwords}

    def _calculate_lexical_overlap(self, query: str, text: str) -> float:
        """Compute Jaccard/overlap score between query and context tokens."""
        q_tokens = self._extract_keywords(query)
        if not q_tokens:
            return 0.5

        t_tokens = self._extract_keywords(text)
        if not t_tokens:
            return 0.0

        intersection = q_tokens.intersection(t_tokens)
        return len(intersection) / len(q_tokens)

    def rerank(
        self,
        query: str,
        candidates: List[RetrievedChunk],
        top_k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[RetrievedChunk]:
        """Re-rank candidate chunks, apply threshold filtering, and return top-n evidence."""
        if not candidates:
            return []

        k = top_k or self.top_k
        min_score = threshold or self.threshold

        reranked: List[RetrievedChunk] = []

        for chunk in candidates:
            # Signal 1: Dense Vector Similarity (0.0 to 1.0)
            dense_score = max(0.0, min(1.0, chunk.score))

            # Signal 2: Lexical Token Overlap (0.0 to 1.0)
            lexical_score = self._calculate_lexical_overlap(query, chunk.text)

            # Signal 3: Medical Keyword Density Bonus
            bonus = 0.0
            if "treatment" in query.lower() and "treatment" in chunk.text.lower():
                bonus += 0.05
            if "diagnosis" in query.lower() and "diagnosis" in chunk.text.lower():
                bonus += 0.05
            if "dosage" in query.lower() and ("mg" in chunk.text.lower() or "dose" in chunk.text.lower()):
                bonus += 0.05

            # Blended Re-ranking Score
            final_score = (0.65 * dense_score) + (0.35 * lexical_score) + bonus
            final_score = min(1.0, final_score)

            # Update chunk with blended score
            updated_chunk = RetrievedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                score=final_score,
                metadata=dict(chunk.metadata)
            )
            updated_chunk.metadata["dense_score"] = round(dense_score, 4)
            updated_chunk.metadata["lexical_score"] = round(lexical_score, 4)
            updated_chunk.metadata["rerank_score"] = round(final_score, 4)

            # Prune noisy / irrelevant chunks below confidence threshold
            if final_score >= min_score or len(candidates) <= 2:
                reranked.append(updated_chunk)

        # If strict threshold pruned everything, retain top candidate
        if not reranked and candidates:
            best_fallback = max(candidates, key=lambda c: c.score)
            reranked.append(best_fallback)

        # Sort descending by rerank score
        reranked.sort(key=lambda c: c.score, reverse=True)
        return reranked[:k]
