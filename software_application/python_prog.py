"""PYTHON PROG (CLI / Script Execution)
Software Application Layer (Commandment 9: Software Application Layer).
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fundamentals.models import ModelRegistry
from fundamentals.user_system_prompts import MedicalPrompts
from ingestion.load_data import DataLoader
from ingestion.chunking_embedding import ChunkerEmbedder
from ingestion.store_vector_db import VectorDBStore
from retrieval.retrieve_chunks import ChunkRetriever
from retrieval.results_reranking import MedicalReranker
from retrieval.evals_framework import EvalsFramework

def run_ingest(source_path: str):
    """Ingest medical textbooks or clinical markdown files into the persistent vector database."""
    print(f"\n=======================================================")
    print(f"📖 MediScribe Ingestion: {source_path}")
    print(f"=======================================================")
    loader = DataLoader()
    embedder = ChunkerEmbedder()
    store = VectorDBStore()

    docs = loader.load(source_path)
    if not docs:
        print(f"❌ No valid medical documents found at '{source_path}'.")
        return

    print(f"Loaded {len(docs)} document sections.")
    chunks = embedder.process_documents(docs)
    print(f"Generated {len(chunks)} chunks with dense vector embeddings.")

    added = store.add_chunks(chunks)
    store.save()
    print(f"✅ Successfully stored and indexed {added} chunks in vector database.")
    print(f"📊 Vector Store Stats: {store.get_stats()}\n")

def run_query(query_text: str, top_k: int = 4, rerank: bool = True):
    """Execute evidence-grounded clinical query against indexed medical literature."""
    print(f"\n=======================================================")
    print(f"🩺 MediScribe Clinical Query")
    print(f"Query: '{query_text}'")
    print(f"=======================================================")

    store = VectorDBStore()
    retriever = ChunkRetriever(vector_store=store, top_k=top_k)
    reranker = MedicalReranker()

    chunks = retriever.retrieve(query_text, top_k=top_k * 2 if rerank else top_k)
    if not chunks:
        print("⚠️ No relevant medical chunks retrieved from index.")
        return

    print(f"Retrieved {len(chunks)} initial chunks via dense vector search.")

    if rerank:
        reranked = reranker.rerank(query_text, chunks, top_k=top_k)
        print(f"Re-ranked top {len(reranked)} chunks with medical keyword boosting:")
        for idx, r in enumerate(reranked, 1):
            delta = f"(+{r.rank_delta})" if r.rank_delta > 0 else f"({r.rank_delta})"
            print(f"  [{idx}] Score: {r.reranked_score:.3f} {delta} | Source: {r.source} (p.{r.page})")
        final_chunks = [r.chunk for r in reranked]
    else:
        final_chunks = chunks[:top_k]

    print("\nSynthesizing grounded response...")
    result = retriever.synthesize_answer(query_text, final_chunks)

    print("\n------------------- CLINICAL ANSWER -------------------")
    print(result["answer"])
    print("-------------------------------------------------------")
    print("CITATIONS:")
    for c in result["citations"]:
        print(f"  • {c}")
    print(f"Model: {result['model_used']}")
    print("-------------------------------------------------------\n")

def run_eval(query_text: str, top_k: int = 3, use_llm_judge: bool = False):
    """Run DeepEval RAG Triad evaluation on a query."""
    print(f"\n=======================================================")
    print(f"⚖️ DeepEval RAG Triad Evaluation")
    print(f"Query: '{query_text}' | Method: {'LLM Judge' if use_llm_judge else 'Heuristic Non-Judge'}")
    print(f"=======================================================")

    store = VectorDBStore()
    retriever = ChunkRetriever(vector_store=store, top_k=top_k)
    evaluator = EvalsFramework()

    chunks = retriever.retrieve(query_text, top_k=top_k)
    result = retriever.synthesize_answer(query_text, chunks)

    context_texts = [c.text for c in chunks]
    triad = evaluator.evaluate_rag(
        query=query_text,
        context_chunks=context_texts,
        answer=result["answer"],
        use_llm_judge=use_llm_judge
    )

    print(f"\nFaithfulness:        {triad.faithfulness:.2f}")
    print(f"Context Relevance:   {triad.context_relevance:.2f}")
    print(f"Answer Relevance:    {triad.answer_relevance:.2f}")
    print(f"Overall Triad Score: {triad.overall_score:.2f} [{'PASS' if triad.passed else 'FAIL'}]")
    if triad.details:
        print(f"Details: {json.dumps(triad.details, indent=2)}")
    print("=======================================================\n")

def run_stats():
    """Print vector store and model registry status."""
    store = VectorDBStore()
    stats = store.get_stats()
    print("\n=======================================================")
    print("📊 MediScribe Platform Status")
    print("=======================================================")
    print(f"Active LLM:             {ModelRegistry.get_default_llm()}")
    print(f"Active Embedder:        {ModelRegistry.get_default_embedder()}")
    print(f"Indexed Chunks:         {stats['total_chunks']}")
    print(f"Indexed Documents:      {stats['total_documents']}")
    print(f"Vector Store Directory: {stats['storage_dir']}")
    print(f"Persistent On Disk:     {stats['is_persisted']}")
    print("=======================================================\n")

def main():
    parser = argparse.ArgumentParser(description="MediScribe Python Program (Commandment 9 Application Runner)")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Ingest
    ingest_p = subparsers.add_parser("ingest", help="Ingest .md, .pdf, or directory into vector database")
    ingest_p.add_argument("source", type=str, help="File or folder path")

    # Query
    query_p = subparsers.add_parser("query", help="Run clinical query with RAG synthesis")
    query_p.add_argument("query", type=str, help="Clinical question")
    query_p.add_argument("--top-k", type=int, default=4, help="Number of chunks")
    query_p.add_argument("--no-rerank", action="store_true", help="Disable re-ranking")

    # Eval
    eval_p = subparsers.add_parser("eval", help="Run DeepEval RAG Triad on a clinical query")
    eval_p.add_argument("query", type=str, help="Clinical question to evaluate")
    eval_p.add_argument("--llm-judge", action="store_true", help="Use Gemini LLM-as-a-judge")

    # Stats
    subparsers.add_parser("stats", help="Inspect vector database and models")

    args = parser.parse_args()

    if args.command == "ingest":
        run_ingest(args.source)
    elif args.command == "query":
        run_query(args.query, top_k=args.top_k, rerank=not args.no_rerank)
    elif args.command == "eval":
        run_eval(args.query, use_llm_judge=args.llm_judge)
    elif args.command == "stats":
        run_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
