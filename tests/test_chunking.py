"""Unit tests for sentence and semantic chunking."""

import unittest
from core.ingestion.loader import Document
from core.chunking.chunker import DocumentChunker, ChunkingStrategy

class TestChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = DocumentChunker(
            strategy=ChunkingStrategy.SENTENCE,
            chunk_size=200,
            chunk_overlap=40
        )

    def test_sentence_chunking(self):
        doc = Document(
            text="First sentence in cardiology. Second sentence discusses ECG findings. Third sentence covers troponin levels.",
            metadata={"filename": "heart.md", "page_number": 1}
        )
        chunks = self.chunker.split_document(doc)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].source, "heart.md")
        self.assertEqual(chunks[0].page, 1)

if __name__ == "__main__":
    unittest.main()
