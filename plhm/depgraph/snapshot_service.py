from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from plhm.depgraph.analyzer import ImportGraph, ModuleRecord, build_import_graph
from plhm.depgraph.contracts import (
    GraphEdge,
    GraphNode,
    GraphSnapshot,
    GraphSummary,
    GraphViolation,
)
from plhm.depgraph.rules import evaluate_dependency, resolve_layer


ERROR_RANK = 2
WARNING_RANK = 1
NORMAL_RANK = 0


class SnapshotService:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def build_snapshot(self) -> GraphSnapshot:
        graph = build_import_graph(self.root)
        package_records = build_package_records(graph)
        edges, violations, status_by_node = build_edges_and_violations(graph)
        cycle_modules = {module for cycle in graph.cycles for module in cycle}
        for module in cycle_modules:
            status_by_node[file_node_id(module)] = max(
                status_by_node[file_node_id(module)],
                WARNING_RANK,
            )

        nodes = build_nodes(graph, package_records, status_by_node)
        summary = GraphSummary(
            node_count=len(nodes),
            edge_count=len(edges),
            violation_count=len(violations),
            cycle_count=len(graph.cycles),
        )
        return GraphSnapshot(
            version="1.0",
            generated_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            nodes=tuple(nodes),
            edges=tuple(edges),
            violations=tuple(violations),
        )

    def export_json(self, output_path: Path) -> Path:
        snapshot = self.build_snapshot()
        output_path.write_text(
            serialize_snapshot(snapshot),
            encoding="utf-8",
        )
        return output_path


def serialize_snapshot(snapshot: GraphSnapshot) -> str:
    import json

    return json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2) + "\n"


def build_package_records(graph: ImportGraph) -> dict[str, ModuleRecord | None]:
    package_records: dict[str, ModuleRecord | None] = {}
    for module, record in graph.modules.items():
        package = record.package
        while package:
            package_records.setdefault(package, graph.modules.get(package))
            if "." not in package:
                break
            package = package.rsplit(".", 1)[0]
    for module, record in graph.modules.items():
        if record.is_package:
            package_records[module] = record
    return dict(sorted(package_records.items()))


def build_edges_and_violations(
    graph: ImportGraph,
) -> tuple[list[GraphEdge], list[GraphViolation], defaultdict[str, int]]:
    status_by_node: defaultdict[str, int] = defaultdict(int)
    edges: list[GraphEdge] = []
    violations: list[GraphViolation] = []

    for index, ((source_module, target_module), import_count) in enumerate(graph.imports.items(), start=1):
        evaluation = evaluate_dependency(source_module, target_module)
        edge_id = edge_node_id(source_module, target_module)
        edges.append(
            GraphEdge(
                id=edge_id,
                source=file_node_id(source_module),
                target=file_node_id(target_module),
                kind="import",
                allowed=evaluation.allowed,
                reasons=evaluation.reasons,
                import_count=import_count,
            )
        )
        if evaluation.allowed:
            continue

        violations.append(
            GraphViolation(
                id=f"violation:{index}",
                rule_id="layer-direction",
                severity="error",
                edge_id=edge_id,
                message=evaluation.violation_message or evaluation.reasons[0],
            )
        )
        status_by_node[file_node_id(source_module)] = ERROR_RANK
        status_by_node[file_node_id(target_module)] = max(
            status_by_node[file_node_id(target_module)],
            WARNING_RANK,
        )

    return edges, violations, status_by_node


def build_nodes(
    graph: ImportGraph,
    package_records: dict[str, ModuleRecord | None],
    status_by_node: defaultdict[str, int],
) -> list[GraphNode]:
    nodes: list[GraphNode] = []
    package_status = propagate_package_status(graph, package_records, status_by_node)

    for package, record in package_records.items():
        path = record.relative_path.parent.as_posix() if record is not None else package.replace(".", "/")
        nodes.append(
            GraphNode(
                id=package_node_id(package),
                label=package.split(".")[-1],
                module=package,
                path=path,
                kind="package",
                layer=resolve_layer(package),
                status=status_name(package_status[package_node_id(package)]),
                parent_id=package_node_id(package.rsplit(".", 1)[0]) if "." in package else None,
            )
        )

    for module, record in sorted(graph.modules.items()):
        parent_id = package_node_id(record.package) if record.package else None
        nodes.append(
            GraphNode(
                id=file_node_id(module),
                label=record.relative_path.name,
                module=module,
                path=record.relative_path.as_posix(),
                kind="file",
                layer=resolve_layer(module),
                status=status_name(status_by_node[file_node_id(module)]),
                parent_id=parent_id,
            )
        )

    return sorted(nodes, key=lambda node: (node.kind, node.module, node.id))


def propagate_package_status(
    graph: ImportGraph,
    package_records: dict[str, ModuleRecord | None],
    status_by_node: defaultdict[str, int],
) -> defaultdict[str, int]:
    package_status: defaultdict[str, int] = defaultdict(int)
    for module, record in graph.modules.items():
        current_status = status_by_node[file_node_id(module)]
        package = record.module if record.is_package else record.package
        while package:
            package_status[package_node_id(package)] = max(
                package_status[package_node_id(package)],
                current_status,
            )
            if "." not in package:
                break
            package = package.rsplit(".", 1)[0]

    for package in package_records:
        package_status[package_node_id(package)] = max(
            package_status[package_node_id(package)],
            NORMAL_RANK,
        )
    return package_status


def status_name(rank: int) -> str:
    if rank >= ERROR_RANK:
        return "error"
    if rank >= WARNING_RANK:
        return "warning"
    return "normal"


def package_node_id(module: str) -> str:
    return f"package:{module}"


def file_node_id(module: str) -> str:
    return f"file:{module}"


def edge_node_id(source_module: str, target_module: str) -> str:
    return f"edge:{source_module}->{target_module}"
