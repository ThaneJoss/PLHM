# Depgraph 使用说明

这份文档只讲一件事：如何使用 `PLHM` 当前内置的 `depgraph` 工具观察仓库里的 Python `import` 依赖关系。

当前实现对应的是 `PLAN.md` 里的第一阶段可用版本：

- 后端先定义 `GraphSnapshot` contract
- 只分析仓库内部的 Python 文件级 `import`
- 提供一次性导出和本地只读服务
- 提供浏览器面板查看 package/file 视图

它不是通用架构分析平台，也不是运行时 tracing 工具。第一版聚焦的是：

- `main.py`
- `plhm/**/*.py`
- 以及 watcher 关注到的 `.py`、`.yaml`、`.yml` 变更

## 1. 先知道它能做什么

当前 `depgraph` 可以回答这些问题：

- 现在仓库里有哪些内部 Python 模块
- 哪些模块之间存在 `import` 依赖
- 某条依赖边是否违反了当前的层级方向约束
- 当前是否存在循环依赖
- 修改源码后，浏览器里的快照是否已经刷新

当前不会做这些事情：

- 不分析第三方包之间的关系
- 不画函数调用图
- 不做运行时依赖采样
- 不做 tensor / dataflow 可视化

## 2. 命令入口

你可以直接用模块入口：

```bash
python -m plhm.depgraph <subcommand>
```

也可以用脚本入口：

```bash
plhm-depgraph <subcommand>
```

当前支持两个子命令：

- `export`
- `serve`

## 3. 导出快照

如果你只想拿到依赖图数据，不需要开浏览器页面，可以直接导出 JSON：

```bash
python -m plhm.depgraph export --root . --output graph.json
```

或者：

```bash
plhm-depgraph export --root . --output graph.json
```

参数说明：

- `--root`
  - 要分析的仓库根目录
  - 一般在仓库根目录下执行时写成 `.`
- `--output`
  - 导出的 JSON 文件路径

执行成功后会输出类似信息：

```text
Wrote dependency graph snapshot to /abs/path/to/graph.json
```

## 4. 启动浏览器面板

如果你想直接看图，可以启动本地只读服务：

```bash
python -m plhm.depgraph serve --root . --host 127.0.0.1 --port 8765
```

或者：

```bash
plhm-depgraph serve --root . --host 127.0.0.1 --port 8765
```

然后在浏览器里访问：

```text
http://127.0.0.1:8765
```

这个服务会同时提供：

- 静态前端页面 `/`
- 当前快照接口 `/api/depgraph/snapshot`
- 事件流接口 `/api/depgraph/events`

## 5. 页面里怎么看

当前页面支持这些能力：

- `Package` 视图
  - 聚合到包级别，适合先看整体结构
- `File` 视图
  - 下钻到具体 `.py` 文件
- `Layer` 过滤
  - 只看某个层级里的节点
- `只看违规边`
  - 只保留不允许的依赖边
- `搜索`
  - 按模块名、路径、文件名过滤
- `详情侧栏`
  - 点节点看模块信息
  - 点边看 `allowed`、`import_count` 和原因解释

如果你只是第一次使用，推荐顺序是：

1. 先看 `Package` 视图确认整体结构
2. 再开 `只看违规边`
3. 最后切到 `File` 视图定位具体文件

## 6. `GraphSnapshot` 里有什么

当前前后端之间只交换 `GraphSnapshot`，不直接暴露分析器内部对象。

顶层结构大致如下：

```json
{
  "version": "1.0",
  "generated_at": "2026-04-22T06:46:02.048702+00:00",
  "summary": {
    "node_count": 30,
    "edge_count": 26,
    "violation_count": 0,
    "cycle_count": 0
  },
  "nodes": [],
  "edges": [],
  "violations": []
}
```

其中：

- `summary`
  - 汇总节点数、边数、违规数和 cycle 数
- `nodes`
  - 同时包含 `package` 和 `file` 两类节点
- `edges`
  - 当前主要是 `import` 边
- `violations`
  - 当前主要是层级方向违规

节点里比较重要的字段：

- `id`
- `module`
- `path`
- `kind`
- `layer`
- `status`
- `parent_id`

边里比较重要的字段：

- `source`
- `target`
- `allowed`
- `reasons`
- `import_count`

## 7. watcher 怎么工作

`serve` 模式下，服务会轮询检测仓库里的这些文件变化：

- `*.py`
- `*.yaml`
- `*.yml`

检测到变化后会重建 snapshot，并通过 `SSE` 向前端发送更新事件。

这意味着你不需要手动重启服务才能看到最新结构。正常流程是：

1. 开着 `serve`
2. 修改 Python 文件
3. 保存
4. 页面自动刷新快照

## 8. 当前层级规则怎么理解

当前实现里有一组内置层级：

- `entry`
  - 例如 `main`、`plhm.hydra_loader`、`plhm.app`
- `adapter`
  - 例如 `plhm.lightning`、`plhm.integrations`、`plhm.reporting`
- `support`
  - 例如 `plhm.runtime`、`plhm.mlflow`、`plhm.depgraph`
- `core`
  - 例如 `plhm.pytorch`、`plhm.settings`

规则方向是高层可以依赖低层，反过来不允许。

也就是：

- `entry -> adapter -> support -> core` 是允许方向
- 反向依赖会被标成 violation

## 9. 常见用法

### 只想拿一个可提交的图快照

```bash
python -m plhm.depgraph export --root . --output graph.json
```

### 一边改代码一边看结构变化

```bash
python -m plhm.depgraph serve --root . --host 127.0.0.1 --port 8765
```

### 看某个模块有没有不该出现的反向依赖

推荐操作：

1. 打开页面
2. 勾选 `只看违规边`
3. 在搜索框里输入模块名
4. 点边看右侧解释

## 10. 当前限制

这版实现是可用的，但还有明确边界：

- 分析器现在是基于 `ast` 的内部实现，不是 `grimp` / `import-linter` 正式接入版
- 前端当前是静态页面 + ESM 依赖，不是完整 `Vite + Vue + TypeScript` 构建链
- watcher 当前是 polling，不是 `watchfiles`
- API 是本地只读使用场景，还没有做认证、权限或生产部署封装

所以这版更适合：

- 本地结构观察
- 重构前后快速比对
- 依赖方向回归检查

而不是：

- 大规模仓库分析平台
- 生产环境长期服务

## 11. 推荐使用姿势

如果你只是想日常用它，我建议：

1. 改代码前先开一次 `serve`
2. 先看 `Package` 视图掌握整体结构
3. 做重构时常开 `只看违规边`
4. 需要留档时再执行一次 `export`

这样它更像一个结构观察面板，而不是额外的维护负担。
