"""Software Application Layer: CLI execution, Code Generation AI, FastAPI Microservice, and Streamlit UI.
Architecture Mapping: PYTHON PROG, CODE GEN AI, FAST API, UI.
"""

from .code_gen_ai import ClinicalCodeGenAI
from .fast_api import app

__all__ = [
    "ClinicalCodeGenAI",
    "app",
]
