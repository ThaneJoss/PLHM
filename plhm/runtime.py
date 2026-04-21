from __future__ import annotations

import os
from dataclasses import dataclass

import torch

from plhm.settings import DataSettings, TrainerSettings


@dataclass(frozen=True)
class RuntimeConfig:
    accelerator: str
    devices: int | str
    precision: str
    strategy: str
    matmul_precision: str | None
    benchmark: bool
    global_batch_size: int


@dataclass(frozen=True)
class DataLoaderConfig:
    num_workers: int
    prefetch_factor: int | None
    persistent_workers: bool
    pin_memory: bool


def resolve_num_workers(requested_workers: int, device_count: int) -> int:
    if requested_workers >= 0:
        return requested_workers

    cpu_count = os.cpu_count() or 8
    process_count = max(1, device_count)
    return max(2, min(8, cpu_count // (process_count * 4)))


def resolve_runtime(trainer_cfg: TrainerSettings, batch_size: int) -> RuntimeConfig:
    accelerator = trainer_cfg.accelerator
    if accelerator == "auto":
        accelerator = "gpu" if torch.cuda.is_available() else "cpu"

    devices: int | str = trainer_cfg.devices if accelerator == "gpu" else 1
    if isinstance(devices, str) and devices.isdigit():
        devices = int(devices)
    if accelerator == "gpu" and devices == "auto":
        visible_devices = torch.cuda.device_count()
        devices = visible_devices if visible_devices > 0 else 1

    precision = trainer_cfg.precision
    if precision == "auto":
        if accelerator == "gpu":
            precision = "bf16-mixed" if torch.cuda.is_bf16_supported() else "16-mixed"
        else:
            precision = "32-true"

    strategy = trainer_cfg.strategy
    if accelerator != "gpu":
        strategy = "auto"
    elif strategy == "auto" and isinstance(devices, int) and devices > 1:
        strategy = "ddp_find_unused_parameters_false"

    matmul_precision = trainer_cfg.matmul_precision
    if matmul_precision == "auto":
        matmul_precision = "high" if accelerator == "gpu" else None

    device_count = devices if isinstance(devices, int) else torch.cuda.device_count()
    global_batch_size = batch_size * max(1, device_count if accelerator == "gpu" else 1)
    benchmark = bool(trainer_cfg.benchmark and accelerator == "gpu" and not trainer_cfg.deterministic)

    return RuntimeConfig(
        accelerator=accelerator,
        devices=devices,
        precision=precision,
        strategy=strategy,
        matmul_precision=matmul_precision,
        benchmark=benchmark,
        global_batch_size=global_batch_size,
    )


def resolve_dataloader_config(data_cfg: DataSettings, runtime: RuntimeConfig) -> DataLoaderConfig:
    device_count = runtime.devices if isinstance(runtime.devices, int) else 1
    num_workers = resolve_num_workers(data_cfg.num_workers, device_count)

    return DataLoaderConfig(
        num_workers=num_workers,
        prefetch_factor=data_cfg.prefetch_factor if num_workers > 0 else None,
        persistent_workers=bool(data_cfg.persistent_workers and num_workers > 0),
        pin_memory=runtime.accelerator == "gpu" and torch.cuda.is_available(),
    )
