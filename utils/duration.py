import math


def estimate_speech_seconds(
    text: str,
    words_per_minute: int = 145,
) -> float:

    words = len(text.split())

    if words == 0:
        return 2.0

    seconds = (
        words / words_per_minute
    ) * 60

    return max(
        2.0,
        seconds
    )


def allocate_scene_durations(
    scenes: list[dict],
    target_seconds: int,
) -> list[float]:

    if not scenes:
        return []

    weights = []

    for scene in scenes:

        narration = scene.get(
            "narration",
            ""
        )

        words = len(
            narration.split()
        )

        weights.append(
            max(1, words)
        )

    total_weight = sum(weights)

    durations = []

    for weight in weights:

        duration = (
            target_seconds
            * weight
            / total_weight
        )

        durations.append(
            max(2.5, duration)
        )

    return durations


def calculate_scene_count(
    target_seconds: int,
) -> int:

    estimated = round(
        target_seconds / 20
    )

    return max(
        4,
        min(
            8,
            estimated
        )
    )
