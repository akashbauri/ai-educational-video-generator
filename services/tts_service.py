import asyncio
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
):

    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
    )

    await communicator.save(
        output_path
    )


def generate_voice(
    text: str,
    language: str,
    output_path: Path,
) -> Path:

    voice = VOICE_MAP.get(
        language,
        VOICE_MAP["English"],
    )

    asyncio.run(
        save_tts(
            text,
            voice,
            str(output_path),
        )
    )

    if not output_path.exists():

        raise RuntimeError(
            "TTS did not create the audio file."
        )

    return output_path
