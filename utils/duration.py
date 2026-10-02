def calculate_total_duration(
    durations: list[float],
) -> float:

    return sum(
        durations
    )


def validate_duration(
    duration: float,
) -> float:

    return max(
        0.5,
        float(duration),
    )
