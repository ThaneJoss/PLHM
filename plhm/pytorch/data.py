from __future__ import annotations

from dataclasses import dataclass

import torch
from torch.utils.data import Dataset, TensorDataset, random_split


@dataclass(frozen=True)
class DatasetSplits:
    train: Dataset
    val: Dataset


def build_gaussian_blob_dataset(n_samples: int, seed: int) -> TensorDataset:
    generator = torch.Generator().manual_seed(seed)
    half = n_samples // 2

    class_zero = torch.randn(half, 2, generator=generator) * 0.9 + torch.tensor([-2.0, -2.0])
    class_one = torch.randn(n_samples - half, 2, generator=generator) * 0.9 + torch.tensor([2.0, 2.0])

    features = torch.cat([class_zero, class_one], dim=0)
    labels = torch.cat(
        [
            torch.zeros(half, dtype=torch.long),
            torch.ones(n_samples - half, dtype=torch.long),
        ]
    )

    permutation = torch.randperm(n_samples, generator=generator)
    features = features[permutation]
    labels = labels[permutation]
    return TensorDataset(features, labels)


def build_gaussian_blob_splits(
    n_samples: int,
    seed: int,
    train_fraction: float = 0.8,
) -> DatasetSplits:
    dataset = build_gaussian_blob_dataset(n_samples=n_samples, seed=seed)
    generator = torch.Generator().manual_seed(seed)

    train_size = int(train_fraction * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size], generator=generator)
    return DatasetSplits(train=train_dataset, val=val_dataset)
