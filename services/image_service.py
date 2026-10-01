from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from config.settings import (
    HF_TOKEN,
    IMAGE_MODEL,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)


def get_font(size: int):

    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]

    for font_path in font_candidates:

        path = Path(
            font_path
        )

        if path.exists():

            return ImageFont.truetype(
                str(path),
                size=size,
            )

    return ImageFont.load_default()


def create_fallback_slide(
    title: str,
    text: str,
    output_path: Path,
) -> Path:

    image = Image.new(
        "RGB",
        (
            VIDEO_WIDTH,
            VIDEO_HEIGHT,
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
        30
    )

    draw.text(
        (70, 60),
        title[:80],
        font=title_font,
        fill="black",
    )

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            f"{current_line} {word}"
        ).strip()

        if len(test_line) > 52:

            if current_line:
                lines.append(
                    current_line
                )

            current_line = word

        else:

            current_line = test_line

    if current_line:
        lines.append(
            current_line
        )

    y = 190

    for line in lines[:10]:

        draw.text(
            (80, y),
            line,
            font=body_font,
            fill="black",
        )

        y += 55

    image.save(
        output_path,
        quality=95,
    )

    return output_path


def generate_scene_image(
    prompt: str,
    on_screen_text: str,
    scene_title: str,
    output_path: Path,
) -> tuple[Path, bool]:

    if not HF_TOKEN:

        return (
            create_fallback_slide(
                scene_title,
                on_screen_text,
                output_path,
            ),
            False,
        )

    try:

        client = InferenceClient(
            api_key=HF_TOKEN
        )

        full_prompt = f"""
Educational illustration for a classroom video.

{prompt}

Style:
clean educational illustration,
professional,
clear subject,
good composition,
high quality,
classroom friendly,
no watermark,
no logo,
no readable text.
"""

        image = client.text_to_image(
            prompt=full_prompt,
            model=IMAGE_MODEL,
        )

        image = image.convert(
            "RGB"
        )

        image = image.resize(
            (
                VIDEO_WIDTH,
                VIDEO_HEIGHT,
            )
        )

        image.save(
            output_path,
            quality=95,
        )

        return (
            output_path,
            True,
        )

    except Exception:

        # IMPORTANT:
        # The video should still be able to render
        # if free image inference is temporarily unavailable.

        return (
            create_fallback_slide(
                scene_title,
                on_screen_text,
                output_path,
            ),
            False,
        )
