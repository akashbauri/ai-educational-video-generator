import asyncio
import subprocess
from pathlib import Path

import edge_tts


VOICE_MAP = {
    "English": "en-IN-NeerjaNeural",
    "Hindi": "hi-IN-SwaraNeural",
    "Bengali": "bn-IN-TanishaaNeural",
}


async def save_tts(
    text: str,
    voice: str,
    output_path: str,
) -> None:

    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
    )

    await communicator.save(
        output_path
    )


def get_audio_duration(
    audio_path: Path,
) -> float:

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "Could not determine audio duration.\n"
            + result.stderr
        )

    try:

        return float(
            result.stdout.strip()
        )

    except ValueError as exc:

        raise RuntimeError(
            "FFprobe returned an invalid audio duration."
        ) from exc


def generate_voice(
    text: str,
    language: str,
    output_path: Path,
) -> tuple[Path, float]:

    if not text.strip():

        raise ValueError(
            "Narration text is empty."
        )

    voice = VOICE_MAP.get(
        language,
        VOICE_MAP["English"],
    )

    asyncio.run(
        save_tts(
            text=text,
            voice=voice,
            output_path=str(
                output_path
            ),
        )
    )

    if not output_path.exists():

        raise RuntimeError(
            "TTS failed to create audio."
        )

    actual_duration = get_audio_duration(
        output_path
    )

    if actual_duration <= 0:

        raise RuntimeError(
            "Generated audio has zero duration."
        )

    return (
        output_path,
        actual_duration,
    )
