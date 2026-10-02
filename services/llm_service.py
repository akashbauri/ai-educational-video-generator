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


# ============================================================
# AIVA CHARACTER DEFINITION
# ============================================================

AIVA_CHARACTER = """
AIVA is the main recurring character.

AIVA must always look consistent:

- small friendly educational robot
- rounded white body
- soft blue accents
- large expressive blue eyes
- small blue glowing chest light
- small blue educational backpack
- friendly child-safe appearance
- cute but professional
- no weapons
- no scary appearance
- no realistic human face

IMPORTANT:
Keep AIVA's physical appearance consistent across every scene.
"""


# ============================================================
# VISUAL STYLE
# ============================================================

VISUAL_STYLE = """
Visual style:

- premium 3D educational animation
- modern educational technology aesthetic
- cinematic but child-friendly
- professional classroom visuals
- soft studio lighting
- subtle depth of field
- clean composition
- rich but not distracting background
- realistic 3D materials
- high visual quality
- 16:9 landscape composition
- suitable for YouTube educational videos
- suitable for Class 5 students
- no watermark
- no logo
- no distorted objects
- no unnecessary text
- NO readable text inside generated images
"""


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = f"""
You are a professional educational video director.

You create production-ready educational video scenes.

{AIVA_CHARACTER}

{VISUAL_STYLE}

IMPORTANT RULES:

1. Never invent facts.
2. Stay faithful to the source material.
3. Use simple language appropriate for the education level.
4. The narration must contain complete sentences.
5. NEVER remove important information from the source.
6. Every sentence generated for narration must be spoken.
7. Do not create narration that is longer than the requested duration.
8. Do not create extremely short narration.
9. Every scene should have one clear educational purpose.
10. Maintain continuity between scenes.
11. AIVA must look consistent whenever she appears.
12. Use visual storytelling rather than random pictures.
13. Generated images must NOT contain readable text.
14. On-screen text will be added separately by the application.
15. Keep on-screen text short.
16. Do not put subtitles inside image prompts.
17. Use professional visual composition.
18. Use different camera compositions between scenes.
19. Use classroom, laboratory, digital learning or technology environments
    when appropriate.
20. The final scene should summarize the lesson.
21. Return ONLY valid JSON.

Allowed visual types:

ai_image
diagram
formula
animated_text

Allowed animations:

zoom
pan
fade
slide
camera_push
camera_pull

Required JSON:

{{
    "title": "Video title",
    "style": "professional educational 3D animation",
    "character": "AIVA",
    "scenes": [
        {{
            "scene_id": 1,
            "narration": "Complete spoken narration.",
            "visual_type": "ai_image",
            "image_prompt": "Detailed visual description without readable text.",
            "on_screen_text": "Short educational text",
            "animation": "camera_push",
            "camera_angle": "medium shot",
            "visual_focus": "What the viewer should understand"
        }}
    ]
}}
"""


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(
    text: str,
) -> dict[str, Any]:

    text = text.strip()

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
            "AI did not return valid JSON."
        )

    return json.loads(
        text[start:end + 1]
    )


# ============================================================
# CLEAN SCENE
# ============================================================

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
        "camera_push",
        "camera_pull",
    }

    visual_type = scene.get(
        "visual_type",
        "ai_image",
    )

    animation = scene.get(
        "animation",
        "camera_push",
    )

    if visual_type not in allowed_visuals:
        visual_type = "ai_image"

    if animation not in allowed_animations:
        animation = "camera_push"

    narration = str(
        scene.get(
            "narration",
            "",
        )
    ).strip()

    image_prompt = str(
        scene.get(
            "image_prompt",
            "",
        )
    ).strip()

    on_screen_text = str(
        scene.get(
            "on_screen_text",
            "",
        )
    ).strip()

    # Add AIVA consistency instructions automatically.
    image_prompt = f"""
{AIVA_CHARACTER}

{VISUAL_STYLE}

SCENE:
{image_prompt}

IMPORTANT:
AIVA's appearance must remain consistent with previous scenes.
Do not add readable text to the image.
""".strip()

    return {
        "scene_id": index,
        "narration": narration,
        "visual_type": visual_type,
        "image_prompt": image_prompt,
        "on_screen_text": on_screen_text[:120],
        "animation": animation,
        "camera_angle": str(
            scene.get(
                "camera_angle",
                "medium shot",
            )
        ),
        "visual_focus": str(
            scene.get(
                "visual_focus",
                "",
            )
        ),
    }


# ============================================================
# MAIN SCENE GENERATOR
# ============================================================

def generate_scene_plan(
    educational_text: str,
    language: str,
    education_level: str,
    target_seconds: int,
) -> dict[str, Any]:

    if not GROQ_API_KEY:

        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Add it to Streamlit Secrets."
        )

    client = Groq(
        api_key=GROQ_API_KEY
    )

    target_words = round(
        target_seconds * 130 / 60
    )

    user_prompt = f"""
Create a professional educational video.

LANGUAGE:
{language}

EDUCATION LEVEL:
{education_level}

TARGET DURATION:
{target_seconds} seconds

TARGET NARRATION:
Approximately {target_words} words.

IMPORTANT:
Every word written in "narration" will be spoken by the
AI voice.

Do not put important information outside narration.

Create {MIN_SCENES} to {MAX_SCENES} scenes.

Each scene should contain:

1. Complete narration.
2. Strong visual storytelling.
3. Short on-screen text.
4. Camera direction.
5. Animation.
6. Visual focus.

Make the video feel like a professional educational
YouTube animation rather than a slideshow.

SOURCE MATERIAL:

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

            temperature=0.25,

            max_tokens=3500,

            response_format={
                "type": "json_object"
            },
        )

    except Exception as exc:

        raise RuntimeError(
            "Qwen scene generation failed through Groq.\n\n"
            f"{exc}"
        ) from exc

    if not response.choices:

        raise RuntimeError(
            "The AI returned no response."
        )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    if not content:

        raise RuntimeError(
            "The AI returned empty content."
        )

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
            "Invalid scenes returned by AI."
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
            f"AI created only {len(scenes)} usable scenes."
        )

    return {
        "title": str(
            plan.get(
                "title",
                "AI Educational Lesson",
            )
        ).strip()[:120],

        "style": str(
            plan.get(
                "style",
                "professional educational animation",
            )
        ),

        "character": "AIVA",

        "scenes": scenes,
    }
