from __future__ import annotations

from pathlib import Path

import lightning as L
import torch

from plhm.integrations.lightning_mlflow import build_mlflow_logger
from plhm.lightning.datamodule import GaussianBlobDataModule
from plhm.lightning.module import ClassificationModule, OptimizerConfig
from plhm.mlflow import build_tracking_uri
from plhm.pytorch.data import build_gaussian_blob_splits
from plhm.pytorch.model import TinyClassifier
from plhm.reporting import extract_final_metrics, print_banner, print_final_metrics
from plhm.runtime import resolve_dataloader_config, resolve_runtime
from plhm.settings import AppSettings


def run_training(cfg: AppSettings, project_root: Path) -> dict[str, float]:
    # Keep cross-framework assembly in one place.
    L.seed_everything(cfg.seed, workers=True)

    runtime = resolve_runtime(cfg.trainer, cfg.data.batch_size)
    dataloader_config = resolve_dataloader_config(cfg.data, runtime)

    if runtime.matmul_precision is not None:
        torch.set_float32_matmul_precision(runtime.matmul_precision)

    tracking_uri = build_tracking_uri(project_root, cfg.mlflow.db_file)
    logger = build_mlflow_logger(cfg, runtime, tracking_uri)

    datamodule = GaussianBlobDataModule(
        dataset_factory=lambda: build_gaussian_blob_splits(
            n_samples=cfg.data.n_samples,
            seed=cfg.seed,
        ),
        batch_size=cfg.data.batch_size,
        num_workers=dataloader_config.num_workers,
        prefetch_factor=dataloader_config.prefetch_factor,
        persistent_workers=dataloader_config.persistent_workers,
        pin_memory=dataloader_config.pin_memory,
    )
    network = TinyClassifier(
        input_dim=cfg.model.input_dim,
        hidden_dim=cfg.model.hidden_dim,
    )
    model = ClassificationModule(
        network=network,
        optimizer_config=OptimizerConfig(lr=cfg.model.lr),
    )

    print_banner(project_root, runtime, tracking_uri)

    trainer = L.Trainer(
        max_epochs=cfg.trainer.max_epochs,
        accelerator=runtime.accelerator,
        devices=runtime.devices,
        precision=runtime.precision,
        strategy=runtime.strategy,
        logger=logger,
        log_every_n_steps=cfg.trainer.log_every_n_steps,
        enable_checkpointing=False,
        enable_model_summary=cfg.trainer.enable_model_summary,
        deterministic=cfg.trainer.deterministic,
        benchmark=runtime.benchmark,
        num_sanity_val_steps=cfg.trainer.num_sanity_val_steps,
    )
    trainer.fit(model=model, datamodule=datamodule)

    metrics = extract_final_metrics(trainer)
    print_final_metrics(metrics)
    return metrics
