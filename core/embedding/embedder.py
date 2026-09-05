"""Embedding Generation Service for MediScribe.
Commandment 4: Choice of Embedding (Google text-embedding-004 / embedding-001, 768 dimensions).
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import hashlib
import math
import requests

from core.config import settings

class BaseEmbedder(ABC):
    """Abstract base class for vector embedding engines."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

class GeminiEmbedder(BaseEmbedder):
    """Google Gemini Vector Embedder via REST / GenAI API."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.api_key
        self.model_name = model_name or settings.embedding.model_name
        self._dimension = settings.embedding.dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension

        clean_model = self.model_name.replace("models/", "")
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            res = client.models.embed_content(
                model=clean_model,
                contents=text[:8000]
            )
            if res and res.embeddings and res.embeddings[0].values:
                return list(res.embeddings[0].values)
        except Exception:
            pass

        # If remote call fails, fallback gracefully to deterministic local vector
        return LocalHashEmbedder(dimension=self.dimension).embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

class LocalHashEmbedder(BaseEmbedder):
    """Deterministic, zero-dependency offline embedding model for testing and offline fallback."""

    def __init__(self, dimension: int = 768):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dimension

        vec = [0.0] * self._dimension
        words = text.lower().split()
        for i, word in enumerate(words):
            # Generate deterministic feature hash
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1.0 if (h // self._dimension) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 / math.sqrt(i + 1))

        # Cosine unit-norm normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]

def get_embedder(api_key: Optional[str] = None) -> BaseEmbedder:
    """Factory helper to obtain the configured embedding service."""
    key = api_key or settings.api_key
    if key and len(key) > 15:
        return GeminiEmbedder(api_key=key)
    return LocalHashEmbedder(dimension=settings.embedding.dimension)
