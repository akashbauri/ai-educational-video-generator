def diagram_template(
    title: str,
    description: str,
) -> dict:

    return {
        "type": "diagram",
        "title": title,
        "description": description,
        "animation": "zoom",
    }
