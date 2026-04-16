# PLHM

GPU-capable training scaffold built with PyTorch, Lightning, Hydra, and MLflow.

## What it does

- Trains a compact MLP on a synthetic 2D binary classification dataset.
- Uses Hydra only as the configuration entrypoint.
- Uses Lightning only as the training-loop adapter.
- Uses MLflow only as the experiment tracker.
- Uses GPU automatically when CUDA is available.

## Module boundaries

The repository is split by responsibility so beginners can follow one layer at a time:

- `main.py`: Hydra entrypoint. Reads config and hands off to the app layer.
- `plhm/hydra_loader.py`: Converts Hydra config into framework-neutral settings objects.
- `plhm/settings.py`: Shared config schema used by the rest of the codebase.
- `plhm/app.py`: Composition root. The only place that wires frameworks together.
- `plhm/pytorch/`: Pure PyTorch code for data generation and model definition.
- `plhm/lightning/`: Thin Lightning adapters around the PyTorch code.
- `plhm/mlflow.py`: MLflow-only setup.
- `plhm/integrations/lightning_mlflow.py`: Explicit bridge between Lightning and MLflow.
- `plhm/runtime.py`: Runtime resolution for devices, precision, and dataloader settings.

Dependency flow:

```text
Hydra -> hydra_loader -> settings -> app
app -> Lightning adapters -> PyTorch
app -> MLflow
app -> runtime helpers
```

## Read order for beginners

1. `plhm/pytorch/model.py`
2. `plhm/pytorch/data.py`
3. `plhm/lightning/module.py`
4. `plhm/lightning/datamodule.py`
5. `plhm/settings.py`
6. `plhm/app.py`
7. `plhm/hydra_loader.py`
8. `main.py`

## Run

```bash
uv sync
uv run python main.py
```

## Useful overrides

```bash
uv run python main.py trainer.max_epochs=10
uv run python main.py trainer.accelerator=gpu trainer.devices=1
uv run python main.py data.batch_size=512 model.hidden_dim=128
```

## Outputs

- Hydra run outputs: `outputs/`
- MLflow SQLite database: `mlflow.db`
