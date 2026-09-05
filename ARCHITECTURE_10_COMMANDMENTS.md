# MediScribe: Decentralized Clinical RAG Platform
*Embodying Abhilash Sir's "10 Commandments of RAG" Architecture for the AI Evolve Meetup*

## Architectural Transformation Overview

Per your explicit command:
> **"no app.py file is needed use abhilash sir's idea to create the files"**

The monolithic `app.py` has been completely eliminated. The entire platform has been structured directly after **Abhilash Sir's 4-Tier RAG Architecture Diagram** and the **10 Commandments of RAG**:

```
                                  USER QUERY
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
         [SOFTWARE APPLICATION]                [RETRIEVAL LAYER]
         • python_prog.py                      • retrieve_chunks.py
         • code_gen_ai.py                      • results_reranking.py
         • fast_api.py                         • evals_framework.py
         • ui.py                               (DeepEval RAG Triad)
                     │                                 │
                     └────────────────┬────────────────┘
                                      ▼
                             [INGESTION LAYER]
                             • load_data.py (.md / PDF)
                             • chunking_embedding.py
                             • store_vector_db.py (Vector Store)
                                      │
                                      ▼
                            [FUNDAMENTALS LAYER]
                            • transformers.py
                            • models.py (gemini-3.6-flash, gemini-embedding-001)
                            • user_system_prompts.py
```

---

## 1. Directory & Layer Organization

| Layer | Module File | Abhilash Sir's Diagram Box / Commandment | Functionality |
| :--- | :--- | :--- | :--- |
| **Ingestion** | [`ingestion/load_data.py`](file:///home/prak05/MediScribe/ingestion/load_data.py) | `(1) -> DATA .md -> LOAD DATA` (Cmd 1) | Ingests `.md`, `.pdf`, and `.txt` files with line-wrap sanitization, OCR repair, and metadata tracking. |
| **Ingestion** | [`ingestion/chunking_embedding.py`](file:///home/prak05/MediScribe/ingestion/chunking_embedding.py) | `-> CHUNKING & EMBEDDING (LLM)` (Cmd 3 & 4) | Sentence-boundary chunking and 3072-dimension dense vector embeddings with fallback. |
| **Ingestion** | [`ingestion/store_vector_db.py`](file:///home/prak05/MediScribe/ingestion/store_vector_db.py) | `-> STORE IN VECTOR DATABASE (Vector Store)` (Cmd 5) | Persistent local vector index with cosine similarity search and manifest storage. |
| **Retrieval** | [`retrieval/retrieve_chunks.py`](file:///home/prak05/MediScribe/retrieval/retrieve_chunks.py) | `RETRIEVE CHUNKS` (Cmd 6) | Dense semantic retrieval, context block assembly, and evidence-grounded synthesis. |
| **Retrieval** | [`retrieval/results_reranking.py`](file:///home/prak05/MediScribe/retrieval/results_reranking.py) | `RESULTS (RERANKING)` (Cmd 8) | Hybrid scoring: vector similarity + lexical overlap + medical keyword boosting + threshold cutoff. |
| **Retrieval** | [`retrieval/evals_framework.py`](file:///home/prak05/MediScribe/retrieval/evals_framework.py) | `EVALS FRAMEWORK` (Cmd 10) | DeepEval RAG Triad: Faithfulness, Context Relevance, and Answer Relevance (LLM-as-judge & Heuristic). |
| **Fundamentals**| [`fundamentals/transformers.py`](file:///home/prak05/MediScribe/fundamentals/transformers.py) | `Transformers / Tokenizer` | Context window token budget management and cosine similarity calculation. |
| **Fundamentals**| [`fundamentals/models.py`](file:///home/prak05/MediScribe/fundamentals/models.py) | `Choosing Models` (Cmd 2 & 4) | Model registry choosing `gemini-3.6-flash` (LLM) and `gemini-embedding-001` (3072-dim embedder). |
| **Fundamentals**| [`fundamentals/user_system_prompts.py`](file:///home/prak05/MediScribe/fundamentals/user_system_prompts.py) | `USER & SYSTEM PROMPT` (Cmd 7) | Anti-hallucination guardrails, strict bracketed citations, and medical disclaimers. |
| **Software App**| [`software_application/python_prog.py`](file:///home/prak05/MediScribe/software_application/python_prog.py) | `PYTHON PROG` (Cmd 9) | CLI pipeline runner for ingesting, querying, re-ranking, evaluating, and inspecting stats. |
| **Software App**| [`software_application/code_gen_ai.py`](file:///home/prak05/MediScribe/software_application/code_gen_ai.py) | `CODE GEN AI` (Cmd 9) | Clinical generator for HL7 FHIR R4 resources, ICD-10 codings, and synthetic benchmarks. |
| **Software App**| [`software_application/fast_api.py`](file:///home/prak05/MediScribe/software_application/fast_api.py) | `FAST API` (Cmd 9) | REST microservice with `/health`, `/query`, `/rerank`, `/evaluate`, `/ingest`, `/models`. |
| **Software App**| [`software_application/ui.py`](file:///home/prak05/MediScribe/software_application/ui.py) | `UI` (Cmd 9) | Interactive Streamlit workspace with RAG search, re-ranking inspector, and RAG Triad quality visualizer. |

---

## 2. Materials & Deduplication

All 66 unique documents, clinical guidelines, research papers, presentations, and reports from `Desktop/mini projectx/Medbuddy` and `GITHUB/windsurf/MediScribe-AI` have been deduplicated by MD5 hash into:
- [`materials/sample_data/`](file:///home/prak05/MediScribe/materials/sample_data/) (e.g. `clinical_guidelines_sample.md`)
- [`materials/research/`](file:///home/prak05/MediScribe/materials/research/)
- [`materials/presentations/`](file:///home/prak05/MediScribe/materials/presentations/)
- [`materials/reports/`](file:///home/prak05/MediScribe/materials/reports/)
- Cataloged with hashes in [`materials/INDEX.md`](file:///home/prak05/MediScribe/materials/INDEX.md).

---

## 3. Verification & Live Execution Results

### A. Automated Pytest Test Suite
Ran full test suite with 18 unit and integration tests covering all 4 architectural layers:
```bash
/home/prak05/MediScribe/venv/bin/pytest tests/
```
**Result**:
```
tests/test_abhilash_architecture.py .............                        [ 72%]
tests/test_chunking.py .                                                 [ 77%]
tests/test_ingestion.py ..                                               [ 88%]
tests/test_pipeline.py .                                                 [ 94%]
tests/test_vector_store.py .                                             [100%]
======================= 18 passed in 54.19s =======================
```

### B. Live Ingestion via `python_prog.py`
```bash
python -m software_application.python_prog ingest materials/sample_data/clinical_guidelines_sample.md
```
**Result**:
- Loaded 1 document sections.
- Generated 3 chunks with 3072-dimensional dense embeddings (`gemini-embedding-001`).
- Saved persistent vector index to `.vector_index/`.

### C. Live Clinical Query via `python_prog.py`
```bash
python -m software_application.python_prog query "What is the first-line fluid resuscitation protocol for Diabetic Ketoacidosis (DKA)?"
```
**Output**:
```
------------------- CLINICAL ANSWER -------------------
Based on the provided medical text, the first-line fluid resuscitation protocol for Diabetic Ketoacidosis (DKA) is as follows:

* Initial Fluid Choice and Rate: First-line therapy consists of prompt intravenous fluid resuscitation using normal saline (0.9% NaCl) at a rate of 15–20 mL/kg/hour during the first hour [Source 1, clinical_guidelines_sample.md, Page 1].
* Electrolyte Management in IV Fluids: Potassium repletion is vital alongside fluid therapy; if the patient's serum potassium level is between 3.3 and 5.2 mEq/L, administer 20–30 mEq K+ per liter of IV fluid [Source 1, clinical_guidelines_sample.md, Page 1].

⚠️ Educational & Clinical Reference Only: Not a substitute for formal medical diagnosis or physician prescription.
-------------------------------------------------------
CITATIONS:
  • [Source 1: clinical_guidelines_sample.md, Page 1]
  • [Source 2: clinical_guidelines_sample.md, Page 1]
  • [Source 3: clinical_guidelines_sample.md, Page 1]
Model: gemini-3.6-flash
-------------------------------------------------------
```

### D. Anti-Hallucination Guardrail Check
When queried on a topic not present in the indexed literature (*"What is the recommended first-line therapy for Stage 2 hypertension?"*):
```
------------------- CLINICAL ANSWER -------------------
The provided medical textbooks do not contain sufficient evidence to answer this question.

⚠️ Educational & Clinical Reference Only: Not a substitute for formal medical diagnosis or physician prescription.
```
The system strictly adhered to Commandment 7 without fabricating facts.

### E. DeepEval RAG Triad Evaluation
```bash
python -m software_application.python_prog eval "What is the fluid resuscitation protocol for DKA?"
```
**Output**:
```
Faithfulness:        0.62
Context Relevance:   0.75
Answer Relevance:    0.88
Overall Triad Score: 0.75 [PASS]
```

---

## 4. How to Run the Applications

Activate the virtual environment:
```bash
source /home/prak05/MediScribe/venv/bin/activate
cd /home/prak05/MediScribe
```

### 1. Interactive Streamlit Clinical UI
```bash
streamlit run software_application/ui.py
```
Provides:
- 🩺 Clinical Assistant (live grounded queries with citations)
- ⚡ Re-Ranking Inspector (side-by-side diagnostic table)
- ⚖️ DeepEval RAG Triad (interactive quality auditor)
- 📚 Ingestion & Vector DB (upload .md / PDF files)
- 💻 Clinical Code Gen AI (FHIR R4 JSON & ICD-10 generator)

### 2. FastAPI Microservice
```bash
uvicorn software_application.fast_api:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation available at `http://localhost:8000/docs`.

### 3. CLI Runner
```bash
python -m software_application.python_prog stats
python -m software_application.python_prog ingest <path_to_file.md_or_pdf>
python -m software_application.python_prog query "<clinical question>"
python -m software_application.python_prog eval "<clinical question>"
```
