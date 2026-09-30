from pathlib import Path
import tempfile


def make_job_dir() -> Path:
    """
    Creates a temporary working directory for one video.
    """

    return Path(
        tempfile.mkdtemp(
            prefix="educational_video_"
        )
    )


def ensure_dir(path: Path) -> Path:
    """
    Create a directory if it does not exist.
    """

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return path
