"""Unit tests for vector storage and cosine similarity."""

import unittest
from core.chunking.chunker import TextChunk
from core.embedding.embedder import LocalHashEmbedder
from core.indexing.vector_store import VectorIndex

class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.embedder = LocalHashEmbedder(dimension=64)
        self.index = VectorIndex()
        self.index.clear()

    def test_indexing_and_query(self):
        chunks = [
            TextChunk(text="Diabetic ketoacidosis requires intravenous normal saline and insulin.", metadata={"filename": "dka.md", "page_number": 1}),
            TextChunk(text="Myocardial infarction presents with ST-segment elevation and chest pain.", metadata={"filename": "stemi.md", "page_number": 2}),
        ]
        indexed = self.index.add_chunks(chunks, embedder=self.embedder)
        self.assertEqual(indexed, 2)
        self.assertEqual(len(self.index), 2)

        # Query
        q_vec = self.embedder.embed_text("ketoacidosis insulin")
        matches = self.index.query(q_vec, top_k=1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0].source, "dka.md")
        self.assertGreater(matches[0][1], 0.0)

if __name__ == "__main__":
    unittest.main()
