"""
deepseek_client.py

Client interface for DeepSeek AI API (DeepSeek-V3 & DeepSeek-R1) in Production OS.
Provides both asynchronous and synchronous execution routines with graceful error handling,
OpenAI SDK compatibility, and fallback resilience.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("DeepSeekClient")

DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def get_deepseek_api_key() -> Optional[str]:
    """Retrieve DeepSeek API key from environment."""
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key or key == "your_deepseek_api_key_here" or "placeholder" in key.lower():
        return None
    return key


def get_deepseek_model() -> str:
    """Retrieve configured DeepSeek model or default to deepseek-chat."""
    return os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL


def get_deepseek_base_url() -> str:
    """Retrieve configured DeepSeek base URL or default."""
    return os.getenv("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip() or DEFAULT_DEEPSEEK_BASE_URL


def is_deepseek_configured() -> bool:
    """Check if a valid DeepSeek API key is present."""
    return get_deepseek_api_key() is not None


async def query_deepseek(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    extra_messages: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Asynchronously queries the DeepSeek API using openai.AsyncOpenAI client.
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured in .env.")

    from openai import AsyncOpenAI

    base_url = get_deepseek_base_url()
    model_name = model or get_deepseek_model()

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": prompt})

    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=45.0)

    try:
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if "reasoner" not in model_name.lower():
            kwargs["temperature"] = temperature

        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        content = choice.message.content or ""
        return content.strip()
    finally:
        await client.close()


def query_deepseek_sync(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    extra_messages: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Synchronously queries the DeepSeek API using openai.OpenAI client.
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not configured in .env.")

    from openai import OpenAI

    base_url = get_deepseek_base_url()
    model_name = model or get_deepseek_model()

    messages: List[Dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if extra_messages:
        messages.extend(extra_messages)
    messages.append({"role": "user", "content": prompt})

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=45.0)

    try:
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if "reasoner" not in model_name.lower():
            kwargs["temperature"] = temperature

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        content = choice.message.content or ""
        return content.strip()
    finally:
        client.close()
