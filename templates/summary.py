def summary_template(
    title: str,
    summary: str,
) -> dict:

    return {
        "type": "summary",
        "title": title,
        "summary": summary,
        "animation": "fade",
    }
