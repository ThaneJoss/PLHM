from __future__ import annotations

import ast
from collections import Counter, defaultdict
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path, PurePosixPath


IGNORED_ROOTS = {
    ".git",
    ".venv",
    "__pycache__",
    "frontend",
    "outputs",
}


@dataclass(frozen=True)
class ModuleRecord:
    module: str
    path: Path
    relative_path: PurePosixPath
    is_package: bool

    @property
    def package(self) -> str:
        if self.is_package:
            return self.module
        if "." not in self.module:
            return ""
        return self.module.rsplit(".", 1)[0]


@dataclass(frozen=True)
class ImportGraph:
    root: Path
    modules: dict[str, ModuleRecord]
    imports: dict[tuple[str, str], int]
    cycles: tuple[tuple[str, ...], ...]


def discover_modules(root: Path) -> dict[str, ModuleRecord]:
    modules: dict[str, ModuleRecord] = {}
    for path in sorted(root.rglob("*.py")):
        relative_path = PurePosixPath(path.relative_to(root).as_posix())
        if any(part in IGNORED_ROOTS or part.startswith(".") for part in relative_path.parts[:-1]):
            continue
        module = module_name_from_path(relative_path)
        if module is None:
            continue
        modules[module] = ModuleRecord(
            module=module,
            path=path,
            relative_path=relative_path,
            is_package=relative_path.name == "__init__.py",
        )
    return modules


def build_import_graph(root: Path) -> ImportGraph:
    root = root.resolve()
    modules = discover_modules(root)
    edge_counts: Counter[tuple[str, str]] = Counter()
    for module, record in modules.items():
        for target in iter_internal_imports(record, modules):
            if target == module:
                edge_counts[(module, target)] += 1
                continue
            edge_counts[(module, target)] += 1
    cycles = detect_cycles(modules, edge_counts)
    return ImportGraph(
        root=root,
        modules=modules,
        imports=dict(sorted(edge_counts.items())),
        cycles=cycles,
    )


def module_name_from_path(relative_path: PurePosixPath) -> str | None:
    if relative_path.name == "__init__.py":
        parts = relative_path.parts[:-1]
        return ".".join(parts) if parts else None
    return ".".join(relative_path.with_suffix("").parts)


def iter_internal_imports(
    record: ModuleRecord,
    modules: dict[str, ModuleRecord],
) -> tuple[str, ...]:
    source = record.path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(record.relative_path))
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = match_known_module(alias.name, modules)
                if target is not None:
                    targets.append(target)
        elif isinstance(node, ast.ImportFrom):
            targets.extend(resolve_from_import(record, node, modules))
    return tuple(targets)


def resolve_from_import(
    record: ModuleRecord,
    node: ast.ImportFrom,
    modules: dict[str, ModuleRecord],
) -> tuple[str, ...]:
    base_module = node.module or ""
    if node.level:
        package = record.package or record.module
        relative_name = "." * node.level + base_module
        try:
            base_module = resolve_name(relative_name, package)
        except ImportError:
            return ()

    resolved: list[str] = []
    for alias in node.names:
        candidates: list[str] = []
        if alias.name == "*":
            if base_module:
                target = match_known_module(base_module, modules)
                if target is not None:
                    resolved.append(target)
            continue
        if base_module:
            candidates.append(f"{base_module}.{alias.name}")
            candidates.append(base_module)
        if not base_module and node.level == 0:
            candidates.append(alias.name)
        for candidate in candidates:
            target = match_known_module(candidate, modules)
            if target is not None:
                resolved.append(target)
                break
    return tuple(resolved)


def match_known_module(
    candidate: str,
    modules: dict[str, ModuleRecord],
) -> str | None:
    parts = candidate.split(".")
    for size in range(len(parts), 0, -1):
        module = ".".join(parts[:size])
        if module in modules:
            return module
    return None


def detect_cycles(
    modules: dict[str, ModuleRecord],
    edge_counts: Counter[tuple[str, str]],
) -> tuple[tuple[str, ...], ...]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for (source, target), _count in edge_counts.items():
        adjacency[source].add(target)

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[tuple[str, ...]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in adjacency.get(node, ()):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] != indices[node]:
            return

        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1:
            components.append(tuple(sorted(component)))
            return
        member = component[0]
        if member in adjacency.get(member, set()):
            components.append((member,))

    for module in sorted(modules):
        if module not in indices:
            strongconnect(module)

    return tuple(sorted(components))
