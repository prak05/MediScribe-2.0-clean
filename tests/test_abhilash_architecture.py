"""Comprehensive test suite for Abhilash Sir's 10 Commandments RAG Architecture:
- Fundamentals Layer (transformers, models, user_system_prompts)
- Ingestion Layer (load_data, chunking_embedding, store_vector_db)
- Retrieval Layer (retrieve_chunks, results_reranking, evals_framework)
- Software Application Layer (python_prog, code_gen_ai, fast_api)
"""

import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from fundamentals.models import ModelRegistry
from fundamentals.transformers import TransformerTokenizer
from fundamentals.user_system_prompts import MedicalPrompts
from ingestion.load_data import DataLoader, IngestedDocument
from ingestion.chunking_embedding import ChunkerEmbedder, ChunkedEmbedding
from ingestion.store_vector_db import VectorDBStore
from retrieval.retrieve_chunks import ChunkRetriever, RetrievedChunk
from retrieval.results_reranking import MedicalReranker
from retrieval.evals_framework import EvalsFramework, HeuristicEvaluator, RAGTriadScores
from software_application.code_gen_ai import ClinicalCodeGenAI
from software_application.fast_api import app

class TestFundamentalsLayer(unittest.TestCase):
    """Test Commandment 2 (Models), Transformers, and Commandment 7 (Prompts)."""

    def test_transformer_tokenizer(self):
        tok = TransformerTokenizer(avg_chars_per_token=4.0)
        text = "Hypertension guideline treatment protocol."
        est = tok.estimate_tokens(text)
        self.assertGreater(est, 0)

        # Cosine similarity
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        self.assertAlmostEqual(tok.cosine_similarity(v1, v2), 1.0)
        self.assertAlmostEqual(tok.cosine_similarity(v1, v3), 0.0)

    def test_model_registry(self):
        llm = ModelRegistry.get_default_llm()
        self.assertIn("gemini", llm.lower())
        embedder = ModelRegistry.get_default_embedder()
        self.assertIn("embedding", embedder.lower())

    def test_medical_prompts_evidence_formatting(self):
        prompt = MedicalPrompts.format_user_prompt(
            query="What is the first-line therapy for Stage 1 hypertension?",
            context_blocks=["[Source 1, Page 12] Thiazides and ACE inhibitors are first-line."]
        )
        self.assertIn("EVIDENCE BLOCKS", prompt)
        self.assertIn("Stage 1 hypertension", prompt)
        self.assertIn(MedicalPrompts.DISCLAIMER, prompt)

class TestIngestionLayer(unittest.TestCase):
    """Test Commandment 1 (Data), Commandment 3 (Chunking), Commandment 4 (Embedding), Commandment 5 (Vector DB)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "clinical_doc.md"
        self.test_file.write_text(
            "# Clinical Guideline\n\n"
            "Patients presenting with acute coronary syndrome require immediate aspirin 325 mg chewed.\n"
            "High-intensity statin therapy (Atorvastatin 80 mg) should be initiated as soon as possible.\n"
            "Dual antiplatelet therapy reduces stent thrombosis risk.",
            encoding="utf-8"
        )
        self.store_dir = Path(self.temp_dir.name) / "vector_db"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_data_loader_and_sanitization(self):
        loader = DataLoader()
        docs = loader.load(self.test_file)
        self.assertEqual(len(docs), 1)
        self.assertIn("acute coronary syndrome", docs[0].text)
        self.assertEqual(docs[0].metadata["source_type"], "markdown")

    def test_chunking_and_embedding(self):
        chunker = ChunkerEmbedder(chunk_size=150, chunk_overlap=30, offline=True)
        loader = DataLoader()
        docs = loader.load(self.test_file)
        chunks = chunker.process_documents(docs)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(len(chunks[0].embedding), chunker.dimension)

    def test_vector_db_store_and_persistence(self):
        store = VectorDBStore(storage_dir=self.store_dir)
        vec = [0.1] * 3072
        norm = sum(x * x for x in vec) ** 0.5
        norm_vec = [x / norm for x in vec]

        chunk = ChunkedEmbedding(
            chunk_id="test-c1",
            text="Aspirin is indicated for acute coronary syndrome.",
            embedding=norm_vec,
            metadata={"filename": "acs.md", "page_number": 1}
        )
        store.add_chunks([chunk])
        self.assertEqual(len(store), 1)

        # Persistence test
        self.assertTrue(store.save())
        store2 = VectorDBStore(storage_dir=self.store_dir)
        self.assertEqual(len(store2), 1)

        # Search test
        res = store2.search(norm_vec, top_k=1)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][0].chunk_id, "test-c1")
        self.assertGreater(res[0][1], 0.99)

class TestRetrievalLayer(unittest.TestCase):
    """Test Commandment 6 (Retrieval), Commandment 8 (Re-ranking), Commandment 10 (DeepEval RAG Triad)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = VectorDBStore(storage_dir=Path(self.temp_dir.name) / "db")
        embedder = ChunkerEmbedder(offline=True)
        self.retriever = ChunkRetriever(vector_store=self.store, embedder=embedder)
        self.reranker = MedicalReranker()
        self.evaluator = EvalsFramework(default_use_llm_judge=False)

        # Seed knowledge
        doc = IngestedDocument(
            text="Metformin 500 mg twice daily is the initial pharmacotherapy for Type 2 Diabetes mellitus. Common adverse effects include gastrointestinal distress and rare lactic acidosis.",
            metadata={"filename": "diabetes_guidelines.md", "page_number": 42}
        )
        chunks = embedder.process_documents([doc])
        self.store.add_chunks(chunks)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dense_retrieval(self):
        chunks = self.retriever.retrieve("What is the initial medication for Type 2 Diabetes?", top_k=2)
        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0].source, "diabetes_guidelines.md")

    def test_medical_reranker(self):
        chunks = self.retriever.retrieve("Metformin adverse effects dosage", top_k=3)
        reranked = self.reranker.rerank("Metformin adverse effects dosage", chunks, top_k=2)
        self.assertGreater(len(reranked), 0)
        self.assertGreaterEqual(reranked[0].medical_boost, 0.0)

    def test_rag_triad_evaluator(self):
        query = "What is the initial medication for Type 2 Diabetes?"
        context = ["Metformin 500 mg is the initial pharmacotherapy for Type 2 Diabetes."]
        answer = "Metformin is the initial pharmacotherapy for Type 2 Diabetes."

        scores = self.evaluator.evaluate_rag(query, context, answer, use_llm_judge=False)
        self.assertIsInstance(scores, RAGTriadScores)
        self.assertGreaterEqual(scores.faithfulness, 0.5)
        self.assertGreaterEqual(scores.answer_relevance, 0.5)
        self.assertTrue(scores.passed)

class TestSoftwareApplicationLayer(unittest.TestCase):
    """Test Commandment 9 (CLI, CodeGen AI, FastAPI)."""

    def setUp(self):
        self.client = TestClient(app)
        self.codegen = ClinicalCodeGenAI()

    def test_codegen_fhir_generation(self):
        res = self.codegen.generate_fhir_resource(
            resource_type="Condition",
            patient_id="pat-42",
            clinical_data={"condition_name": "Essential Hypertension", "snomed_code": "38341003"}
        )
        self.assertEqual(res["resourceType"], "Condition")
        self.assertEqual(res["subject"]["reference"], "Patient/pat-42")

    def test_codegen_icd10_mapping(self):
        mapped = self.codegen.generate_icd10_mapping("Stage 2 hypertension")
        self.assertTrue(mapped["matched"])
        self.assertEqual(mapped["icd10_code"], "I10")

    def test_fastapi_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("vector_store", data)

    def test_fastapi_models_endpoint(self):
        resp = self.client.get("/models")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("gemini-3.6-flash", data["models"])

if __name__ == "__main__":
    unittest.main()
