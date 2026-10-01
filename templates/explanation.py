def explanation_template(
    title: str,
    explanation: str,
) -> dict:

    return {
        "type": "explanation",
        "title": title,
        "text": explanation,
        "animation": "slide",
    }
