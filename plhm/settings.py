from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataSettings:
    n_samples: int
    batch_size: int
    num_workers: int
    prefetch_factor: int
    persistent_workers: bool


@dataclass(frozen=True)
class ModelSettings:
    input_dim: int
    hidden_dim: int
    lr: float


@dataclass(frozen=True)
class TrainerSettings:
    max_epochs: int
    accelerator: str
    devices: int | str
    strategy: str
    precision: str
    matmul_precision: str
    benchmark: bool
    deterministic: bool
    num_sanity_val_steps: int
    log_every_n_steps: int
    enable_model_summary: bool


@dataclass(frozen=True)
class MlflowSettings:
    experiment_name: str
    run_name: str
    db_file: str


@dataclass(frozen=True)
class AppSettings:
    seed: int
    data: DataSettings
    model: ModelSettings
    trainer: TrainerSettings
    mlflow: MlflowSettings
