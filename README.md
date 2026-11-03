# 🩺 MediScribe: Decentralized Evidence-Based Medical AI Platform

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29+-FF4B4B.svg)](https://streamlit.io/)
[![Gemini](https://img.shields.io/badge/Google-Gemini_1.5_Flash-8E75C2.svg)](https://ai.google.dev/)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-Core-black.svg)](https://www.llamaindex.ai/)

Consolidated medical artificial intelligence ecosystem uniting **MedBuddy** (PDF Textbook RAG Engine) and **MediScribe-AI** (Clinical Practice Management Suite).

Engineered following **Abhilash Sir's 3-Tier Layered Architecture** and **The 10 Commandments of RAG** for the **September 12, 2026 AI Evolve Meetup at RIET Vidhya**.

---

## ✨ Features

- **Decentralized Modular Pipeline**: Strict separation of concerns across ingestion, chunking, embedding, indexing, retrieval, re-ranking, and generation.
- **Evidence-Based Grounded QA**: Context-constrained synthesis citing exact source files and page numbers (`[Source 1, Page X]`).
- **Anti-Hallucination Guardrails**: Strictly refuses out-of-context queries with clinical disclaimers.
- **PubMed Live Literature Search**: Direct integration with NCBI Entrez E-Utilities for real-time peer-reviewed research lookup.
- **DeepEval RAG Triad**: Built-in quantitative scoring for Groundedness (target 84%), Context Relevance (80%), and Answer Faithfulness.
- **Performance Benchmarking**: Multithreaded test suite reporting P50/P95/P99 latency and throughput (QPS).
- **Dual Interfaces**:
  1. **Streamlit Interactive Console (`app.py`)**: For live 55-minute workshop demos.
  2. **FastAPI Microservice (`api/main.py`)**: REST endpoints for external integrations.
  3. **Fullstack Clinical Web Suite (`web/`)**: Dual-mode React + Vite + Express + SQLite application (Journal Mode & Patient Mode).

---

## 🚀 Quick Start

### 1. Python Environment Setup

```bash
cd /home/prak05/MediScribe

# Activate the dedicated virtual environment
source .venv/bin/activate

# Install requirements (if not already installed)
pip install -r requirements.txt
```

### 2. Configure API Key

API keys are auto-detected from `.env`, but can also be exported:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 3. Launch the Streamlit Demo App

```bash
streamlit run app.py
```
*Access at: `http://localhost:8501`*

### 4. Launch the FastAPI Microservice

```bash
uvicorn api.main:app --reload --port 8000
```
*Interactive Swagger docs available at: `http://localhost:8000/docs`*

### 5. Run Performance Benchmarks

```bash
python3 -m core.benchmarks.load_test --queries 6 --concurrency 2
```

---

## 📁 Repository Structure

- `core/`: Decoupled RAG pipeline modules.
  - `ingestion/`: Document loaders for PDF, Markdown, and plaintext.
  - `chunking/`: Sentence-boundary and semantic chunkers.
  - `embedding/`: Vector embedder with Gemini and offline fallback.
  - `indexing/`: Persistent vector store index.
  - `retrieval/`: Dense nearest-neighbor retrieval and re-ranking.
  - `pubmed/`: NCBI PubMed literature search.
  - `llm/`: Prompts and grounded response generator.
  - `evaluation/`: DeepEval metrics (Groundedness, Relevance, Faithfulness).
  - `benchmarks/`: Latency and throughput testing harness.
- `api/`: FastAPI REST endpoints.
- `app.py`: Streamlit console.
- `web/`: React 19 + TypeScript + Express + SQLite clinical suite.
- `materials/`: Consolidated library of 66+ research papers, reports, slides, and sample data.
- `docs/`: 10 Commandments documentation and workshop guide.
- `tests/`: Automated test suite.

---

## 🏛️ Alignment with Abhilash Sir's Vision

See [`docs/10_COMMANDMENTS.md`](docs/10_COMMANDMENTS.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md) for full architectural mapping and decision records.

## Portfolio brief

An evidence-grounded medical knowledge and clinical workflow platform for document retrieval, cited answers, and review-oriented tooling.

### Visual system

Apple-inspired clinical calm: generous whitespace, neutral surfaces, precise typography, and restrained health-system accents.

### Architecture

The platform separates ingestion, chunking, retrieval, generation, API services, and interactive interfaces. Local mode is the default; provider credentials are supplied only through environment configuration.

### Run and output

Follow the repository setup instructions for the Python service and web interfaces. Outputs should retain source references and clinical disclaimers.

