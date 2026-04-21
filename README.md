# PLHM

基于 PyTorch、Lightning、Hydra 和 MLflow 构建的 GPU 训练脚手架。

## 功能

- 在一个合成的二维二分类数据集上训练紧凑型 MLP。
- 使用 Hydra 管理配置。
- 使用 Lightning 驱动训练流程。
- 使用 MLflow 记录实验结果。
- 在 CUDA 可用时自动启用 GPU。

## 运行

```bash
export PATH="$HOME/.local/bin:$PATH"
cd <仓库根目录>
uv sync
uv run python main.py
```

## 常用覆盖参数

```bash
uv run python main.py trainer.max_epochs=10
uv run python main.py trainer.accelerator=gpu trainer.devices=1
uv run python main.py data.batch_size=512 model.hidden_dim=128
```

## 输出

- Hydra 运行输出：`outputs/`
- MLflow 跟踪数据：`mlruns/`
