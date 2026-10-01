import json
import re
from typing import Any

from huggingface_hub import InferenceClient

from config.settings import (
    HF_TOKEN,
    LLM_MODEL,
    MAX_SCENES,
    MIN_SCENES,
)


SYSTEM_PROMPT = """
You are an expert educational video director.

Your job is to convert educational source material into a
short, accurate educational video plan.

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

Required JSON:

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


def extract_json(text: str) -> dict[str, Any]:

    text = text.strip()

    # Remove Markdown JSON fences if the model accidentally adds them.
    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"^```",
        "",
        text,
    )

    text = re.sub(
        r"```$",
        "",
        text,
    )

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Qwen did not return a valid JSON object."
        )

    json_text = text[
        start:end + 1
    ]

    return json.loads(
        json_text
    )


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

    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is missing. "
            "Add HF_TOKEN to Streamlit Secrets."
        )

    client = InferenceClient(
        api_key=HF_TOKEN
    )

    target_words = round(
        target_seconds * 145 / 60
    )

    user_prompt = f"""
Create an educational video plan.

Language:
{language}

Education level:
{education_level}

Target duration:
approximately {target_seconds} seconds

Target total narration length:
approximately {target_words} words

Number of scenes:
{MIN_SCENES} to {MAX_SCENES}

SOURCE EDUCATIONAL TEXT:

{educational_text[:18000]}
"""

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

            max_tokens=2400,

            temperature=0.2,
        )

    except Exception as exc:

        raise RuntimeError(
            "Qwen inference failed. "
            "Check HF_TOKEN, model access, or the "
            "free inference allowance.\n\n"
            f"Original error: {exc}"
        ) from exc

    if not response.choices:
        raise RuntimeError(
            "Qwen returned no response."
        )

    content = response.choices[
        0
    ].message.content

    plan = extract_json(
        content
    )

    raw_scenes = plan.get(
        "scenes",
        [],
    )

    if not isinstance(
        raw_scenes,
        list,
    ):
        raise ValueError(
            "Qwen returned an invalid scenes list."
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

    if len(scenes) < MIN_SCENES:

        raise ValueError(
            f"Qwen returned only "
            f"{len(scenes)} usable scenes. "
            f"Please provide more educational content."
        )

    return {
        "title": str(
            plan.get(
                "title",
                "Educational Lesson",
            )
        ).strip()[:120],

        "scenes": scenes,
    }
