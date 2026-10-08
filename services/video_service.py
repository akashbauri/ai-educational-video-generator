from pathlib import Path
import subprocess
import tempfile


WIDTH = 1280
HEIGHT = 720
FPS = 24


# ============================================================
# FFmpeg HELPER
# ============================================================

def run_ffmpeg(
    command: list[str],
) -> None:

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg failed:\n\n"
            + result.stderr[-5000:]
        )


# ============================================================
# IMAGE SCENE
# ============================================================

def render_scene(
    image_path: Path,
    audio_path: Path,
    output_path: Path,
    duration: float,
    animation: str = "zoom",
) -> Path:

    frames = max(
        1,
        int(duration * FPS),
    )

    # --------------------------------------------------------
    # PAN
    # --------------------------------------------------------

    if animation == "pan":

        zoom_filter = (
            "zoompan="
            "z='min(zoom+0.0005,1.08)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS}"
        )

    # --------------------------------------------------------
    # SLIDE
    # --------------------------------------------------------

    elif animation == "slide":

        zoom_filter = (
            "zoompan="
            "z='1.04':"
            f"x='(iw-iw/zoom)*on/{frames}':"
            "y='(ih-ih/zoom)/2':"
            f"d={frames}:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS}"
        )

    # --------------------------------------------------------
    # CAMERA PUSH / ZOOM
    # --------------------------------------------------------

    elif animation in {
        "camera_push",
        "zoom",
        "fade",
    }:

        zoom_filter = (
            "zoompan="
            "z='min(zoom+0.0005,1.10)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS}"
        )

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    else:

        zoom_filter = (
            "zoompan="
            "z='min(zoom+0.0004,1.06)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s={WIDTH}x{HEIGHT}:"
            f"fps={FPS}"
        )


    command = [
        "ffmpeg",
        "-y",

        "-loop",
        "1",

        "-i",
        str(image_path),

        "-i",
        str(audio_path),

        "-vf",
        zoom_filter,

        "-t",
        f"{duration:.3f}",

        "-r",
        str(FPS),

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-shortest",

        str(output_path),
    ]

    run_ffmpeg(command)

    return output_path


# ============================================================
# ADD AUDIO TO TRUE ANIMATION
# ============================================================

def add_audio_to_animation(
    animation_path: Path,
    audio_path: Path,
    output_path: Path,
    duration: float,
) -> Path:

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(animation_path),

        "-i",
        str(audio_path),

        "-t",
        f"{duration:.3f}",

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-shortest",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    run_ffmpeg(command)

    return output_path


# ============================================================
# CONCATENATE SCENES
# ============================================================

def concat_scenes(
    scene_files: list[Path],
    output_path: Path,
    work_dir: Path,
) -> Path:

    concat_file = (
        work_dir /
        "concat.txt"
    )

    lines = []

    for scene_file in scene_files:

        safe_path = (
            str(
                scene_file.resolve()
            )
            .replace(
                "'",
                "'\\''",
            )
        )

        lines.append(
            f"file '{safe_path}'"
        )

    concat_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    command = [
        "ffmpeg",
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-c",
        "copy",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    run_ffmpeg(command)

    return output_path


# ============================================================
# BACKGROUND AUDIO
# ============================================================

def create_background_audio(
    output_path: Path,
    duration: float,
) -> Path:

    filter_complex = (
        "[0:a]volume=0.018[a0];"
        "[1:a]volume=0.012[a1];"
        "[a0][a1]"
        "amix=inputs=2:"
        "duration=longest"
    )

    command = [
        "ffmpeg",
        "-y",

        "-f",
        "lavfi",

        "-i",
        (
            "sine="
            "frequency=220:"
            "sample_rate=44100"
        ),

        "-f",
        "lavfi",

        "-i",
        (
            "sine="
            "frequency=330:"
            "sample_rate=44100"
        ),

        "-filter_complex",
        filter_complex,

        "-t",
        f"{duration:.3f}",

        "-c:a",
        "aac",

        "-b:a",
        "96k",

        str(output_path),
    ]

    run_ffmpeg(command)

    return output_path


# ============================================================
# SUBTITLES + MUSIC
# ============================================================

def add_subtitles_and_music(
    video_path: Path,
    subtitle_path: Path,
    music_path: Path,
    output_path: Path,
) -> Path:

    subtitle_path_string = (
        str(
            subtitle_path.resolve()
        )
        .replace(
            "\\",
            "/",
        )
        .replace(
            ":",
            "\\:",
        )
        .replace(
            "'",
            "\\'",
        )
    )

    subtitle_filter = (
        f"subtitles='{subtitle_path_string}':"
        "force_style='"
        "FontName=DejaVu Sans,"
        "FontSize=18,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=35'"
    )

    command = [
        "ffmpeg",
        "-y",

        "-i",
        str(video_path),

        "-i",
        str(music_path),

        "-vf",
        subtitle_filter,

        "-filter_complex",
        (
            "[1:a]volume=0.08[music];"
            "[0:a][music]"
            "amix=inputs=2:"
            "duration=first:"
            "dropout_transition=2"
            "[a]"
        ),

        "-map",
        "0:v:0",

        "-map",
        "[a]",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-b:a",
        "160k",

        "-shortest",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    run_ffmpeg(command)

    return output_path


# ============================================================
# FINAL VIDEO BUILDER
# ============================================================

def build_video(
    image_files: list[Path],
    animation_files: list[Path],
    audio_files: list[Path],
    durations: list[float],
    subtitle_path: Path,
    output_path: Path,
) -> Path:

    """
    Build the final educational video.

    A scene can contain either:

    1. AI-generated image
    2. True frame-based animation

    Each scene receives:

    Visual
        +
    Narration
        +
    Duration

    Then all scenes are combined,
    background audio is added,
    subtitles are burned,
    and the final MP4 is produced.
    """

    output_path = Path(
        output_path
    )

    work_dir = Path(
        tempfile.mkdtemp(
            prefix="educational_video_"
        )
    )

    rendered_scene_files = []


    # ========================================================
    # CREATE LOOKUP TABLES
    # ========================================================

    image_lookup = {
        Path(file).stem: Path(file)
        for file in image_files
    }

    animation_lookup = {
        Path(file).stem: Path(file)
        for file in animation_files
    }


    # ========================================================
    # PROCESS EVERY SCENE
    # ========================================================

    for index, (
        audio_file,
        duration,
    ) in enumerate(
        zip(
            audio_files,
            durations,
        ),
        start=1,
    ):

        scene_key = (
            f"scene_{index:02d}"
        )

        scene_video = (
            work_dir /
            f"{scene_key}.mp4"
        )

        duration = max(
            0.5,
            float(duration),
        )


        # ====================================================
        # TRUE ANIMATION SCENE
        # ====================================================

        if scene_key in animation_lookup:

            add_audio_to_animation(
                animation_path=(
                    animation_lookup[
                        scene_key
                    ]
                ),
                audio_path=Path(
                    audio_file
                ),
                output_path=scene_video,
                duration=duration,
            )


        # ====================================================
        # AI IMAGE SCENE
        # ====================================================

        elif scene_key in image_lookup:

            render_scene(
                image_path=(
                    image_lookup[
                        scene_key
                    ]
                ),
                audio_path=Path(
                    audio_file
                ),
                output_path=scene_video,
                duration=duration,
                animation="zoom",
            )


        # ====================================================
        # NO VISUAL
        # ====================================================

        else:

            raise RuntimeError(
                f"No visual found for "
                f"{scene_key}."
            )


        if not scene_video.exists():

            raise RuntimeError(
                f"Scene video was not created "
                f"for {scene_key}."
            )


        rendered_scene_files.append(
            scene_video
        )


    # ========================================================
    # CONCATENATE
    # ========================================================

    combined_video = (
        work_dir /
        "combined.mp4"
    )

    concat_scenes(
        scene_files=rendered_scene_files,
        output_path=combined_video,
        work_dir=work_dir,
    )


    # ========================================================
    # BACKGROUND AUDIO
    # ========================================================

    total_duration = sum(
        float(duration)
        for duration in durations
    )

    background_music = (
        work_dir /
        "background.m4a"
    )

    create_background_audio(
        output_path=background_music,
        duration=total_duration,
    )


    # ========================================================
    # FINAL VIDEO
    # ========================================================

    final_video = (
        work_dir /
        "educational_video.mp4"
    )

    add_subtitles_and_music(
        video_path=combined_video,
        subtitle_path=Path(
            subtitle_path
        ),
        music_path=background_music,
        output_path=final_video,
    )


    # ========================================================
    # COPY FINAL FILE TO REQUESTED LOCATION
    # ========================================================

    if final_video.resolve() != output_path.resolve():

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = [
            "ffmpeg",
            "-y",

            "-i",
            str(final_video),

            "-c",
            "copy",

            "-movflags",
            "+faststart",

            str(output_path),
        ]

        run_ffmpeg(command)


    return output_path
