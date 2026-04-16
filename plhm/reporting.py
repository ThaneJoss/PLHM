from __future__ import annotations

from pathlib import Path

import lightning as L
import torch
from lightning.pytorch.utilities.rank_zero import rank_zero_only

from plhm.runtime import RuntimeConfig


@rank_zero_only
def print_banner(project_root: Path, runtime: RuntimeConfig, tracking_uri: str) -> None:
    device_name = "cpu"
    if runtime.accelerator == "gpu" and torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)

    print("=" * 80)
    print(f"Project root: {project_root}")
    print(f"Python: {torch.__version__=}")
    print(f"CUDA build: {torch.version.cuda}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"Accelerator: {runtime.accelerator}")
    print(f"Devices: {runtime.devices}")
    print(f"Precision: {runtime.precision}")
    print(f"Strategy: {runtime.strategy}")
    print(f"Matmul precision: {runtime.matmul_precision}")
    print(f"Global batch size: {runtime.global_batch_size}")
    print(f"Primary device: {device_name}")
    print(f"MLflow tracking URI: {tracking_uri}")
    print("=" * 80)


@rank_zero_only
def print_final_metrics(metrics: dict[str, float]) -> None:
    print(f"Final metrics: {metrics}")


def extract_final_metrics(trainer: L.Trainer) -> dict[str, float]:
    return {
        name: float(value.detach().cpu())
        for name, value in trainer.callback_metrics.items()
        if torch.is_tensor(value)
    }
