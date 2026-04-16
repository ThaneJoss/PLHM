from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from lightning.pytorch.loggers import MLFlowLogger

from plhm.runtime import RuntimeConfig
from plhm.settings import AppSettings


def build_mlflow_logger(cfg: AppSettings, runtime: RuntimeConfig, tracking_uri: str) -> MLFlowLogger:
    logger = MLFlowLogger(
        experiment_name=cfg.mlflow.experiment_name,
        tracking_uri=tracking_uri,
        run_name=cfg.mlflow.run_name,
        log_model=False,
    )
    logger.log_hyperparams(_flatten_dict({"config": asdict(cfg), "runtime": asdict(runtime)}))
    return logger


def _flatten_dict(values: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in values.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if is_dataclass(value):
            flat.update(_flatten_dict(asdict(value), full_key))
            continue

        if isinstance(value, dict):
            flat.update(_flatten_dict(value, full_key))
            continue

        flat[full_key] = value
    return flat
