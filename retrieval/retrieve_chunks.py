"""RETRIEVE CHUNKS (Vector Search & Dense Retrieval)
Retrieval Layer (Commandment 6: Retrieval & Commandment 7: Framing Prompts).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from core.config import settings
from fundamentals.models import ModelRegistry
from fundamentals.user_system_prompts import MedicalPrompts
from ingestion.chunking_embedding import ChunkerEmbedder
from ingestion.store_vector_db import VectorDBStore

logger = logging.getLogger(__name__)

@dataclass
class RetrievedChunk:
    """A scored medical context block retrieved from the vector index."""
    chunk_id: str
    text: str
    score: float
    source: str = "Unknown Document"
    page: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_citation(self, index: int) -> str:
        return f"[Source {index}: {self.source}, Page {self.page}]"

class ChunkRetriever:
    """Executes dense vector semantic retrieval against indexed medical textbooks."""

    def __init__(
        self,
        vector_store: Optional[VectorDBStore] = None,
        embedder: Optional[ChunkerEmbedder] = None,
        top_k: int = 5
    ):
        self.vector_store = vector_store if vector_store is not None else VectorDBStore()
        self.embedder = embedder if embedder is not None else ChunkerEmbedder()
        self.top_k = top_k if top_k is not None else settings.retrieval.similarity_top_k

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: float = 0.0
    ) -> List[RetrievedChunk]:
        """Convert clinical query to dense vector embedding and search vector store."""
        k = top_k or self.top_k
        if not query or not query.strip():
            return []

        # 1. Embed user query using the same embedding model as indexing
        query_vector = self.embedder.embed_text(query)

        # 2. Search nearest neighbor chunks
        raw_results = self.vector_store.search(
            query_vector=query_vector,
            top_k=k,
            score_threshold=score_threshold
        )

        retrieved: List[RetrievedChunk] = []
        for chunk, score in raw_results:
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=float(score),
                    source=chunk.metadata.get("filename", "Unknown Medical Text"),
                    page=chunk.metadata.get("page_number", 1),
                    metadata=chunk.metadata
                )
            )

        return retrieved

    def format_context_blocks(self, chunks: List[RetrievedChunk]) -> List[str]:
        """Format retrieved chunks into numbered citations for the prompt context."""
        blocks = []
        for idx, c in enumerate(chunks, start=1):
            citation_header = f"[Source {idx}: {c.source}, Page {c.page}] (Similarity Score: {c.score:.3f})"
            blocks.append(f"{citation_header}\n{c.text.strip()}")
        return blocks

    def synthesize_answer(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Feed retrieved evidence and clinical prompt into LLM for evidence-grounded response."""
        context_blocks = self.format_context_blocks(chunks)
        prompt = MedicalPrompts.format_user_prompt(query, context_blocks)
        model = model_name or ModelRegistry.get_default_llm()
        clean_model = model.replace("models/", "")

        citations = [c.to_citation(i) for i, c in enumerate(chunks, start=1)]

        # If no context found, return strict disclaimer per Commandment 7
        if not chunks:
            return {
                "answer": "The provided medical textbooks do not contain sufficient evidence to answer this question.",
                "citations": [],
                "chunks": [],
                "model_used": clean_model,
                "disclaimer": MedicalPrompts.DISCLAIMER
            }

        try:
            from google import genai
            client = genai.Client(api_key=settings.api_key)
            response = client.models.generate_content(
                model=clean_model,
                contents=prompt
            )
            raw_text = response.text if response and hasattr(response, "text") else ""
            answer = raw_text.strip() if raw_text else "Unable to generate answer from clinical context."
        except Exception as e:
            logger.warning(f"LLM API call failed: {e}. Generating grounded synthesis fallback.")
            # Grounded offline fallback synthesis
            primary_evidence = chunks[0].text if chunks else "No evidence available."
            answer = (
                f"Based on clinical evidence in {chunks[0].source} (Page {chunks[0].page}):\n"
                f"{primary_evidence[:400]}...\n\n"
                f"[Grounded strictly in retrieved sources: {', '.join(citations[:2])}]\n\n"
                f"{MedicalPrompts.DISCLAIMER}"
            )

        return {
            "answer": answer,
            "citations": citations,
            "chunks": [
                {
                    "chunk_id": c.chunk_id,
                    "source": c.source,
                    "page": c.page,
                    "score": c.score,
                    "text": c.text
                }
                for c in chunks
            ],
            "model_used": clean_model,
            "disclaimer": MedicalPrompts.DISCLAIMER
        }
