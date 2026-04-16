# PLHM

GPU-capable training scaffold built with PyTorch, Lightning, Hydra, and MLflow.

## What it does

- Trains a compact MLP on a synthetic 2D binary classification dataset.
- Uses Hydra for configuration.
- Uses Lightning for the training loop.
- Uses MLflow for experiment logging.
- Uses GPU automatically when CUDA is available.

## Run

```bash
export PATH="$HOME/.local/bin:$PATH"
cd ~/PLHM
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
- MLflow tracking data: `mlruns/`
