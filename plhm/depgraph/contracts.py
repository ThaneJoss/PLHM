from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GraphSummary:
    node_count: int
    edge_count: int
    violation_count: int
    cycle_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "violation_count": self.violation_count,
            "cycle_count": self.cycle_count,
        }


@dataclass(frozen=True)
class GraphNode:
    id: str
    label: str
    module: str
    path: str
    kind: str
    layer: str
    status: str
    parent_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "module": self.module,
            "path": self.path,
            "kind": self.kind,
            "layer": self.layer,
            "status": self.status,
            "parent_id": self.parent_id,
        }


@dataclass(frozen=True)
class GraphEdge:
    id: str
    source: str
    target: str
    kind: str
    allowed: bool
    reasons: tuple[str, ...]
    import_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "import_count": self.import_count,
        }


@dataclass(frozen=True)
class GraphViolation:
    id: str
    rule_id: str
    severity: str
    edge_id: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "edge_id": self.edge_id,
            "message": self.message,
        }


@dataclass(frozen=True)
class GraphSnapshot:
    version: str
    generated_at: str
    summary: GraphSummary
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    violations: tuple[GraphViolation, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "summary": self.summary.to_dict(),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "violations": [violation.to_dict() for violation in self.violations],
        }
