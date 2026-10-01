from pathlib import Path
import subprocess


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


def render_scene(
    image_path: Path,
    audio_path: Path,
    output_path: Path,
    duration: float,
    animation: str,
) -> Path:

    fps = 24

    frames = max(
        1,
        int(duration * fps)
    )

    if animation == "pan":

        zoom_filter = (
            f"zoompan="
            f"z='min(zoom+0.0005,1.08)':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s=1280x720:"
            f"fps={fps}"
        )

    elif animation == "slide":

        zoom_filter = (
            f"zoompan="
            f"z='1.04':"
            f"x='(iw-iw/zoom)*on/{frames}':"
            f"y='(ih-ih/zoom)/2':"
            f"d={frames}:"
            f"s=1280x720:"
            f"fps={fps}"
        )

    else:

        zoom_filter = (
            f"zoompan="
            f"z='min(zoom+0.0005,1.10)':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:"
            f"s=1280x720:"
            f"fps={fps}"
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
        str(fps),

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

    run_ffmpeg(
        command
    )

    return output_path


def concat_scenes(
    scene_files: list[Path],
    output_path: Path,
    work_dir: Path,
) -> Path:

    concat_file = (
        work_dir
        / "concat.txt"
    )

    lines = []

    for scene_file in scene_files:

        safe_path = (
            str(scene_file)
            .replace(
                "'",
                "'\\''"
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

        str(output_path),
    ]

    run_ffmpeg(
        command
    )

    return output_path


def create_background_audio(
    output_path: Path,
    duration: float,
) -> Path:

    # Procedural ambient background.
    # No external audio file or paid API is required.

    filter_complex = (
        "[0:a]volume=0.025[a0];"
        "[1:a]volume=0.018[a1];"
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
        "sine=frequency=220:"
        "sample_rate=44100",

        "-f",
        "lavfi",

        "-i",
        "sine=frequency=330:"
        "sample_rate=44100",

        "-filter_complex",
        filter_complex,

        "-t",
        f"{duration:.3f}",

        "-c:a",
        "aac",

        str(output_path),
    ]

    run_ffmpeg(
        command
    )

    return output_path


def add_subtitles_and_music(
    video_path: Path,
    subtitle_path: Path,
    music_path: Path,
    output_path: Path,
) -> Path:

    subtitle_path_string = (
        str(subtitle_path)
        .replace(
            "\\",
            "/",
        )
        .replace(
            ":",
            "\\:",
        )
    )

    subtitle_filter = (
        f"subtitles={subtitle_path_string}:"
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
            "dropout_transition=2[a]"
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

        str(output_path),
    ]

    run_ffmpeg(
        command
    )

    return output_path


def build_video(
    image_files: list[Path],
    audio_files: list[Path],
    durations: list[float],
    animations: list[str],
    subtitle_path: Path,
    work_dir: Path,
) -> Path:

    rendered_scene_files = []

    for index, (
        image_file,
        audio_file,
        duration,
        animation,
    ) in enumerate(
        zip(
            image_files,
            audio_files,
            durations,
            animations,
        ),
        start=1,
    ):

        scene_video = (
            work_dir
            / f"scene_{index:02d}.mp4"
        )

        render_scene(
            image_path=image_file,
            audio_path=audio_file,
            output_path=scene_video,
            duration=duration,
            animation=animation,
        )

        rendered_scene_files.append(
            scene_video
        )

    combined_video = (
        work_dir
        / "combined.mp4"
    )

    concat_scenes(
        rendered_scene_files,
        combined_video,
        work_dir,
    )

    total_duration = sum(
        durations
    )

    background_music = (
        work_dir
        / "background.m4a"
    )

    create_background_audio(
        background_music,
        total_duration,
    )

    final_video = (
        work_dir
        / "educational_video.mp4"
    )

    add_subtitles_and_music(
        video_path=combined_video,
        subtitle_path=subtitle_path,
        music_path=background_music,
        output_path=final_video,
    )

    return final_video
