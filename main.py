from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import hydra
import lightning as L
import mlflow
import torch
from hydra.utils import get_original_cwd
from lightning.pytorch.loggers import MLFlowLogger
from lightning.pytorch.utilities.rank_zero import rank_zero_only
from omegaconf import DictConfig, OmegaConf
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split


@dataclass
class RuntimeConfig:
    accelerator: str
    devices: int | str
    precision: str
    strategy: str
    matmul_precision: str | None
    benchmark: bool
    global_batch_size: int


class GaussianBlobDataModule(L.LightningDataModule):
    def __init__(
        self,
        n_samples: int,
        batch_size: int,
        num_workers: int,
        prefetch_factor: int | None,
        persistent_workers: bool,
        seed: int,
    ) -> None:
        super().__init__()
        self.n_samples = n_samples
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.persistent_workers = persistent_workers
        self.seed = seed
        self.train_dataset: TensorDataset | None = None
        self.val_dataset: TensorDataset | None = None

    def setup(self, stage: str | None = None) -> None:
        generator = torch.Generator().manual_seed(self.seed)
        half = self.n_samples // 2

        class_zero = torch.randn(half, 2, generator=generator) * 0.9 + torch.tensor([-2.0, -2.0])
        class_one = torch.randn(self.n_samples - half, 2, generator=generator) * 0.9 + torch.tensor([2.0, 2.0])

        features = torch.cat([class_zero, class_one], dim=0)
        labels = torch.cat([
            torch.zeros(half, dtype=torch.long),
            torch.ones(self.n_samples - half, dtype=torch.long),
        ])

        permutation = torch.randperm(self.n_samples, generator=generator)
        features = features[permutation]
        labels = labels[permutation]

        dataset = TensorDataset(features, labels)
        train_size = int(0.8 * len(dataset))
        val_size = len(dataset) - train_size
        self.train_dataset, self.val_dataset = random_split(dataset, [train_size, val_size], generator=generator)

    def train_dataloader(self) -> DataLoader:
        if self.train_dataset is None:
            raise RuntimeError("Data module has not been set up.")
        return DataLoader(
            self.train_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=True,
            pin_memory=torch.cuda.is_available(),
            persistent_workers=self.persistent_workers,
            prefetch_factor=self.prefetch_factor,
        )

    def val_dataloader(self) -> DataLoader:
        if self.val_dataset is None:
            raise RuntimeError("Data module has not been set up.")
        return DataLoader(
            self.val_dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=False,
            pin_memory=torch.cuda.is_available(),
            persistent_workers=self.persistent_workers,
            prefetch_factor=self.prefetch_factor,
        )


class TinyClassifier(L.LightningModule):
    def __init__(self, input_dim: int, hidden_dim: int, lr: float) -> None:
        super().__init__()
        self.save_hyperparameters()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 2),
        )
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.network(inputs)

    def _shared_step(self, batch: tuple[torch.Tensor, torch.Tensor], stage: str) -> torch.Tensor:
        features, targets = batch
        logits = self(features)
        loss = self.loss_fn(logits, targets)
        predictions = logits.argmax(dim=1)
        accuracy = (predictions == targets).float().mean()
        sync_dist = self.trainer.world_size > 1

        if stage == "train":
            self.log(
                "train/loss_step",
                loss,
                on_step=True,
                on_epoch=False,
                prog_bar=True,
                batch_size=features.size(0),
                sync_dist=False,
            )

        self.log(
            f"{stage}/loss",
            loss,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            batch_size=features.size(0),
            sync_dist=sync_dist,
        )
        self.log(
            f"{stage}/acc",
            accuracy,
            on_step=False,
            on_epoch=True,
            prog_bar=True,
            batch_size=features.size(0),
            sync_dist=sync_dist,
        )
        return loss

    def training_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        return self._shared_step(batch, "train")

    def validation_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> None:
        self._shared_step(batch, "val")

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)


@rank_zero_only
def print_banner(project_root: Path, runtime: RuntimeConfig, tracking_uri: str) -> None:
    device_name = torch.cuda.get_device_name(0) if runtime.accelerator == "gpu" else "cpu"
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


def resolve_num_workers(requested_workers: int, device_count: int) -> int:
    if requested_workers >= 0:
        return requested_workers

    cpu_count = os.cpu_count() or 8
    process_count = max(1, device_count)
    return max(2, min(8, cpu_count // (process_count * 4)))


def resolve_runtime(cfg: DictConfig) -> RuntimeConfig:
    accelerator = cfg.trainer.accelerator
    if accelerator == "auto":
        accelerator = "gpu" if torch.cuda.is_available() else "cpu"

    devices: int | str = cfg.trainer.devices if accelerator == "gpu" else 1
    if isinstance(devices, str) and devices.isdigit():
        devices = int(devices)
    if accelerator == "gpu" and devices == "auto":
        visible_devices = torch.cuda.device_count()
        devices = visible_devices if visible_devices > 0 else 1

    precision = cfg.trainer.precision
    if precision == "auto":
        if accelerator == "gpu":
            precision = "bf16-mixed" if torch.cuda.is_bf16_supported() else "16-mixed"
        else:
            precision = "32-true"

    strategy = cfg.trainer.strategy
    if accelerator != "gpu":
        strategy = "auto"
    elif strategy == "auto" and isinstance(devices, int) and devices > 1:
        strategy = "ddp_find_unused_parameters_false"

    matmul_precision = cfg.trainer.matmul_precision
    if matmul_precision == "auto":
        matmul_precision = "high" if accelerator == "gpu" else None

    device_count = devices if isinstance(devices, int) else torch.cuda.device_count()
    global_batch_size = cfg.data.batch_size * max(1, device_count if accelerator == "gpu" else 1)
    benchmark = bool(cfg.trainer.benchmark and accelerator == "gpu" and not cfg.trainer.deterministic)

    return RuntimeConfig(
        accelerator=accelerator,
        devices=devices,
        precision=precision,
        strategy=strategy,
        matmul_precision=matmul_precision,
        benchmark=benchmark,
        global_batch_size=global_batch_size,
    )


@hydra.main(config_path="conf", config_name="config", version_base="1.3")
def main(cfg: DictConfig) -> None:
    L.seed_everything(cfg.seed, workers=True)
    runtime = resolve_runtime(cfg)
    device_count = runtime.devices if isinstance(runtime.devices, int) else 1
    num_workers = resolve_num_workers(cfg.data.num_workers, device_count)
    prefetch_factor = cfg.data.prefetch_factor if num_workers > 0 else None
    persistent_workers = bool(cfg.data.persistent_workers and num_workers > 0)

    if runtime.matmul_precision is not None:
        torch.set_float32_matmul_precision(runtime.matmul_precision)

    project_root = Path(get_original_cwd())
    tracking_uri = f"sqlite:///{(project_root / cfg.mlflow.db_file).resolve()}"
    mlflow.set_tracking_uri(tracking_uri)

    logger = MLFlowLogger(
        experiment_name=cfg.mlflow.experiment_name,
        tracking_uri=tracking_uri,
        run_name=cfg.mlflow.run_name,
        log_model=False,
    )
    logger.log_hyperparams(OmegaConf.to_container(cfg, resolve=True))

    datamodule = GaussianBlobDataModule(
        n_samples=cfg.data.n_samples,
        batch_size=cfg.data.batch_size,
        num_workers=num_workers,
        prefetch_factor=prefetch_factor,
        persistent_workers=persistent_workers,
        seed=cfg.seed,
    )
    model = TinyClassifier(
        input_dim=cfg.model.input_dim,
        hidden_dim=cfg.model.hidden_dim,
        lr=cfg.model.lr,
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

    metrics = {
        name: float(value.detach().cpu())
        for name, value in trainer.callback_metrics.items()
        if torch.is_tensor(value)
    }
    print_final_metrics(metrics)


if __name__ == "__main__":
    main()
