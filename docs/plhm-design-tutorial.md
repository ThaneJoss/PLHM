# PLHM 架构设计教程

## 1. 这个项目到底在做什么

PLHM 是一个刻意做得很小的训练项目。它的业务内容非常简单：

- 数据是二维二分类的高斯点云
- 模型是一个小型 MLP
- 训练通过 Lightning 的 `Trainer.fit(...)` 运行
- 配置从 Hydra 进入
- 实验记录交给 MLflow

之所以把例子做得这么小，不是因为项目目标小，而是因为这里真正要展示的是架构：

> 当一个训练项目同时用了 PyTorch、Lightning、Hydra、MLflow，怎样拆才能不把代码写成一个大泥球。

## 2. P/L/H/M 不是四个库名，而是四类职责

PLHM 里的四个字母可以直接这样理解：

- `P` = PyTorch
- `L` = Lightning
- `H` = Hydra
- `M` = MLflow

但更重要的是，它们在这个项目里分别代表四类职责：

- `P` 负责训练核心：模型、张量、数据
- `L` 负责训练流程：step、optimizer、dataloader 生命周期
- `H` 负责配置入口：默认值、命令行覆盖、配置装载
- `M` 负责实验记录：tracking URI、logger、超参数记录

如果只把它们理解成“用了四个框架”，那这个项目就很普通。

如果把它们理解成“四类职责必须分开”，你才会真正明白这个仓库为什么要这样写。

## 3. 当前代码的总体形状

先看最重要的依赖方向：

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

这张图里最关键的不是文件数量，而是方向：

- `main.py` 只负责进门
- `hydra_loader.py` 只负责把 Hydra 对象翻译成项目对象
- `settings.py` 定义项目自己的配置语言
- `app.py` 是 Composition Root
- `pytorch/` 是训练核心
- `lightning/` 是训练适配器
- `mlflow.py` 和 `integrations/` 是实验记录边界

这意味着：

> 不是每一层都能知道所有东西，只有 Composition Root 可以看到全局。

## 4. 为什么要有 Composition Root

这个项目里最关键的文件是 [`plhm/app.py`](../plhm/app.py)。

它的地位不是“主逻辑文件”，而是 Composition Root，也就是唯一负责“总装”的地方。

在这个文件里，项目完成了这些动作：

1. 拿到 `AppSettings`
2. 推导运行时设置
3. 构造 MLflow Logger
4. 构造 `GaussianBlobDataModule`
5. 构造 `TinyClassifier`
6. 构造 `ClassificationModule`
7. 构造 `L.Trainer`
8. 调用 `trainer.fit(...)`
9. 收集最终指标

这里有一个很重要的工程原则：

> 耦合本身不是罪，分散的耦合才是罪。

`app.py` 允许耦合，因为它本来就是用来收口耦合的。真正要避免的是：

- 在 `main.py` 拼一点
- 在 `lightning/module.py` 再拼一点
- 在 `mlflow.py` 再偷塞一点

那样最后你根本不知道项目真正的组装发生在哪里。

## 5. 从入口到训练完成，代码怎么流动

### 5.1 `main.py` 只做入口

[`main.py`](../main.py) 很短，这是刻意设计的结果。

它只做三件事：

1. 通过 `@hydra.main(...)` 接收配置
2. 调用 `load_app_settings(...)`
3. 调用 `run_training(...)`

它不做这些事：

- 不定义模型
- 不创建 Logger
- 不解析设备策略
- 不构造 Trainer

这样入口就不会变成“大控制器”。

### 5.2 `hydra_loader.py` 把 Hydra 挡在边界上

[`plhm/hydra_loader.py`](../plhm/hydra_loader.py) 的职责非常纯粹：

- 接收 Hydra 的 `DictConfig`
- 转成普通 `dict`
- 再转成 `AppSettings`

这一步的意义非常大，因为 Hydra 的 `DictConfig` 虽然好用，但它本质上仍然是框架对象。

如果你让它一路传进模型层、训练层、日志层，会出现两个问题：

1. 每一层都开始依赖 Hydra
2. 以后要换配置系统时，重构成本会陡增

所以这个项目的做法是：

> Hydra 对象一进门就被翻译成项目自己的对象。

这是 `H` 层最重要的边界。

### 5.3 `settings.py` 定义项目内部协议

[`plhm/settings.py`](../plhm/settings.py) 定义了：

- `DataSettings`
- `ModelSettings`
- `TrainerSettings`
- `MlflowSettings`
- `AppSettings`

这几个 dataclass 的价值不只是“好看”，而是它们让项目后面的代码都围绕自己的协议工作，而不是围绕 Hydra 的协议工作。

这会带来几个直接收益：

- 类型更清楚
- IDE 补全更稳定
- 配置结构更可读
- 子模块边界更明确

简单说：

> `settings.py` 让项目拥有了自己的语言。

### 5.4 `runtime.py` 负责“根据环境做决定”

[`plhm/runtime.py`](../plhm/runtime.py) 负责把配置和机器状态组合起来，得到真正用于训练的运行时设置。

它处理的内容包括：

- accelerator 的选择
- devices 的解析
- precision 的选择
- strategy 的推导
- dataloader worker 数量的推导

这层存在的意义是：不要把这些环境决策散在 `main.py`、`app.py`、`lightning/module.py` 里。

否则以后你一旦需要：

- 切换 CPU/GPU
- 增加多卡策略
- 调整 BF16/FP16

这些判断就会四处蔓延。

## 6. P/L/H/M 四层各自应该负责什么

这一节是这个项目最核心的阅读方式。

### 6.1 P 层：PyTorch 只负责训练核心

对应文件：

- [`plhm/pytorch/model.py`](../plhm/pytorch/model.py)
- [`plhm/pytorch/data.py`](../plhm/pytorch/data.py)

P 层应该负责：

- 模型结构
- 前向计算
- 张量和数据集构造
- 数据切分

P 层不应该负责：

- Hydra 配置装载
- Lightning 生命周期
- MLflow 记录逻辑
- 设备和精度策略

当前实现的优点很清楚：

- `TinyClassifier` 是纯 `nn.Module`
- `build_gaussian_blob_dataset(...)` 是纯 PyTorch 数据逻辑
- `build_gaussian_blob_splits(...)` 仍然保持在数据层，而没有溢出到训练框架里

这意味着你要替换模型和数据时，可以先只动 `P` 层，不一定要碰 `L/H/M`。

### 6.2 L 层：Lightning 只是训练流程适配器

对应文件：

- [`plhm/lightning/module.py`](../plhm/lightning/module.py)
- [`plhm/lightning/datamodule.py`](../plhm/lightning/datamodule.py)

L 层应该负责：

- `training_step` / `validation_step`
- `configure_optimizers`
- DataModule 形式
- 与 Trainer 生命周期对接

L 层不应该负责：

- 自己定义业务模型
- 自己决定配置来源
- 自己创建 MLflow Logger
- 自己推导硬件和精度策略

当前实现里有两个很好的地方：

- `ClassificationModule` 接收 `network`
- `GaussianBlobDataModule` 接收 `dataset_factory`

这两个设计都在表达同一个意思：

> Lightning 不应该拥有训练核心，它只应该接住训练核心。

这正是 `L` 层应有的边界。

### 6.3 H 层：Hydra 只负责把配置送进来

对应文件：

- [`main.py`](../main.py)
- [`plhm/hydra_loader.py`](../plhm/hydra_loader.py)
- [`conf/config.yaml`](../conf/config.yaml)

H 层应该负责：

- 默认值
- 命令行覆盖
- 配置装载
- 配置翻译

H 层不应该负责：

- 训练流程
- 模型结构
- Logger 创建
- 数据逻辑

这一层最重要的不是“会不会写 Hydra”，而是“有没有把 Hydra 控制在边界上”。

当前项目在这件事上是做对了的，因为 `DictConfig` 没有继续向里层扩散。

### 6.4 M 层：MLflow 只负责记录，不负责训练

对应文件：

- [`plhm/mlflow.py`](../plhm/mlflow.py)
- [`plhm/integrations/lightning_mlflow.py`](../plhm/integrations/lightning_mlflow.py)

M 层应该负责：

- Tracking URI 构造
- MLflow Logger 构造
- 超参数展开和记录

M 层不应该负责：

- 模型定义
- 训练 step
- 硬件策略
- 数据生成

这一层最关键的设计点不是 `mlflow.py` 本身，而是 `integrations/lightning_mlflow.py` 的存在。

因为真正容易失控的不是“单一框架代码”，而是“跨框架胶水代码”。只要 Lightning 和 MLflow 的桥接代码被明确收口，项目就不会出现到处乱插 logger 调用的情况。

## 7. 这个项目现在已经做对了什么

很多 MVP 的常见写法是把下面这些东西全部塞进一个 `main.py`：

- 读配置
- 定义模型
- 定义数据
- 创建 dataloader
- 创建 logger
- 创建 trainer
- 打印环境信息
- 开始训练
- 汇总结果

这种写法的最大问题不是文件长，而是职责完全混在一起。

PLHM 当前已经避免了最糟糕的几种耦合：

- 入口和组装分离
- 配置对象和内部对象分离
- PyTorch 核心和 Lightning 生命周期分离
- MLflow 和训练流程的桥接代码单独收口

这说明它已经不是一个“能跑就行”的脚本，而是一个可以继续往上长的最小架构。

## 8. 这个项目现在还耦合在哪里

说清优点不难，真正有价值的是把剩余耦合也讲清楚。

### 8.1 `app.py` 是主动保留的集中耦合点

`app.py` 确实耦合很多模块，但这是设计结果，不是设计失败。

Composition Root 本来就应该知道：

- 配置对象
- 训练核心
- 训练适配器
- 日志适配器
- 运行时设置

只要这种全局耦合只出现在一个短小、稳定、容易读的文件里，它就是可接受的。

### 8.2 `ClassificationModule` 仍然带着任务假设

现在的 `ClassificationModule` 里仍然直接内嵌了：

- `CrossEntropyLoss`
- accuracy 计算
- metric 名称规则

这说明它不只是 Lightning 适配器，它还是“分类任务适配器”。

这没错，但如果以后项目要支持：

- 多标签任务
- 回归
- 多任务训练

你就会发现这里是一个真实的变化点。

### 8.3 `runtime.py` 仍然直接依赖 PyTorch 环境探测

`runtime.py` 会直接调用：

- `torch.cuda.is_available()`
- `torch.cuda.device_count()`
- `torch.cuda.is_bf16_supported()`

这说明运行时策略和环境探测还在同一个模块里。

如果以后你想把这层做得更极致，可以继续拆成：

- `hardware_probe`
- `runtime_policy`

这样“采集事实”和“根据事实做决策”就能分开。

### 8.4 `reporting.py` 里仍然有框架知识

[`plhm/reporting.py`](../plhm/reporting.py) 现在会直接碰：

- `L.Trainer`
- `torch`

这说明“展示结果”和“框架对象”还没有彻底分离。

如果项目继续长大，这里也可以继续拆成：

- `environment_snapshot`
- `report_renderer`

## 9. 如果目标是“尽可能最隔离”，应该怎么想

“最隔离”不能理解成“每个模块都完全不知道其他模块存在”，那是伪目标。

工程上更现实的目标应该是：

> 大部分模块只依赖抽象和数据对象，只有极少数边界模块依赖具体框架。

围绕这个目标，可以用下面五条规则判断结构是否健康。

### 规则 1：核心层不要依赖外部编排框架

模型、数据、任务规则、配置 schema 这些东西，尽量不要直接依赖：

- Hydra
- Lightning
- MLflow

当前项目在这件事上已经做得不错。

### 规则 2：框架对象尽早翻译成项目对象

例如：

- `DictConfig` 早一点变成 `AppSettings`
- MLflow Logger 早一点构造成最终对象

不要让框架原生对象在整个项目里四处漂流。

### 规则 3：跨框架代码必须集中收口

真正危险的代码通常不是单一框架代码，而是下面这种混合代码：

- 先从 Hydra 读配置
- 再把值传给 Lightning
- 再顺手送进 MLflow

这种逻辑应该尽量只出现在：

- Composition Root
- `integrations/`

### 规则 4：优先依赖注入，不要优先内部硬编码

当前项目已经有两个好例子：

- `ClassificationModule(network=..., optimizer_config=...)`
- `GaussianBlobDataModule(dataset_factory=...)`

继续往前走，你还可以把下面这些东西继续注入：

- `loss_fn`
- `metrics_computer`
- `optimizer_factory`
- `scheduler_factory`
- `experiment_logger_factory`

### 规则 5：把“流程”和“策略”拆开

很多耦合不是因为功能太多，而是因为把流程和策略混在一起。

例如：

- 流程：训练一个 batch
- 策略：这个任务用什么 loss，怎么记 metric，怎么命名日志

如果流程相对稳定、策略经常变化，那策略就应该往外提。

## 10. 如果继续往前走，可以演进成什么样

如果这个项目以后不只是教学样例，而是要继续承载更多实验，可以朝下面这类结构演进：

```text
plhm/
  domain/
    model.py
    data.py
    task.py
    metrics.py
    protocols.py
  application/
    train_use_case.py
    runtime_policy.py
  adapters/
    hydra/
      loader.py
    lightning/
      module.py
      datamodule.py
    mlflow/
      logger.py
    torch/
      hardware_probe.py
  integrations/
    lightning_mlflow.py
  bootstrap/
    app.py
main.py
```

这套结构的含义是：

- `domain/` 放领域对象和纯规则
- `application/` 放用例和流程编排
- `adapters/` 放框架适配器
- `integrations/` 放跨框架桥接逻辑
- `bootstrap/` 放最终组装入口

这会让项目比现在复杂一些，但规模继续增大时会更稳。

## 11. 下一阶段最值得做的 6 步重构

如果你想继续把 PLHM 做得更干净，我建议按这个顺序推进。

### 第 1 步：把任务逻辑从 LightningModule 里拆出去

例如增加：

- `plhm/task/classification.py`

让里面负责：

- `compute_loss(...)`
- `compute_metrics(...)`

这样以后切换任务类型时，不需要直接大改 LightningModule。

### 第 2 步：把优化器创建方式抽成工厂

现在 `configure_optimizers()` 里直接写死了 `Adam`。

更合适的方向是：

- `OptimizerFactory`
- 或者 `build_optimizer(model, optimizer_settings)`

这样模型层、任务层、训练层的职责会更稳。

### 第 3 步：把环境探测和运行时策略拆开

现在 `runtime.py` 同时做了两件事：

- 探测环境
- 推导策略

如果继续重构，可以拆成：

- `probe_hardware()`
- `resolve_runtime_policy(...)`

### 第 4 步：把 Experiment Logger 再抽一层

如果以后要支持不止一种记录方式，例如：

- MLflow
- TensorBoard
- W&B

那就可以把 Logger 构造统一成：

- `build_experiment_logger(settings, runtime)`

这样 Composition Root 只需要请求“一个实验记录器”，而不是直接知道具体实现。

### 第 5 步：把 Hydra 配置拆成 Config Groups

当配置开始变多时，单个 `conf/config.yaml` 很快就会变得臃肿。

更清楚的做法是拆成：

- `conf/data/default.yaml`
- `conf/model/mlp.yaml`
- `conf/trainer/gpu.yaml`
- `conf/mlflow/local.yaml`

### 第 6 步：给边界层补单元测试

最值得测的，不是框架本身，而是边界翻译逻辑：

- `hydra_loader.py`
- `runtime.py`
- `integrations/lightning_mlflow.py`

这些地方最容易在重构时悄悄出错。

## 12. 日常开发时，代码应该放到哪里

这部分最实用，因为它直接决定以后仓库会不会重新变乱。

### 想加新模型

优先放在：

- `plhm/pytorch/`

不要直接塞进：

- `main.py`
- `plhm/lightning/module.py`

### 想换数据源

优先改：

- `plhm/pytorch/data.py`

如果只是接线方式变化，再去 `app.py` 里替换 `dataset_factory`。

### 想改训练 step 或优化器行为

优先改：

- `plhm/lightning/module.py`

如果你发现这里开始越来越胖，说明任务逻辑应该继续外提，而不是继续往里堆。

### 想改默认配置或命令行覆盖

优先改：

- `conf/config.yaml`
- `plhm/hydra_loader.py`
- `plhm/settings.py`

### 想改实验记录方式

优先改：

- `plhm/mlflow.py`
- `plhm/integrations/lightning_mlflow.py`

而不是直接去 `main.py` 或 `lightning/module.py` 里插 Logger 代码。

## 13. 这类项目最常见的坏味道

下面这些问题在训练项目里非常常见，而且一旦开始，代码会很快退化。

### 错误 1：把一切都塞进 `main.py`

后果不是“文件变长”，而是入口、业务、日志、环境判断全部搅在一起。

### 错误 2：让 Hydra 对象到处流动

后果是整个项目都开始依赖 Hydra，之后想换配置方案会很痛苦。

### 错误 3：让 LightningModule 自己创建模型和数据

后果是训练框架开始拥有训练核心，边界很快失控。

### 错误 4：到处散落 MLflow 调用

后果是实验记录逻辑污染训练逻辑，最后谁都不纯。

### 错误 5：把“简单”误解成“全部写在一个文件里”

真正的简单不是文件少，而是职责清楚、修改路径短、阅读路径稳定。

## 14. 怎么判断当前隔离做得够不够好

可以直接用下面这份清单做自检：

- 改模型时，是否不需要改 Hydra 和 MLflow 代码
- 改 Logger 时，是否不需要改 PyTorch 核心代码
- 改配置来源时，是否不需要改 Lightning step
- 一个框架对象是否只出现在边界层，而不是到处传
- 是否存在一个明确的 Composition Root
- `pytorch/` 里是否没有无关的 Hydra 或 MLflow 依赖
- `lightning/` 里是否主要是在做适配，而不是吞掉全部业务逻辑

如果这些问题大多都能回答“是”，那说明当前的隔离已经进入健康区间。

## 15. 对这个项目的总体评价

PLHM 现在最有价值的地方在于：

- 它足够小，可以完整读完
- 它又不是简单到只有一个脚本
- 它把 `P/L/H/M` 架构拆分真正落到了代码里
- 它已经具备 Composition Root、边界翻译、适配层、桥接层这些关键结构

如果目标是做一个“新手能读懂、后续还能继续长”的 MVP，这个方向是对的。

如果目标升级为“尽可能最大化组件隔离”，那下一阶段最值得继续做的是：

1. 把任务逻辑从 LightningModule 里拆开
2. 把环境探测和运行时策略拆开
3. 把 Experiment Logger 再抽象一层
4. 把 Hydra 配置拆成 Config Groups

## 16. 推荐阅读顺序

最后再给一个完整阅读顺序：

1. [`plhm/pytorch/model.py`](../plhm/pytorch/model.py)
2. [`plhm/pytorch/data.py`](../plhm/pytorch/data.py)
3. [`plhm/settings.py`](../plhm/settings.py)
4. [`plhm/lightning/module.py`](../plhm/lightning/module.py)
5. [`plhm/lightning/datamodule.py`](../plhm/lightning/datamodule.py)
6. [`plhm/runtime.py`](../plhm/runtime.py)
7. [`plhm/mlflow.py`](../plhm/mlflow.py)
8. [`plhm/integrations/lightning_mlflow.py`](../plhm/integrations/lightning_mlflow.py)
9. [`plhm/app.py`](../plhm/app.py)
10. [`plhm/hydra_loader.py`](../plhm/hydra_loader.py)
11. [`main.py`](../main.py)

按这个顺序读，你会先看见训练核心，再看见适配器，最后看见入口和总装逻辑。
