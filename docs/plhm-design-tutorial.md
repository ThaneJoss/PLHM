# PLHM 设计教程

## 1. 先用一句话说清这个项目

这个项目本质上是在演示一件事：

> 用 `PyTorch` 写核心训练对象，用 `Lightning` 接管训练循环，用 `Hydra` 负责配置入口，用 `MLflow` 负责实验记录，并且尽量让这四部分彼此隔离。

所以 `PLHM` 其实可以直接理解为：

- `P`: PyTorch
- `L`: Lightning
- `H`: Hydra
- `M`: MLflow

当前代码不是把这四个框架平铺在一个文件里，而是刻意分层，把它们放在不同职责的模块里。

## 2. 这个项目到底在训练什么

业务本身非常简单，目的是让架构问题更容易看清：

- 数据是一个二维二分类的高斯点云数据集
- 模型是一个小型 MLP
- 训练通过 Lightning 的 `Trainer.fit(...)` 运行
- 配置从 Hydra 进入
- 超参数和运行信息记录到 MLflow

也就是说，项目故意把“机器学习问题”简化成一个最小例子，好让你把注意力放在“软件结构”而不是“算法细节”上。

## 3. 总体架构图

当前项目最重要的设计，不是模型有多复杂，而是依赖方向。

```text
main.py
  -> hydra_loader.py
  -> settings.py
  -> app.py
       -> runtime.py
       -> mlflow.py
       -> integrations/lightning_mlflow.py
       -> lightning/
            -> pytorch/
```

如果换成更抽象的话术，就是：

- `PyTorch` 是核心训练对象层
- `Lightning` 是训练循环适配层
- `Hydra` 是配置输入适配层
- `MLflow` 是实验记录适配层
- `app.py` 是唯一允许“把这些层组装起来”的地方

这里最关键的一条规则是：

> 框架之间不要到处互相 import，跨框架组装只能集中发生在一个很小的地方。

这个“小地方”就是 [plhm/app.py](/root/PLHM/plhm/app.py:1)。

## 4. 代码按什么原则拆的

当前拆分遵循的是经典的“核心逻辑 + 适配器 + 组装层”。

### 4.1 核心层

核心层只表达“训练本身需要什么”，而不表达“用哪个框架跑”。

对应文件：

- [plhm/pytorch/model.py](/root/PLHM/plhm/pytorch/model.py:1)
- [plhm/pytorch/data.py](/root/PLHM/plhm/pytorch/data.py:1)
- [plhm/settings.py](/root/PLHM/plhm/settings.py:1)

这层的目标是：

- 让数据和模型能独立理解
- 让配置结构先变成普通 dataclass
- 尽量不把 Hydra、MLflow 之类的基础设施概念带进来

### 4.2 适配层

适配层负责“把核心层接到某个框架上”。

对应文件：

- [plhm/lightning/module.py](/root/PLHM/plhm/lightning/module.py:1)
- [plhm/lightning/datamodule.py](/root/PLHM/plhm/lightning/datamodule.py:1)
- [plhm/hydra_loader.py](/root/PLHM/plhm/hydra_loader.py:1)
- [plhm/mlflow.py](/root/PLHM/plhm/mlflow.py:1)
- [plhm/integrations/lightning_mlflow.py](/root/PLHM/plhm/integrations/lightning_mlflow.py:1)

这层的目标是：

- 把 Hydra 配置转成普通 Python 对象
- 把 PyTorch 模型包装成 LightningModule
- 把 PyTorch 数据集包装成 LightningDataModule
- 把 MLflow 记录器的构造单独收口

### 4.3 组装层

组装层只有一个：

- [plhm/app.py](/root/PLHM/plhm/app.py:1)

这个文件做的事情是：

1. 拿到中立配置 `AppSettings`
2. 推导运行时参数
3. 构造 MLflow 记录器
4. 构造 DataModule
5. 构造网络和 LightningModule
6. 构造 `L.Trainer`
7. 调用 `trainer.fit(...)`
8. 收集并打印最终指标

换句话说：

> 只有 `app.py` 有资格知道 “P、L、H、M 四部分最终怎么拼在一起”。

## 5. 从入口到训练结束，调用链如何流动

这一段是新手最值得反复看的部分。

### 5.1 `main.py` 只做入口，不做业务

[main.py](/root/PLHM/main.py:1) 很短，这正是设计目标。

它只做三件事：

1. 通过 `@hydra.main(...)` 接收配置
2. 用 `load_app_settings(...)` 把 Hydra 的 `DictConfig` 转成普通 dataclass
3. 调用 `run_training(...)`

这说明 `main.py` 没有直接碰：

- Lightning 训练细节
- MLflow 记录器构造
- PyTorch 模型定义
- dataloader 参数推导

这就是第一层隔离：入口不承担业务。

### 5.2 `hydra_loader.py` 把 Hydra 关在门口

[plhm/hydra_loader.py](/root/PLHM/plhm/hydra_loader.py:1) 的作用非常关键。

Hydra 的 `DictConfig` 很方便，但它本身属于框架对象。如果这个对象在项目里到处流动，会产生两个问题：

- 每一层都被迫理解 Hydra
- 你以后想换配置系统会非常痛苦

所以这里做了一个很重要的动作：

- `DictConfig` -> `dict`
- `dict` -> `AppSettings`

也就是把配置从“框架对象”转换成“项目自己的对象”。

一旦 `AppSettings` 生成完成，后面的绝大多数代码就不需要知道 Hydra 还存在。

这就是第二层隔离：配置框架只出现在入口适配层。

### 5.3 `settings.py` 定义项目自己的语言

[plhm/settings.py](/root/PLHM/plhm/settings.py:1) 不是一个装饰性文件，它其实是项目的“内部配置协议”。

里面定义了：

- `DataSettings`
- `ModelSettings`
- `TrainerSettings`
- `MlflowSettings`
- `AppSettings`

这意味着项目后面的代码不是围绕 Hydra 的结构编程，而是围绕自己定义的 dataclass 编程。

这样做的价值是：

- IDE 补全更明确
- 类型更清楚
- 每个子域的边界更明显
- 配置系统以后更容易替换

这就是第三层隔离：内部代码依赖项目协议，不依赖外部配置协议。

### 5.4 `app.py` 是组合根，不是业务细节仓库

[plhm/app.py](/root/PLHM/plhm/app.py:1) 现在承担的是“组合根”。

它知道所有部件怎么连，但它不应该承载每个部件的具体细节。

你可以把它理解为“总装车间”：

- `settings` 提供零件规格
- `runtime` 提供运行时推导
- `pytorch` 提供核心零件
- `lightning` 提供训练底盘
- `mlflow` 提供记录系统
- `integrations` 提供跨框架胶水

然后 `app.py` 把它们拼成一辆能跑的车。

所以 `app.py` 允许知道很多模块，但别的模块不应该反过来知道 `app.py` 里面的全局拼装信息。

这就是第四层隔离：组装知道一切，零件不知道全局。

## 6. P、L、H、M 四个模块现在分别承担什么职责

这一节是你以后判断“代码放哪”最实用的标准。

### 6.1 P: PyTorch 层

对应：

- [plhm/pytorch/model.py](/root/PLHM/plhm/pytorch/model.py:1)
- [plhm/pytorch/data.py](/root/PLHM/plhm/pytorch/data.py:1)

这层应该只负责：

- 张量如何构造
- 数据集如何产生
- 网络结构如何定义
- 前向计算如何发生

这层不应该负责：

- Hydra 配置读取
- Lightning 日志记录
- MLflow 记录器创建
- GPU/precision 策略选择
- 训练生命周期回调

#### 当前优点

- `TinyClassifier` 是纯 `nn.Module`
- `build_gaussian_blob_dataset(...)` 和 `build_gaussian_blob_splits(...)` 是纯 PyTorch 数据逻辑
- 这层没有依赖 Hydra 和 MLflow

#### 当前还不够“极限隔离”的地方

- 数据函数里把“训练/验证切分策略”也放在了 PyTorch 层
- `TinyClassifier` 里仍然把输出类别数写死为 `2`

这不算错误，但如果你追求更强隔离，可以继续拆成：

- `dataset_factory`
- `split_policy`
- `model_factory`

### 6.2 L: Lightning 层

对应：

- [plhm/lightning/module.py](/root/PLHM/plhm/lightning/module.py:1)
- [plhm/lightning/datamodule.py](/root/PLHM/plhm/lightning/datamodule.py:1)

这层应该只负责：

- 把 PyTorch 对象接到 Lightning 生命周期
- 管理 `training_step` / `validation_step`
- 管理 `configure_optimizers`
- 管理 dataloader 形式

这层不应该负责：

- 直接定义业务模型结构
- 解析 Hydra 配置
- 决定 MLflow 的 tracking URI
- 推导全局 batch size

#### 当前优点

- `ClassificationModule` 接收 `network` 和 `optimizer_config`，而不是自己内部创建网络
- `GaussianBlobDataModule` 接收 `dataset_factory`，而不是自己写死数据生成逻辑

这是当前项目最值得保留的两个隔离点。

它们意味着：

- 你可以替换网络，而不改 Lightning 训练循环
- 你可以替换数据集，而不改 DataModule 的外壳

#### 当前还存在的耦合

`ClassificationModule` 里仍然内嵌了：

- `CrossEntropyLoss`
- accuracy 计算方式
- log metric 的命名规则

如果以后任务从二分类变成多标签、多任务、回归，这里就会被迫改动。

所以更强的隔离方式是把下面这些继续外提：

- `loss_fn`
- `metrics_computer`
- `log_naming_policy`
- `optimizer_factory`

也就是让 LightningModule 更像一个“流程容器”，而不是“训练逻辑全集”。

### 6.3 H: Hydra 层

对应：

- [main.py](/root/PLHM/main.py:1)
- [plhm/hydra_loader.py](/root/PLHM/plhm/hydra_loader.py:1)
- [conf/config.yaml](/root/PLHM/conf/config.yaml:1)

这层应该只负责：

- 接收配置输入
- 做默认值管理
- 处理命令行覆盖参数
- 在入口把配置翻译成项目内部对象

这层不应该负责：

- 训练循环
- 模型定义
- 实验日志写入
- 数据集构造细节

#### 当前优点

- Hydra 没有深入业务层
- `settings.py` 让项目内部不依赖 `DictConfig`
- `conf/config.yaml` 结构和 `AppSettings` 对应得很清晰

#### 当前还可以进一步优化的方向

如果配置越来越复杂，可以继续把 Hydra 配置拆目录：

```text
conf/
  config.yaml
  data/
  model/
  trainer/
  mlflow/
```

这样可以把“配置组合”也模块化。

### 6.4 M: MLflow 层

对应：

- [plhm/mlflow.py](/root/PLHM/plhm/mlflow.py:1)
- [plhm/integrations/lightning_mlflow.py](/root/PLHM/plhm/integrations/lightning_mlflow.py:1)

这层应该只负责：

- tracking URI 构造
- 记录器构造
- 超参数扁平化

这层不应该负责：

- 决定模型如何训练
- 决定训练跑在哪张卡
- 决定数据如何产生

#### 当前优点

- `build_tracking_uri(...)` 被单独抽出
- `build_mlflow_logger(...)` 被放进集成层，而不是散落在入口或 LightningModule 里

这非常重要，因为 `Lightning` 和 `MLflow` 的耦合是“跨框架耦合”，最容易越写越乱。

#### 当前还可以更强的地方

如果未来你还要支持：

- TensorBoard
- Weights & Biases
- CSV 记录器

那么更好的做法是再增加一层：

- `experiment_logger_factory`

让 `app.py` 不直接知道具体记录器类型，而只请求“一个实验记录器”。

## 7. 当前设计为什么已经比很多 MVP 干净

很多 MVP 的典型写法是把下面这些全部塞进 `main.py`：

- 读配置
- 定义模型
- 定义 dataset
- 构造 dataloader
- 构造 trainer
- 构造记录器
- 打印环境信息
- 训练
- 汇总指标

这样会导致四类耦合同时出现：

1. 配置耦合
2. 训练框架耦合
3. 日志系统耦合
4. 业务逻辑耦合

当前项目已经避免了最严重的部分，因为它做到了：

- 入口和组装分离
- 框架配置和项目设置分离
- 核心 PyTorch 代码和 Lightning 生命周期分离
- MLflow 和训练主流程的耦合集中到集成层

这意味着它已经不是“单文件脚本”，而是一个真正有演进空间的最小架构。

## 8. 目前还剩下哪些真实耦合点

这里不讲理想化，只讲当前代码里仍然真实存在的耦合。

### 8.1 `app.py` 是有意存在的“中心耦合点”

这不是坏事。

组合根本来就应该承担集中耦合。真正要避免的是：

- 到处都有一点点耦合

而不是：

- 有一个明确、可控、短小的耦合点

所以 `app.py` 的耦合是“好耦合”，因为它是被收口过的。

### 8.2 `runtime.py` 仍然依赖 PyTorch 环境探测

[plhm/runtime.py](/root/PLHM/plhm/runtime.py:1) 里会调用：

- `torch.cuda.is_available()`
- `torch.cuda.device_count()`
- `torch.cuda.is_bf16_supported()`

这意味着“运行时决策”目前仍然绑定了 PyTorch。

如果你追求更高隔离，可以把这部分再拆成：

- `hardware_probe`
- `runtime_policy`

前者负责采集环境事实，后者负责根据事实做决策。

### 8.3 `reporting.py` 直接依赖 Lightning 和 Torch

[plhm/reporting.py](/root/PLHM/plhm/reporting.py:1) 里：

- `extract_final_metrics(...)` 依赖 `L.Trainer`
- `print_banner(...)` 依赖 `torch`

这说明“展示逻辑”还混合了一点框架知识。

更强的隔离方式是：

- `environment_snapshot` 单独生成纯数据对象
- `report_renderer` 只负责打印

### 8.4 `ClassificationModule` 里把任务类型写死成分类任务

`CrossEntropyLoss` 和 accuracy 的组合其实代表：

> 这个 LightningModule 不只是一个通用训练容器，它还是一个“分类任务训练容器”。

如果以后项目变复杂，建议继续拆出：

- `TaskSpec`
- `LossAdapter`
- `MetricAdapter`

## 9. 如果目标是“尽可能最隔离各个组件”，应该怎样构造

这一节是核心建议。

如果你把“最隔离”理解成“每个模块都完全不知道其他模块存在”，那在工程里几乎做不到，也没必要。

真正可行的目标应该是：

> 让大部分模块只依赖抽象协议和数据对象，只有极少数边界模块依赖具体框架。

可以用下面这套规则来判断结构是否足够隔离。

### 规则 1：核心层不能 `import` 外部编排框架

核心层通常指：

- 模型定义
- 数据定义
- 任务规则
- 配置 schema

这层最好不要 import：

- Hydra
- Lightning
- MLflow

当前项目已经基本做到。

### 规则 2：所有框架对象都要尽早翻译成项目对象

例如：

- `DictConfig` 尽快变成 `AppSettings`
- MLflow 记录器尽快变成一个组装好的实例

不要让框架原生对象在全项目到处漂流。

### 规则 3：跨框架代码必须集中收口

最危险的代码，不是 PyTorch 代码，也不是 Hydra 代码，而是下面这种：

- “先从 Hydra 读一段值，再传给 Lightning，再顺手记录到 MLflow”

因为这属于多框架混合区。

这类代码应该尽量只出现在：

- `app.py`
- `integrations/`

### 规则 4：用依赖注入替代内部硬编码

比如当前项目里已经有两个不错的例子：

- `ClassificationModule(network=..., optimizer_config=...)`
- `GaussianBlobDataModule(dataset_factory=...)`

这就是依赖注入。

继续往前走，你还可以注入：

- `loss_fn`
- `metrics`
- `optimizer_factory`
- `scheduler_factory`
- `experiment_logger_factory`

### 规则 5：把“策略”从“流程”中拆开

很多代码耦合，不是因为功能太多，而是因为把“流程”和“策略”揉在一起。

例如：

- 流程：训练一个 batch
- 策略：这个任务用什么 loss、怎么记 metric、怎么命名日志

如果流程不变，策略可能经常变，那就应该把策略单独抽象。

## 10. 一套更极致的隔离形态

如果未来你想把这个项目继续升级，可以朝下面这种结构演进：

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

这套结构的意思是：

- `domain/`：只放领域对象和纯规则
- `application/`：只放用例和流程编排
- `adapters/`：专门对接框架
- `integrations/`：专门放跨框架粘合逻辑
- `bootstrap/`：专门做最终组装

这会比当前结构更复杂，但在项目持续长大时更稳定。

## 11. 如果继续重构，这个项目最值得优先做的 6 步

这里给的是“收益最高”的顺序，不是理论上最漂亮的顺序。

### 第 1 步：把任务逻辑从 LightningModule 里再拆出来

新建例如：

- `plhm/task/classification.py`

让里面负责：

- `compute_loss(...)`
- `compute_metrics(...)`

然后 `ClassificationModule` 只调用 task 对象。

这样改完后：

- 换任务类型时，不需要大改 LightningModule

### 第 2 步：把优化器构造变成工厂

现在 `configure_optimizers()` 里写死了 `Adam`。

可以改成：

- `OptimizerFactory`
- 或者一个简单的 `build_optimizer(model, optimizer_settings)`

这样模型层、任务层、训练框架层之间的职责会更清楚。

### 第 3 步：把运行时探测和运行时策略分开

现在 `runtime.py` 同时做了：

- 环境探测
- 策略决策

建议拆成：

- `probe_hardware()`
- `resolve_runtime_policy(...)`

这样测试会更容易写，也更方便以后支持别的硬件环境。

### 第 4 步：把实验记录器做成统一接口

例如抽象成：

- `build_experiment_logger(settings, runtime)`

内部再决定返回 MLflow、TensorBoard 还是别的实现。

这样 `app.py` 不再直接感知具体实验平台。

### 第 5 步：把 Hydra 配置拆成配置组

当配置继续变多时，`conf/config.yaml` 会很快变臃肿。

提前拆开会更清晰：

- `conf/data/default.yaml`
- `conf/model/mlp.yaml`
- `conf/trainer/gpu.yaml`
- `conf/mlflow/local.yaml`

### 第 6 步：为“边界层”写单元测试

最值得测的不是框架本身，而是边界翻译逻辑：

- `hydra_loader.py`
- `runtime.py`
- `integrations/lightning_mlflow.py`

因为这些地方最容易在重构时悄悄出错。

## 12. 新功能应该放在哪里

这是日常开发最常用的判断表。

### 想加新模型

放在：

- `plhm/pytorch/`

不要放在：

- `lightning/module.py`
- `main.py`

### 想换数据源

优先改：

- `plhm/pytorch/data.py`

必要时在 `app.py` 里替换传入的 `dataset_factory`

### 想改训练 step、日志节奏、优化器行为

优先改：

- `plhm/lightning/module.py`

如果是任务规则变化，更应该继续拆出 task 层，而不是把 module.py 写得越来越胖。

### 想改默认配置和命令行覆盖方式

改：

- `conf/config.yaml`
- `plhm/hydra_loader.py`
- `plhm/settings.py`

### 想改实验记录方式

改：

- `plhm/mlflow.py`
- `plhm/integrations/lightning_mlflow.py`

而不是直接去 `main.py` 或 `lightning/module.py` 里插记录器代码。

## 13. 这类项目最常见的错误拆法

下面这些都很常见，而且会迅速把 MVP 写回大泥球。

### 错误 1：在 `main.py` 里直接定义模型和训练逻辑

后果：

- 入口文件越来越胖
- 什么都能改，什么都不好改

### 错误 2：让 Hydra 配置对象流入所有模块

后果：

- 每个模块都被 Hydra 绑定
- 以后想换配置系统时几乎要全项目改

### 错误 3：让 LightningModule 自己创建模型和数据

后果：

- 训练框架和业务实体绑死
- 复用困难

### 错误 4：在训练代码里到处穿插 MLflow 调用

后果：

- 框架耦合扩散
- 训练逻辑被日志逻辑污染

### 错误 5：把“简单”误解为“所有东西放一个文件”

真正的简单，不是文件少，而是职责清楚。

## 14. 你可以用什么标准判断“隔离是否足够好”

给自己做代码评审时，可以直接用下面这份清单。

### 检查清单

- 改模型结构时，是否不需要改 Hydra 和 MLflow 代码
- 改记录器实现时，是否不需要改 PyTorch 核心代码
- 改配置来源时，是否不需要改 Lightning 训练步骤
- 一个框架对象是否只在边界层出现，而不是到处传递
- 是否存在一个明确的组合根，而不是多个地方都在偷偷组装
- 某个模块名字里如果写着 `pytorch`，它是否真的不该 `import hydra` 或 `mlflow`
- 某个模块名字里如果写着 `lightning`，它是否只是适配训练流程，而不是吞掉全部业务逻辑

如果这几条大多能满足，说明你的隔离已经进入比较健康的状态。

## 15. 对这个项目的最终评价

这个项目现在已经具备一个很好的教学价值：

- 它足够小，新手能完整读完
- 它又不至于小到只剩一个脚本
- 它明确展示了如何把 `P/L/H/M` 拆成不同层次
- 它已经有了“组合根”“适配层”“中立配置对象”这些关键结构

如果你现在的目标是“做一个新手易懂、但不是脚本堆砌的 MVP”，那这个方向是对的。

如果你的目标升级为“尽可能最大程度地隔离组件”，那下一阶段最应该继续做的是：

1. 把任务逻辑从 LightningModule 中拆开
2. 把 runtime 的环境探测和策略决策拆开
3. 把实验记录器再抽象一层
4. 把配置拆成 Hydra 配置组

## 16. 推荐阅读顺序

如果你准备自己继续演进这个项目，建议按这个顺序读代码：

1. [plhm/pytorch/model.py](/root/PLHM/plhm/pytorch/model.py:1)
2. [plhm/pytorch/data.py](/root/PLHM/plhm/pytorch/data.py:1)
3. [plhm/settings.py](/root/PLHM/plhm/settings.py:1)
4. [plhm/lightning/module.py](/root/PLHM/plhm/lightning/module.py:1)
5. [plhm/lightning/datamodule.py](/root/PLHM/plhm/lightning/datamodule.py:1)
6. [plhm/runtime.py](/root/PLHM/plhm/runtime.py:1)
7. [plhm/mlflow.py](/root/PLHM/plhm/mlflow.py:1)
8. [plhm/integrations/lightning_mlflow.py](/root/PLHM/plhm/integrations/lightning_mlflow.py:1)
9. [plhm/app.py](/root/PLHM/plhm/app.py:1)
10. [plhm/hydra_loader.py](/root/PLHM/plhm/hydra_loader.py:1)
11. [main.py](/root/PLHM/main.py:1)

这样读，你会先理解核心，再理解适配器，最后理解总装层。
