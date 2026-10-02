import json
import re
from typing import Any

from groq import Groq

from config.settings import (
    GROQ_API_KEY,
    LLM_MODEL,
    MAX_SCENES,
    MIN_SCENES,
)


SYSTEM_PROMPT = """
You are an expert educational video director.

Your job is to convert educational source material into
a short, accurate educational video plan.

IMPORTANT RULES:

1. Never invent facts.
2. Stay faithful to the supplied educational material.
3. Explain at the requested education level.
4. Use simple spoken language.
5. Each scene should teach one clear idea.
6. Keep narration natural for voice narration.
7. Use short on-screen text.
8. Image prompts must describe visuals only.
9. Do not put text inside image prompts.
10. The final scene must summarize the lesson.
11. Return ONLY valid JSON.
12. Do not use Markdown.
13. Do not put JSON inside ``` fences.

Required JSON format:

{
    "title": "Video title",
    "scenes": [
        {
            "scene_id": 1,
            "narration": "spoken narration",
            "visual_type": "ai_image",
            "image_prompt": "visual description",
            "on_screen_text": "short text",
            "animation": "zoom"
        }
    ]
}

Allowed visual_type values:

ai_image
animated_text
diagram
formula

Allowed animation values:

zoom
pan
fade
slide
"""


def extract_json(
    text: str,
) -> dict[str, Any]:

    text = text.strip()

    # Remove Markdown fences if model adds them.
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```\s*",
        "",
        text,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Groq/Qwen did not return valid JSON."
        )

    json_text = text[
        start:end + 1
    ]

    try:

        return json.loads(
            json_text
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "The AI returned malformed JSON."
        ) from exc


def clean_scene(
    scene: dict,
    index: int,
) -> dict:

    allowed_visuals = {
        "ai_image",
        "animated_text",
        "diagram",
        "formula",
    }

    allowed_animations = {
        "zoom",
        "pan",
        "fade",
        "slide",
    }

    visual_type = scene.get(
        "visual_type",
        "ai_image",
    )

    animation = scene.get(
        "animation",
        "zoom",
    )

    if visual_type not in allowed_visuals:
        visual_type = "ai_image"

    if animation not in allowed_animations:
        animation = "zoom"

    return {
        "scene_id": index,

        "narration": str(
            scene.get(
                "narration",
                "",
            )
        ).strip(),

        "visual_type": visual_type,

        "image_prompt": str(
            scene.get(
                "image_prompt",
                "",
            )
        ).strip(),

        "on_screen_text": str(
            scene.get(
                "on_screen_text",
                "",
            )
        ).strip()[:150],

        "animation": animation,
    }


def generate_scene_plan(
    educational_text: str,
    language: str,
    education_level: str,
    target_seconds: int,
) -> dict[str, Any]:

    # ========================================================
    # CHECK GROQ KEY
    # ========================================================

    if not GROQ_API_KEY:

        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add GROQ_API_KEY to Streamlit Secrets."
        )

    # ========================================================
    # CREATE GROQ CLIENT
    # ========================================================

    try:

        client = Groq(
            api_key=GROQ_API_KEY
        )

    except Exception as exc:

        raise RuntimeError(
            "Could not initialize Groq client."
        ) from exc

    # ========================================================
    # CALCULATE TARGET WORD COUNT
    # ========================================================

    target_words = round(
        target_seconds * 145 / 60
    )

    # ========================================================
    # USER PROMPT
    # ========================================================

    user_prompt = f"""
Create an educational video plan.

Language:
{language}

Education level:
{education_level}

Target duration:
approximately {target_seconds} seconds

Target narration length:
approximately {target_words} words

Number of scenes:
{MIN_SCENES} to {MAX_SCENES}

The video should be suitable for the selected
education level.

SOURCE EDUCATIONAL TEXT:

{educational_text[:18000]}
"""

    # ========================================================
    # GROQ REQUEST
    # ========================================================

    try:

        response = client.chat.completions.create(

            model=LLM_MODEL,

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            temperature=0.2,

            max_tokens=3000,

            response_format={
                "type": "json_object"
            },
        )

    except Exception as exc:

        raise RuntimeError(
            "Qwen inference through Groq failed.\n\n"
            "Check:\n"
            "1. GROQ_API_KEY\n"
            "2. Groq model availability\n"
            "3. Groq free-plan limits\n\n"
            f"Original error: {exc}"
        ) from exc

    # ========================================================
    # CHECK RESPONSE
    # ========================================================

    if not response.choices:

        raise RuntimeError(
            "Groq returned no response."
        )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise RuntimeError(
            "Groq returned an empty response."
        )

    # ========================================================
    # PARSE JSON
    # ========================================================

    plan = extract_json(
        content
    )

    # ========================================================
    # VALIDATE SCENES
    # ========================================================

    raw_scenes = plan.get(
        "scenes",
        [],
    )

    if not isinstance(
        raw_scenes,
        list,
    ):

        raise ValueError(
            "AI returned an invalid scenes list."
        )

    scenes = []

    for index, scene in enumerate(
        raw_scenes[:MAX_SCENES],
        start=1,
    ):

        if not isinstance(
            scene,
            dict,
        ):
            continue

        cleaned = clean_scene(
            scene,
            index,
        )

        if cleaned["narration"]:

            scenes.append(
                cleaned
            )

    # ========================================================
    # MINIMUM SCENE CHECK
    # ========================================================

    if len(scenes) < MIN_SCENES:

        raise ValueError(
            f"AI returned only "
            f"{len(scenes)} usable scenes. "
            f"Expected at least {MIN_SCENES}."
        )

    # ========================================================
    # RETURN FINAL PLAN
    # ========================================================

    return {
        "title": str(
            plan.get(
                "title",
                "Educational Lesson",
            )
        ).strip()[:120],

        "scenes": scenes,
    }
