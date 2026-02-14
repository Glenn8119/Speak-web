"""
Dependency injection utilities for FastAPI.
"""

import logging
from pathlib import Path

from graph import compile_graph
from langgraph.graph.state import CompiledStateGraph
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings

logger = logging.getLogger(__name__)

# Singleton graph instance
_graph: CompiledStateGraph | None = None

# Singleton FAISS index instance
_ielts_index: FAISS | None = None

# Path to pre-built IELTS index
IELTS_INDEX_PATH = Path(__file__).parent / "data" / "ielts_index"

# Embedding model - must match the one used to build the index
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"


def get_graph() -> CompiledStateGraph:
    """
    Get the compiled LangGraph instance (singleton).

    This ensures the same MemorySaver instance is used across all requests,
    maintaining conversation persistence.
    """
    global _graph
    if _graph is None:
        _graph = compile_graph()
    return _graph


def load_ielts_index() -> FAISS | None:
    """
    Load the pre-built FAISS index for IELTS vocabulary.

    Returns:
        FAISS index if loaded successfully, None otherwise
    """
    global _ielts_index

    if _ielts_index is not None:
        return _ielts_index

    if not IELTS_INDEX_PATH.exists():
        logger.warning(f"IELTS index not found at {IELTS_INDEX_PATH}")
        return None

    try:
        embeddings = BedrockEmbeddings(model_id=EMBEDDING_MODEL_ID)
        _ielts_index = FAISS.load_local(
            str(IELTS_INDEX_PATH),
            embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info(f"IELTS FAISS index loaded from {IELTS_INDEX_PATH}")
        return _ielts_index
    except Exception as e:
        logger.error(f"Failed to load IELTS index: {e}")
        return None


def get_ielts_index() -> FAISS | None:
    """
    Get the IELTS FAISS index (singleton).

    Returns:
        FAISS index if available, None otherwise (graceful degradation)
    """
    return _ielts_index
