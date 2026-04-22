from __future__ import annotations

import threading
from pathlib import Path
from time import sleep
from typing import Callable

from plhm.depgraph.analyzer import IGNORED_ROOTS


class PollingWatcher:
    def __init__(
        self,
        root: Path,
        on_change: Callable[[], None],
        interval_seconds: float = 1.0,
    ) -> None:
        self.root = root.resolve()
        self.on_change = on_change
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, name="plhm-depgraph-watch", daemon=True)
        self._known_mtimes = self._collect_mtimes()

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            current_mtimes = self._collect_mtimes()
            if current_mtimes != self._known_mtimes:
                self._known_mtimes = current_mtimes
                self.on_change()
            sleep(self.interval_seconds)

    def _collect_mtimes(self) -> dict[str, int]:
        mtimes: dict[str, int] = {}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(self.root)
            if any(part in IGNORED_ROOTS or part.startswith(".") for part in relative.parts[:-1]):
                continue
            if path.suffix not in {".py", ".yaml", ".yml"}:
                continue
            mtimes[str(relative)] = path.stat().st_mtime_ns
        return mtimes
