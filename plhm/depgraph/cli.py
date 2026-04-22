from __future__ import annotations

import argparse
from pathlib import Path

from plhm.depgraph.server import serve_depgraph
from plhm.depgraph.snapshot_service import SnapshotService


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
        print(f"Serving PLHM dependency graph at http://{args.host}:{args.port}")
        serve_depgraph(root, args.host, args.port)
        return

    parser.error(f"Unsupported command: {args.command}")
