from __future__ import annotations

from collections.abc import Callable

import lightning as L
from torch.utils.data import DataLoader, Dataset

from plhm.pytorch.data import DatasetSplits


class GaussianBlobDataModule(L.LightningDataModule):
    def __init__(
        self,
        dataset_factory: Callable[[], DatasetSplits],
        batch_size: int,
        num_workers: int,
        prefetch_factor: int | None,
        persistent_workers: bool,
        pin_memory: bool,
    ) -> None:
        super().__init__()
        self.dataset_factory = dataset_factory
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.prefetch_factor = prefetch_factor
        self.persistent_workers = persistent_workers
        self.pin_memory = pin_memory
        self.train_dataset: Dataset | None = None
        self.val_dataset: Dataset | None = None

    def setup(self, stage: str | None = None) -> None:
        if self.train_dataset is None or self.val_dataset is None:
            splits = self.dataset_factory()
            self.train_dataset = splits.train
            self.val_dataset = splits.val

    def _build_dataloader(self, dataset: Dataset, shuffle: bool) -> DataLoader:
        return DataLoader(
            dataset,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            shuffle=shuffle,
            pin_memory=self.pin_memory,
            persistent_workers=self.persistent_workers,
            prefetch_factor=self.prefetch_factor,
        )

    def train_dataloader(self) -> DataLoader:
        if self.train_dataset is None:
            raise RuntimeError("Data module has not been set up.")
        return self._build_dataloader(self.train_dataset, shuffle=True)

    def val_dataloader(self) -> DataLoader:
        if self.val_dataset is None:
            raise RuntimeError("Data module has not been set up.")
        return self._build_dataloader(self.val_dataset, shuffle=False)
