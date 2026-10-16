"""Shared API clients, built from the settings in config.py.

Create a client once at the entry point (e.g. kb_develop/ingestion.py) and pass it to
the functions that need it, so its connection pool is reused and missing settings
are reported before any work starts.
"""

from openai import OpenAI

import config


def openai_client():
    """OpenAI-compatible client for the LLM / embedding API at OPENLLM_BASE_URL.
    Its built-in retries are off (max_retries=0): callers retry with their own
    backoff (see kb_develop/embed.py request_with_retry)."""
    config.require("OPENLLM_API_KEY", "OPENLLM_BASE_URL")
    return OpenAI(base_url=config.OPENLLM_BASE_URL, api_key=config.OPENLLM_API_KEY, max_retries=0)
