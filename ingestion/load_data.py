"""(1) -> DATA .md -> LOAD DATA
Ingestion Layer (Commandment 1: Choice of Data - PDF, Markdown, Plaintext).
"""

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import datetime
import os
import re
import uuid

@dataclass
class IngestedDocument:
    """Document extracted from .md, .pdf, or plaintext files."""
    text: str
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def source(self) -> str:
        return self.metadata.get("filename", "Unknown Document")

    @property
    def page(self) -> int:
        return self.metadata.get("page_number", 1)

    def __len__(self) -> int:
        return len(self.text)

class DataLoader:
    """Loads and sanitizes medical data from .md files, textbook PDFs, and clinical notes."""

    @staticmethod
    def sanitize(text: str) -> str:
        """Clean whitespace, unicode inconsistencies, and hyphenated breaks."""
        if not text:
            return ""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Repair broken words across lines (e.g. car- / diovascular -> cardiovascular)
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def load_markdown_data(self, file_path: Path | str) -> List[IngestedDocument]:
        """(1) -> DATA .md: Ingest structured clinical markdown files."""
        path = Path(file_path)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        cleaned = self.sanitize(content)
        if not cleaned:
            return []

        return [
            IngestedDocument(
                text=cleaned,
                metadata={
                    "filename": path.name,
                    "filepath": str(path),
                    "page_number": 1,
                    "source_type": "markdown",
                    "file_size_bytes": path.stat().st_size if path.exists() else len(content),
                    "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
            )
        ]

    def load_pdf_data(self, file_path: Path | str) -> List[IngestedDocument]:
        """Extract multi-page medical textbook PDF documents."""
        path = Path(file_path)
        documents = []

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            for idx, page in enumerate(reader.pages):
                txt = page.extract_text() or ""
                cleaned = self.sanitize(txt)
                if cleaned:
                    documents.append(
                        IngestedDocument(
                            text=cleaned,
                            metadata={
                                "filename": path.name,
                                "page_number": idx + 1,
                                "total_pages": total_pages,
                                "source_type": "pdf",
                                "file_size_bytes": path.stat().st_size,
                                "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            }
                        )
                    )
        except Exception:
            # Fallback simple binary read
            with open(path, "rb") as f:
                raw = f.read()
            return self.load_bytes_data(path.name, raw)

        return documents

    def load_bytes_data(self, filename: str, raw_bytes: bytes) -> List[IngestedDocument]:
        """Load in-memory uploaded file bytes from web/UI requests."""
        docs = []
        if filename.lower().endswith(".pdf"):
            try:
                from pypdf import PdfReader
                reader = PdfReader(BytesIO(raw_bytes))
                for idx, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    cleaned = self.sanitize(txt)
                    if cleaned:
                        docs.append(IngestedDocument(
                            text=cleaned,
                            metadata={
                                "filename": filename,
                                "page_number": idx + 1,
                                "total_pages": len(reader.pages),
                                "source_type": "pdf",
                                "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            }
                        ))
                if docs:
                    return docs
            except Exception:
                pass

        # Text/Markdown fallback
        text_str = raw_bytes.decode("utf-8", errors="ignore")
        cleaned = self.sanitize(text_str)
        if cleaned:
            docs.append(IngestedDocument(
                text=cleaned,
                metadata={"filename": filename, "page_number": 1, "source_type": "text"}
            ))
        return docs

    def load(self, source: Path | str) -> List[IngestedDocument]:
        """Universal loader routing by file extension."""
        path = Path(source)
        if path.is_dir():
            all_docs = []
            for root, _, files in os.walk(path):
                for f in files:
                    fp = Path(root) / f
                    if fp.suffix.lower() in [".md", ".pdf", ".txt"]:
                        all_docs.extend(self.load(fp))
            return all_docs

        if path.suffix.lower() == ".md":
            return self.load_markdown_data(path)
        elif path.suffix.lower() == ".pdf":
            return self.load_pdf_data(path)
        else:
            return self.load_markdown_data(path)
