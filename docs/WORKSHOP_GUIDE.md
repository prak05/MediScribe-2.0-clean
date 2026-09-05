# September 12 Meetup: 55-Minute RAG Demo & Walkthrough Guide

**Event:** AI Evolve Meetup at RIET Vidhya  
**Topic:** Build Your RAG: Architecture Overview & Live Hands-on Walkthrough  
**Speaker:** Prakhar Sharma (Demo: 55 mins) | Abhilash Gopalakrishnan (Architecture Overview: 15 mins)

---

## 55-Minute Demo Timeline

### Part 1: Architecture Overview & Separation of Concerns (10 Mins)
- Show the transformation from the legacy monolithic `app.py` (536 lines) into the decentralized **3-Tier Layered Architecture**:
  - `core/ingestion/`: Document loaders
  - `core/chunking/`: Sentence-boundary splitter
  - `core/embedding/`: Gemini embeddings
  - `core/indexing/`: Persistent vector store
  - `core/retrieval/`: Retriever & Re-ranker
  - `core/llm/`: Prompts & Grounded Generator
  - `core/evaluation/`: DeepEval metrics
- Present **Abhilash Sir's 10 Commandments of RAG** using the interactive showcase tab.

### Part 2: Ingestion & Chunking Deep-Dive (12 Mins)
- Open the **Document Ingestion Tab**.
- Click **Load Sample Chapters** or upload a medical PDF.
- Show the visual chunk inspector:
  - Demonstrate how sentences are split at boundary punctuation without cutting medical terms.
  - Explain the 1024-char chunk size and 100-char overlap.
  - View the generated JSON index manifest in `.vector_index/`.

### Part 3: Live Clinical Query & Evidence Citations (15 Mins)
- Open the **Clinical Chat Tab**.
- Ask: *"What is the first-line treatment for diabetic ketoacidosis?"*
- Observe:
  - Sub-second turnaround.
  - Bracketed evidence citations: `[Source 1, Page 1]`.
  - Open the **Cited Evidence Expander** to demonstrate exact text grounding.
- Ask an ungrounded or off-topic query:
  - *"How do I repair an automobile engine?"*
  - Demonstrate the anti-hallucination refusal: *"The provided medical textbooks do not contain sufficient evidence to answer this question."*

### Part 4: Re-ranking & PubMed NCBI Fallback (10 Mins)
- Show how the **ReRanker** blends dense vector similarity with lexical term overlap to prune low-confidence nodes.
- Switch to the **PubMed Research Tab**:
  - Run a live query: *"SGLT2 inhibitors in heart failure"*.
  - Show real-time NCBI Entrez E-Utilities search returning PMIDs and clickable paper links.

### Part 5: DeepEval Quality & Benchmarking (8 Mins)
- Open the **DeepEval Quality Tab**:
  - Review Groundedness (target 84%), Context Relevance (target 80%), and Faithfulness scores.
- Run the terminal performance benchmark:
  ```bash
  python3 -m core.benchmarks.load_test --queries 6 --concurrency 2
  ```
  - Highlight P50 latency and throughput (QPS).
- Conclude with next steps: Edge AI integration and AWS deployment sprints.
