import os
from typing import Any

import streamlit as st


def get_secret(name: str, default: Any = None) -> Any:
    """
    Read a value from Streamlit Secrets first.
    If it is not available, use an environment variable.
    """

    try:
        value = st.secrets.get(name)

        if value not in (None, ""):
            return value

    except Exception:
        pass

    return os.getenv(name, default)


# ============================================================
# AI CONFIGURATION
# ============================================================

HF_TOKEN = get_secret("HF_TOKEN", "")

LLM_MODEL = get_secret(
    "LLM_MODEL",
    "Qwen/Qwen3-4B-Instruct-2507",
)

IMAGE_MODEL = get_secret(
    "IMAGE_MODEL",
    "black-forest-labs/FLUX.1-schnell",
)


# ============================================================
# VIDEO CONFIGURATION
# ============================================================

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
FPS = 24

MIN_SCENES = 4
MAX_SCENES = 8

WORDS_PER_MINUTE = 145
