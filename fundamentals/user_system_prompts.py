"""User & System Prompt Engineering.
Fundamentals Layer (Commandment 7).
"""

from typing import List

class MedicalPrompts:
    """Clinical system prompts and evidence-constrained user query formatting."""

    SYSTEM_PROMPT = (
        "You are MediScribe, an advanced evidence-based clinical AI assistant grounded strictly in "
        "indexed medical textbooks and peer-reviewed literature.\n"
        "Strict rules:\n"
        "1. Answer ONLY using the facts present in the retrieved textbook context blocks.\n"
        "2. For every clinical fact or claim, cite the source in brackets: [Source {i}, {filename}, Page {p}].\n"
        "3. If the retrieved evidence does not contain the answer, respond strictly with: "
        "'The provided medical textbooks do not contain sufficient evidence to answer this question.'\n"
        "4. Include an educational and non-prescriptive medical disclaimer."
    )

    DISCLAIMER = "⚠️ Educational & Clinical Reference Only: Not a substitute for formal medical diagnosis or physician prescription."

    @classmethod
    def format_user_prompt(cls, query: str, context_blocks: List[str]) -> str:
        """Combine user question with numbered evidence blocks."""
        joined_contexts = "\n\n".join(context_blocks) if context_blocks else "NO CONTEXT FOUND."
        return f"""{cls.SYSTEM_PROMPT}

EVIDENCE BLOCKS FROM INDEXED TEXTBOOKS:
=======================================
{joined_contexts}
=======================================

USER CLINICAL QUERY:
"{query}"

SYNTHESIS REQUIREMENTS:
- Provide an accurate, grounded synthesis citing exact evidence blocks.
- Conclude with: {cls.DISCLAIMER}
"""
