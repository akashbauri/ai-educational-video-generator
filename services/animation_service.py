from pathlib import Path
import math
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1280
HEIGHT = 720
FPS = 24


# ---------------------------------------------------------
# FONT SYSTEM
# ---------------------------------------------------------

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/opentype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def get_font(size: int, bold: bool = False):
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_CANDIDATES

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# ---------------------------------------------------------
# BASIC DRAWING HELPERS
# ---------------------------------------------------------

def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def draw_centered(draw, text, y, font, fill="white"):
    bbox = draw.textbbox((0, 0), text, font=font)
    width = bbox[2] - bbox[0]

    draw.text(
        ((WIDTH - width) / 2, y),
        text,
        font=font,
        fill=fill,
    )


def draw_arrow(draw, start, end, fill="white", width=6):
    x1, y1 = start
    x2, y2 = end

    draw.line(
        [x1, y1, x2, y2],
        fill=fill,
        width=width,
    )

    angle = math.atan2(y2 - y1, x2 - x1)

    size = 18

    p1 = (
        x2 - size * math.cos(angle - math.pi / 6),
        y2 - size * math.sin(angle - math.pi / 6),
    )

    p2 = (
        x2 - size * math.cos(angle + math.pi / 6),
        y2 - size * math.sin(angle + math.pi / 6),
    )

    draw.polygon(
        [(x2, y2), p1, p2],
        fill=fill,
    )


# ---------------------------------------------------------
# BASE CANVAS
# ---------------------------------------------------------

def create_canvas():
    return Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (13, 22, 38),
    )


# ---------------------------------------------------------
# FORMULA DRAWING
# ---------------------------------------------------------

def render_formula_frame(
    formula: str,
    explanation: str,
    progress: float,
):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)
    formula_font = get_font(72, True)
    body_font = get_font(30)

    draw_centered(
        draw,
        "Let's understand the formula",
        55,
        title_font,
    )

    # Progressive formula writing
    visible_chars = max(
        1,
        int(len(formula) * progress),
    )

    visible_formula = formula[:visible_chars]

    bbox = draw.textbbox(
        (0, 0),
        visible_formula,
        font=formula_font,
    )

    formula_width = bbox[2] - bbox[0]

    draw.text(
        (
            (WIDTH - formula_width) / 2,
            240,
        ),
        visible_formula,
        font=formula_font,
        fill=(90, 200, 255),
    )

    # underline animation
    underline_progress = ease_in_out(progress)

    underline_width = formula_width * underline_progress

    draw.line(
        [
            (
                WIDTH / 2 - formula_width / 2,
                335,
            ),
            (
                WIDTH / 2 - formula_width / 2 + underline_width,
                335,
            ),
        ],
        fill=(255, 210, 80),
        width=6,
    )

    # Explanation
    draw.text(
        (100, 430),
        explanation[:180],
        font=body_font,
        fill="white",
    )

    return image


# ---------------------------------------------------------
# EQUATION STEP-BY-STEP
# ---------------------------------------------------------

def render_equation_steps(
    steps,
    progress: float,
):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)
    formula_font = get_font(58, True)
    small_font = get_font(26)

    draw_centered(
        draw,
        "Step-by-Step Solution",
        45,
        title_font,
    )

    total = len(steps)

    if total == 0:
        return image

    visible = max(
        1,
        min(
            total,
            int(math.ceil(progress * total)),
        ),
    )

    start_y = 150

    for i in range(visible):
        step = steps[i]

        y = start_y + i * 105

        # Step number
        draw.ellipse(
            (90, y, 145, y + 55),
            fill=(60, 150, 230),
        )

        number_font = get_font(25, True)

        draw.text(
            (108, y + 12),
            str(i + 1),
            font=number_font,
            fill="white",
        )

        draw.text(
            (180, y + 5),
            step,
            font=formula_font,
            fill="white",
        )

        if i < visible - 1:
            draw_arrow(
                draw,
                (120, y + 65),
                (120, y + 95),
                fill=(120, 150, 180),
                width=3,
            )

    draw.text(
        (90, 640),
        "Follow each step carefully.",
        font=small_font,
        fill=(190, 205, 220),
    )

    return image


# ---------------------------------------------------------
# DIAGRAM DRAWING
# ---------------------------------------------------------

def render_diagram_frame(
    title,
    nodes,
    progress,
):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)
    node_font = get_font(27, True)

    draw_centered(
        draw,
        title,
        45,
        title_font,
    )

    if not nodes:
        return image

    count = len(nodes)

    center_x = WIDTH // 2
    center_y = 380

    radius = 210

    positions = []

    for i in range(count):
        angle = (
            2 * math.pi * i / count
        ) - math.pi / 2

        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)

        positions.append((x, y))

    visible_nodes = max(
        1,
        min(
            count,
            int(math.ceil(progress * count)),
        ),
    )

    # Connections
    for i in range(visible_nodes):
        if i + 1 < visible_nodes:
            draw_arrow(
                draw,
                positions[i],
                positions[i + 1],
                fill=(90, 160, 220),
                width=5,
            )

    # Nodes
    for i in range(visible_nodes):
        x, y = positions[i]

        r = 65

        draw.ellipse(
            (
                x - r,
                y - r,
                x + r,
                y + r,
            ),
            fill=(40, 90, 150),
            outline=(120, 210, 255),
            width=5,
        )

        text = str(
            nodes[i]
        )[:18]

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=node_font,
        )

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        draw.text(
            (
                x - tw / 2,
                y - th / 2,
            ),
            text,
            font=node_font,
            fill="white",
        )

    return image


# ---------------------------------------------------------
# PHYSICS: FORCE + MOTION
# ---------------------------------------------------------

def render_physics_frame(
    progress,
    force=70,
):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)
    label_font = get_font(30, True)

    draw_centered(
        draw,
        "Force and Motion",
        45,
        title_font,
    )

    # Ground
    draw.line(
        [(100, 520), (1180, 520)],
        fill=(180, 190, 205),
        width=5,
    )

    # Moving object
    movement = ease_in_out(progress)

    x = lerp(
        200,
        900,
        movement,
    )

    y = 430

    draw.rounded_rectangle(
        (
            x - 70,
            y - 50,
            x + 70,
            y + 50,
        ),
        radius=18,
        fill=(60, 150, 230),
        outline=(150, 220, 255),
        width=4,
    )

    # wheels
    draw.ellipse(
        (x - 50, y + 35, x - 15, y + 70),
        fill=(30, 30, 40),
    )

    draw.ellipse(
        (x + 15, y + 35, x + 50, y + 70),
        fill=(30, 30, 40),
    )

    # Force arrow
    draw_arrow(
        draw,
        (x + 80, y),
        (x + 80 + force, y),
        fill=(255, 100, 100),
        width=8,
    )

    draw.text(
        (x + 85, y - 55),
        "Force",
        font=label_font,
        fill=(255, 130, 130),
    )

    draw.text(
        (100, 610),
        "Force changes the motion of an object.",
        font=label_font,
        fill="white",
    )

    return image


# ---------------------------------------------------------
# CHEMISTRY: MOLECULE FORMATION
# ---------------------------------------------------------

def render_chemistry_frame(progress):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)
    atom_font = get_font(32, True)

    draw_centered(
        draw,
        "How Water Molecules Form",
        45,
        title_font,
    )

    # Hydrogen positions
    start_x = 260
    oxygen_x = 640
    end_x = 1020

    y = 360

    # Move atoms toward final positions
    p = ease_in_out(progress)

    h1_x = lerp(start_x, 520, p)
    h2_x = lerp(end_x, 760, p)

    # Hydrogen
    draw.ellipse(
        (h1_x - 55, y - 55, h1_x + 55, y + 55),
        fill=(220, 225, 235),
        outline=(120, 160, 210),
        width=5,
    )

    draw_centered_atom(
        draw,
        "H",
        h1_x,
        y,
        atom_font,
    )

    # Oxygen
    draw.ellipse(
        (585, y - 80, 695, y + 80),
        fill=(230, 90, 90),
        outline=(255, 150, 150),
        width=6,
    )

    draw_centered_atom(
        draw,
        "O",
        oxygen_x,
        y,
        atom_font,
    )

    # Second hydrogen
    draw.ellipse(
        (h2_x - 55, y - 55, h2_x + 55, y + 55),
        fill=(220, 225, 235),
        outline=(120, 160, 210),
        width=5,
    )

    draw_centered_atom(
        draw,
        "H",
        h2_x,
        y,
        atom_font,
    )

    # Bonds appear gradually
    if progress > 0.55:
        bond_progress = (progress - 0.55) / 0.45

        draw.line(
            [
                (h1_x + 55, y),
                (
                    585,
                    y,
                ),
            ],
            fill=(250, 210, 100),
            width=max(
                2,
                int(8 * bond_progress),
            ),
        )

        draw.line(
            [
                (695, y),
                (
                    h2_x - 55,
                    y,
                ),
            ],
            fill=(250, 210, 100),
            width=max(
                2,
                int(8 * bond_progress),
            ),
        )

    if progress > 0.8:
        draw_centered(
            draw,
            "H₂O",
            520,
            get_font(58, True),
            fill=(100, 210, 255),
        )

    return image


def draw_centered_atom(
    draw,
    text,
    x,
    y,
    font,
):
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    draw.text(
        (
            x - tw / 2,
            y - th / 2 - 5,
        ),
        text,
        font=font,
        fill=(20, 30, 45),
    )


# ---------------------------------------------------------
# AIVA MOVEMENT
# ---------------------------------------------------------

def render_aiva_frame(
    progress,
    expression="happy",
):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)

    draw_centered(
        draw,
        "Meet AIVA",
        45,
        title_font,
    )

    # Gentle floating movement
    float_y = math.sin(progress * math.pi * 2) * 10

    cx = WIDTH // 2
    cy = 390 + float_y

    # Body
    draw.rounded_rectangle(
        (
            cx - 130,
            cy - 100,
            cx + 130,
            cy + 130,
        ),
        radius=45,
        fill=(235, 242, 248),
        outline=(100, 180, 230),
        width=6,
    )

    # Head
    draw.rounded_rectangle(
        (
            cx - 150,
            cy - 240,
            cx + 150,
            cy - 60,
        ),
        radius=55,
        fill=(245, 248, 252),
        outline=(100, 180, 230),
        width=6,
    )

    # Eyes
    eye_y = cy - 155

    draw.ellipse(
        (
            cx - 90,
            eye_y - 30,
            cx - 35,
            eye_y + 30,
        ),
        fill=(70, 180, 255),
    )

    draw.ellipse(
        (
            cx + 35,
            eye_y - 30,
            cx + 90,
            eye_y + 30,
        ),
        fill=(70, 180, 255),
    )

    # Chest light
    pulse = 0.5 + 0.5 * math.sin(
        progress * math.pi * 4
    )

    size = int(22 + 8 * pulse)

    draw.ellipse(
        (
            cx - size,
            cy - 5 - size,
            cx + size,
            cy - 5 + size,
        ),
        fill=(80, 190, 255),
    )

    # Backpack
    draw.rounded_rectangle(
        (
            cx - 180,
            cy - 30,
            cx - 125,
            cy + 100,
        ),
        radius=15,
        fill=(70, 130, 200),
    )

    return image


# ---------------------------------------------------------
# GENERIC OBJECT MOVEMENT
# ---------------------------------------------------------

def render_object_motion_frame(
    title,
    progress,
    object_label="Object",
):
    image = create_canvas()
    draw = ImageDraw.Draw(image)

    title_font = get_font(42, True)
    label_font = get_font(30, True)

    draw_centered(
        draw,
        title,
        45,
        title_font,
    )

    p = ease_in_out(progress)

    x = lerp(160, 1080, p)

    y = 370

    # trail
    for i in range(8):
        trail_p = max(
            0,
            p - i * 0.025,
        )

        trail_x = lerp(
            160,
            1080,
            trail_p,
        )

        radius = max(
            5,
            22 - i * 2,
        )

        draw.ellipse(
            (
                trail_x - radius,
                y - radius,
                trail_x + radius,
                y + radius,
            ),
            fill=(70, 120, 170),
        )

    draw.ellipse(
        (
            x - 35,
            y - 35,
            x + 35,
            y + 35,
        ),
        fill=(70, 190, 255),
        outline=(200, 240, 255),
        width=5,
    )

    draw_centered(
        draw,
        object_label,
        540,
        500,
        label_font,
    )

    return image


# ---------------------------------------------------------
# WRITE FRAMES TO MP4
# ---------------------------------------------------------

def create_animation_video(
    animation_type: str,
    output_path: Path,
    duration: float,
    title: str = "",
    formula: str = "",
    explanation: str = "",
    steps=None,
    nodes=None,
    subject: str = "",
):
    steps = steps or []
    nodes = nodes or []

    frame_count = max(
        1,
        int(duration * FPS),
    )

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix="animation_frames_"
        )
    )

    try:
        for frame_number in range(frame_count):

            progress = (
                frame_number /
                max(1, frame_count - 1)
            )

            if animation_type == "formula":
                frame = render_formula_frame(
                    formula=formula or title,
                    explanation=explanation,
                    progress=progress,
                )

            elif animation_type == "equation":
                frame = render_equation_steps(
                    steps=steps,
                    progress=progress,
                )

            elif animation_type == "diagram":
                frame = render_diagram_frame(
                    title=title or "Concept Diagram",
                    nodes=nodes,
                    progress=progress,
                )

            elif animation_type == "physics":
                frame = render_physics_frame(
                    progress=progress,
                )

            elif animation_type == "chemistry":
                frame = render_chemistry_frame(
                    progress=progress,
                )

            elif animation_type == "aiva":
                frame = render_aiva_frame(
                    progress=progress,
                )

            else:
                frame = render_object_motion_frame(
                    title=title or "Learning Animation",
                    progress=progress,
                    object_label="Concept",
                )

            frame_path = (
                temp_dir /
                f"frame_{frame_number:05d}.png"
            )

            frame.save(
                frame_path,
                quality=95,
            )

        command = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(temp_dir / "frame_%05d.png"),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Animation rendering failed:\n"
                + result.stderr[-3000:]
            )

        return output_path

    finally:
        for frame in temp_dir.glob("*.png"):
            try:
                frame.unlink()
            except Exception:
                pass

        try:
            temp_dir.rmdir()
        except Exception:
            pass
