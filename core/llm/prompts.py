"""Framing Prompts and Anti-Hallucination Guardrails for MediScribe.
Commandment 7: Choice of Framing Prompts (System Prompt & Evidence-Constrained User Prompt).
"""

from typing import List
from core.config import settings
from core.retrieval.retriever import RetrievedChunk

class MedicalPrompts:
    """Prompt templates enforcing clinical grounding and zero-hallucination compliance."""

    SYSTEM_PROMPT = settings.prompt.system_prompt
    DISCLAIMER = settings.prompt.disclaimer

    @staticmethod
    def format_context_blocks(chunks: List[RetrievedChunk]) -> str:
        """Format retrieved passages into structured evidence blocks with source tags."""
        if not chunks:
            return "NO RELEVANT TEXTBOOK CONTEXT FOUND."

        blocks = []
        for idx, chunk in enumerate(chunks, 1):
            source = chunk.source
            page = chunk.page
            score = round(chunk.score, 3)
            blocks.append(
                f"--- EVIDENCE BLOCK [{idx}] (Source: {source} | Page: {page} | Relevance: {score}) ---\n"
                f"{chunk.text}\n"
            )
        return "\n".join(blocks)

    @classmethod
    def build_generation_prompt(cls, query: str, chunks: List[RetrievedChunk]) -> str:
        """Assemble the complete grounded prompt for the LLM."""
        context_str = cls.format_context_blocks(chunks)
        return f"""
{cls.SYSTEM_PROMPT}

EVIDENCE FROM INDEXED MEDICAL TEXTBOOKS:
========================================
{context_str}
========================================

CLINICAL QUERY:
"{query}"

INSTRUCTIONS FOR SYNTHESIS:
1. Answer the query thoroughly using ONLY facts stated in the evidence blocks above.
2. For each clinical claim or fact, cite the corresponding block: e.g. [Source 1, Page X].
3. If the evidence blocks above DO NOT contain the answer, respond strictly with:
   "The provided medical textbooks do not contain sufficient evidence to answer this question."
4. Close your answer with the disclaimer:
   "{cls.DISCLAIMER}"
"""
