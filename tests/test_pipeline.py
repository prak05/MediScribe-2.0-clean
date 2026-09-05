"""End-to-end integration test of the modular RAG pipeline."""

import unittest
from core.ingestion.loader import Document
from core.chunking.chunker import DocumentChunker
from core.embedding.embedder import LocalHashEmbedder
from core.indexing.vector_store import VectorIndex
from core.retrieval.retriever import SemanticRetriever
from core.retrieval.reranker import ReRanker
from core.llm.generator import ClinicalGenerator
from core.evaluation.evaluator import RAGEvaluator

class TestRAGPipeline(unittest.TestCase):
    def setUp(self):
        self.embedder = LocalHashEmbedder(dimension=128)
        self.index = VectorIndex()
        self.index.clear()

        # Ingest test clinical document
        doc = Document(
            text="First-line therapy for severe sepsis includes broad-spectrum intravenous antimicrobials and fluid resuscitation with 30 mL/kg crystalloids within the first 3 hours.",
            metadata={"filename": "sepsis_guidelines.md", "page_number": 5}
        )
        chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
        chunks = chunker.split_document(doc)
        self.index.add_chunks(chunks, embedder=self.embedder)

        self.retriever = SemanticRetriever(vector_index=self.index, embedder=self.embedder)
        self.reranker = ReRanker(top_k=2, threshold=0.1)
        self.generator = ClinicalGenerator()
        self.evaluator = RAGEvaluator()

    def test_full_pipeline_flow(self):
        query = "What is the fluid resuscitation volume in sepsis?"
        # 1. Retrieve
        raw = self.retriever.retrieve(query, top_k=3)
        self.assertGreater(len(raw), 0)

        # 2. Rerank
        ranked = self.reranker.rerank(query, raw, top_k=2)
        self.assertGreater(len(ranked), 0)
        self.assertEqual(ranked[0].source, "sepsis_guidelines.md")

        # 3. Generate
        res = self.generator.generate(query, ranked)
        self.assertIsNotNone(res.answer)
        self.assertGreater(len(res.citations), 0)

        # 4. Evaluate
        ev = self.evaluator.evaluate_heuristic(query, res.answer, ranked)
        self.assertGreater(ev.overall_score, 0.0)

if __name__ == "__main__":
    unittest.main()
