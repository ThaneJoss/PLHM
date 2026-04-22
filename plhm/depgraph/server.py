from __future__ import annotations

import json
import mimetypes
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from plhm.depgraph.snapshot_service import SnapshotService
from plhm.depgraph.watcher import PollingWatcher


FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "depgraph"


class SnapshotStore:
    def __init__(self, root: Path) -> None:
        self.service = SnapshotService(root)
        self._condition = threading.Condition()
        self._snapshot = self.service.build_snapshot()
        self._revision = 1

    def get_snapshot_payload(self) -> dict[str, object]:
        with self._condition:
            return self._snapshot.to_dict()

    def get_revision(self) -> int:
        with self._condition:
            return self._revision

    def refresh(self) -> None:
        snapshot = self.service.build_snapshot()
        with self._condition:
            self._snapshot = snapshot
            self._revision += 1
            self._condition.notify_all()

    def wait_for_change(self, last_revision: int, timeout: float) -> tuple[int, dict[str, object] | None]:
        with self._condition:
            if self._revision <= last_revision:
                self._condition.wait(timeout=timeout)
            if self._revision <= last_revision:
                return self._revision, None
            return self._revision, self._snapshot.to_dict()


class DepgraphHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], root: Path) -> None:
        super().__init__(server_address, DepgraphRequestHandler)
        self.store = SnapshotStore(root)
        self.watcher = PollingWatcher(root, on_change=self.store.refresh)


class DepgraphRequestHandler(BaseHTTPRequestHandler):
    server: DepgraphHTTPServer

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/depgraph/snapshot":
            self._serve_json(self.server.store.get_snapshot_payload())
            return
        if parsed.path == "/api/depgraph/events":
            self._serve_events()
            return
        self._serve_frontend(parsed.path)

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _serve_json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_events(self) -> None:
        try:
            last_revision = int(self.headers.get("Last-Event-ID", "0"))
        except ValueError:
            last_revision = 0

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        while True:
            revision, payload = self.server.store.wait_for_change(last_revision, timeout=15.0)
            try:
                if payload is None:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                    continue
                event = {
                    "generated_at": payload["generated_at"],
                    "summary": payload["summary"],
                }
                self.wfile.write(f"id: {revision}\n".encode("utf-8"))
                self.wfile.write(b"event: snapshot\n")
                self.wfile.write(f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8"))
                self.wfile.flush()
                last_revision = revision
            except (BrokenPipeError, ConnectionResetError):
                return

    def _serve_frontend(self, raw_path: str) -> None:
        path = raw_path.lstrip("/") or "index.html"
        candidate = (FRONTEND_ROOT / path).resolve()
        if FRONTEND_ROOT not in candidate.parents and candidate != FRONTEND_ROOT / "index.html":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.exists() or not candidate.is_file():
            candidate = FRONTEND_ROOT / "index.html"
            if not candidate.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return

        body = candidate.read_bytes()
        content_type, _encoding = mimetypes.guess_type(candidate.name)
        self.send_response(HTTPStatus.OK)
        self.send_header(
            "Content-Type",
            f"{content_type or 'text/plain'}; charset=utf-8",
        )
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_depgraph(root: Path, host: str, port: int) -> None:
    server = DepgraphHTTPServer((host, port), root.resolve())
    try:
        server.watcher.start()
        server.serve_forever()
    finally:
        server.watcher.stop()
        server.server_close()
