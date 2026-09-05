"""Choosing Models: LLM and Embedding Architecture Selection.
Fundamentals Layer (Commandment 2 & 4).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import os

from core.config import settings

@dataclass
class ModelSpec:
    name: str
    family: str
    dimension: Optional[int] = None
    context_window: int = 128000
    supports_tools: bool = True
    is_embedding: bool = False

class ModelRegistry:
    """Central registry for choosing LLMs and embedding models (Online & Offline)."""

    AVAILABLE_MODELS: Dict[str, ModelSpec] = {
        "gemini-3.6-flash": ModelSpec("models/gemini-3.6-flash", "Gemini 3.6 Flash", context_window=1000000),
        "gemini-flash-latest": ModelSpec("models/gemini-flash-latest", "Gemini Latest", context_window=1000000),
        "gemini-3.1-pro-preview": ModelSpec("models/gemini-3.1-pro-preview", "Gemini 3.1 Pro", context_window=2000000),
        "gemini-embedding-001": ModelSpec("models/gemini-embedding-001", "Gemini Embeddings", dimension=3072, is_embedding=True),
        "gemini-embedding-2": ModelSpec("models/gemini-embedding-2", "Gemini Embeddings v2", dimension=3072, is_embedding=True),
        "offline-hash-embedder": ModelSpec("offline-hash-embedder", "Deterministic Hash", dimension=3072, is_embedding=True),
    }

    @classmethod
    def get_default_llm(cls) -> str:
        return settings.model.default_model

    @classmethod
    def get_default_embedder(cls) -> str:
        return settings.embedding.model_name

def get_active_model() -> str:
    return ModelRegistry.get_default_llm()

def get_embedding_model() -> str:
    return ModelRegistry.get_default_embedder()
