"""Secure Hugging Face client factory for ALFA OMEGA.

The token is read only from the runtime environment. This module never prints,
returns, or persists the credential.
"""

from __future__ import annotations

import os
from typing import Any

HF_TOKEN_ENV = "HF_TOKEN"


def create_huggingface_api() -> Any:
    """Create an authenticated Hugging Face API client from HF_TOKEN."""
    token = os.getenv(HF_TOKEN_ENV)
    if not token:
        raise RuntimeError(f"{HF_TOKEN_ENV} is not configured")

    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is required for Hugging Face data access"
        ) from exc

    return HfApi(token=token)
