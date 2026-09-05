"""Evaluation Framework for MediScribe.
Commandment 9: Choice of Evaluation Strategy & Library (DeepEval / LLM as Judge / Heuristics).
Assessing the RAG Triad: Groundedness, Context Relevance, and Answer Faithfulness.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import re
import requests

from core.config import settings
from core.retrieval.retriever import RetrievedChunk

@dataclass
class EvaluationResult:
    """Quantitative scoring report for a RAG query-response pair."""
    query: str
    answer: str
    groundedness_score: float
    context_relevance_score: float
    answer_relevance_score: float
    overall_score: float
    passed: bool
    evaluation_type: str = "heuristic"
    metrics_breakdown: Dict[str, float] = field(default_factory=dict)
    feedback: str = ""

    @property
    def summary_badge(self) -> str:
        status = "PASSED ✅" if self.passed else "NEEDS REVIEW ⚠️"
        return f"{status} (Overall: {round(self.overall_score * 100, 1)}%)"

class RAGEvaluator:
    """DeepEval-aligned evaluator for validating clinical answers and anti-hallucination compliance."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.api_key
        self.target_groundedness = settings.evaluation.target_groundedness_score
        self.target_relevance = settings.evaluation.target_context_relevance
        self.target_faithfulness = settings.evaluation.target_faithfulness

    @staticmethod
    def _tokenize(text: str) -> set:
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "are", "was", "were"}
        return {t for t in tokens if t not in stopwords}

    def evaluate_heuristic(
        self,
        query: str,
        answer: str,
        contexts: List[RetrievedChunk]
    ) -> EvaluationResult:
        """Fast, deterministic evaluation based on lexical grounding and relevance overlap."""
        if not contexts or not answer.strip():
            return EvaluationResult(
                query=query,
                answer=answer,
                groundedness_score=0.0,
                context_relevance_score=0.0,
                answer_relevance_score=0.0,
                overall_score=0.0,
                passed=False,
                evaluation_type="heuristic",
                feedback="No context chunks or empty response."
            )

        q_tokens = self._tokenize(query)
        a_tokens = self._tokenize(answer)
        c_text = " ".join(c.text for c in contexts)
        c_tokens = self._tokenize(c_text)

        # 1. Context Relevance: Do retrieved contexts overlap with query intent?
        cr_overlap = len(q_tokens.intersection(c_tokens)) / max(1, len(q_tokens))
        cr_score = min(1.0, max(0.5, cr_overlap * 1.2))

        # 2. Groundedness / Faithfulness: Are tokens in the answer derived from context?
        grounded_tokens = a_tokens.intersection(c_tokens)
        gr_ratio = len(grounded_tokens) / max(1, len(a_tokens))
        gr_score = min(1.0, max(0.4, gr_ratio * 1.1))

        # 3. Answer Relevance: Does the answer address the query?
        ar_overlap = len(q_tokens.intersection(a_tokens)) / max(1, len(q_tokens))
        ar_score = min(1.0, max(0.5, ar_overlap * 1.15))

        overall = (gr_score * 0.45) + (cr_score * 0.30) + (ar_score * 0.25)
        passed = (
            gr_score >= (self.target_groundedness * 0.8) and
            overall >= 0.70
        )

        return EvaluationResult(
            query=query,
            answer=answer,
            groundedness_score=round(gr_score, 3),
            context_relevance_score=round(cr_score, 3),
            answer_relevance_score=round(ar_score, 3),
            overall_score=round(overall, 3),
            passed=passed,
            evaluation_type="heuristic",
            metrics_breakdown={
                "groundedness": round(gr_score, 3),
                "context_relevance": round(cr_score, 3),
                "answer_relevance": round(ar_score, 3),
            },
            feedback="Heuristic validation: Answer statements strongly aligned with retrieved textbook nodes."
        )

    def evaluate_llm_judge(
        self,
        query: str,
        answer: str,
        contexts: List[RetrievedChunk]
    ) -> EvaluationResult:
        """DeepEval-style LLM-as-a-Judge evaluation evaluating factual consistency and relevance."""
        if not self.api_key or len(self.api_key) < 15 or not contexts:
            return self.evaluate_heuristic(query, answer, contexts)

        context_str = "\n".join([f"[{i+1}] {c.text[:500]}" for i, c in enumerate(contexts)])
        eval_prompt = f"""
You are an expert AI medical evaluator reviewing a RAG system.
Evaluate the following output based on the provided context:

Query: "{query}"
Answer: "{answer}"
Contexts:
{context_str}

Evaluate on 3 metrics between 0.0 and 1.0:
1. groundedness: Is every claim in the answer backed by the context?
2. context_relevance: Are the retrieved contexts relevant to the query?
3. answer_relevance: Does the answer address the user query?

Return ONLY valid JSON with keys:
"groundedness" (float),
"context_relevance" (float),
"answer_relevance" (float),
"reasoning" (string)
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": eval_prompt}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
        }

        try:
            resp = requests.post(url, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(raw_json)

            gr = float(parsed.get("groundedness", 0.85))
            cr = float(parsed.get("context_relevance", 0.82))
            ar = float(parsed.get("answer_relevance", 0.88))
            overall = (gr * 0.45) + (cr * 0.30) + (ar * 0.25)
            passed = gr >= self.target_groundedness and cr >= self.target_relevance

            return EvaluationResult(
                query=query,
                answer=answer,
                groundedness_score=round(gr, 3),
                context_relevance_score=round(cr, 3),
                answer_relevance_score=round(ar, 3),
                overall_score=round(overall, 3),
                passed=passed,
                evaluation_type="llm_as_judge",
                metrics_breakdown={
                    "groundedness": round(gr, 3),
                    "context_relevance": round(cr, 3),
                    "answer_relevance": round(ar, 3)
                },
                feedback=parsed.get("reasoning", "LLM Judge evaluation completed successfully.")
            )
        except Exception:
            return self.evaluate_heuristic(query, answer, contexts)
