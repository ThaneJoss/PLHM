# PLHM

`PLHM` 是一个最小但完整的训练项目骨架，名字来自四个组成部分：

- `P` = PyTorch
- `L` = Lightning
- `H` = Hydra
- `M` = MLflow

如果你只想先记住一句话，可以记这句：

> `PLHM` 不是“大而全训练框架”，而是一个把训练入口、配置边界、训练循环和实验记录拆清楚的示例项目。

---

## 1. 项目定位

项目名：`PLHM`

项目类型：训练项目骨架

当前示例任务：二维二分类高斯点云

当前附带工具：

- 训练入口：`main.py`
- 结构观察工具：`depgraph`

---

## 2. 适用场景

这个仓库适合这些场景：

- 想快速搭一个结构清楚的训练项目
- 想学习 `PyTorch + Lightning + Hydra + MLflow` 的基本职责边界
- 想把“配置对象”和“项目内部对象”分开
- 想用一个最小例子理解 `Composition Root` 应该放在哪里
- 想观察仓库内部模块的 `import` 依赖关系

---

## 3. 非目标

这个仓库当前不适合这些预期：

- 把它当成生产级大规模训练平台
- 把它当成包含所有算法组件的框架
- 期待这里直接提供运行时 tracing、函数调用图或 tensor/dataflow 可视化
- 期待这里自动解决实验调度、分布式集群运维、模型注册全流程

简单说，它现在解决的是“结构清晰”和“最小可运行”，不是“全家桶”。

---

## 4. 模块职责总览

下面这张表可以把仓库里的关键模块快速对上号。

| 模块 | 负责什么 | 输入 | 输出 |
| --- | --- | --- | --- |
| [`main.py`](main.py) | 训练入口，只接住 Hydra | `DictConfig` | 调用应用层 |
| [`plhm/hydra_loader.py`](plhm/hydra_loader.py) | 把 Hydra 配置转成项目内部配置对象 | `DictConfig` | `AppSettings` |
| [`plhm/settings.py`](plhm/settings.py) | 定义项目内部配置 contract | 普通 Python 值 | `AppSettings` 及其子结构 |
| [`plhm/app.py`](plhm/app.py) | `Composition Root`，负责组装训练所需对象 | `AppSettings`、项目根目录 | 训练执行结果 |
| [`plhm/runtime.py`](plhm/runtime.py) | 推导设备、precision、worker 等运行时参数 | `TrainerSettings`、`DataSettings` | `RuntimeConfig`、`DataLoaderConfig` |
| [`plhm/pytorch/`](plhm/pytorch/) | 纯训练核心，包括数据和模型 | 普通 Python 参数 | 数据集与模型对象 |
| [`plhm/lightning/`](plhm/lightning/) | Lightning 适配层，把模型和数据接到训练循环 | 模型、数据配置 | `LightningModule`、`LightningDataModule` |
| [`plhm/mlflow.py`](plhm/mlflow.py) | 构造 MLflow `Tracking URI` | 项目根目录、数据库文件名 | URI 字符串 |
| [`plhm/integrations/lightning_mlflow.py`](plhm/integrations/lightning_mlflow.py) | 组装 Lightning 的 MLflow Logger | `AppSettings`、`RuntimeConfig` | `MLFlowLogger` |
| [`plhm/depgraph/`](plhm/depgraph/) | 导出结构快照、提供只读 API 和浏览器面板 | 仓库源码 | `GraphSnapshot`、本地页面与接口 |

---

## 5. 仓库结构与阅读顺序

当前仓库结构的核心部分如下：

```text
.
├── main.py
├── conf/
│   └── config.yaml
├── plhm/
│   ├── app.py
│   ├── hydra_loader.py
│   ├── settings.py
│   ├── runtime.py
│   ├── mlflow.py
│   ├── pytorch/
│   ├── lightning/
│   ├── integrations/
│   └── depgraph/
├── frontend/
│   └── depgraph/
├── PLAN.md
└── DEPGRAPH.md
```

建议阅读顺序：

1. [`conf/config.yaml`](conf/config.yaml)
2. [`main.py`](main.py)
3. [`plhm/settings.py`](plhm/settings.py)
4. [`plhm/hydra_loader.py`](plhm/hydra_loader.py)
5. [`plhm/pytorch/model.py`](plhm/pytorch/model.py)
6. [`plhm/pytorch/data.py`](plhm/pytorch/data.py)
7. [`plhm/lightning/module.py`](plhm/lightning/module.py)
8. [`plhm/lightning/datamodule.py`](plhm/lightning/datamodule.py)
9. [`plhm/runtime.py`](plhm/runtime.py)
10. [`plhm/mlflow.py`](plhm/mlflow.py)
11. [`plhm/integrations/lightning_mlflow.py`](plhm/integrations/lightning_mlflow.py)
12. [`plhm/app.py`](plhm/app.py)

---

## 6. 环境与默认配置

当前项目的基础环境如下：

- Python：`>=3.13,<3.14`
- 核心依赖：
  - `hydra-core==1.3.2`
  - `lightning==2.6.1`
  - `mlflow==3.11.1`
  - `torch==2.6.0`

默认配置来自 [`conf/config.yaml`](conf/config.yaml)。

其中最重要的默认项有：

- `data.n_samples = 262144`
- `data.batch_size = 2048`
- `model.hidden_dim = 256`
- `trainer.max_epochs = 5`
- `trainer.accelerator = auto`
- `trainer.devices = auto`
- `mlflow.experiment_name = plhm`
- `mlflow.run_name = train`

这意味着你即使不传任何覆盖参数，也能得到一个完整训练流程。

---

## 7. 常用命令

### 7.1 训练入口

最常见的运行方式是：

```bash
uv run python main.py
```

常见覆盖参数：

```bash
uv run python main.py trainer.max_epochs=10
uv run python main.py trainer.accelerator=gpu trainer.devices=1
uv run python main.py data.batch_size=512 model.hidden_dim=128
```

### 7.2 depgraph 导出

如果你只想导出当前结构快照：

```bash
uv run plhm-depgraph export --root . --output graph.json
```

### 7.3 depgraph 面板

如果你想直接看结构图：

```bash
uv run plhm-depgraph serve --root . --host 127.0.0.1 --port 8765
```

然后访问：

```text
http://127.0.0.1:8765
```

这里推荐显式通过 `uv run` 启动，而不是直接用系统 `python` 或裸跑 `plhm-depgraph`，因为 `depgraph` 对 Python 版本和项目环境有依赖，跑到默认解释器时很容易出现版本不一致或缺依赖导致的启动失败。

更完整的 `depgraph` 用法见 [DEPGRAPH.md](DEPGRAPH.md)。

---

## 8. 运行流程

如果你执行的是：

```bash
uv run python main.py
```

项目内部会按这个顺序工作：

1. Hydra 读取 [`conf/config.yaml`](conf/config.yaml)
2. [`main.py`](main.py) 接收 `DictConfig`
3. [`plhm/hydra_loader.py`](plhm/hydra_loader.py) 把 `DictConfig` 转成 `AppSettings`
4. [`plhm/app.py`](plhm/app.py) 作为 `Composition Root` 组装对象
5. [`plhm/runtime.py`](plhm/runtime.py) 推导运行时策略
6. [`plhm/pytorch/`](plhm/pytorch/) 构造数据和模型
7. [`plhm/lightning/`](plhm/lightning/) 接入 Lightning 训练循环
8. [`plhm/mlflow.py`](plhm/mlflow.py) 和 [`plhm/integrations/lightning_mlflow.py`](plhm/integrations/lightning_mlflow.py) 准备 MLflow 记录
9. Lightning 开始训练并输出最终指标

如果你执行的是：

```bash
uv run plhm-depgraph serve --root . --host 127.0.0.1 --port 8765
```

则流程会变成：

1. 分析仓库内部 Python 模块
2. 构建 `GraphSnapshot`
3. 提供 `/api/depgraph/snapshot`
4. 提供 `/api/depgraph/events`
5. 浏览器页面读取快照并展示 package/file 视图
6. 文件变化后 watcher 重建快照并通过 `SSE` 通知前端

---

## 9. 开发约束

这部分最重要，不是“友情提示”，而是结构纪律。

### 9.1 不要把 Hydra 深传进项目内部

`DictConfig` 应该尽快被转换成 `AppSettings`。

也就是说：

- 可以让 Hydra 停在入口层
- 不要让模型层、训练层、日志层直接依赖 Hydra 对象

### 9.2 不要把组装逻辑堆进 `main.py`

[`main.py`](main.py) 现在刻意保持很短。

如果你开始在里面做这些事情，说明结构在退化：

- 直接 new 模型
- 直接 new Logger
- 直接写训练循环
- 直接做 dataloader 细节处理

这些应该集中在 [`plhm/app.py`](plhm/app.py)。

### 9.3 不要让低层反向依赖高层

当前 `depgraph` 默认层级方向是：

`entry -> adapter -> support -> core`

允许高层依赖低层，不允许反向依赖。

### 9.4 不要把 `depgraph` 当成运行时追踪器

它当前看的是静态 `import` 关系，不是运行时调用链。

---

## 10. 组件协作关系

这个项目里几个核心组件的配合方式如下：

- Hydra
  - 负责读取配置
  - 不负责训练细节
- Lightning
  - 负责训练循环
  - 不负责项目级配置转换
- PyTorch
  - 负责模型和数据核心
  - 不负责实验记录
- MLflow
  - 负责记录实验信息
  - 不负责训练组装
- depgraph
  - 负责观察结构
  - 不参与训练执行

如果某个组件开始承担上面不属于它的职责，通常就说明边界开始糊了。

---

## 11. 常见问题与排查

### 11.1 训练跑不起来

优先看这几件事：

- Python 版本是否满足 `>=3.13,<3.14`
- 依赖是否已经安装完整
- `uv run python main.py` 是否能正常读取配置

### 11.2 GPU 没有被用上

优先检查：

- 是否传了 `trainer.accelerator=gpu`
- 是否传了合适的 `trainer.devices`
- 当前环境是否真的可见 CUDA

### 11.3 想改配置但不知道改哪里

先看 [`conf/config.yaml`](conf/config.yaml)，再决定是否用命令行覆盖。

### 11.4 `main.py` 越改越长

这通常不是“功能变多了”，而是职责开始泄漏。

优先把逻辑回收到：

- [`plhm/hydra_loader.py`](plhm/hydra_loader.py)
- [`plhm/app.py`](plhm/app.py)
- [`plhm/runtime.py`](plhm/runtime.py)

### 11.5 depgraph 页面打不开

先检查：

- 是否已经执行 `serve`
- 访问地址是否和 `--host`、`--port` 一致
- `/api/depgraph/snapshot` 是否能返回 JSON

### 11.6 depgraph 没看到想要的关系

先确认：

- 这是不是仓库内部模块之间的 `import`
- 这是不是 Python 文件级关系，而不是函数调用关系
- 这是不是当前版本明确支持的范围

---

## 12. 输出与产物

训练运行后常见产物：

- `outputs/`
  - Hydra 的运行输出目录
- `mlflow.db`
  - MLflow SQLite 数据库

depgraph 运行后常见产物：

- `graph.json`
  - 导出的结构快照

`GraphSnapshot` 顶层字段包括：

- `version`
- `generated_at`
- `summary`
- `nodes`
- `edges`
- `violations`

---

## 13. 延伸阅读

如果你想继续往下看，建议按这个顺序：

1. [DEPGRAPH.md](DEPGRAPH.md)
2. [PLAN.md](PLAN.md)
3. [`conf/config.yaml`](conf/config.yaml)
4. [`plhm/app.py`](plhm/app.py)

如果你只是想快速上手：

1. 先跑一次训练
2. 再开一次 `depgraph`
3. 然后对着页面回看模块边界

这样比直接从源代码里硬读要快很多。
