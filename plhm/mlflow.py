from __future__ import annotations

from pathlib import Path


def build_tracking_uri(project_root: Path, db_file: str) -> str:
    return f"sqlite:///{(project_root / db_file).resolve()}"
