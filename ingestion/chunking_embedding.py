"""-> CHUNKING & EMBEDDING (LLM)
Ingestion Layer (Commandment 3: Chunking & Commandment 4: Embedding).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import math
import re
import uuid

from core.config import settings
from fundamentals.transformers import TransformerTokenizer
from .load_data import IngestedDocument

@dataclass
class ChunkedEmbedding:
    """Atomic text chunk bundled with its computed LLM vector embedding."""
    chunk_id: str
    text: str
    embedding: List[float]
    doc_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.metadata.get("filename", "Unknown Document")

    @property
    def page(self) -> int:
        return self.metadata.get("page_number", 1)

class ChunkerEmbedder:
    """Performs sentence-boundary chunking and vector embedding using Gemini."""

    def __init__(
        self,
        chunk_size: int = 1024,
        chunk_overlap: int = 100,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        offline: bool = False
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.api_key = api_key or settings.api_key
        self.model_name = model_name or settings.embedding.model_name
        self.dimension = settings.embedding.dimension
        self.offline = offline or (self.model_name == "offline-hash-embedder")
        self.tokenizer = TransformerTokenizer()
        self._sent_regex = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

    def _split_sentences(self, text: str) -> List[str]:
        return [s.strip() for s in self._sent_regex.split(text) if s.strip()]

    def chunk_text(self, text: str) -> List[str]:
        """Split text while keeping medical sentence structure intact."""
        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks = []
        curr: List[str] = []
        curr_len = 0

        for s in sentences:
            slen = len(s)
            if curr_len + slen + 1 > self.chunk_size and curr:
                chunks.append(" ".join(curr))
                # Overlap
                overlap: List[str] = []
                olen = 0
                for prev in reversed(curr):
                    if olen + len(prev) <= self.chunk_overlap:
                        overlap.insert(0, prev)
                        olen += len(prev) + 1
                    else:
                        break
                curr = overlap
                curr_len = sum(len(x) for x in curr) + len(curr)

            curr.append(s)
            curr_len += slen + 1

        if curr:
            chunks.append(" ".join(curr))
        return chunks

    def _hash_embed(self, text: str) -> List[float]:
        """High-entropy deterministic token-frequency vector for offline / testing."""
        import hashlib
        vec = [0.0] * self.dimension
        tokens = re.findall(r"\b\w{2,}\b", text.lower())
        if not tokens:
            return [1.0] + [0.0] * (self.dimension - 1)

        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            vec[idx] += 1.0

        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec] if norm > 0 else [1.0] + [0.0] * (self.dimension - 1)

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector using Gemini or deterministic local fallback."""
        if not text:
            return [0.0] * self.dimension

        if self.offline:
            return self._hash_embed(text)

        clean_model = self.model_name.replace("models/", "")
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            res = client.models.embed_content(
                model=clean_model,
                contents=text[:8000]
            )
            if res and res.embeddings and res.embeddings[0].values:
                return list(res.embeddings[0].values)
        except Exception:
            pass

        # Deterministic unit-norm hash fallback for offline continuity
        return self._hash_embed(text)

    def process_document(self, doc: IngestedDocument) -> List[ChunkedEmbedding]:
        """Chunk a document and compute vector embeddings for each chunk."""
        raw_chunks = self.chunk_text(doc.text)
        results: List[ChunkedEmbedding] = []

        for idx, text in enumerate(raw_chunks):
            vector = self.embed_text(text)
            meta = dict(doc.metadata)
            meta.update({
                "chunk_index": idx,
                "total_chunks": len(raw_chunks),
                "estimated_tokens": self.tokenizer.estimate_tokens(text),
                "doc_id": doc.doc_id
            })
            results.append(
                ChunkedEmbedding(
                    chunk_id=str(uuid.uuid4()),
                    text=text,
                    embedding=vector,
                    doc_id=doc.doc_id,
                    metadata=meta
                )
            )
        return results

    def process_documents(self, docs: List[IngestedDocument]) -> List[ChunkedEmbedding]:
        """Batch process multiple documents."""
        all_chunks = []
        for d in docs:
            all_chunks.extend(self.process_document(d))
        return all_chunks
