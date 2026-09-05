"""Grounded Response Generation Engine for MediScribe.
Commandment 2: Choice of LLM & Model (Gemini 1.5/2.0 Flash / Pro).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import requests

from core.config import settings
from core.retrieval.retriever import RetrievedChunk
from .prompts import MedicalPrompts

@dataclass
class RAGResponse:
    """Structured response object containing the synthesized answer and metadata."""
    query: str
    answer: str
    sources: List[RetrievedChunk] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    model_name: str = ""
    latency_ms: float = 0.0
    confidence_score: float = 0.0
    tokens_estimate: int = 0

    @property
    def has_sources(self) -> bool:
        return len(self.sources) > 0

class ClinicalGenerator:
    """Invokes Google Gemini with structured medical prompts and collects grounded output."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.api_key
        self.model_name = model_name or settings.model.default_model

    def generate(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        model_name: Optional[str] = None
    ) -> RAGResponse:
        """Synthesize a grounded answer from the provided evidence chunks."""
        start_time = time.perf_counter()
        active_model = model_name or self.model_name

        # If no chunks provided, reject immediately
        if not chunks:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return RAGResponse(
                query=query,
                answer=(
                    "The provided medical textbooks do not contain sufficient evidence to answer this question. "
                    "Please upload relevant textbook chapters or verify that the term is present in the index."
                ),
                sources=[],
                citations=[],
                model_name=active_model,
                latency_ms=round(elapsed_ms, 2),
                confidence_score=0.0
            )

        # Build prompt
        prompt = MedicalPrompts.build_generation_prompt(query, chunks)
        citations = [f"{c.source} (Page {c.page})" for c in chunks]
        avg_confidence = sum(c.score for c in chunks) / len(chunks) if chunks else 0.0

        # Attempt Gemini call using google.genai SDK first, then REST
        answer_text = ""
        clean_model = active_model.replace("models/", "")

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            res = client.models.generate_content(
                model=clean_model,
                contents=prompt
            )
            if res and res.text:
                answer_text = res.text
        except Exception:
            # Fallback to direct REST endpoint
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": settings.model.temperature,
                        "topP": settings.model.top_p,
                        "maxOutputTokens": settings.model.max_output_tokens
                    }
                }
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    answer_text = "".join(p.get("text", "") for p in parts)
            except Exception:
                pass

        if not answer_text.strip():
            # If API is unreachable offline, synthesize grounded deterministic summary from top chunks
            top_context = "\n\n".join([f"From {c.source} (Page {c.page}):\n{c.text[:400]}..." for c in chunks[:2]])
            answer_text = (
                f"**Grounded Clinical Summary:**\n\n"
                f"Based on the indexed medical literature, the following evidence addresses your query:\n\n"
                f"{top_context}\n\n"
                f"*{MedicalPrompts.DISCLAIMER}*"
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        approx_tokens = len(prompt.split()) + len(answer_text.split())

        return RAGResponse(
            query=query,
            answer=answer_text.strip(),
            sources=chunks,
            citations=citations,
            model_name=active_model,
            latency_ms=round(elapsed_ms, 2),
            confidence_score=round(avg_confidence, 3),
            tokens_estimate=approx_tokens
        )
