"""-> STORE IN VECTOR DATABASE (Vector Store)
Ingestion Layer (Commandment 5: Storage - Choice of Vector Database & Indexing).
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import logging
import math
import os
import time

from core.config import settings
from fundamentals.transformers import TransformerTokenizer
from .chunking_embedding import ChunkedEmbedding

logger = logging.getLogger(__name__)

class VectorDBStore:
    """Local, high-performance persistent vector database store for clinical embeddings."""

    def __init__(self, storage_dir: Optional[Path | str] = None, auto_load: bool = True):
        self.storage_dir = Path(storage_dir or settings.vector_db.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.storage_dir / "index_manifest.json"
        self.data_path = self.storage_dir / "vector_chunks.json"

        self._chunks: Dict[str, ChunkedEmbedding] = {}
        self._doc_ids: Dict[str, List[str]] = {}
        self.tokenizer = TransformerTokenizer()

        if auto_load and self.manifest_path.exists() and self.data_path.exists():
            self.load()

    def add_chunks(self, chunks: List[ChunkedEmbedding]) -> int:
        """Add chunked embeddings to the in-memory vector store."""
        added = 0
        for chunk in chunks:
            if not chunk or not chunk.chunk_id:
                continue
            self._chunks[chunk.chunk_id] = chunk
            doc_id = chunk.doc_id or chunk.metadata.get("doc_id", "default")
            if doc_id not in self._doc_ids:
                self._doc_ids[doc_id] = []
            if chunk.chunk_id not in self._doc_ids[doc_id]:
                self._doc_ids[doc_id].append(chunk.chunk_id)
            added += 1
        return added

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Tuple[ChunkedEmbedding, float]]:
        """Search nearest neighbor chunks by cosine similarity."""
        if not query_vector or not self._chunks:
            return []

        scored_chunks: List[Tuple[ChunkedEmbedding, float]] = []
        for chunk in self._chunks.values():
            sim = self.tokenizer.cosine_similarity(query_vector, chunk.embedding)
            if sim >= score_threshold:
                scored_chunks.append((chunk, float(sim)))

        # Sort descending by similarity score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:top_k]

    def save(self) -> bool:
        """Persist vector index and metadata to disk."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

            # Serialize all chunks
            chunks_data = []
            for chunk in self._chunks.values():
                chunks_data.append({
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "embedding": chunk.embedding,
                    "doc_id": chunk.doc_id,
                    "metadata": chunk.metadata
                })

            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(chunks_data, f)

            manifest = {
                "index_name": settings.vector_db.index_name,
                "total_chunks": len(self._chunks),
                "total_documents": len(self._doc_ids),
                "dimension": settings.embedding.dimension,
                "last_updated": time.time(),
                "chunk_ids": list(self._chunks.keys())
            }

            with open(self.manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error persisting vector store: {e}")
            return False

    def load(self) -> bool:
        """Load vector store from disk."""
        if not self.data_path.exists() or not self.manifest_path.exists():
            return False

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                chunks_data = json.load(f)

            self._chunks.clear()
            self._doc_ids.clear()

            for item in chunks_data:
                chunk = ChunkedEmbedding(
                    chunk_id=item["chunk_id"],
                    text=item["text"],
                    embedding=item["embedding"],
                    doc_id=item.get("doc_id"),
                    metadata=item.get("metadata", {})
                )
                self._chunks[chunk.chunk_id] = chunk
                doc_id = chunk.doc_id or chunk.metadata.get("doc_id", "default")
                if doc_id not in self._doc_ids:
                    self._doc_ids[doc_id] = []
                self._doc_ids[doc_id].append(chunk.chunk_id)

            return True
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            return False

    def clear(self):
        """Clear the vector store memory and disk index."""
        self._chunks.clear()
        self._doc_ids.clear()
        if self.manifest_path.exists():
            self.manifest_path.unlink(missing_ok=True)
        if self.data_path.exists():
            self.data_path.unlink(missing_ok=True)

    def get_stats(self) -> Dict[str, Any]:
        """Return index statistics for observability."""
        return {
            "total_chunks": len(self._chunks),
            "total_documents": len(self._doc_ids),
            "storage_dir": str(self.storage_dir),
            "is_persisted": self.manifest_path.exists() and self.data_path.exists(),
            "dimension": settings.embedding.dimension,
        }

    def __len__(self) -> int:
        return len(self._chunks)
