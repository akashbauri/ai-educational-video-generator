"""
Visual Decision Engine
----------------------

Decides the best visual teaching method for each educational scene.

Supported visual types:
- ai_image
- diagram
- chart
- formula
- whiteboard
- animation
- character
"""

import json
from typing import Any

from groq import Groq

from config.settings import GROQ_API_KEY, LLM_MODEL


# ============================================================
# SUPPORTED VISUAL TYPES
# ============================================================

VISUAL_TYPES = {
    "ai_image",
    "diagram",
    "chart",
    "formula",
    "whiteboard",
    "animation",
    "character",
}


# ============================================================
# SUPPORTED SUBJECTS
# ============================================================

SUBJECTS = {
    "general",
    "mathematics",
    "physics",
    "chemistry",
    "biology",
    "computer_science",
    "history",
    "geography",
}


# ============================================================
# VISUAL DECISION PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an expert educational visual director.

Your job is to decide HOW a concept should be visually taught.

You are NOT simply selecting an image.

Choose the visual method that gives students the clearest
understanding of the concept.

Available visual types:

1. ai_image
   Use for realistic or illustrative educational scenes.

2. diagram
   Use for relationships, structures, processes, systems,
   scientific diagrams and concept maps.

3. chart
   Use for numerical comparisons, trends and data.

4. formula
   Use for mathematical equations, scientific equations,
   calculations and symbolic explanations.

5. whiteboard
   Use for step-by-step teaching, mathematical solving,
   derivations and teacher-style explanations.

6. animation
   Use when objects, forces, motion, transformations,
   reactions or processes need to move.

7. character
   Use when AIVA should directly explain, introduce,
   question or summarize a concept.

SUBJECT RULES:

MATHEMATICS:
Prefer formula, whiteboard, chart, diagram or animation.

PHYSICS:
Prefer animation, diagram, formula, chart or whiteboard.

CHEMISTRY:
Prefer diagram, animation, formula or whiteboard.

BIOLOGY:
Prefer diagram, ai_image, animation or character.

HISTORY:
Prefer ai_image, timeline/diagram or character.

GEOGRAPHY:
Prefer map/diagram, chart, ai_image or animation.

COMPUTER SCIENCE:
Prefer diagram, animation, formula or whiteboard.

GENERAL:
Choose the most educational visual method.

IMPORTANT:

- Never choose an AI image when a precise mathematical,
  scientific or technical diagram would be better.
- Mathematical formulas must use formula or whiteboard.
- Physics motion should normally use animation.
- Chemical reactions should normally use animation or diagram.
- Step-by-step calculations should normally use whiteboard.
- Data should normally use charts.
- Use character scenes for introductions and summaries.
- Keep the visual appropriate for the student's education level.
- Avoid unnecessary visual complexity.

Return ONLY valid JSON.
"""


# ============================================================
# CLIENT
# ============================================================

def get_groq_client() -> Groq:
    """
    Create Groq client.
    """

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Add it to Streamlit Secrets."
        )

    return Groq(api_key=GROQ_API_KEY)


# ============================================================
# FALLBACK DECISION
# ============================================================

def fallback_decision(
    narration: str,
    subject: str = "general",
) -> dict[str, Any]:
    """
    Safe fallback when the LLM cannot make a decision.
    """

    text = narration.lower()

    if subject == "mathematics":
        if any(symbol in narration for symbol in ["=", "+", "-", "×", "÷", "²", "³"]):
            visual_type = "formula"
        else:
            visual_type = "whiteboard"

    elif subject == "physics":
        if any(
            word in text
            for word in [
                "move",
                "motion",
                "force",
                "speed",
                "velocity",
                "acceleration",
                "gravity",
            ]
        ):
            visual_type = "animation"
        else:
            visual_type = "diagram"

    elif subject == "chemistry":
        if any(
            word in text
            for word in [
                "reaction",
                "react",
                "molecule",
                "atom",
                "bond",
            ]
        ):
            visual_type = "animation"
        else:
            visual_type = "diagram"

    else:
        visual_type = "ai_image"

    return {
        "visual_type": visual_type,
        "subject": subject,
        "reason": "Fallback educational visual selection.",
        "animation": "fade",
        "visual_prompt": narration,
        "formula": "",
        "chart_data": [],
        "diagram_elements": [],
        "whiteboard_steps": [],
    }


# ============================================================
# CLEAN DECISION
# ============================================================

def clean_decision(
    decision: dict[str, Any],
    narration: str,
    subject: str,
) -> dict[str, Any]:
    """
    Validate and normalize the AI decision.
    """

    visual_type = str(
        decision.get("visual_type", "")
    ).strip().lower()

    if visual_type not in VISUAL_TYPES:
        visual_type = fallback_decision(
            narration=narration,
            subject=subject,
        )["visual_type"]

    normalized_subject = str(
        decision.get("subject", subject)
    ).strip().lower()

    if normalized_subject not in SUBJECTS:
        normalized_subject = subject

    animation = str(
        decision.get("animation", "fade")
    ).strip().lower()

    allowed_animations = {
        "fade",
        "slide",
        "zoom",
        "pan",
        "camera_push",
        "camera_pull",
        "write",
        "draw",
        "highlight",
        "move",
        "transform",
    }

    if animation not in allowed_animations:
        animation = "fade"

    chart_data = decision.get("chart_data", [])

    if not isinstance(chart_data, list):
        chart_data = []

    diagram_elements = decision.get(
        "diagram_elements",
        [],
    )

    if not isinstance(diagram_elements, list):
        diagram_elements = []

    whiteboard_steps = decision.get(
        "whiteboard_steps",
        [],
    )

    if not isinstance(whiteboard_steps, list):
        whiteboard_steps = []

    return {
        "visual_type": visual_type,
        "subject": normalized_subject,
        "reason": str(
            decision.get(
                "reason",
                "Educational visual selected by AI.",
            )
        ),
        "animation": animation,
        "visual_prompt": str(
            decision.get(
                "visual_prompt",
                narration,
            )
        ),
        "formula": str(
            decision.get(
                "formula",
                "",
            )
        ),
        "chart_data": chart_data,
        "diagram_elements": diagram_elements,
        "whiteboard_steps": whiteboard_steps,
    }


# ============================================================
# MAIN DECISION FUNCTION
# ============================================================

def decide_visual(
    narration: str,
    subject: str = "general",
    education_level: str = "Class 5",
    language: str = "English",
) -> dict[str, Any]:
    """
    Decide the best visual teaching method for one scene.
    """

    if not narration.strip():
        return fallback_decision(
            narration=narration,
            subject=subject,
        )

    subject = subject.lower().strip()

    if subject not in SUBJECTS:
        subject = "general"

    client = get_groq_client()

    user_prompt = f"""
Decide the best educational visual for this scene.

SUBJECT:
{subject}

EDUCATION LEVEL:
{education_level}

LANGUAGE:
{language}

NARRATION:
{narration}

Return JSON using exactly this structure:

{{
    "visual_type": "formula",
    "subject": "{subject}",
    "reason": "Why this visual method is best.",
    "animation": "write",
    "visual_prompt": "Detailed instructions for the visual renderer.",
    "formula": "",
    "chart_data": [],
    "diagram_elements": [],
    "whiteboard_steps": []
}}

Additional rules:

- If this is a mathematical equation, use formula or whiteboard.
- If it is a step-by-step calculation, use whiteboard.
- If it describes motion or force, consider animation.
- If it describes a scientific structure, consider diagram.
- If it contains numerical data, consider chart.
- If it needs a friendly explanation from AIVA, use character.
- Do not use ai_image for precise equations.
- Keep visual_prompt detailed enough for a renderer to understand.
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
            temperature=0.15,
            max_tokens=1200,
            response_format={
                "type": "json_object",
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Visual decision model returned empty content."
            )

        decision = json.loads(content)

        return clean_decision(
            decision=decision,
            narration=narration,
            subject=subject,
        )

    except Exception:
        return fallback_decision(
            narration=narration,
            subject=subject,
        )
