from __future__ import annotations

import argparse
from pathlib import Path

from plhm.depgraph.server import serve_depgraph
from plhm.depgraph.snapshot_service import SnapshotService


def build_serve_message(root: Path, host: str, port: int) -> str:
    lines = [
        f"Serving PLHM dependency graph from {root}",
        f"Browser URL: http://{host}:{port}",
        "This command starts an HTTP server. It does not render a UI in the terminal.",
    ]
    if host in {"127.0.0.1", "localhost", "::1"}:
        lines.extend(
            [
                "If this server is running on a remote machine, forward the port before opening it locally:",
                f"  ssh -L {port}:127.0.0.1:{port} <remote-host>",
            ]
        )
    lines.append("Press Ctrl+C to stop.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PLHM dependency graph tooling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a dependency graph snapshot.")
    export_parser.add_argument(
        "--root",
        default=".",
        help="Repository root to analyze.",
    )
    export_parser.add_argument(
        "--output",
        default="graph.json",
        help="Output JSON path.",
    )

    serve_parser = subparsers.add_parser("serve", help="Serve snapshot APIs and the browser viewer.")
    serve_parser.add_argument(
        "--root",
        default=".",
        help="Repository root to analyze.",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    serve_parser.add_argument("--port", type=int, default=8765, help="Port to bind.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "export":
        output_path = Path(args.output).resolve()
        SnapshotService(root).export_json(output_path)
        print(f"Wrote dependency graph snapshot to {output_path}")
        return

    if args.command == "serve":
        print(build_serve_message(root, args.host, args.port), flush=True)
        serve_depgraph(root, args.host, args.port)
        return

    parser.error(f"Unsupported command: {args.command}")
