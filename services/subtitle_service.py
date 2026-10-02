from pathlib import Path


def srt_time(
    seconds: float,
) -> str:

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = (
        milliseconds // 3_600_000
    )

    milliseconds %= 3_600_000

    minutes = (
        milliseconds // 60_000
    )

    milliseconds %= 60_000

    secs = (
        milliseconds // 1000
    )

    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


def split_text(
    text: str,
    max_words: int = 9,
) -> list[str]:

    words = text.split()

    chunks = []

    current = []

    for word in words:

        current.append(
            word
        )

        if len(current) >= max_words:

            chunks.append(
                " ".join(current)
            )

            current = []

    if current:

        chunks.append(
            " ".join(current)
        )

    return chunks


def create_srt(
    scenes: list[dict],
    durations: list[float],
    output_path: Path,
) -> Path:

    blocks = []

    current_time = 0.0

    subtitle_number = 1

    for scene, duration in zip(
        scenes,
        durations,
    ):

        narration = scene.get(
            "narration",
            "",
        ).strip()

        if not narration:
            continue

        chunks = split_text(
            narration,
            max_words=9,
        )

        total_words = sum(
            len(chunk.split())
            for chunk in chunks
        )

        if total_words == 0:
            continue

        for chunk in chunks:

            word_count = len(
                chunk.split()
            )

            chunk_duration = (
                duration
                * word_count
                / total_words
            )

            start = current_time

            end = (
                current_time
                + chunk_duration
            )

            blocks.append(
                f"{subtitle_number}\n"
                f"{srt_time(start)} --> "
                f"{srt_time(end)}\n"
                f"{chunk}\n"
            )

            subtitle_number += 1

            current_time = end

    output_path.write_text(
        "\n".join(blocks),
        encoding="utf-8",
    )

    return output_path
