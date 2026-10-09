import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI


# Keep requests modest for free/restricted provider tiers.
# A 300-word input should produce a compact plan, not verbose visual prose.
DEFAULT_OUTPUT_TOKENS = 650
COMPACT_OUTPUT_TOKENS = 480
MAX_RETRIES = 2
MAX_SCENES = 16

SUPPORTED_VISUAL_TYPES = {
    "ai_image",
    "title_screen",
    "explanation_screen",
    "summary_screen",
    "whiteboard",
    "diagram",
    "chart",
    "formula",
    "equation",
    "physics",
    "chemistry",
    "aiva",
    "animation",
}

SYSTEM_PROMPT = """
You are an educational video director and scriptwriter.
Turn the supplied lesson into a concise, accurate, visually rich video plan.

Return ONLY valid JSON:
{
  "title": "Video title",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "Words spoken by the teacher.",
      "visual_type": "whiteboard",
      "visual_focus": "What this scene teaches",
      "image_prompt": "Short image-generation prompt if an image is needed",
      "on_screen_text": "Short label",
      "animation": "draw",
      "duration_seconds": 12,
      "formula": "",
      "explanation": "Short visual explanation",
      "whiteboard_steps": ["First drawing step", "Second drawing step"],
      "diagram_elements": ["Start", "Process", "Result"],
      "equation_steps": [],
      "chart_data": []
    }
  ]
}

Rules:
1. Use the requested language for title, narration, on-screen text, and labels.
2. Explain for the requested education level and preserve key source facts.
3. Aim for the requested duration. For 120 seconds, target about 240-280 spoken words,
   adjusting naturally for the language and the selected voice speed.
4. Choose the number of scenes based on the lesson and duration; do not force a fixed count.
5. Usually use about 8-18 seconds per scene. Duration estimates must add up approximately
   to the target duration.
6. Use a mix of visual styles when useful:
   title_screen, explanation_screen, summary_screen, ai_image, whiteboard,
   diagram, chart, formula, equation, physics, chemistry, aiva, animation.
7. Use whiteboard for progressive marker-style drawing; diagram for processes;
   chart for data/trends; formula/equation for mathematical steps; ai_image for
   illustrative scenes; title_screen for the opening; summary_screen for the recap.
8. Keep image_prompt to one concise sentence (ideally under 15 words).
9. Keep on_screen_text short (2-7 words). Avoid large paragraphs on screen.
10. Keep whiteboard_steps, diagram_elements, and equation_steps short.
11. Use chart_data only when the source provides meaningful values; do not invent data.
12. Use only the keys in the JSON structure. Empty arrays/strings are allowed.
13. Do not include Markdown fences, commentary, or facts not supported by the source.
14. Keep JSON compact. Never repeat the narration inside the visual description.
"""


def _get_setting(name: str, default: Optional[str] = None) -> Optional[str]:
    """Read settings from environment variables first, then Streamlit secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def _get_api_keys() -> List[str]:
    """Load keys from GROQ_API_KEYS; fall back to the legacy LLM_API_KEY."""
    raw_keys = _get_setting("GROQ_API_KEYS")
    keys: List[str] = []

    if isinstance(raw_keys, (list, tuple)):
        keys = [str(item).strip() for item in raw_keys if str(item).strip()]
    elif isinstance(raw_keys, str) and raw_keys.strip():
        keys = [item.strip().strip("\\\"'") for item in raw_keys.split(",") if item.strip()]

    if not keys:
        single_key = _get_setting("LLM_API_KEY")
        if single_key and str(single_key).strip():
            keys = [str(single_key).strip()]

    return list(dict.fromkeys(keys))


def _is_auth_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()
    return status in (401, 403) or any(
        phrase in message
        for phrase in ("invalid api key", "incorrect api key", "authentication", "unauthorized", "revoked")
    )


def _extract_json(content: str) -> Dict[str, Any]:
    """Parse a JSON object, tolerating accidental Markdown code fences."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("The AI returned an empty scene plan.")

    content = content.strip()
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content,
        flags=re.IGNORECASE,
    ).strip()

    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("The AI response did not contain a complete JSON object.")

    try:
        result = json.loads(content[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(
            "The AI returned incomplete or invalid JSON. "
            "Retry generation; if this repeats, reduce source length."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError("The AI response must be a JSON object.")
    return result


def _as_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return fallback


def _as_short_list(value: Any, max_items: int = 8) -> List[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:max_items]:
        text = _as_text(item)
        if text:
            result.append(text[:160])
    return result


def _normalize_plan(plan: Any, target_seconds: int = 120) -> Dict[str, Any]:
    """Validate and normalize scene data for the downstream video pipeline."""
    if isinstance(plan, list):
        plan = {"title": "Educational Video", "scenes": plan}
    if not isinstance(plan, dict):
        raise ValueError("The AI returned an invalid video plan.")

    scenes = plan.get("scenes")
    if isinstance(scenes, dict):
        scenes = scenes.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("The AI did not return a valid scene list.")

    normalized = []
    for index, raw_scene in enumerate(scenes[:MAX_SCENES], start=1):
        if isinstance(raw_scene, str):
            raw_scene = {"narration": raw_scene}
        if not isinstance(raw_scene, dict):
            raise ValueError(f"Scene {index} has an unsupported data format.")

        narration = _as_text(raw_scene.get("narration"))
        if not narration:
            raise ValueError(f"Scene {index} has no narration.")

        visual_type = _as_text(raw_scene.get("visual_type"), "ai_image").lower()
        if visual_type not in SUPPORTED_VISUAL_TYPES:
            visual_type = "ai_image"

        # Provide compatible defaults used by the existing app/services.
        scene = {
            "scene_id": index,
            "narration": narration,
            "visual_type": visual_type,
            "visual_focus": _as_text(
                raw_scene.get("visual_focus"),
                _as_text(raw_scene.get("on_screen_text"), f"Scene {index}")
            ),
            "image_prompt": _as_text(raw_scene.get("image_prompt"), narration),
            "on_screen_text": _as_text(raw_scene.get("on_screen_text")),
            "animation": _as_text(raw_scene.get("animation"), "fade").lower(),
            "duration_seconds": raw_scene.get("duration_seconds"),
            "formula": _as_text(raw_scene.get("formula")),
            "explanation": _as_text(raw_scene.get("explanation"), narration),
            "whiteboard_steps": _as_short_list(raw_scene.get("whiteboard_steps")),
            "diagram_elements": _as_short_list(raw_scene.get("diagram_elements")),
            "equation_steps": _as_short_list(raw_scene.get("equation_steps")),
            "chart_data": raw_scene.get("chart_data", []),
        }

        try:
            scene["duration_seconds"] = float(scene["duration_seconds"])
            if scene["duration_seconds"] <= 0:
                raise ValueError
        except (TypeError, ValueError):
            scene["duration_seconds"] = None

        if not isinstance(scene["chart_data"], list):
            scene["chart_data"] = []

        normalized.append(scene)

    if not normalized:
        raise ValueError("The AI returned no usable scenes.")

    # If durations are absent, distribute target time evenly.
    missing = [s for s in normalized if s["duration_seconds"] is None]
    if missing:
        assigned = sum(
            s["duration_seconds"] or 0
            for s in normalized
            if s["duration_seconds"] is not None
        )
        remaining = max(1.0, float(target_seconds) - assigned)
        per_scene = remaining / len(missing)
        for scene in missing:
            scene["duration_seconds"] = round(per_scene, 2)

    normalized_total = sum(s["duration_seconds"] for s in normalized)
    if normalized_total > 0:
        # Scale scene duration estimates to the target duration.
        scale = float(target_seconds) / normalized_total
        for scene in normalized:
            scene["duration_seconds"] = round(
                max(2.0, scene["duration_seconds"] * scale), 2
            )

    return {
        "title": _as_text(plan.get("title"), "Educational Video"),
        "scenes": normalized,
    }


def _is_rate_limit_error(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    message = str(exc).lower()
    return (
        status == 429
        or "rate_limit_exceeded" in message
        or "tokens per minute" in message
        or "rate limit" in message
    )


def create_video_plan(
    text: str,
    language: str = "English",
    education_level: str = "General",
    duration: int = 120,
) -> Dict[str, Any]:
    """Generate a compact scene plan compatible with Phase 2 visual services."""
    api_keys = _get_api_keys()
    base_url = _get_setting("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    model = _get_setting("LLM_MODEL")

    if not api_keys:
        raise ValueError(
            "Missing GROQ_API_KEYS (or legacy LLM_API_KEY) in Streamlit Secrets."
        )
    if not base_url:
        raise ValueError("Missing LLM_BASE_URL in Streamlit Secrets.")
    if not model:
        raise ValueError("Missing LLM_MODEL in Streamlit Secrets.")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Please provide educational content.")

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 120
    duration = max(15, min(duration, 600))

    word_count = len(text.split())
    # Scene count is a hint only; the model may adjust for topic complexity.
    scene_hint = max(3, (duration + 14) // 15, (word_count + 39) // 40)
    scene_hint = min(scene_hint, MAX_SCENES)

    prompt = f"""
Language: {language}
Education level: {education_level}
Target duration: {duration} seconds
Input word count: {word_count}
Suggested scene count: about {scene_hint} (adjust if necessary)

Create a complete educational video plan. Target narration length for 120 seconds:
about 240-280 words, adjusted for language and natural speech.
Make each scene concise. Mix animated screens, whiteboard drawings, diagrams,
charts, formulas, and AI images when appropriate. Do not invent chart values.
The scene durations should add up to approximately {duration} seconds.
Return only the JSON schema from the system prompt.

LESSON:
{text.strip()}
"""

    last_error = None
    token_budgets = [DEFAULT_OUTPUT_TOKENS, COMPACT_OUTPUT_TOKENS, 350]
    cycle_number = 0

    # Continuous circular rotation: key 1 -> ... -> key N -> key 1.
    # Each full cycle pauses before retrying, and the secrets are re-read so
    # a manually replaced key can be picked up after the app refreshes.
    while True:
        cycle_number += 1
        # Reload keys each cycle to pick up updated Streamlit Secrets/env vars.
        refreshed_keys = _get_api_keys()
        if refreshed_keys:
            api_keys = refreshed_keys

        token_budget = token_budgets[min(cycle_number - 1, len(token_budgets) - 1)]
        compact_instruction = ""
        if cycle_number > 1:
            compact_instruction = (
                "\nIMPORTANT: Keep the JSON compact. Use 5-8 scenes if suitable, "
                "short visual fields, and no redundant detail. Preserve useful "
                "narration and return complete valid JSON.\n"
            )
        request_prompt = prompt + compact_instruction
        last_error = None
        saw_rate_limit = False
        saw_auth_error = False

        # This for-loop wraps naturally to key 1 on the next while-loop cycle.
        for key_index, api_key in enumerate(api_keys):
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=90.0,
                max_retries=0,
            )

            try:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.2,
                    max_tokens=token_budget,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": request_prompt},
                    ],
                )

                if not response.choices:
                    raise ValueError("The AI returned no choices.")

                choice = response.choices[0]
                content = choice.message.content
                if not content or not content.strip():
                    raise ValueError("The AI returned an empty scene plan.")

                if choice.finish_reason == "length":
                    last_error = ValueError(
                        "The response was truncated by the token limit."
                    )
                    # Try the next key, then retry with a smaller output budget.
                    continue

                plan = _extract_json(content)
                return _normalize_plan(plan, target_seconds=duration)

            except Exception as exc:
                last_error = exc
                if _is_auth_error(exc):
                    saw_auth_error = True
                    # This key may be revoked/invalid; move to the next slot.
                    continue
                if _is_rate_limit_error(exc):
                    saw_rate_limit = True
                    # Try the next key. If all keys fail, pause before cycling.
                    continue
                if isinstance(exc, ValueError):
                    # Invalid/truncated model output: move through keys and
                    # then retry the next cycle with a smaller output budget.
                    continue
                raise RuntimeError(
                    f"Video scene planning failed on key slot {key_index + 1}: {exc}"
                ) from exc

        # Every configured key failed this cycle. Pause to avoid hammering the API.
        if saw_rate_limit:
            time.sleep(62)
        elif saw_auth_error:
            # Allows time for a manually replaced key/app secrets refresh.
            time.sleep(20)
        else:
            # Repeated malformed/truncated responses: pause, then retry compactly.
            time.sleep(5)


def generate_scene_plan(
    educational_text: str,
    language: str = "English",
    education_level: str = "General",
    target_seconds: int = 120,
) -> List[Dict[str, Any]]:
    """Compatibility wrapper: the existing Streamlit app expects a scene list."""
    plan = create_video_plan(
        text=educational_text,
        language=language,
        education_level=education_level,
        duration=target_seconds,
    )
    return plan["scenes"]
