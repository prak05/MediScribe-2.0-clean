==============================
PROJECT REQUIREMENT DOCUMENT (PRD)
==============================

Project Title:
Medical Chatbot for Medical Books using Retrieval-Augmented Generation (RAG) with Gemini and LlamaIndex

1. Introduction

This project is inspired directly from the abstract of the base research paper "Chatbot to chat with medical books using Retrieval-Augmented Generation Model" fileciteturn1file0 and its equivalent version fileciteturn1file1.

The core objective is to develop an AI-powered medical study assistant that helps medical students query their textbooks efficiently. The system focuses on:
- Improving learning efficiency
- Reducing time spent on manual information retrieval
- Ensuring grounded and contextually accurate answers
- Supporting stress management through reliable academic assistance

The implementation will use:
- Gemini (LLM)
- LlamaIndex (Indexing and retrieval layer)
- Streamlit (User Interface)
- Trulens (Evaluation)

2. Problem Statement

Medical students face:
- High academic workload
- Time-consuming textbook navigation
- Difficulty retrieving precise information quickly
- Stress due to academic pressure

Traditional search methods in PDFs are inefficient and lack contextual understanding. LLMs alone may hallucinate if not grounded. Therefore, a Retrieval-Augmented Generation (RAG) system is required.

3. Objectives

The system aims to:

1. Build a medical chatbot that can answer questions from uploaded medical textbooks.
2. Implement a RAG pipeline using Gemini and LlamaIndex.
3. Ensure grounded responses with measurable accuracy.
4. Maintain a simple, clutter-free, user-friendly interface.
5. Avoid hallucinations by strictly grounding responses in retrieved context.

4. Functional Requirements

FR1: The system shall allow users to upload medical textbooks in PDF format.
FR2: The system shall extract text from uploaded PDFs.
FR3: The system shall chunk and index the extracted content using LlamaIndex.
FR4: The system shall generate embeddings and store them in a vector index.
FR5: The system shall accept user medical queries via Streamlit interface.
FR6: The system shall retrieve top-k relevant chunks.
FR7: The system shall pass retrieved context to Gemini for answer generation.
FR8: The system shall return context-grounded responses.
FR9: The system shall log evaluation metrics using Trulens.

5. Non-Functional Requirements

- The application must run locally.
- The GUI must be simple and minimalistic.
- No placeholder or dummy responses.
- All answers must be derived from indexed textbook content.
- Python-only implementation.

6. Success Criteria

- Achieve groundedness comparable to ~84% accuracy reported in the base abstract fileciteturn1file0.
- Accurate context relevance.
- Fast response time.
- Stable local execution.



==============================
DESIGN ARCHITECTURE AND WORKFLOW
==============================

1. Overall Architecture

The architecture follows the RAG structure described in the base paper:

User → Streamlit UI → LlamaIndex Retrieval Layer → Gemini LLM → Response → Trulens Evaluation

2. System Components

A. Frontend Layer
- Built using Streamlit
- Upload PDF
- Input medical question
- Display answer
- Display optional evaluation metrics

B. Document Processing Layer
- PDF Reader (PyMuPDF or similar)
- Text cleaning
- Chunking strategy

C. Indexing Layer (LlamaIndex)
- Create document nodes
- Generate embeddings
- Store in vector index
- Enable semantic retrieval

D. Retrieval Layer
- Accept user query
- Convert query into embedding
- Retrieve top-k most relevant chunks

E. Generation Layer (Gemini)
- Provide retrieved context to Gemini
- Use context-constrained prompt
- Generate answer
- Prevent hallucination using strict prompt design

F. Evaluation Layer (Trulens)
- Measure groundedness
- Measure context relevance
- Measure answer relevance

3. Detailed Workflow

Step 1: User uploads PDF.
Step 2: System extracts text.
Step 3: Text is split into chunks.
Step 4: LlamaIndex creates vector embeddings.
Step 5: Index stored locally.
Step 6: User submits question.
Step 7: Query embedding generated.
Step 8: Top-k relevant chunks retrieved.
Step 9: Retrieved chunks + query sent to Gemini.
Step 10: Gemini generates grounded response.
Step 11: Trulens evaluates response quality.
Step 12: Final answer displayed in UI.

4. Anti-Hallucination Strategy

- Strict system prompt: "Answer only from provided context. If information not present, say 'Not found in textbook.'"
- Limit token generation.
- Retrieve high-confidence chunks only.



==============================
TECH STACK REPORT
==============================

1. Programming Language
- Python 3.x

2. Large Language Model
- Google Gemini (Generative AI model)
Reason: As stated in the abstract, Gemini is used as the primary LLM fileciteturn1file0.

3. Retrieval & Indexing Framework
- LlamaIndex
Reason: Provides structured document indexing and RAG integration.

4. Frontend Framework
- Streamlit
Reason: Lightweight, minimal, and user-friendly UI consistent with the abstract fileciteturn1file0.

5. Evaluation Framework
- Trulens
Reason: Used for measuring groundedness and relevance as mentioned in abstract fileciteturn1file0.

6. Vector Store
- FAISS (local)
Reason: Fast similarity search and lightweight.

7. PDF Processing
- PyMuPDF / pdfminer

8. Embeddings
- Gemini Embedding Model

9. Development Environment
- Virtual Environment (venv)
- pip for dependency management
- Local system deployment

10. Key Libraries
- streamlit
- llama-index
- google-generativeai
- faiss-cpu
- pymupdf
- trulens
- python-dotenv



==============================
CONCLUSION
==============================

This project strictly follows the abstract of the base research work fileciteturn1file0 by:
- Using Gemini as the LLM
- Using Streamlit for interface
- Using Trulens for evaluation
- Implementing Retrieval-Augmented Generation

Additionally, LlamaIndex is incorporated to strengthen indexing and retrieval efficiency while maintaining groundedness.

The final system will be a minimal, accurate, locally executable medical study assistant with no hallucinated outputs and a clean, professional structure suitable for CSD 344 mini project implementation.

