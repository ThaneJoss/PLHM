# PLHM

这份 `README` 直接对应当前仓库本身，按“从 0 开始”的顺序讲清楚三件事：

1. 这个项目怎么跑起来
2. 这个项目为什么这样拆
3. 你以后应该改哪里

项目名 `PLHM` 对应四个部分：

- `P` = PyTorch
- `L` = Lightning
- `H` = Hydra
- `M` = MLflow

这个项目的目标不是做一个复杂模型，而是把训练项目里最常见的四类职责拆开：

- PyTorch 负责训练核心
- Lightning 负责训练流程
- Hydra 负责配置入口
- MLflow 负责实验记录

---

## 1. 先知道这个项目在做什么

当前示例很小：

- 数据是二维二分类的高斯点云
- 模型是一个小型 MLP
- 训练通过 Lightning 的 `Trainer.fit(...)` 运行
- 配置由 Hydra 提供
- 实验信息由 MLflow 记录

你可以把它看成一个“最小但完整”的训练项目骨架。以后你换成自己的模型、自己的数据、自己的实验记录方式，整体思路也是类似的。

---

## 2. 运行前你需要知道什么

这个仓库的代码可以在本地编辑，但依赖安装、训练和测试应当在远程 GPU 环境执行。

常用运行方式：

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

运行后常见输出：

- Hydra 输出目录：`outputs/`
- MLflow SQLite 数据库：`mlflow.db`

如果你是第一次接触这类项目，可以先记住一件事：

> `conf/config.yaml` 决定默认行为，命令行覆盖参数决定这一次运行想怎么改。

---

## 3. 第一次运行时，项目内部发生了什么

从你执行下面这条命令开始：

```bash
uv run python main.py
```

项目内部大致会按这个顺序工作：

1. Hydra 读取 `conf/config.yaml`
2. `main.py` 接收 Hydra 配置
3. `plhm/hydra_loader.py` 把 Hydra 的 `DictConfig` 转成项目自己的 `AppSettings`
4. `plhm/app.py` 作为 Composition Root 组装整个训练过程
5. `plhm/runtime.py` 推导设备、精度、worker 等运行时参数
6. `plhm/pytorch/` 提供模型和数据
7. `plhm/lightning/` 把模型和数据接到 Lightning 的训练循环
8. `plhm/mlflow.py` 和 `plhm/integrations/lightning_mlflow.py` 准备 MLflow Logger
9. Lightning 开始训练并汇总指标

如果你先有一个整体流程图，后面再看代码时就不会迷路。

---

## 4. 仓库结构怎么读

当前仓库的核心文件很少：

- [`main.py`](main.py)
- [`conf/config.yaml`](conf/config.yaml)
- [`plhm/settings.py`](plhm/settings.py)
- [`plhm/hydra_loader.py`](plhm/hydra_loader.py)
- [`plhm/runtime.py`](plhm/runtime.py)
- [`plhm/app.py`](plhm/app.py)
- [`plhm/pytorch/model.py`](plhm/pytorch/model.py)
- [`plhm/pytorch/data.py`](plhm/pytorch/data.py)
- [`plhm/lightning/module.py`](plhm/lightning/module.py)
- [`plhm/lightning/datamodule.py`](plhm/lightning/datamodule.py)
- [`plhm/mlflow.py`](plhm/mlflow.py)
- [`plhm/integrations/lightning_mlflow.py`](plhm/integrations/lightning_mlflow.py)

建议按下面顺序阅读：

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

这个顺序不是按“哪个文件最重要”，而是按“初学者最容易顺着理解”来排的。

---

## 5. 先看配置：`conf/config.yaml`

[`conf/config.yaml`](conf/config.yaml) 是整个项目的默认配置入口。

它目前分成几个部分：

- `seed`
- `data`
- `model`
- `trainer`
- `mlflow`
- `hydra`

你可以这样理解：

### `data`

控制数据规模和 dataloader 参数，例如：

- `n_samples`
- `batch_size`
- `num_workers`
- `prefetch_factor`
- `persistent_workers`

### `model`

控制模型结构和优化器学习率，例如：

- `input_dim`
- `hidden_dim`
- `lr`

### `trainer`

控制训练流程和硬件策略，例如：

- `max_epochs`
- `accelerator`
- `devices`
- `strategy`
- `precision`

### `mlflow`

控制实验记录，例如：

- `experiment_name`
- `run_name`
- `db_file`

### `hydra`

控制 Hydra 自己的行为，例如输出目录。

第一次看训练项目时，很多人会急着先看模型文件。实际上先看配置更容易建立全局感，因为你会先知道这个项目到底有哪些“可调旋钮”。

---

## 6. 入口文件：`main.py`

[`main.py`](main.py) 很短：

- 它通过 `@hydra.main(...)` 接收配置
- 调用 `load_app_settings(...)`
- 调用 `run_training(...)`

短是好事。

这说明入口文件没有承担这些职责：

- 没有直接定义模型
- 没有直接创建 Logger
- 没有直接写训练循环
- 没有直接处理 dataloader 细节

如果一个训练项目的 `main.py` 越来越长，通常说明职责已经开始混乱了。

在这个项目里，`main.py` 的定位只有一个：

> 接住 Hydra，交给应用层。

---

## 7. 为什么还需要 `settings.py`

[`plhm/settings.py`](plhm/settings.py) 定义了项目自己的配置数据结构：

- `DataSettings`
- `ModelSettings`
- `TrainerSettings`
- `MlflowSettings`
- `AppSettings`

这一步很关键，因为 Hydra 的 `DictConfig` 虽然方便，但它仍然是 Hydra 的对象，不是项目自己的对象。

这个项目的做法是：

- 先让 Hydra 读配置
- 再尽快把配置翻译成 `AppSettings`
- 后面的代码都尽量围绕 `AppSettings` 工作

这样做有几个好处：

- 类型更清楚
- 自动补全更稳定
- 每个子配置的边界更清楚
- 以后如果不想用 Hydra，替换成本会更低

简单说，`settings.py` 是项目内部自己的“配置语言”。

---

## 8. `hydra_loader.py` 在做什么

[`plhm/hydra_loader.py`](plhm/hydra_loader.py) 的职责很单一：

- 接收 Hydra 的 `DictConfig`
- 转成普通 `dict`
- 再转成 `AppSettings`

为什么要多做这一层？

因为如果你让 Hydra 的 `DictConfig` 一路传到训练层、模型层、日志层，项目就会慢慢变成“到处都依赖 Hydra”。

这个文件的意义就是：

> 把 Hydra 控制在边界上，不让它深入整个项目内部。

这正是 `H` 这一层该做的事。

---

## 9. `P` 层：PyTorch 负责训练核心

`P` 层对应两个文件：

- [`plhm/pytorch/model.py`](plhm/pytorch/model.py)
- [`plhm/pytorch/data.py`](plhm/pytorch/data.py)

### 9.1 模型：`plhm/pytorch/model.py`

这里定义了 `TinyClassifier`，它本质上就是一个普通的 `nn.Module`。

它不关心：

- Hydra 从哪里来
- Lightning 怎么训练
- MLflow 怎么记录

它只关心一件事：

- 输入一个张量，输出一个分类 logits

这就是 `P` 层该有的样子。模型层应该尽可能“只谈模型”。

### 9.2 数据：`plhm/pytorch/data.py`

这里定义了：

- `DatasetSplits`
- `build_gaussian_blob_dataset(...)`
- `build_gaussian_blob_splits(...)`

它负责生成数据、打乱数据、切分训练集和验证集。

它同样不关心：

- Hydra
- Lightning Trainer
- MLflow

它只关心数据本身。

### 9.3 你应该怎么理解 `P` 层

可以把 `P` 层理解成：

> 这个项目里真正与“训练内容”有关的东西。

如果你以后要：

- 换模型
- 换数据
- 换输入维度
- 换输出类别数

你大概率应该先看 `P` 层。

---

## 10. `L` 层：Lightning 负责训练流程适配

`L` 层对应：

- [`plhm/lightning/module.py`](plhm/lightning/module.py)
- [`plhm/lightning/datamodule.py`](plhm/lightning/datamodule.py)

### 10.1 `ClassificationModule`

这个类做了几件标准 Lightning 事情：

- 定义 `training_step`
- 定义 `validation_step`
- 定义 `configure_optimizers`
- 调用 `self.log(...)`

这里最值得注意的一点不是它做了什么，而是它没做什么：

- 它没有自己定义网络结构
- 它接收外部传进来的 `network`
- 它接收外部传进来的 `optimizer_config`

这说明：

> LightningModule 在这里不是训练核心本身，而是训练流程的适配器。

### 10.2 `GaussianBlobDataModule`

这个类也有同样的特点：

- 它没有把数据写死在内部
- 它接收一个 `dataset_factory`
- 它负责把 dataset 封装成 dataloader

也就是说，DataModule 在这里承担的是“接线”和“适配”，不是“拥有数据逻辑”。

### 10.3 你应该怎么理解 `L` 层

如果 `P` 层是在回答“训练什么”，那 `L` 层是在回答：

> 这些训练对象要怎么接进 Lightning 的训练生命周期。

如果以后你想改：

- `training_step`
- `validation_step`
- optimizer 行为
- dataloader 封装方式

你大概率应该先看 `L` 层。

---

## 11. `runtime.py` 为什么单独存在

[`plhm/runtime.py`](plhm/runtime.py) 负责把配置和机器环境结合起来，得到真正的运行时参数。

它会处理这些事情：

- `accelerator` 到底是 `cpu` 还是 `gpu`
- `devices` 到底是多少
- `precision` 怎么选
- `strategy` 怎么选
- dataloader worker 怎么推导

为什么不把这些逻辑直接写进 `main.py` 或 `app.py`？

因为这类逻辑虽然不属于训练核心，但也绝不是“随手一写”的杂项。它们是硬件和执行策略的一部分，单独放一个模块会更清楚。

如果以后你要支持：

- 单卡
- 多卡
- 混合精度
- 不同 worker 策略

这一层就会非常重要。

---

## 12. `M` 层：MLflow 只负责实验记录

`M` 层对应：

- [`plhm/mlflow.py`](plhm/mlflow.py)
- [`plhm/integrations/lightning_mlflow.py`](plhm/integrations/lightning_mlflow.py)

### 12.1 `plhm/mlflow.py`

这里只做一件事：

- 构造 Tracking URI

### 12.2 `plhm/integrations/lightning_mlflow.py`

这里做的是跨框架桥接：

- 创建 `MLflowLogger`
- 把配置和运行时参数展开成可记录的形式

这个文件存在的价值很大，因为最容易把项目写乱的不是单个框架代码，而是“跨框架胶水代码”。

如果你在很多地方同时写：

- 一点 Hydra
- 一点 Lightning
- 一点 MLflow

最后往往会变成到处都是耦合。

这个项目把这类桥接逻辑明确收口到了 `integrations/`，这是一个很好的习惯。

---

## 13. `app.py` 才是全项目真正的总装处

[`plhm/app.py`](plhm/app.py) 是 Composition Root。

它知道全局，但别的模块不应该知道全局。

在这里你会看到完整装配过程：

- 先拿到 `AppSettings`
- 再解析 runtime
- 再构造 MLflow Logger
- 再构造 DataModule
- 再构造网络
- 再构造 LightningModule
- 再构造 Trainer
- 最后启动训练

如果你想知道“整个项目到底怎么从配置走到训练”，这一份文件就是最直接的答案。

也可以换个说法：

> 项目允许在 Composition Root 里集中耦合，但不允许到处零散耦合。

---

## 14. 现在这套设计好在哪里

很多训练项目在一开始都能跑，但后面会很难维护。原因往往不是模型难，而是结构乱。

这个项目当前已经做对了几件事：

- 入口和应用组装分开
- Hydra 配置对象和项目内部对象分开
- PyTorch 核心和 Lightning 生命周期分开
- MLflow 相关逻辑没有四处散落
- 跨框架桥接代码有明确位置

所以它虽然小，但已经不是“脚本堆砌”，而是一套可以继续长的最小架构。

---

## 15. 现在这套设计还没有完全解耦的地方

一个项目是否健康，不只看它拆了什么，也要看它还耦合在哪里。

当前项目仍然有几个真实的耦合点：

### 15.1 `app.py` 天然是集中耦合点

这不是问题，Composition Root 本来就应该集中知道全局。

### 15.2 `ClassificationModule` 仍然带着分类任务假设

它内部仍然直接使用：

- `CrossEntropyLoss`
- accuracy
- 当前的 metric 命名方式

这说明它不只是 Lightning 适配器，还是“分类任务”的适配器。

### 15.3 `runtime.py` 把环境探测和策略决策放在一起

以后如果继续细拆，可以分成：

- `hardware_probe`
- `runtime_policy`

### 15.4 `reporting.py` 里还带着框架知识

如果以后继续长，可以把它再拆成：

- `environment_snapshot`
- `report_renderer`

这些都不是现在必须立刻改的事，但你应该知道耦合点还在哪里。

---

## 16. 如果你现在要改项目，应该改哪里

这一节最适合真正准备动手的人。

### 想改模型结构

优先改：

- [`plhm/pytorch/model.py`](plhm/pytorch/model.py)

### 想改数据集或数据生成方式

优先改：

- [`plhm/pytorch/data.py`](plhm/pytorch/data.py)

必要时再去：

- [`plhm/app.py`](plhm/app.py)

调整 `dataset_factory` 的接线方式。

### 想改训练 step、loss、optimizer

优先改：

- [`plhm/lightning/module.py`](plhm/lightning/module.py)

### 想改默认配置

优先改：

- [`conf/config.yaml`](conf/config.yaml)
- [`plhm/settings.py`](plhm/settings.py)
- [`plhm/hydra_loader.py`](plhm/hydra_loader.py)

### 想改实验记录方式

优先改：

- [`plhm/mlflow.py`](plhm/mlflow.py)
- [`plhm/integrations/lightning_mlflow.py`](plhm/integrations/lightning_mlflow.py)

---

## 17. 如果继续重构，下一步最值得做什么

如果你想在当前基础上继续把 `P/L/H/M` 架构做得更清楚，可以按下面顺序继续：

1. 把任务逻辑从 LightningModule 拆出来
2. 把优化器创建逻辑变成工厂
3. 把环境探测和运行时策略拆开
4. 把 Experiment Logger 再抽象一层
5. 把 Hydra 配置拆成 Config Groups
6. 给边界层补单元测试

对应的方向大概会像这样：

- `task/`
- `optimizer_factory`
- `hardware_probe`
- `runtime_policy`
- `experiment_logger_factory`

这一步不是现在必须马上做，而是当项目开始继续变大时，可以顺着这个方向演进。

---

## 18. 最后给一个一句话总结

如果你只想记住这个项目的一句话，可以记这个：

> `P/L/H/M` 架构的核心，不是用了哪四个框架，而是把“训练核心、训练流程、配置入口、实验记录”四类职责拆开，并把跨层组装集中收口到 Composition Root。
