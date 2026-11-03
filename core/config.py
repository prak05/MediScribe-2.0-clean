"""Configuration Management for MediScribe RAG Platform
Embodying Abhilash Sir's "10 Commandments of RAG" Architecture.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import os

def load_default_api_key() -> str:
    """Resolve the Gemini API key from the runtime environment."""
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return key.strip() if key and key.strip() else ""

@dataclass
class DataConfig:
    """Commandment 1: Choice of Data (Timeliness, Credibility, Availability, Format)."""
    allowed_extensions: List[str] = field(default_factory=lambda: [".pdf", ".txt", ".md"])
    storage_dir: Path = Path("/home/prak05/MediScribe/materials/sample_data")
    max_file_size_mb: int = 150
    default_medical_domain: str = "Evidence-based Clinical Medicine"

@dataclass
class ModelConfig:
    """Commandment 2: Choice of LLM & Model (Online/Offline, Dimensionality, Parameters)."""
    default_model: str = "gemini-3.6-flash"
    fallback_model: str = "gemini-flash-latest"
    pro_model: str = "gemini-3.1-pro-preview"
    temperature: float = 0.1
    top_p: float = 0.95
    max_output_tokens: int = 2048

@dataclass
class ChunkingConfig:
    """Commandment 3: Choice of Chunking Strategy (Sentence vs Semantic)."""
    strategy: str = "sentence"  # "sentence" or "semantic"
    chunk_size: int = 1024
    chunk_overlap: int = 100
    separator: str = " "

@dataclass
class EmbeddingConfig:
    """Commandment 4: Choice of Embedding (Model, Dimensionality, Storage)."""
    model_name: str = "gemini-embedding-001"
    fallback_model_name: str = "gemini-embedding-2"
    dimension: int = 3072
    batch_size: int = 32

@dataclass
class VectorDBConfig:
    """Commandment 5: Choice of Vector Database & Indexing."""
    storage_dir: Path = Path("/home/prak05/MediScribe/.vector_index")
    index_name: str = "mediscribe_clinical_index"
    similarity_metric: str = "cosine"
    persist_on_disk: bool = True

@dataclass
class PromptConfig:
    """Commandment 7: Choice of Framing Prompts (System, User, Anti-hallucination)."""
    system_prompt: str = (
        "You are MediScribe, an advanced clinical AI assistant grounded exclusively in peer-reviewed "
        "medical textbooks and literature. "
        "Strict rules:\n"
        "1. Base your answer STRICTLY on the retrieved context provided below.\n"
        "2. If the context does not provide sufficient information to answer the question with certainty, "
        "explicitly state: 'The provided medical textbooks do not contain sufficient evidence to answer this question.'\n"
        "3. Cite source references using bracketed notations (e.g., [Source 1, Page X]) for every medical statement.\n"
        "4. Always include the standard clinical disclaimer that this tool is for academic and educational purposes only."
    )
    disclaimer: str = "⚠️ Educational & Clinical Reference Only: Not a substitute for formal medical advice or physician diagnosis."

@dataclass
class RetrievalConfig:
    """Commandment 8: Choice of Retrieval Interface (Cross HF, Query Re-ranking)."""
    similarity_top_k: int = 5
    rerank_top_k: int = 3
    similarity_threshold: float = 0.20
    enable_reranking: bool = True
    enable_pubmed_fallback: bool = True

@dataclass
class EvaluationConfig:
    """Commandment 9: Choice of Evaluation Strategy & Library (DeepEval / LLM as Judge)."""
    target_groundedness_score: float = 0.84
    target_context_relevance: float = 0.80
    target_faithfulness: float = 0.85
    llm_judge_model: str = "gemini-1.5-flash"

@dataclass
class PerformanceConfig:
    """Commandment 10: Performance Testing Framework (Load Test, Latency, Throughput)."""
    max_latency_budget_ms: int = 4000
    target_throughput_qps: float = 2.0
    concurrency_workers: int = 4

@dataclass
class AppSettings:
    """Root Application Configuration synthesizing all 10 Commandments."""
    api_key: str = field(default_factory=load_default_api_key)
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    def is_api_key_valid(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 15)

    @property
    def vectordb(self) -> VectorDBConfig:
        return self.vector_db

# Singleton global settings
settings = AppSettings()
