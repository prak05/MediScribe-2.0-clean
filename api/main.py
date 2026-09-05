"""FastAPI Microservice for MediScribe Decentralized RAG Architecture.
Part of the Software Application Layer (FastAPI, Python Prog, Code Gen AI, UI).
"""

from typing import Any, Dict, List, Optional
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import settings
from core.ingestion.loader import DocumentLoader
from core.chunking.chunker import ChunkingStrategy, DocumentChunker
from core.embedding.embedder import get_embedder
from core.indexing.vector_store import get_vector_store
from core.retrieval.retriever import SemanticRetriever
from core.retrieval.reranker import ReRanker
from core.pubmed.pubmed_client import PubMedClient
from core.llm.generator import ClinicalGenerator
from core.evaluation.evaluator import RAGEvaluator

app = FastAPI(
    title="MediScribe Clinical AI API",
    description="Decentralized modular REST API for Medical Textbook RAG and Literature Search",
    version="1.0.0"
)

# Enable CORS for local dev and web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
loader = DocumentLoader()
chunker = DocumentChunker(
    strategy=ChunkingStrategy.SENTENCE,
    chunk_size=settings.chunking.chunk_size,
    chunk_overlap=settings.chunking.chunk_overlap
)
vector_store = get_vector_store()
retriever = SemanticRetriever(vector_index=vector_store)
reranker = ReRanker()
generator = ClinicalGenerator()
pubmed_client = PubMedClient()
evaluator = RAGEvaluator()

# Request/Response Schemas
class QueryRequest(BaseModel):
    query: str = Field(..., example="What are the main indications for insulin therapy in diabetes?")
    top_k: Optional[int] = Field(5, description="Number of candidate chunks to retrieve")
    rerank: Optional[bool] = Field(True, description="Enable relevance re-ranking")
    evaluate: Optional[bool] = Field(False, description="Run real-time DeepEval evaluation")

class ChunkSource(BaseModel):
    chunk_id: str
    source: str
    page: int
    score: float
    text_snippet: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float
    latency_ms: float
    model_name: str
    sources: List[ChunkSource]
    citations: List[str]
    evaluation: Optional[Dict[str, Any]] = None

class IngestTextRequest(BaseModel):
    title: str = Field(..., example="Clinical Guidelines for Sepsis")
    content: str
    source_type: Optional[str] = "text"

@app.get("/api/v1/health")
def health_check():
    """System health check and vector store statistics."""
    stats = vector_store.get_stats()
    return {
        "status": "healthy",
        "vector_store": stats,
        "api_key_configured": settings.is_api_key_valid(),
        "model": settings.model.default_model,
        "architecture": "3-Tier Modular Decentralized RAG"
    }

@app.post("/api/v1/query", response_model=QueryResponse)
def execute_query(req: QueryRequest):
    """Execute grounded clinical query with semantic search, re-ranking, and citation mapping."""
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Semantic Retrieval
    raw_chunks = retriever.retrieve(query, top_k=req.top_k or 5)

    # 2. Re-ranking
    if req.rerank:
        active_chunks = reranker.rerank(query, raw_chunks, top_k=settings.retrieval.rerank_top_k)
    else:
        active_chunks = raw_chunks[:settings.retrieval.rerank_top_k]

    # 3. Generation
    rag_res = generator.generate(query, active_chunks)

    # 4. Optional Evaluation
    eval_dict = None
    if req.evaluate and active_chunks:
        eval_res = evaluator.evaluate_heuristic(query, rag_res.answer, active_chunks)
        eval_dict = {
            "groundedness": eval_res.groundedness_score,
            "context_relevance": eval_res.context_relevance_score,
            "answer_relevance": eval_res.answer_relevance_score,
            "overall_score": eval_res.overall_score,
            "passed": eval_res.passed
        }

    sources = [
        ChunkSource(
            chunk_id=c.chunk_id,
            source=c.source,
            page=c.page,
            score=c.score,
            text_snippet=c.text[:250] + "..." if len(c.text) > 250 else c.text
        )
        for c in active_chunks
    ]

    return QueryResponse(
        query=query,
        answer=rag_res.answer,
        confidence_score=rag_res.confidence_score,
        latency_ms=rag_res.latency_ms,
        model_name=rag_res.model_name,
        sources=sources,
        citations=rag_res.citations,
        evaluation=eval_dict
    )

@app.post("/api/v1/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """Upload and index a PDF, Markdown, or Plaintext medical textbook file."""
    content_bytes = await file.read()
    filename = file.filename or "uploaded_document"

    if filename.lower().endswith(".pdf"):
        docs = loader.load_pdf_bytes(filename, content_bytes)
    else:
        text_str = content_bytes.decode("utf-8", errors="ignore")
        cleaned = loader.clean_text(text_str)
        from core.ingestion.loader import Document
        docs = [Document(text=cleaned, metadata={"filename": filename, "page_number": 1})]

    if not docs:
        raise HTTPException(status_code=400, detail="Could not extract text from uploaded document.")

    chunks = chunker.split_documents(docs)
    indexed_count = vector_store.add_chunks(chunks)

    return {
        "success": True,
        "filename": filename,
        "pages_processed": len(docs),
        "chunks_indexed": indexed_count,
        "total_index_chunks": len(vector_store)
    }

@app.post("/api/v1/ingest/text")
def ingest_text(req: IngestTextRequest):
    """Ingest raw clinical text notes directly into the vector database."""
    from core.ingestion.loader import Document
    cleaned = loader.clean_text(req.content)
    if not cleaned:
        raise HTTPException(status_code=400, detail="Text content is empty.")

    doc = Document(text=cleaned, metadata={"filename": req.title, "page_number": 1, "source_type": req.source_type})
    chunks = chunker.split_document(doc)
    indexed_count = vector_store.add_chunks(chunks)

    return {
        "success": True,
        "title": req.title,
        "chunks_indexed": indexed_count,
        "total_index_chunks": len(vector_store)
    }

@app.get("/api/v1/pubmed/search")
def search_pubmed(term: str = Query(..., description="Medical search term"), limit: int = 5):
    """Search live NCBI PubMed literature for validation and latest research."""
    articles = pubmed_client.search(term=term, retmax=limit)
    return {
        "query": term,
        "total_results": len(articles),
        "articles": [
            {
                "pmid": a.pmid,
                "title": a.title,
                "journal": a.journal,
                "pubdate": a.pubdate,
                "authors": a.authors,
                "url": a.url
            }
            for a in articles
        ]
    }

@app.post("/api/v1/index/reset")
def reset_index():
    """Clear all indexed documents and vectors."""
    vector_store.clear()
    return {"success": True, "message": "Vector index cleared successfully."}

@app.get("/api/v1/commandments")
def get_commandments():
    """Architectural decision matrix mapping to Abhilash Sir's 10 Commandments of RAG."""
    return {
        "D1_Choice_of_Data": {"format": "PDF / MD / Plaintext / PubMed", "domain": settings.data.default_medical_domain},
        "D2_Choice_of_LLM": {"default": settings.model.default_model, "pro": settings.model.pro_model},
        "D3_Choice_of_Chunking": {"strategy": settings.chunking.strategy, "size": settings.chunking.chunk_size, "overlap": settings.chunking.chunk_overlap},
        "D4_Choice_of_Embedding": {"model": settings.embedding.model_name, "dim": settings.embedding.dimension},
        "D5_Choice_of_Vector_DB": {"type": "Local Persistent Vector Index with Cosine Metric", "path": str(settings.vector_db.storage_dir)},
        "D6_Choice_of_Framework": {"framework": "LlamaIndex + Modular Python Microservice"},
        "D7_Choice_of_Framing_Prompts": {"anti_hallucination": True, "system_prompt_length": len(settings.prompt.system_prompt)},
        "D8_Choice_of_Retrieval_Interface": {"top_k": settings.retrieval.similarity_top_k, "reranker": "Dense + Lexical + Keyword Boost"},
        "D9_Choice_of_Evaluation": {"framework": "DeepEval Groundedness + Faithfulness + Relevance", "target": settings.evaluation.target_groundedness_score},
        "D10_Choice_of_Performance_Testing": {"latency_budget_ms": settings.performance.max_latency_budget_ms, "qps_target": settings.performance.target_throughput_qps}
    }
