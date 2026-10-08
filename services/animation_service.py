import json

from groq import Groq

from config.settings import GROQ_API_KEY, LLM_MODEL


VISUAL_TYPES = {
    "ai_image",
    "formula",
    "equation",
    "diagram",
    "chart",
    "whiteboard",
    "physics",
    "chemistry",
    "aiva",
    "animation",
}


def decide_visual(
    narration: str,
    subject: str,
    education_level: str,
    language: str,
):
    client = Groq(
        api_key=GROQ_API_KEY
    )

    prompt = f"""
You are an expert educational video visual director.

Topic subject:
{subject}

Education level:
{education_level}

Language:
{language}

Narration:
{narration}

Choose the BEST visual type.

Allowed types:

ai_image
formula
equation
diagram
chart
whiteboard
physics
chemistry
aiva
animation

Rules:

Use formula when the scene teaches a formula.

Use equation when solving mathematics step-by-step.

Use diagram for processes, systems and relationships.

Use chart for numerical data.

Use physics for force, motion, gravity, vectors,
electricity, waves, optics or mechanics.

Use chemistry for atoms, molecules, bonds,
chemical reactions and equations.

Use aiva when AIVA should appear as the main teacher.

Use animation when an object should visibly move.

Use ai_image for general educational scenes.

Return ONLY JSON:

{{
    "visual_type": "formula",
    "visual_prompt": "",
    "formula": "",
    "explanation": "",
    "diagram_elements": [],
    "whiteboard_steps": [],
    "equation_steps": [],
    "animation_objects": [],
    "chart_data": []
}}
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an educational visual "
                    "planning engine."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.15,
        max_tokens=1500,
        response_format={
            "type": "json_object"
        },
    )

    result = json.loads(
        response.choices[0].message.content
    )

    if (
        result.get("visual_type")
        not in VISUAL_TYPES
    ):
        result["visual_type"] = "ai_image"

    return result
