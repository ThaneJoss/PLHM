# PLHM

一个基于 PyTorch、Lightning、Hydra 和 MLflow 的 GPU 训练脚手架。

## 项目做什么

- 在一个合成的二维二分类数据集上训练一个小型 MLP。
- 只把 Hydra 用作配置入口。
- 只把 Lightning 用作训练循环适配层。
- 只把 MLflow 用作实验记录层。
- 当 CUDA 可用时自动使用 GPU。

## 模块边界

仓库按职责拆分，方便新手一层一层读：

- `main.py`：Hydra 入口。读取配置后交给应用层。
- `plhm/hydra_loader.py`：把 Hydra 配置转换成框架无关的设置对象。
- `plhm/settings.py`：整个代码库共享的配置 schema。
- `plhm/app.py`：Composition Root。唯一负责把各个框架拼起来的地方。
- `plhm/pytorch/`：纯 PyTorch 代码，负责数据生成和模型定义。
- `plhm/lightning/`：围绕 PyTorch 代码的一层薄 Lightning 适配器。
- `plhm/mlflow.py`：只负责 MLflow 初始化。
- `plhm/integrations/lightning_mlflow.py`：显式收口 Lightning 和 MLflow 的桥接逻辑。
- `plhm/runtime.py`：解析设备、精度和 dataloader 等运行时设置。

依赖方向：

```text
Hydra -> hydra_loader -> settings -> app
app -> Lightning adapters -> PyTorch
app -> MLflow
app -> runtime helpers
```

## 新手阅读顺序

1. `plhm/pytorch/model.py`
2. `plhm/pytorch/data.py`
3. `plhm/lightning/module.py`
4. `plhm/lightning/datamodule.py`
5. `plhm/settings.py`
6. `plhm/app.py`
7. `plhm/hydra_loader.py`
8. `main.py`

## 架构教程

- 详细的设计与解耦分析： [docs/plhm-design-tutorial.md](/root/PLHM/docs/plhm-design-tutorial.md:1)

## 运行方式

```bash
uv sync
uv run python main.py
```

## 常用覆盖参数

```bash
uv run python main.py trainer.max_epochs=10
uv run python main.py trainer.accelerator=gpu trainer.devices=1
uv run python main.py data.batch_size=512 model.hidden_dim=128
```

## 输出内容

- Hydra 运行输出：`outputs/`
- MLflow SQLite 数据库：`mlflow.db`
