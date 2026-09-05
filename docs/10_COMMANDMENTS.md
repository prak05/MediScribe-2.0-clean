# Abhilash Sir's 10 Commandments of RAG: Architectural Decisions & Implementation

> *"Architecture is nothing but a set of decisions."*
> — **Abhilash Gopalakrishnan (AI Evolve)**

This document details the architectural decisions and concrete implementations underpinning the **MediScribe** platform, prepared for the **September 12, 2026 AI Evolve Meetup at RIET Vidhya**.

---

## The Decision Matrix

```
Begin: Start with the end in mind -> What is the resulting business value?
Resulting Business Value: Zero-hallucination, evidence-backed clinical decision assistance grounded in peer-reviewed medical textbooks and NCBI PubMed literature.
```

### D1: Choice of Data
- **Decisions**: Timeliness, Credibility, Availability, Format (`<text>`, PDF, Markdown).
- **Implementation**: `core/ingestion/loader.py`
- **Details**: Ingests textbook PDFs using `pypdf`, supports markdown clinical guidelines and structured text notes. Normalizes unicode characters, repairs hyphenated medical terms, and maintains page and source lineage metadata.

### D2: Choice of LLM & the Model
- **Decisions**: Availability, Dimensions, Online vs. Offline.
- **Implementation**: `core/config.py` & `core/llm/generator.py`
- **Details**: Uses **Google Gemini 1.5 Flash** as primary fast-inference engine (sub-second TTFT) with fallback to **Gemini 2.0 Flash** and **Gemini 1.5 Pro**. Employs deterministic offline summarization if disconnected from the network.

### D3: Choice of Chunking Strategy
- **Decisions**: Sentence Splitter vs. Semantic Splitter.
- **Implementation**: `core/chunking/chunker.py`
- **Details**: Configurable `DocumentChunker` using sentence-boundary aware splitting (`chunk_size = 1024`, `chunk_overlap = 100`) preserving clinical continuity across chunk margins, with optional semantic paragraph grouping.

### D4: Choice of Embedding
- **Decisions**: Model, Dimensionality, Storage & Indexing.
- **Implementation**: `core/embedding/embedder.py`
- **Details**: Uses `models/text-embedding-004` (768 dimensions) via Google GenAI. Includes deterministic cosine-normalized offline hash vectorizer for reliable unit testing and offline development.

### D5: Choice of Vector Database
- **Decisions**: Minimum Pinecone / local persistent vector index.
- **Implementation**: `core/indexing/vector_store.py`
- **Details**: High-performance local persistent vector index (`.vector_index/index_manifest.json`) supporting fast in-memory cosine similarity search, chunk metadata tracking, and disk serialization.

### D6: Choice of Frameworks for LLM Interaction
- **Decisions**: LlamaIndex vs. LangChain.
- **Implementation**: LlamaIndex core integrated with a decentralized Python microservice architecture, decoupling pipeline stages from monolithic framework abstractions.

### D7: Choice of Framing Prompts
- **Decisions**: System Prompt vs. User Prompt design.
- **Implementation**: `core/llm/prompts.py`
- **Details**: Strict medical prompt constraining the model to answer *only* from verified context blocks, requiring bracketed citations `[Source 1, Page X]`, refusing ungrounded queries with a standardized disclaimer, and eliminating hallucinations.

### D8: Choice of Retrieval Interface
- **Decisions**: Dense Vector Search + Cross HF / Query Re-ranking + PubMed API.
- **Implementation**: `core/retrieval/retriever.py`, `core/retrieval/reranker.py`, `core/pubmed/pubmed_client.py`
- **Details**: Combines dense vector retrieval (top-5 candidates) with multi-signal re-ranking (dense similarity + lexical Jaccard overlap + medical keyword boost) and similarity thresholding (pruning noise below 0.55). Live fallback to NCBI PubMed literature.

### D9: Choice of Evaluation Strategy & Library
- **Decisions**: DeepEval (LLM as Judge vs. Heuristic Metrics, Standard Metrics).
- **Implementation**: `core/evaluation/evaluator.py`
- **Details**: Evaluates the RAG Triad:
  1. **Groundedness / Faithfulness**: Target ≥ 84% (aligned with base research paper).
  2. **Context Relevance**: Target ≥ 80%.
  3. **Answer Relevancy**: Target ≥ 85%.

### D10: Choice of Performance Testing Framework & Tools
- **Decisions**: Load Test, Throughput (QPS), Saturation, Latency (P50/P95/P99).
- **Implementation**: `core/benchmarks/load_test.py`
- **Details**: Multithreaded benchmarking tool providing latency histograms, throughput (QPS), and failure rate metrics under concurrent workloads.
