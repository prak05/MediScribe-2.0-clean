"""Vector Store & Indexing Engine for MediScribe.
Commandment 5: Choice of Vector Database & Local Persistent Storage.
Commandment 6: Choice of Frameworks for Interaction.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import math
import os
import shutil

from core.config import settings
from core.chunking.chunker import TextChunk
from core.embedding.embedder import BaseEmbedder, get_embedder

@dataclass
class IndexedNode:
    """Represents a chunk indexed with its vector embedding."""
    node_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_chunk(self) -> TextChunk:
        return TextChunk(
            text=self.text,
            chunk_id=self.node_id,
            doc_id=self.metadata.get("doc_id"),
            metadata=self.metadata
        )

class VectorIndex:
    """Vector storage and similarity indexing engine with persistence."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or settings.vector_db.storage_dir
        self.nodes: List[IndexedNode] = []
        self._doc_ids = set()
        self._sources = set()

    def __len__(self) -> int:
        return len(self.nodes)

    def clear(self) -> None:
        """Reset the index and delete persisted files."""
        self.nodes.clear()
        self._doc_ids.clear()
        self._sources.clear()
        if self.storage_dir.exists():
            shutil.rmtree(self.storage_dir, ignore_errors=True)

    def add_chunks(self, chunks: List[TextChunk], embedder: Optional[BaseEmbedder] = None) -> int:
        """Embed and index candidate chunks into the vector store."""
        if not chunks:
            return 0

        embed_engine = embedder or get_embedder()
        texts = [c.text for c in chunks]
        embeddings = embed_engine.embed_batch(texts)

        for chunk, emb in zip(chunks, embeddings):
            node = IndexedNode(
                node_id=chunk.chunk_id,
                text=chunk.text,
                embedding=emb,
                metadata=dict(chunk.metadata)
            )
            self.nodes.append(node)
            if chunk.doc_id:
                self._doc_ids.add(chunk.doc_id)
            if chunk.source:
                self._sources.add(chunk.source)

        if settings.vector_db.persist_on_disk:
            self.save()

        return len(chunks)

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two high-dimensional vectors."""
        if len(vec1) != len(vec2) or not vec1:
            return 0.0

        dot = 0.0
        norm1 = 0.0
        norm2 = 0.0
        for a, b in zip(vec1, vec2):
            dot += a * b
            norm1 += a * a
            norm2 += b * b

        if norm1 <= 0.0 or norm2 <= 0.0:
            return 0.0
        return dot / (math.sqrt(norm1) * math.sqrt(norm2))

    def query(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[TextChunk, float]]:
        """Retrieve top-k nearest chunks ranked by cosine similarity."""
        if not self.nodes:
            return []

        scored_nodes: List[Tuple[IndexedNode, float]] = []
        for node in self.nodes:
            sim = self._cosine_similarity(query_vector, node.embedding)
            scored_nodes.append((node, sim))

        # Sort descending by similarity score
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored_nodes[:top_k]

        return [(node.to_chunk(), score) for node, score in top_matches]

    def save(self, target_dir: Optional[Path] = None) -> Path:
        """Persist the vector index manifest and nodes to disk."""
        dest = target_dir or self.storage_dir
        dest.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0.0",
            "total_nodes": len(self.nodes),
            "sources": list(self._sources),
            "nodes": [
                {
                    "node_id": n.node_id,
                    "text": n.text,
                    "embedding": n.embedding,
                    "metadata": n.metadata
                }
                for n in self.nodes
            ]
        }

        manifest_path = dest / "index_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return manifest_path

    def load(self, target_dir: Optional[Path] = None) -> bool:
        """Load persisted index from disk if present."""
        dest = target_dir or self.storage_dir
        manifest_path = dest / "index_manifest.json"
        if not manifest_path.exists():
            return False

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.nodes = []
            self._doc_ids = set()
            self._sources = set()

            for item in data.get("nodes", []):
                node = IndexedNode(
                    node_id=item["node_id"],
                    text=item["text"],
                    embedding=item["embedding"],
                    metadata=item.get("metadata", {})
                )
                self.nodes.append(node)
                if node.metadata.get("doc_id"):
                    self._doc_ids.add(node.metadata["doc_id"])
                if node.metadata.get("filename"):
                    self._sources.add(node.metadata["filename"])
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return analytics and health statistics for the index."""
        manifest_path = self.storage_dir / "index_manifest.json"
        size_bytes = manifest_path.stat().st_size if manifest_path.exists() else 0
        avg_chunk_len = sum(len(n.text) for n in self.nodes) // len(self.nodes) if self.nodes else 0

        return {
            "total_chunks": len(self.nodes),
            "total_documents": len(self._doc_ids) or len(self._sources),
            "sources": list(self._sources),
            "average_chunk_chars": avg_chunk_len,
            "dimension": len(self.nodes[0].embedding) if self.nodes else settings.embedding.dimension,
            "storage_size_bytes": size_bytes,
            "storage_path": str(self.storage_dir),
            "is_ready": len(self.nodes) > 0,
        }

# Global singleton instance
_index_instance: Optional[VectorIndex] = None

def get_vector_store() -> VectorIndex:
    global _index_instance
    if _index_instance is None:
        _index_instance = VectorIndex()
        # Attempt auto-load from disk
        _index_instance.load()
    return _index_instance
