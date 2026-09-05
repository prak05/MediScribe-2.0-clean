"""Document Ingestion Module for MediScribe.
Commandment 1: Choice of Data (Formats: PDF, Markdown, Plain Text).
"""

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import re
import uuid
import datetime

@dataclass
class Document:
    """Represents a standardized ingested document unit."""
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

class DocumentLoader:
    """Universal loader for medical textbooks and clinical literature."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Sanitize raw extracted text from PDFs or notes."""
        if not text:
            return ""
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Fix hyphenated line breaks in medical terms (e.g. car- / diovascular -> cardiovascular)
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
        # Collapse multiple spaces
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def load_pdf(self, file_path: Path) -> List[Document]:
        """Extract pages from a PDF file using pypdf."""
        documents = []
        filename = file_path.name
        file_size = file_path.stat().st_size

        try:
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = self.clean_text(page_text)
                if cleaned:
                    doc = Document(
                        text=cleaned,
                        metadata={
                            "filename": filename,
                            "filepath": str(file_path),
                            "page_number": idx + 1,
                            "total_pages": total_pages,
                            "source_type": "pdf",
                            "file_size_bytes": file_size,
                            "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        }
                    )
                    documents.append(doc)
        except Exception as e:
            # Fallback simple text read if pypdf fails or not yet loaded
            with open(file_path, "rb") as f:
                raw_bytes = f.read()
            return self.load_pdf_bytes(filename, raw_bytes)

        return documents

    def load_pdf_bytes(self, filename: str, pdf_bytes: bytes) -> List[Document]:
        """Extract pages from an in-memory PDF byte stream (e.g. from Streamlit upload)."""
        documents = []
        try:
            from pypdf import PdfReader
            stream = BytesIO(pdf_bytes)
            reader = PdfReader(stream)
            total_pages = len(reader.pages)

            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                cleaned = self.clean_text(page_text)
                if cleaned:
                    doc = Document(
                        text=cleaned,
                        metadata={
                            "filename": filename,
                            "page_number": idx + 1,
                            "total_pages": total_pages,
                            "source_type": "pdf",
                            "file_size_bytes": len(pdf_bytes),
                            "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        }
                    )
                    documents.append(doc)
        except Exception as e:
            # Fallback raw text decode if binary extraction fails
            try:
                raw_text = pdf_bytes.decode("utf-8", errors="ignore")
                cleaned = self.clean_text(raw_text)
                if cleaned:
                    documents.append(Document(
                        text=cleaned[:50000],
                        metadata={"filename": filename, "page_number": 1, "source_type": "pdf_raw"}
                    ))
            except Exception:
                pass
        return documents

    def load_text_file(self, file_path: Path) -> List[Document]:
        """Load markdown or plaintext document."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        cleaned = self.clean_text(content)
        if not cleaned:
            return []

        ext = file_path.suffix.lower()
        return [
            Document(
                text=cleaned,
                metadata={
                    "filename": file_path.name,
                    "filepath": str(file_path),
                    "page_number": 1,
                    "total_pages": 1,
                    "source_type": "markdown" if ext == ".md" else "text",
                    "file_size_bytes": file_path.stat().st_size,
                    "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
            )
        ]

    def load_file(self, file_path: Path | str) -> List[Document]:
        """Auto-detect format and load document."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self.load_pdf(path)
        elif suffix in [".txt", ".md", ".json"]:
            return self.load_text_file(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def load_directory(self, directory_path: Path | str) -> List[Document]:
        """Recursively load all supported medical textbooks from a directory."""
        path = Path(directory_path)
        if not path.exists():
            return []

        all_docs = []
        for root, _, files in os.walk(path):
            for file in files:
                p = Path(root) / file
                if p.suffix.lower() in [".pdf", ".txt", ".md"]:
                    try:
                        all_docs.extend(self.load_file(p))
                    except Exception:
                        continue
        return all_docs
