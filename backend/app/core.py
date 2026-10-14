"""Storage paths and local/hosted runtime settings."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("NOTEPILOT_DATA_DIR", ROOT / "data")).resolve()
MAX_UPLOAD = int(os.environ.get("NOTEPILOT_MAX_UPLOAD_MB", "40")) * 1024 * 1024
MAX_PAGES = 30
MAX_PIXELS = 35_000_000
OMR_PYTHON = Path(
    os.environ.get(
        "NOTEPILOT_OMR_PYTHON",
        ROOT / ".omr-venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python"),
    )
)
OMR_TIMEOUT = int(os.environ.get("NOTEPILOT_OMR_TIMEOUT", "900"))


def init_paths():
    for folder in ["originals", "processed", "musicxml", "exports", "cache", "logs"]:
        (DATA / folder).mkdir(parents=True, exist_ok=True)


def local_path(relative: str) -> Path:
    path = (DATA / relative).resolve()
    if not path.is_relative_to(DATA):
        raise ValueError("Ungültiger Dateipfad.")
    return path


HOSTED_PREVIEW = os.environ.get("NOTEPILOT_HOSTED_PREVIEW") == "1"
ALLOWED_HOSTS = frozenset(
    host.strip().lower() for host in os.environ.get("NOTEPILOT_ALLOWED_HOSTS", "").split(",") if host.strip()
)
