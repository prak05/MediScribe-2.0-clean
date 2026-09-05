"""Semantic Retrieval Service for MediScribe.
Commandment 8: Choice of Retrieval Interface (Dense Vector Nearest Neighbor Search).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.config import settings
from core.embedding.embedder import BaseEmbedder, get_embedder
from core.indexing.vector_store import VectorIndex, get_vector_store

@dataclass
class RetrievedChunk:
    """Represents a retrieved context chunk with confidence score."""
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.metadata.get("filename", "Medical Source")

    @property
    def page(self) -> int:
        return self.metadata.get("page_number", 1)

    @property
    def doc_id(self) -> Optional[str]:
        return self.metadata.get("doc_id")

class SemanticRetriever:
    """Retrieves top-k relevant chunks from the indexed vector store."""

    def __init__(
        self,
        vector_index: Optional[VectorIndex] = None,
        embedder: Optional[BaseEmbedder] = None,
        top_k: Optional[int] = None,
    ):
        self.vector_index = vector_index or get_vector_store()
        self.embedder = embedder or get_embedder()
        self.top_k = top_k or settings.retrieval.similarity_top_k

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[RetrievedChunk]:
        """Perform dense vector retrieval for the user query."""
        clean_query = (query or "").strip()
        if not clean_query or len(self.vector_index) == 0:
            return []

        k = top_k or self.top_k
        query_vector = self.embedder.embed_text(clean_query)
        matches = self.vector_index.query(query_vector, top_k=k)

        results: List[RetrievedChunk] = []
        for chunk, score in matches:
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=float(score),
                    metadata=dict(chunk.metadata)
                )
            )
        return results
