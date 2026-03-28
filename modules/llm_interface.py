"""Module for interfacing with GitHub Models using OpenAI-compatible clients."""

import importlib
import logging
import os
from typing import Any

import config

logger = logging.getLogger(__name__)


def _build_auth_help_message() -> str:
    return (
        "GitHub Models authentication failed. Set GITHUB_TOKEN to a fine-grained token "
        "with access to GitHub Models (Models: Read), then retry."
    )


def _get_github_token() -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise PermissionError(
            "Missing GITHUB_TOKEN. Please set a fine-grained GitHub token with "
            "GitHub Models access (Models: Read)."
        )
    return token


def is_auth_or_permission_error(error: Exception) -> bool:
    """Detect auth/permission style errors from OpenAI-compatible backends."""
    message = str(error).lower()
    markers = (
        "401",
        "403",
        "unauthorized",
        "forbidden",
        "permission",
        "insufficient",
        "invalid api key",
        "authentication",
        "access denied",
    )
    return any(marker in message for marker in markers)


def explain_model_error(error: Exception) -> str:
    """Return a user-facing, clear error message for model-related failures."""
    if isinstance(error, PermissionError) or is_auth_or_permission_error(error):
        return _build_auth_help_message()
    return str(error)


def create_github_embedding() -> Any:
    """Create GitHub Models embedding client through OpenAI-compatible API."""
    token = _get_github_token()
    embeddings_module = importlib.import_module("llama_index.embeddings.openai")
    openai_embedding_cls = getattr(embeddings_module, "OpenAIEmbedding")
    embedding = openai_embedding_cls(
        model=config.EMBEDDING_MODEL_ID,
        api_key=token,
        api_base=config.GITHUB_MODELS_BASE_URL,
    )
    logger.info(f"Created GitHub Models embedding: {config.EMBEDDING_MODEL_ID}")
    return embedding


def create_github_llm(
    temperature: float = config.TEMPERATURE,
    max_new_tokens: int = config.MAX_NEW_TOKENS,
    decoding_method: str = "sample",
) -> Any:
    """Create GitHub Models LLM client through OpenAI-compatible API."""
    _ = decoding_method  # Keep signature parity with previous implementation.
    token = _get_github_token()
    llms_module = importlib.import_module("llama_index.llms.openai")
    openai_llm_cls = getattr(llms_module, "OpenAI")
    llm = openai_llm_cls(
        model=config.LLM_MODEL_ID,
        api_key=token,
        api_base=config.GITHUB_MODELS_BASE_URL,
        temperature=temperature,
        max_tokens=max_new_tokens,
    )
    logger.info(f"Created GitHub Models LLM: {config.LLM_MODEL_ID}")
    return llm


def change_llm_model(new_model_id: str) -> None:
    """Change the LLM model to use.

    Args:
        new_model_id: New LLM model ID to use.
    """
    config.LLM_MODEL_ID = new_model_id
    logger.info(f"Changed LLM model to: {new_model_id}")