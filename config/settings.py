import os
from typing import Any

import streamlit as st


def get_secret(name: str, default: Any = None) -> Any:
    """
    Read configuration from Streamlit Secrets first,
    then fall back to environment variables.
    """

    try:
        value = st.secrets.get(name)

        if value not in (None, ""):
            return value

    except Exception:
        pass

    return os.getenv(name, default)


# ============================================================
# API KEYS
# ============================================================

GROQ_API_KEY = get_secret(
    "GROQ_API_KEY",
    "",
)

HF_TOKEN = get_secret(
    "HF_TOKEN",
    "",
)

GEMINI_API_KEY = get_secret(
    "GEMINI_API_KEY",
    "",
)


# ============================================================
# LLM CONFIGURATION
# ============================================================

# Primary LLM provider
LLM_PROVIDER = "groq"

# Current Groq Qwen model.
LLM_MODEL = get_secret(
    "LLM_MODEL",
    "qwen/qwen3.8-27b",
)


# ============================================================
# IMAGE CONFIGURATION
# ============================================================

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


# ============================================================
# SCENE CONFIGURATION
# ============================================================

MIN_SCENES = 4
MAX_SCENES = 8


# ============================================================
# NARRATION CONFIGURATION
# ============================================================

WORDS_PER_MINUTE = 145
