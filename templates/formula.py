def formula_template(
    title: str,
    formula: str,
) -> dict:

    return {
        "type": "formula",
        "title": title,
        "formula": formula,
        "animation": "fade",
    }
