import os
import json
from openai import OpenAI


SYSTEM_PROMPT = """
You are an educational video director.

Your job is to convert educational material
into a short educational video plan.

Return ONLY valid JSON.

Use this structure:

{
    "title": "Video title",
    "scenes": [
        {
            "scene_id": 1,
            "narration": "Narration...",
            "visual_type": "ai_image",
            "image_prompt": "Image description...",
            "on_screen_text": "Short text",
            "animation": "zoom"
        }
    ]
}

Rules:

1. Use simple educational language.
2. Preserve important facts.
3. Create 6 to 10 scenes.
4. Keep narration suitable for approximately 2 minutes.
5. Use ai_image when an illustration helps.
6. Use diagram for processes.
7. Use formula for mathematics/science formulas.
8. Keep on-screen text short.
"""


def create_video_plan(
    text,
    language,
    education_level,
    duration
):

    api_key = os.environ["LLM_API_KEY"]
    base_url = os.environ["LLM_BASE_URL"]
    model = os.environ["LLM_MODEL"]

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    prompt = f"""
Language: {language}

Education level:
{education_level}

Target duration:
{duration} seconds

Educational content:

{text}
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    return json.loads(content)
