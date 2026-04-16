# PLHM

PLHM 是一个用来演示 `P/L/H/M` 架构拆分方式的最小训练项目：

- `P` = PyTorch
- `L` = Lightning
- `H` = Hydra
- `M` = MLflow

它的重点不是模型本身有多复杂，而是如何把训练核心、训练框架、配置系统和实验记录系统拆开，让职责清楚、依赖方向清楚、初学者也能读懂。

## 项目内容

当前示例做了几件很小但足够完整的事：

- 在一个合成的二维二分类数据集上训练一个小型 MLP
- 用 Hydra 作为配置入口
- 用 Lightning 管理训练循环
- 用 MLflow 记录实验信息
- 在 CUDA 可用时自动选择 GPU

## 为什么叫 P/L/H/M

这个仓库把四类职责刻意拆开：

- `P` 层只负责模型和数据本身
- `L` 层只负责把 `P` 层接到训练循环
- `H` 层只负责把配置输入翻译成项目内部对象
- `M` 层只负责实验记录

最重要的约束不是“把代码分成四个目录”，而是：

> P/L/H/M 之间不能到处直接耦合，跨层组装必须集中收口。

当前负责收口的地方是 `plhm/app.py`，也就是整个项目的 Composition Root。

## 当前目录结构

- `main.py`
  Hydra 入口，只接收配置并调用应用层。
- `conf/config.yaml`
  当前示例的默认配置。
- `plhm/settings.py`
  项目内部使用的配置数据结构。
- `plhm/hydra_loader.py`
  把 Hydra 的 `DictConfig` 转换成 `AppSettings`。
- `plhm/pytorch/`
  纯 PyTorch 代码，负责模型和数据。
- `plhm/lightning/`
  薄 Lightning 适配层。
- `plhm/mlflow.py`
  MLflow 基础初始化。
- `plhm/integrations/lightning_mlflow.py`
  Lightning 和 MLflow 的显式桥接代码。
- `plhm/runtime.py`
  运行时设置解析，例如设备、精度、worker 数量。
- `plhm/app.py`
  Composition Root，负责把所有部件组装成一次完整训练。

## 依赖方向

```text
main.py
  -> hydra_loader.py
  -> settings.py
  -> app.py
       -> runtime.py
       -> pytorch/
       -> lightning/
       -> mlflow.py
       -> integrations/lightning_mlflow.py
```

可以把它理解成一句话：

> Hydra 只负责进门，PyTorch 只负责核心，Lightning 和 MLflow 只是适配器，真正的组装只发生在 Composition Root。

## 建议阅读顺序

如果你第一次读这个项目，建议按下面顺序看：

1. `plhm/pytorch/model.py`
2. `plhm/pytorch/data.py`
3. `plhm/lightning/module.py`
4. `plhm/lightning/datamodule.py`
5. `plhm/settings.py`
6. `plhm/runtime.py`
7. `plhm/mlflow.py`
8. `plhm/integrations/lightning_mlflow.py`
9. `plhm/app.py`
10. `plhm/hydra_loader.py`
11. `main.py`

这样读的好处是：先理解训练核心，再理解适配器，最后理解入口和总装。

## 详细教程

更完整的设计分析、边界说明和进一步解耦建议见：

- [docs/plhm-design-tutorial.md](docs/plhm-design-tutorial.md)

## 运行说明

这个仓库的代码编辑可以在本地完成，但依赖安装、训练和测试应当在远程 GPU 环境执行。

远程 GPU 环境中的常用命令示例：

```bash
uv sync
uv run python main.py
```

常用覆盖参数：

```bash
uv run python main.py trainer.max_epochs=10
uv run python main.py trainer.accelerator=gpu trainer.devices=1
uv run python main.py data.batch_size=512 model.hidden_dim=128
```

## 输出内容

- Hydra 输出目录：`outputs/`
- MLflow SQLite 数据库：`mlflow.db`
