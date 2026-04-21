from __future__ import annotations

from dataclasses import dataclass

import lightning as L
import torch
from torch import nn


@dataclass(frozen=True)
class OptimizerConfig:
    lr: float


class ClassificationModule(L.LightningModule):
    def __init__(self, network: nn.Module, optimizer_config: OptimizerConfig) -> None:
        super().__init__()
        self.network = network
        self.optimizer_config = optimizer_config
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
        return torch.optim.Adam(self.parameters(), lr=self.optimizer_config.lr)
