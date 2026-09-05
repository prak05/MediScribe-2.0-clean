# MediScribe: System Architecture & Design

## 1. 3-Tier Layered Architecture

The system is organized into three distinct tiers based on Abhilash Sir's design diagram:

```
========================================================================================
TIER 1: SOFTWARE APPLICATION LAYER
========================================================================================
• Interactive Web UI        : Streamlit App (app.py) & React Suite (web/)
• FastAPI REST Service      : api/main.py (Microservices for Ingest, Query, Rerank, Eval)
• Code Gen & Diagnostics    : Automated Benchmarks & Testing Suite (core/benchmarks/)

========================================================================================
TIER 2: INGESTION & RETRIEVAL LAYER
========================================================================================
• Ingestion Pipeline        : Data Loaders (core/ingestion/loader.py) -> PDF, MD, TXT
• Chunking Strategy         : SentenceSplitter & SemanticSplitter (core/chunking/)
• Embedding Engine          : Google GenAI Text Embedding 004 / 001 (core/embedding/)
• Vector Database           : Persistent Vector Index with Cosine Metric (core/indexing/)
• Semantic Retrieval        : Dense Vector Similarity Search (core/retrieval/retriever.py)
• Results Re-ranking        : Dense + Lexical + Keyword Boost (core/retrieval/reranker.py)
• External Verification     : NCBI PubMed E-Utilities Client (core/pubmed/pubmed_client.py)
• Quality & Evals Framework : DeepEval Groundedness & Faithfulness (core/evaluation/)

========================================================================================
TIER 3: FUNDAMENTALS (ARCHITECTURE) LAYER
========================================================================================
• Transformers & Models     : Google Gemini 1.5/2.0 Flash / Pro (core/config.py)
• Framing Prompts           : Clinical System Prompt, Citation Anchoring, Anti-Hallucination
• Guardrails & Fallbacks    : Context-Constrained Refusal Policy & Educational Disclaimers
========================================================================================
```

## 2. Directory Layout

```
MediScribe/
├── app.py                      # Main Streamlit clinical UI orchestrator
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI REST microservice
├── core/
│   ├── config.py               # Centralized configuration & 10 Commandments parameters
│   ├── ingestion/              # Document loaders (PDF, MD, TXT)
│   ├── chunking/               # Sentence-boundary & semantic splitters
│   ├── embedding/              # Vector embedder with Gemini & offline fallback
│   ├── indexing/               # Persistent vector store index
│   ├── retrieval/              # Dense retriever & multi-signal re-ranker
│   ├── pubmed/                 # Live PubMed E-Utilities literature search
│   ├── llm/                    # Prompts & grounded answer generator
│   ├── evaluation/             # DeepEval RAG Triad evaluator
│   └── benchmarks/             # Latency & throughput performance test harness
├── web/                        # React 19 + TypeScript + Express + SQLite platform
├── materials/
│   ├── research/               # Base research paper & PRD documentation
│   ├── reports/                # Project reports, abstracts, and KTU submissions
│   ├── presentations/          # Pitch decks & slide presentations
│   └── sample_data/            # Sample medical textbook chapters
├── docs/
│   ├── 10_COMMANDMENTS.md      # Detailed breakdown of Abhilash Sir's 10 Commandments
│   └── WORKSHOP_GUIDE.md       # 55-minute demo walkthrough guide for Sept 12
└── tests/                      # Automated unit and integration test suite
```
