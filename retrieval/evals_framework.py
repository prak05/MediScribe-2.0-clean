"""EVALS FRAMEWORK (DeepEval RAG Triad: LLM as Judge & Not as Judge)
Retrieval Layer (Commandment 10: Evaluation & Observability).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import logging
import re

from core.config import settings
from fundamentals.models import ModelRegistry

logger = logging.getLogger(__name__)

@dataclass
class RAGTriadScores:
    """RAG Triad metrics: Faithfulness, Context Relevance, and Answer Relevance."""
    faithfulness: float
    context_relevance: float
    answer_relevance: float
    overall_score: float
    evaluation_method: str  # "llm_as_judge" or "heuristic_non_judge"
    details: Dict[str, Any] = field(default_factory=dict)
    passed: bool = False

    def summary(self) -> str:
        return (
            f"RAG Triad ({self.evaluation_method}) -> "
            f"Faithfulness: {self.faithfulness:.2f}, "
            f"Context Relevance: {self.context_relevance:.2f}, "
            f"Answer Relevance: {self.answer_relevance:.2f} | "
            f"Overall: {self.overall_score:.2f} ({'PASS' if self.passed else 'FAIL'})"
        )

class HeuristicEvaluator:
    """Non-judge, fast deterministic evaluation using lexical overlap, entity coverage, and negation checks."""

    @staticmethod
    def _words(text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def evaluate(self, query: str, context_chunks: List[str], answer: str) -> RAGTriadScores:
        """Compute heuristic RAG Triad scores."""
        q_words = set(self._words(query))
        joined_context = " ".join(context_chunks).lower()
        ctx_words = set(self._words(joined_context))
        ans_words = set(self._words(answer))

        # 1. Context Relevance: overlap of query terms in retrieved context
        if not q_words:
            ctx_rel = 1.0
        else:
            overlap_qc = q_words.intersection(ctx_words)
            ctx_rel = min(1.0, len(overlap_qc) / max(1, len(q_words)))

        # 2. Answer Relevance: overlap of query terms in answer
        if not q_words or not ans_words:
            ans_rel = 0.5 if ans_words else 0.0
        else:
            overlap_qa = q_words.intersection(ans_words)
            ans_rel = min(1.0, len(overlap_qa) / max(1, len(q_words)))

        # 3. Faithfulness / Groundedness: proportion of answer content words found in context
        # Filter stop words to look at substantive claim words
        stopwords = {"the", "is", "at", "which", "on", "and", "a", "an", "in", "to", "for", "of", "with", "this", "that", "it"}
        substantive_ans = ans_words - stopwords
        if not substantive_ans:
            faith = 1.0
        elif not ctx_words:
            faith = 0.0
        else:
            overlap_ac = substantive_ans.intersection(ctx_words)
            faith = min(1.0, len(overlap_ac) / max(1, len(substantive_ans)))

        overall = (ctx_rel + ans_rel + faith) / 3.0
        passed = overall >= 0.60 and faith >= 0.50

        return RAGTriadScores(
            faithfulness=round(faith, 3),
            context_relevance=round(ctx_rel, 3),
            answer_relevance=round(ans_rel, 3),
            overall_score=round(overall, 3),
            evaluation_method="heuristic_non_judge",
            details={
                "query_word_count": len(q_words),
                "context_word_count": len(ctx_words),
                "substantive_answer_word_count": len(substantive_ans)
            },
            passed=passed
        )

class LLMJudgeEvaluator:
    """LLM-as-a-judge evaluation using Gemini 2.5 Flash to critique clinical RAG outputs."""

    EVAL_PROMPT_TEMPLATE = """You are an expert clinical AI evaluation judge.
Evaluate the following RAG output based on the DeepEval RAG Triad:
1. Faithfulness (0.0 to 1.0): Is the clinical answer strictly supported by the retrieved context without hallucination?
2. Context Relevance (0.0 to 1.0): Is the retrieved textbook context relevant to the user's clinical query?
3. Answer Relevance (0.0 to 1.0): Does the answer directly address the user's clinical question?

USER QUERY:
{query}

RETRIEVED CONTEXT:
{context}

GENERATED ANSWER:
{answer}

Respond ONLY in valid JSON format with this exact structure:
{{
    "faithfulness": 0.95,
    "context_relevance": 0.90,
    "answer_relevance": 0.92,
    "critique": "Brief explanation of the scores."
}}
"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or ModelRegistry.get_default_llm()

    def evaluate(self, query: str, context_chunks: List[str], answer: str) -> RAGTriadScores:
        """Call Gemini to act as an impartial clinical judge."""
        joined_context = "\n---\n".join(context_chunks)
        prompt = self.EVAL_PROMPT_TEMPLATE.format(
            query=query,
            context=joined_context[:6000],
            answer=answer[:2000]
        )

        clean_model = self.model_name.replace("models/", "")
        try:
            from google import genai
            client = genai.Client(api_key=settings.api_key)
            resp = client.models.generate_content(
                model=clean_model,
                contents=prompt
            )
            raw_text = resp.text.strip()
            # Extract JSON
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                faith = float(data.get("faithfulness", 0.8))
                ctx_rel = float(data.get("context_relevance", 0.8))
                ans_rel = float(data.get("answer_relevance", 0.8))
                critique = data.get("critique", "LLM Judge evaluation completed.")
                overall = (faith + ctx_rel + ans_rel) / 3.0

                return RAGTriadScores(
                    faithfulness=round(faith, 3),
                    context_relevance=round(ctx_rel, 3),
                    answer_relevance=round(ans_rel, 3),
                    overall_score=round(overall, 3),
                    evaluation_method="llm_as_judge",
                    details={"critique": critique, "judge_model": clean_model},
                    passed=overall >= 0.70 and faith >= 0.70
                )
        except Exception as e:
            logger.warning(f"LLM Judge call failed: {e}. Falling back to heuristic evaluator.")

        # Fallback to heuristic
        return HeuristicEvaluator().evaluate(query, context_chunks, answer)

class EvalsFramework:
    """Unified DeepEval RAG Triad evaluation interface."""

    def __init__(self, default_use_llm_judge: bool = True):
        self.default_use_llm_judge = default_use_llm_judge
        self.heuristic = HeuristicEvaluator()
        self.llm_judge = LLMJudgeEvaluator()

    def evaluate_rag(
        self,
        query: str,
        context_chunks: List[str],
        answer: str,
        use_llm_judge: Optional[bool] = None
    ) -> RAGTriadScores:
        """Run RAG Triad evaluation using either LLM-as-judge or non-judge."""
        use_llm = self.default_use_llm_judge if use_llm_judge is None else use_llm_judge
        if use_llm:
            return self.llm_judge.evaluate(query, context_chunks, answer)
        return self.heuristic.evaluate(query, context_chunks, answer)
