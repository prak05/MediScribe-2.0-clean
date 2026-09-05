"""Document Chunking Engine for MediScribe.
Commandment 3: Choice of Chunking Strategy (Sentence vs Semantic Splitting).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import re
import uuid

from core.ingestion.loader import Document

class ChunkingStrategy(str, Enum):
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    PARAGRAPH = "paragraph"

@dataclass
class TextChunk:
    """Represents an atomic, searchable text unit."""
    text: str
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.metadata.get("filename", "Unknown Document")

    @property
    def page(self) -> int:
        return self.metadata.get("page_number", 1)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def __len__(self) -> int:
        return len(self.text)

class DocumentChunker:
    """Configurable text chunking system respecting sentence and semantic boundaries."""

    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.SENTENCE,
        chunk_size: int = 1024,
        chunk_overlap: int = 100,
        separator: str = " "
    ):
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        # Sentence boundary regex (handles abbreviations like Dr., etc.)
        self._sentence_regex = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text while keeping medical punctuation intact."""
        sentences = self._sentence_regex.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Group sentences until chunk_size is approached, then overlap."""
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []

        chunks = []
        current_chunk: List[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_len + sentence_len + 1 > self.chunk_size and current_chunk:
                # Save current chunk
                full_chunk_text = self.separator.join(current_chunk)
                chunks.append(full_chunk_text)

                # Prepare overlap: retain trailing sentences up to chunk_overlap chars
                overlap_chunk: List[str] = []
                overlap_len = 0
                for prev_s in reversed(current_chunk):
                    if overlap_len + len(prev_s) <= self.chunk_overlap:
                        overlap_chunk.insert(0, prev_s)
                        overlap_len += len(prev_s) + 1
                    else:
                        break
                current_chunk = overlap_chunk
                current_len = sum(len(s) for s in current_chunk) + len(current_chunk)

            current_chunk.append(sentence)
            current_len += sentence_len + 1

        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks

    def _chunk_by_semantic_paragraphs(self, text: str) -> List[str]:
        """Group paragraphs and sub-sections for semantic continuity."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return self._chunk_by_sentences(text)

        chunks = []
        current_chunk: List[str] = []
        current_len = 0

        for p in paragraphs:
            # If paragraph itself is too large, split by sentences
            if len(p) > self.chunk_size:
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                chunks.extend(self._chunk_by_sentences(p))
                continue

            if current_len + len(p) + 2 > self.chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [p]
                current_len = len(p)
            else:
                current_chunk.append(p)
                current_len += len(p) + 2

        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks

    def split_document(self, document: Document) -> List[TextChunk]:
        """Split a single Document into TextChunks with preserved lineage metadata."""
        if not document.text.strip():
            return []

        if self.strategy == ChunkingStrategy.SEMANTIC:
            raw_chunks = self._chunk_by_semantic_paragraphs(document.text)
        else:
            raw_chunks = self._chunk_by_sentences(document.text)

        result_chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            meta = dict(document.metadata)
            meta.update({
                "chunk_index": idx,
                "total_chunks_in_doc": len(raw_chunks),
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "chunking_strategy": self.strategy.value,
            })
            result_chunks.append(
                TextChunk(
                    text=chunk_text,
                    doc_id=document.doc_id,
                    metadata=meta
                )
            )
        return result_chunks

    def split_documents(self, documents: List[Document]) -> List[TextChunk]:
        """Batch chunk a collection of medical documents."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.split_document(doc))
        return all_chunks
