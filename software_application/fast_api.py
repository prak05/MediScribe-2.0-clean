"""FAST API (Microservice REST API)
Software Application Layer (Commandment 9: Software Application Layer).
"""

from typing import Any, Dict, List, Optional
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import settings
from fundamentals.models import ModelRegistry
from fundamentals.user_system_prompts import MedicalPrompts
from ingestion.load_data import DataLoader
from ingestion.chunking_embedding import ChunkerEmbedder
from ingestion.store_vector_db import VectorDBStore
from retrieval.retrieve_chunks import ChunkRetriever
from retrieval.results_reranking import MedicalReranker
from retrieval.evals_framework import EvalsFramework
from software_application.code_gen_ai import ClinicalCodeGenAI

app = FastAPI(
    title="MediScribe Clinical RAG API",
    description="Decentralized, Evidence-Grounded Medical RAG Microservice following Abhilash Sir's Architecture.",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared singletons
_store = VectorDBStore()
_retriever = ChunkRetriever(vector_store=_store)
_reranker = MedicalReranker()
_evaluator = EvalsFramework()
_codegen = ClinicalCodeGenAI()

# --- Request / Response Models ---
class QueryRequest(BaseModel):
    query: str = Field(..., example="What is the first-line therapy for Stage 2 hypertension?")
    top_k: int = Field(default=4, ge=1, le=20)
    rerank: bool = Field(default=True)
    model_name: Optional[str] = Field(default=None)

class RerankRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)

class EvalRequest(BaseModel):
    query: str
    top_k: int = Field(default=3)
    use_llm_judge: bool = Field(default=False)

class IngestPathRequest(BaseModel):
    file_path: str = Field(..., example="/home/prak05/MediScribe/materials/sample_data/clinical_guidelines_sample.md")

class FHIRRequest(BaseModel):
    resource_type: str = Field(default="Condition", example="Condition")
    patient_id: str = Field(default="pat-101")
    clinical_data: Dict[str, Any] = Field(default_factory=dict)

# --- Endpoints ---
@app.get("/health")
def health():
    """System health check, active models, and index stats."""
    return {
        "status": "healthy",
        "service": "MediScribe Clinical RAG",
        "active_llm": ModelRegistry.get_default_llm(),
        "active_embedder": ModelRegistry.get_default_embedder(),
        "vector_store": _store.get_stats()
    }

@app.get("/models")
def list_models():
    """List supported LLM and embedding models."""
    return {
        "models": {k: v.__dict__ for k, v in ModelRegistry.AVAILABLE_MODELS.items()}
    }

@app.get("/stats")
def get_stats():
    """Detailed vector index and document statistics."""
    return _store.get_stats()

@app.post("/query")
def execute_query(req: QueryRequest):
    """Run dense semantic retrieval, re-ranking, and grounded LLM answer synthesis."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve initial candidate chunks
    initial_chunks = _retriever.retrieve(
        req.query,
        top_k=req.top_k * 2 if req.rerank else req.top_k
    )

    if not initial_chunks:
        return {
            "answer": "The provided medical textbooks do not contain sufficient evidence to answer this question.",
            "citations": [],
            "chunks": [],
            "model_used": req.model_name or ModelRegistry.get_default_llm(),
            "disclaimer": MedicalPrompts.DISCLAIMER
        }

    # 2. Re-rank if requested
    if req.rerank:
        reranked_results = _reranker.rerank(req.query, initial_chunks, top_k=req.top_k)
        active_chunks = [r.chunk for r in reranked_results]
    else:
        active_chunks = initial_chunks[:req.top_k]

    # 3. Synthesize grounded answer
    synthesis = _retriever.synthesize_answer(req.query, active_chunks, model_name=req.model_name)
    return synthesis

@app.post("/rerank")
def inspect_reranking(req: RerankRequest):
    """Retrieve chunks and show detailed before/after re-ranking score breakdown."""
    chunks = _retriever.retrieve(req.query, top_k=req.top_k * 2)
    reranked = _reranker.rerank(req.query, chunks, top_k=req.top_k)
    return {
        "query": req.query,
        "reranked_chunks": [
            {
                "chunk_id": r.chunk_id,
                "source": r.source,
                "page": r.page,
                "original_vector_score": round(r.original_score, 4),
                "lexical_score": round(r.lexical_score, 4),
                "medical_boost": round(r.medical_boost, 4),
                "final_reranked_score": round(r.reranked_score, 4),
                "rank_delta": r.rank_delta,
                "text_snippet": r.text[:200] + "..."
            }
            for r in reranked
        ]
    }

@app.post("/evaluate")
def evaluate_rag(req: EvalRequest):
    """Evaluate pipeline quality using DeepEval RAG Triad (LLM as Judge or Heuristic)."""
    chunks = _retriever.retrieve(req.query, top_k=req.top_k)
    synthesis = _retriever.synthesize_answer(req.query, chunks)

    context_texts = [c.text for c in chunks]
    triad = _evaluator.evaluate_rag(
        query=req.query,
        context_chunks=context_texts,
        answer=synthesis["answer"],
        use_llm_judge=req.use_llm_judge
    )

    return {
        "query": req.query,
        "answer": synthesis["answer"],
        "triad_scores": {
            "faithfulness": triad.faithfulness,
            "context_relevance": triad.context_relevance,
            "answer_relevance": triad.answer_relevance,
            "overall_score": triad.overall_score,
            "evaluation_method": triad.evaluation_method,
            "passed": triad.passed,
            "details": triad.details
        }
    }

@app.post("/ingest/path")
def ingest_from_path(req: IngestPathRequest):
    """Ingest .md or .pdf documents from local filesystem into vector database."""
    loader = DataLoader()
    embedder = ChunkerEmbedder()

    docs = loader.load(req.file_path)
    if not docs:
        raise HTTPException(status_code=404, detail=f"No valid documents found at '{req.file_path}'.")

    chunks = embedder.process_documents(docs)
    added = _store.add_chunks(chunks)
    _store.save()

    return {
        "message": f"Successfully ingested {added} chunks from {len(docs)} documents.",
        "documents_loaded": len(docs),
        "chunks_indexed": added,
        "stats": _store.get_stats()
    }

@app.post("/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)):
    """Upload and ingest a medical textbook .md or .pdf file."""
    content = await file.read()
    loader = DataLoader()
    embedder = ChunkerEmbedder()

    docs = loader.load_bytes_data(file.filename, content)
    if not docs:
        raise HTTPException(status_code=400, detail="Could not extract text from uploaded file.")

    chunks = embedder.process_documents(docs)
    added = _store.add_chunks(chunks)
    _store.save()

    return {
        "filename": file.filename,
        "documents_extracted": len(docs),
        "chunks_indexed": added,
        "stats": _store.get_stats()
    }

@app.post("/codegen/fhir")
def generate_fhir(req: FHIRRequest):
    """Generate HL7 FHIR R4 clinical resource from data."""
    return _codegen.generate_fhir_resource(
        resource_type=req.resource_type,
        patient_id=req.patient_id,
        clinical_data=req.clinical_data
    )

@app.get("/codegen/icd10")
def get_icd10(condition: str = Query(..., description="Condition name to map")):
    """Map condition text to ICD-10-CM code."""
    return _codegen.generate_icd10_mapping(condition)
