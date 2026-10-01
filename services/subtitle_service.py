from pathlib import Path


def srt_time(
    seconds: float,
) -> str:

    milliseconds = int(
        round(seconds * 1000)
    )

    hours = (
        milliseconds
        // 3_600_000
    )

    milliseconds %= 3_600_000

    minutes = (
        milliseconds
        // 60_000
    )

    milliseconds %= 60_000

    secs = (
        milliseconds
        // 1000
    )

    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


def create_srt(
    scenes: list[dict],
    durations: list[float],
    output_path: Path,
) -> Path:

    current_time = 0.0

    blocks = []

    for index, (
        scene,
        duration,
    ) in enumerate(
        zip(
            scenes,
            durations,
        ),
        start=1,
    ):

        start = current_time

        end = (
            current_time
            + duration
        )

        narration = scene.get(
            "narration",
            "",
        )

        narration = (
            narration
            .replace("\n", " ")
            .strip()
        )

        block = (
            f"{index}\n"
            f"{srt_time(start)} --> "
            f"{srt_time(end)}\n"
            f"{narration}\n"
        )

        blocks.append(
            block
        )

        current_time = end

    output_path.write_text(
        "\n".join(blocks),
        encoding="utf-8",
    )

    return output_path
