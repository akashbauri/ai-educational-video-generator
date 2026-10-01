from pathlib import Path

from PIL import Image, ImageDraw

from services.image_service import get_font


def create_text_scene(
    title: str,
    text: str,
    output_path: Path,
    width: int = 1280,
    height: int = 720,
) -> Path:

    image = Image.new(
        "RGB",
        (
            width,
            height,
        ),
        "white",
    )

    draw = ImageDraw.Draw(
        image
    )

    title_font = get_font(
        48
    )

    body_font = get_font(
        32
    )

    draw.text(
        (60, 60),
        title[:80],
        font=title_font,
        fill="black",
    )

    draw.text(
        (70, 190),
        text[:500],
        font=body_font,
        fill="black",
    )

    image.save(
        output_path,
        quality=95,
    )

    return output_path
