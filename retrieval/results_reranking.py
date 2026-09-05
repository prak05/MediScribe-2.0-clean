"""RESULTS (RERANKING)
Retrieval Layer (Commandment 8: Re-ranking & Post-Processing).
"""

from dataclasses import dataclass
from typing import List, Optional, Set
import math
import re

from core.config import settings
from .retrieve_chunks import RetrievedChunk

@dataclass
class RerankedChunk:
    """Retrieved chunk post-reranking with diagnostic score breakdown."""
    chunk: RetrievedChunk
    original_score: float
    reranked_score: float
    lexical_score: float
    medical_boost: float
    rank_delta: int = 0

    @property
    def chunk_id(self) -> str:
        return self.chunk.chunk_id

    @property
    def text(self) -> str:
        return self.chunk.text

    @property
    def source(self) -> str:
        return self.chunk.source

    @property
    def page(self) -> int:
        return self.chunk.page

class MedicalReranker:
    """Re-ranks retrieved chunks using hybrid lexical overlap, medical terminology boosting, and thresholding."""

    CLINICAL_KEYWORDS: Set[str] = {
        "treatment", "diagnosis", "therapy", "contraindication", "contraindicated",
        "dosage", "dose", "adverse", "syndrome", "guideline", "first-line",
        "second-line", "pediatric", "geriatric", "hypertension", "diabetes",
        "cardiovascular", "renal", "hepatic", "toxicity", "pathology",
        "pharmacology", "staging", "mortality", "morbidity", "indication",
        "mg", "mcg", "g", "iv", "po", "subcutaneous", "infusion"
    }

    def __init__(
        self,
        vector_weight: float = 0.55,
        lexical_weight: float = 0.30,
        medical_boost_weight: float = 0.15,
        min_threshold: float = 0.0
    ):
        self.vector_weight = vector_weight
        self.lexical_weight = lexical_weight
        self.medical_boost_weight = medical_boost_weight
        self.min_threshold = min_threshold

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def compute_lexical_score(self, query_tokens: List[str], chunk_tokens: List[str]) -> float:
        """Compute term overlap score between query and candidate chunk."""
        if not query_tokens or not chunk_tokens:
            return 0.0
        q_set = set(query_tokens)
        c_set = set(chunk_tokens)
        overlap = q_set.intersection(c_set)
        return len(overlap) / float(len(q_set))

    def compute_medical_boost(self, query_tokens: List[str], chunk_tokens: List[str]) -> float:
        """Check for presence of critical clinical indicators relevant to query."""
        c_set = set(chunk_tokens)
        clinical_matches = c_set.intersection(self.CLINICAL_KEYWORDS)
        if not clinical_matches:
            return 0.0
        # Normalized boost capped at 1.0
        return min(1.0, len(clinical_matches) / 5.0)

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: Optional[int] = None
    ) -> List[RerankedChunk]:
        """Apply multi-factor re-ranking formula to prioritize high-fidelity evidence."""
        if not chunks:
            return []

        query_tokens = self._tokenize(query)
        scored: List[RerankedChunk] = []

        for original_idx, chunk in enumerate(chunks):
            chunk_tokens = self._tokenize(chunk.text)
            lexical_score = self.compute_lexical_score(query_tokens, chunk_tokens)
            medical_boost = self.compute_medical_boost(query_tokens, chunk_tokens)

            # Combined multi-factor score
            final_score = (
                (self.vector_weight * chunk.score) +
                (self.lexical_weight * lexical_score) +
                (self.medical_boost_weight * medical_boost)
            )

            # Threshold filtering (Commandment 8: drop irrelevant chunks)
            if final_score >= self.min_threshold:
                scored.append(
                    RerankedChunk(
                        chunk=chunk,
                        original_score=chunk.score,
                        reranked_score=final_score,
                        lexical_score=lexical_score,
                        medical_boost=medical_boost,
                        rank_delta=0
                    )
                )

        # Sort descending by re-ranked score
        scored.sort(key=lambda x: x.reranked_score, reverse=True)

        # Compute rank deltas
        k = top_k or len(scored)
        final_results = scored[:k]
        for new_idx, r in enumerate(final_results):
            orig_idx = next((i for i, c in enumerate(chunks) if c.chunk_id == r.chunk_id), new_idx)
            r.rank_delta = orig_idx - new_idx  # positive means moved up in rank

        return final_results
