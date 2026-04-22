from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayerRule:
    name: str
    prefixes: tuple[str, ...]
    rank: int


DEFAULT_LAYER_RULES: tuple[LayerRule, ...] = (
    LayerRule(
        name="entry",
        prefixes=("main", "plhm.hydra_loader", "plhm.app"),
        rank=3,
    ),
    LayerRule(
        name="adapter",
        prefixes=("plhm.lightning", "plhm.integrations", "plhm.reporting"),
        rank=2,
    ),
    LayerRule(
        name="support",
        prefixes=("plhm.runtime", "plhm.mlflow", "plhm.depgraph"),
        rank=1,
    ),
    LayerRule(
        name="core",
        prefixes=("plhm.pytorch", "plhm.settings"),
        rank=0,
    ),
)


@dataclass(frozen=True)
class EdgeEvaluation:
    allowed: bool
    reasons: tuple[str, ...]
    violation_message: str | None = None


def resolve_layer(module: str, rules: tuple[LayerRule, ...] = DEFAULT_LAYER_RULES) -> str:
    best_match: tuple[int, str] | None = None
    for rule in rules:
        for prefix in rule.prefixes:
            if module == prefix or module.startswith(f"{prefix}."):
                score = len(prefix)
                if best_match is None or score > best_match[0]:
                    best_match = (score, rule.name)
    return best_match[1] if best_match is not None else "unknown"


def evaluate_dependency(
    source_module: str,
    target_module: str,
    rules: tuple[LayerRule, ...] = DEFAULT_LAYER_RULES,
) -> EdgeEvaluation:
    source_layer = resolve_layer(source_module, rules)
    target_layer = resolve_layer(target_module, rules)

    if "unknown" in {source_layer, target_layer}:
        return EdgeEvaluation(
            allowed=True,
            reasons=(f"Layer check skipped for {source_layer} -> {target_layer}.",),
        )

    ranks = {rule.name: rule.rank for rule in rules}
    if ranks[source_layer] >= ranks[target_layer]:
        return EdgeEvaluation(
            allowed=True,
            reasons=(f"Layer rule allows {source_layer} -> {target_layer}.",),
        )

    message = (
        f"{source_module} ({source_layer}) must not depend on "
        f"{target_module} ({target_layer})."
    )
    return EdgeEvaluation(
        allowed=False,
        reasons=(message,),
        violation_message=message,
    )
