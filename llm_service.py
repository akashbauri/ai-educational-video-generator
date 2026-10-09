
import os
import json
import re
import time
from openai import OpenAI


# Keep the response compact enough for restricted API tiers.
MAX_OUTPUT_TOKENS = 850
MAX_RETRIES = 2


SYSTEM_PROMPT = """
You are an expert educational video scriptwriter and scene director.

Convert the supplied educational material into a concise, accurate,
engaging video plan for the requested duration and education level.

Return ONLY valid JSON in this exact structure:

{
  "title": "Short video title",
  "scenes": [
    {
      "scene_id": 1,
      "narration": "Words spoken by the teacher.",
      "visual_type": "ai_image",
      "image_prompt": "Short visual description.",
      "on_screen_text": "Short label",
      "animation": "zoom"
    }
  ]
}

RULES:

1. Use the requested language for the title, narration,
   and on-screen text.
2. Preserve the important facts from the source material.
3. Explain ideas clearly at the requested education level.
4. Target approximately 120 seconds when the requested duration
   is 120 seconds. Adapt the script to other durations.
5. For a 120-second video, aim for approximately 240-280 spoken
   words, adjusting for language and speech speed.
6. Use as many scenes as the content reasonably requires.
   Do NOT enforce a fixed number of scenes.
7. Prefer roughly 10-20 seconds per scene, but adjust when needed.
8. Divide the narration naturally between scenes. Do not repeat it.
9. Keep image_prompt concise, preferably 8-15 words.
10. Keep on_screen_text short, preferably 2-7 words.
11. Use visual_type "ai_image" for illustrations.
12. Use "diagram" for processes and relationships.
13. Use "formula" for mathematical or scientific formulas.
14. Use "equation" for equations.
15. Use "physics" or "chemistry" when a scientific visual needs it.
16. Use "animation" when motion meaningfully explains a concept.
17. Use only the keys in the required JSON structure.
18. Do not include Markdown fences, introductions, or explanations.
19. Do not invent facts absent from the supplied material.
20. Keep the complete JSON response concise.
"""


def _get_setting(name, default=None):
    """Read a setting from environment variables or Streamlit secrets."""
    value = os.environ.get(name)

    if value:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def _extract_json(content):
    """Extract JSON even if the model accidentally adds code fences."""
    if not content or not isinstance(content, str):
        raise ValueError("The AI returned an empty response.")

    content = content.strip()

    # Remove Markdown code fences if present.
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content,
        flags=re.IGNORECASE,
    ).strip()

    # Recover the JSON object if there is extra text around it.
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("The AI response did not contain a JSON object.")

    return json.loads(content[start:end + 1])


def _normalize_plan(plan):
    """Validate the plan and standardize the scene fields."""
    if isinstance(plan, list):
        plan = {"title": "Educational Video", "scenes": plan}

    if not isinstance(plan, dict):
        raise ValueError("The AI returned an invalid video plan.")

    scenes = plan.get("scenes")

    if isinstance(scenes, dict):
        scenes = scenes.get("scenes", [])

    if not isinstance(scenes, list) or not scenes:
        raise ValueError("The AI did not return a valid scene list.")

    normalized = []

    for index, scene in enumerate(scenes, start=1):
        # Recover simple text-only scene responses.
        if isinstance(scene, str):
            scene = {"narration": scene}

        if not isinstance(scene, dict):
            raise ValueError(
                f"Scene {index} has an unsupported data format."
            )

        narration = scene.get("narration", "")

        if not isinstance(narration, str):
            narration = str(narration or "")

        narration = narration.strip()

        if not narration:
            raise ValueError(
                f"Scene {index} has no narration. Please try again."
            )

        visual_type = scene.get("visual_type", "ai_image")
        if not isinstance(visual_type, str):
            visual_type = "ai_image"

        image_prompt = scene.get("image_prompt", narration)
        if not isinstance(image_prompt, str):
            image_prompt = narration

        on_screen_text = scene.get("on_screen_text", "")
        if not isinstance(on_screen_text, str):
            on_screen_text = str(on_screen_text or "")

        animation = scene.get("animation", "zoom")
        if not isinstance(animation, str):
            animation = "zoom"

        normalized.append({
            "scene_id": index,
            "narration": narration,
            "visual_type": visual_type.strip().lower(),
            "image_prompt": image_prompt.strip() or narration,
            "on_screen_text": on_screen_text.strip(),
            "animation": animation.strip().lower(),
        })

    plan["title"] = str(
        plan.get("title", "Educational Video")
    ).strip()

    plan["scenes"] = normalized

    return plan


def create_video_plan(text, language, education_level, duration):
    """
    Generate a validated educational video plan.

    Uses a conservative output-token cap and retries temporary
    rate-limit failures. The input text is not sent to an image
    generation or video rendering service by this function.
    """
    api_key = _get_setting("LLM_API_KEY")
    base_url = _get_setting("LLM_BASE_URL")
    model = _get_setting("LLM_MODEL")

    if not api_key:
        raise ValueError("Missing LLM_API_KEY configuration.")

    if not base_url:
        raise ValueError("Missing LLM_BASE_URL configuration.")

    if not model:
        raise ValueError("Missing LLM_MODEL configuration.")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Please provide educational content.")

    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 120

    duration = max(15, min(duration, 600))

    # Estimate a suitable scene count from the lesson length and
    # target duration. This is a planning hint, not a fixed rule.
    word_count = len(text.split())
    scene_hint = max(
        3,
        (word_count + 39) // 40,
        (duration + 17) // 18,
    )
    scene_hint = min(scene_hint, 16)

    prompt = f"""
Language: {language}
Education level: {education_level}
Target video duration: {duration} seconds
Source word count: {word_count}
Suggested scene count: approximately {scene_hint}

Create a natural lesson that fits the requested duration.
Choose the final scene count based on the actual content.

Keep every scene's narration and visual description concise.
The total narration must fit the target duration.
Return the required JSON only.

Educational content:
{text}
"""

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=90.0,
        max_retries=0,
    )

    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.2,
                max_completion_tokens=MAX_OUTPUT_TOKENS,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            choice = response.choices[0]
            content = choice.message.content

            if not content or not content.strip():
                raise ValueError("The AI returned an empty scene plan.")

            # A truncated JSON response cannot safely be used.
            finish_reason = choice.finish_reason
            if finish_reason == "length":
                raise ValueError(
                    "The AI response reached its token limit. "
                    "Please try a shorter lesson or reduce the "
                    "amount of visual detail."
                )

            plan = _extract_json(content)
            return _normalize_plan(plan)

        except Exception as exc:
            last_error = exc

            status_code = getattr(exc, "status_code", None)
            error_text = str(exc).lower()

            is_rate_limit = (
                status_code == 429
                or "rate_limit_exceeded" in error_text
                or "rate limit" in error_text
            )

            if is_rate_limit and attempt < MAX_RETRIES:
                # A minute-based limit may need time to reset.
                # Do not retry immediately with the same request.
                time.sleep(65 * (attempt + 1))
                continue

            # Do not repeatedly retry invalid JSON or configuration
            # errors. Let the app display a useful message.
            raise RuntimeError(
                f"Video scene planning failed: {exc}"
            ) from exc

    raise RuntimeError(
        f"Video scene planning failed: {last_error}"
    )


def generate_scene_plan(
    educational_text,
    language="English",
    education_level="General",
    target_seconds=120,
):
    """
    Compatibility wrapper for the existing Streamlit app.
    The app expects a list of scenes, not the complete plan object.
    """
    plan = create_video_plan(
        text=educational_text,
        language=language,
        education_level=education_level,
        duration=target_seconds,
    )

    return plan["scenes"]
