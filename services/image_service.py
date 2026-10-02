from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from huggingface_hub import InferenceClient

from config.settings import (
    HF_TOKEN,
    IMAGE_MODEL,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
)


AIVA_STYLE = """
AIVA CHARACTER DESIGN:

Small friendly educational robot.

Appearance:
- rounded white body
- soft blue metallic accents
- large expressive blue eyes
- small blue glowing chest light
- small blue educational backpack
- friendly smile
- child-safe design
- premium 3D animated character

AIVA must look like the SAME CHARACTER
throughout the entire educational video.
"""


PRO_STYLE = """
VISUAL STYLE:

Premium 3D educational animation.

Modern educational technology aesthetic.

Cinematic classroom lighting.

Soft volumetric light.

Subtle depth of field.

Professional composition.

Clean modern environment.

Rich but controlled background.

High-quality 3D materials.

YouTube educational video quality.

16:9 landscape.

No watermark.

No logo.

No distorted text.

No readable text.
"""


def get_font(
    size: int,
):

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]

    for path in candidates:

        file = Path(path)

        if file.exists():

            return ImageFont.truetype(
                str(file),
                size=size,
            )

    return ImageFont.load_default()


def create_professional_fallback(
    title: str,
    text: str,
    scene_number: int,
    output_path: Path,
) -> Path:

    image = Image.new(
        "RGB",
        (
            VIDEO_WIDTH,
            VIDEO_HEIGHT,
    ),
        "#071426",
    )

    draw = ImageDraw.Draw(
        image
    )

    # Decorative circles.
    draw.ellipse(
        (
            850,
            -100,
            1450,
            500,
        ),
        fill="#12385C",
    )

    draw.ellipse(
        (
            -200,
            500,
            400,
            1100,
        ),
        fill="#102B48",
    )

    title_font = get_font(
        52
    )

    body_font = get_font(
        32
    )

    small_font = get_font(
        22
    )

    draw.text(
        (70, 55),
        title[:80],
        font=title_font,
        fill="white",
    )

    draw.text(
        (70, 135),
        f"LESSON • SCENE {scene_number}",
        font=small_font,
        fill="#8ED8FF",
    )

    # Word wrapping.
    words = text.split()

    lines = []

    current = ""

    for word in words:

        test = (
            f"{current} {word}"
        ).strip()

        if len(test) > 48:

            if current:
                lines.append(
                    current
                )

            current = word

        else:

            current = test

    if current:
        lines.append(
            current
        )

    y = 235

    for line in lines[:8]:

        draw.text(
            (80, y),
            line,
            font=body_font,
            fill="white",
        )

        y += 58

    image.save(
        output_path,
        quality=95,
    )

    return output_path


def generate_scene_image(
    prompt: str,
    on_screen_text: str,
    scene_title: str,
    scene_number: int,
    output_path: Path,
) -> tuple[Path, bool]:

    if not HF_TOKEN:

        return (
            create_professional_fallback(
                scene_title,
                on_screen_text,
                scene_number,
                output_path,
            ),
            False,
        )

    full_prompt = f"""
{AIVA_STYLE}

{PRO_STYLE}

SCENE DESCRIPTION:

{prompt}

IMPORTANT:

AIVA must retain the same:
- body shape
- eye design
- blue accents
- backpack
- chest light
- friendly appearance

Do not put any readable text inside the generated image.

Create a cinematic educational scene.
"""

    try:

        client = InferenceClient(
            api_key=HF_TOKEN
        )

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
            ),
            Image.Resampling.LANCZOS,
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

        return (
            create_professional_fallback(
                scene_title,
                on_screen_text,
                scene_number,
                output_path,
            ),
            False,
        )
