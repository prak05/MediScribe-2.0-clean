"""UI (User Interface - Streamlit Clinical RAG Application)
Software Application Layer (Commandment 9: User Interface).
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

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

# Set page config
st.set_page_config(
    page_title="MediScribe AI | Clinical RAG Platform",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #3B82F6;
    }
    .citation-badge {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# State initialization
@st.cache_resource
def get_services():
    store = VectorDBStore()
    embedder = ChunkerEmbedder()
    retriever = ChunkRetriever(vector_store=store, embedder=embedder)
    reranker = MedicalReranker()
    evaluator = EvalsFramework()
    codegen = ClinicalCodeGenAI()
    loader = DataLoader()
    return store, embedder, retriever, reranker, evaluator, codegen, loader

store, embedder, retriever, reranker, evaluator, codegen, loader = get_services()

# --- Sidebar ---
st.sidebar.markdown("## 🩺 MediScribe Clinical RAG")
st.sidebar.markdown("**Architecture**: Abhilash Sir's 10 Commandments")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "Navigation",
    [
        "🩺 Clinical Assistant (RAG)",
        "⚡ Re-Ranking Inspector",
        "⚖️ DeepEval RAG Triad",
        "📚 Ingestion & Vector DB",
        "💻 Clinical Code Gen AI"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ System Status")
stats = store.get_stats()
st.sidebar.metric("Indexed Chunks", stats["total_chunks"])
st.sidebar.metric("Indexed Documents", stats["total_documents"])
st.sidebar.caption(f"**LLM**: `{ModelRegistry.get_default_llm()}`")
st.sidebar.caption(f"**Embedder**: `{ModelRegistry.get_default_embedder()}`")

# --- Tab 1: Clinical Assistant ---
if app_mode == "🩺 Clinical Assistant (RAG)":
    st.markdown('<div class="main-header">🩺 MediScribe Clinical Evidence Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Grounded strictly in peer-reviewed clinical textbooks and guidelines.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "Enter Clinical Question:",
            value="What is the first-line pharmacologic monotherapy for Stage 2 hypertension in adults?",
            placeholder="Ask medical question..."
        )
    with col2:
        top_k = st.slider("Top Chunks (k)", min_value=1, max_value=8, value=4)
        use_rerank = st.checkbox("Enable Re-ranking", value=True)

    if st.button("🔍 Search & Synthesize Evidence", type="primary"):
        with st.spinner("Retrieving textbook evidence and synthesizing answer..."):
            initial_chunks = retriever.retrieve(query, top_k=top_k * 2 if use_rerank else top_k)

            if not initial_chunks:
                st.warning("⚠️ No relevant medical chunks found in the index.")
            else:
                if use_rerank:
                    reranked = reranker.rerank(query, initial_chunks, top_k=top_k)
                    active_chunks = [r.chunk for r in reranked]
                else:
                    active_chunks = initial_chunks[:top_k]

                result = retriever.synthesize_answer(query, active_chunks)

                st.markdown("### 📋 Clinical Synthesis")
                st.info(result["answer"])

                st.markdown("### 📚 Grounded Source Citations")
                for c in result["citations"]:
                    st.markdown(f"- `{c}`")

                with st.expander("🔍 View Retrieved Evidence Blocks"):
                    for idx, chk in enumerate(active_chunks, start=1):
                        st.markdown(f"**Evidence Block {idx}** | Source: `{chk.source}` (Page {chk.page}) | Score: `{chk.score:.4f}`")
                        st.write(chk.text)
                        st.markdown("---")

                st.warning(result["disclaimer"])

# --- Tab 2: Re-Ranking Inspector ---
elif app_mode == "⚡ Re-Ranking Inspector":
    st.markdown('<div class="main-header">⚡ Hybrid Re-ranking Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect how dense vector similarity is re-scored using lexical overlap and medical terminology boosting (Commandment 8).</div>', unsafe_allow_html=True)

    test_query = st.text_input("Query for Re-ranking:", value="ACE inhibitors contraindications in pregnancy and bilateral renal artery stenosis")
    k_val = st.slider("Candidate Count", 2, 10, 5)

    if st.button("Run Re-ranking Comparison"):
        chunks = retriever.retrieve(test_query, top_k=k_val)
        if not chunks:
            st.info("No chunks retrieved. Make sure documents are indexed.")
        else:
            reranked = reranker.rerank(test_query, chunks, top_k=k_val)

            table_data = []
            for r in reranked:
                table_data.append({
                    "Source": r.source,
                    "Page": r.page,
                    "Initial Vector Score": f"{r.original_score:.4f}",
                    "Lexical Score": f"{r.lexical_score:.4f}",
                    "Medical Boost": f"{r.medical_boost:.4f}",
                    "Final Reranked": f"{r.reranked_score:.4f}",
                    "Rank Shift": f"{'+' if r.rank_delta > 0 else ''}{r.rank_delta}",
                    "Snippet": r.text[:120] + "..."
                })

            st.dataframe(table_data, use_container_width=True)

# --- Tab 3: DeepEval RAG Triad ---
elif app_mode == "⚖️ DeepEval RAG Triad":
    st.markdown('<div class="main-header">⚖️ DeepEval RAG Triad Quality Framework</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Rigorous clinical evaluation: Faithfulness, Context Relevance, and Answer Relevance (Commandment 10).</div>', unsafe_allow_html=True)

    eval_query = st.text_input(
        "Clinical Evaluation Query:",
        value="What are the primary adverse effects and monitoring parameters for Metformin?"
    )
    judge_mode = st.radio("Evaluation Method:", ["Heuristic (Deterministic Non-Judge)", "Gemini 2.5 Flash (LLM as Judge)"])

    if st.button("⚖️ Run RAG Triad Evaluation", type="primary"):
        with st.spinner("Executing RAG pipeline and calculating evaluation metrics..."):
            chunks = retriever.retrieve(eval_query, top_k=3)
            result = retriever.synthesize_answer(eval_query, chunks)

            use_judge = "LLM as Judge" in judge_mode
            triad = evaluator.evaluate_rag(
                query=eval_query,
                context_chunks=[c.text for c in chunks],
                answer=result["answer"],
                use_llm_judge=use_judge
            )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Faithfulness", f"{triad.faithfulness * 100:.1f}%")
            col2.metric("Context Relevance", f"{triad.context_relevance * 100:.1f}%")
            col3.metric("Answer Relevance", f"{triad.answer_relevance * 100:.1f}%")
            col4.metric("Overall Score", f"{triad.overall_score * 100:.1f}%", delta="PASS" if triad.passed else "FAIL")

            st.markdown("#### Clinical Answer Tested:")
            st.write(result["answer"])

            if triad.details:
                st.markdown("#### Evaluation Audit Log:")
                st.json(triad.details)

# --- Tab 4: Ingestion & Vector DB ---
elif app_mode == "📚 Ingestion & Vector DB":
    st.markdown('<div class="main-header">📚 Medical Ingestion & Vector Store</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ingest clinical textbooks, guidelines (.md, .pdf), chunk and embed into local vector index.</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader("Upload Medical Textbooks (.md, .pdf, .txt)", accept_multiple_files=True)
    if uploaded_files and st.button("🚀 Ingest & Index Uploaded Files"):
        total_indexed = 0
        for uf in uploaded_files:
            docs = loader.load_bytes_data(uf.name, uf.getvalue())
            c_embeddings = embedder.process_documents(docs)
            added = store.add_chunks(c_embeddings)
            total_indexed += added
        store.save()
        st.success(f"Successfully processed {len(uploaded_files)} files and indexed {total_indexed} chunks!")

    st.markdown("---")
    st.markdown("### Ingest Sample Clinical Guidelines")
    sample_path = Path("/home/prak05/MediScribe/materials/sample_data/clinical_guidelines_sample.md")
    if sample_path.exists():
        if st.button("🔄 Re-index Default Clinical Guidelines"):
            docs = loader.load(sample_path)
            c_embeddings = embedder.process_documents(docs)
            added = store.add_chunks(c_embeddings)
            store.save()
            st.success(f"Re-indexed {added} chunks from default guidelines.")

# --- Tab 5: Clinical Code Gen AI ---
elif app_mode == "💻 Clinical Code Gen AI":
    st.markdown('<div class="main-header">💻 Clinical Code Gen AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated clinical data schemas, FHIR R4 resources, and synthetic benchmark generators.</div>', unsafe_allow_html=True)

    cg_mode = st.selectbox("Select Generator:", ["HL7 FHIR R4 Resource", "ICD-10-CM Coding", "Synthetic Clinical Benchmark", "DeepEval Python Test Script"])

    if cg_mode == "HL7 FHIR R4 Resource":
        res_type = st.selectbox("FHIR Resource Type", ["Condition", "MedicationRequest", "Observation"])
        pat_id = st.text_input("Patient ID", "pat-1049")
        cond_name = st.text_input("Clinical Display", "Type 2 Diabetes Mellitus")
        if st.button("Generate FHIR JSON"):
            fhir_res = codegen.generate_fhir_resource(res_type, pat_id, {"condition_name": cond_name, "medication_name": cond_name})
            st.json(fhir_res)

    elif cg_mode == "ICD-10-CM Coding":
        cond_input = st.text_input("Clinical Finding / Condition:", "Stage 2 essential hypertension with heart failure")
        if st.button("Lookup ICD-10"):
            res = codegen.generate_icd10_mapping(cond_input)
            st.json(res)

    elif cg_mode == "Synthetic Clinical Benchmark":
        spec = st.selectbox("Medical Specialty", ["Cardiology", "Endocrinology"])
        if st.button("Generate Case"):
            case = codegen.generate_clinical_test_case(spec)
            st.json(case)

    elif cg_mode == "DeepEval Python Test Script":
        q = st.text_input("Query:", "What is the first-line therapy for Stage 2 hypertension?")
        gt = st.text_input("Ground Truth Concept:", "Combination of two first-line agents (ACEi/ARB + CCB or thiazide)")
        if st.button("Generate Python Script"):
            code = codegen.generate_python_eval_script(q, gt)
            st.code(code, language="python")
