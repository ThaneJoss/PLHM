# PLHM 实时依赖图版本计划

## 1. 目标

这个版本的目标不是单纯“画一个图”，而是提供一个可以持续使用的依赖关系观察面板：

- 实时看到 `main.py`、`plhm/**/*.py` 以及后续纳入范围的配置文件之间的依赖有向图
- 当依赖关系被破坏时，能够直接看到是哪一条边违规，而不是只看到“运行失败”
- 前端展示逻辑保持清晰、低耦合，不直接绑定后端分析库的内部格式

当前仓库体量较小，第一版应优先解决 Python 文件级 `import` 依赖关系。函数调用图、tensor/dataflow 图、运行时采样链路都不在本版本范围内。

## 2. 版本原则

- Contract First：先定义稳定的图快照 contract，再实现分析和展示
- Analyzer / Service / UI 分离：后端分析逻辑、实时服务、前端渲染三层职责分开
- Frontend Library Isolation：前端不直接依赖 `grimp`、`import-linter` 或其他分析库的数据结构
- Full Snapshot Before Incremental Patch：第一版优先全量快照替换，不先做复杂增量 diff
- Explainability First：违规边不仅要高亮，还要有可读解释

## 3. 第一版范围

### 3.1 In Scope

- Python 文件级 `import` 依赖图
- 包级 / 文件级视图切换
- 依赖层级规则校验
- 违规边高亮与说明
- 文件变化后的自动重建
- 基于浏览器的本地可视化页面

### 3.2 Out of Scope

- 函数调用图
- 动态运行时依赖采样
- tensor shape / 数据流可视化
- 任意语言或任意文件类型的统一图谱
- 大规模仓库的增量图算法优化

## 4. Contract 设计

前后端之间只交换自定义 `GraphSnapshot`，不直接暴露第三方库原始对象。

建议 contract 至少包含以下信息：

- `version`
- `generated_at`
- `summary`
  - `node_count`
  - `edge_count`
  - `violation_count`
  - `cycle_count`
- `nodes`
  - `id`
  - `label`
  - `module`
  - `path`
  - `kind`，例如 `file` / `package` / `config`
  - `layer`，例如 `entry` / `assembly` / `adapter` / `support` / `core`
  - `status`，例如 `normal` / `warning` / `error`
  - `parent_id`
- `edges`
  - `id`
  - `source`
  - `target`
  - `kind`，第一版以 `import` 为主
  - `allowed`
  - `reasons`
  - `import_count`
- `violations`
  - `id`
  - `rule_id`
  - `severity`
  - `edge_id`
  - `message`

后端建议在 `plhm/depgraph/contracts.py` 中定义 dataclass 或等价的结构化类型，再统一序列化为 JSON。前端只消费这个 contract。

## 5. 后端架构

后端建议新增 `plhm/depgraph/` 模块，并按职责拆成以下部分：

### 5.1 `contracts.py`

定义 `GraphSnapshot`、`GraphNode`、`GraphEdge`、`GraphViolation` 等稳定数据结构。

### 5.2 `analyzers/`

负责从代码构建原始依赖图。

建议使用：

- `grimp`：作为 Python import graph 的主构建工具
- `import-linter`：作为规则表达和违规检测工具

这一层只负责“拿到依赖关系”和“拿到违规结果”，不负责 HTTP 和 UI。

### 5.3 `rules.py`

集中维护架构规则，不把规则散落在前端或各个脚本里。

第一版可先围绕当前 `PLHM` 结构定义层级：

- `entry`
  - `main`
  - `plhm.hydra_loader`
  - `plhm.app`
- `adapter`
  - `plhm.lightning`
  - `plhm.integrations`
  - `plhm.reporting`
- `support`
  - `plhm.runtime`
  - `plhm.mlflow`
- `core`
  - `plhm.pytorch`
  - `plhm.settings`

第一版重点不是追求完美分层，而是尽快定义“哪些反向依赖不允许出现”。

### 5.4 `snapshot_service.py`

负责把分析结果整理成统一的 `GraphSnapshot`。

输入：

- 仓库源码
- 规则配置
- 分析结果

输出：

- 完整、可序列化、可直接给前端消费的快照

### 5.5 `watch/`

使用 `watchfiles` 监听以下路径：

- `main.py`
- `plhm/**/*.py`
- 后续需要纳入图谱的配置文件

检测到变化后重建 snapshot，并更新当前服务状态。

### 5.6 `api/`

提供只读接口：

- `GET /api/depgraph/snapshot`
- `GET /api/depgraph/events`

第一版推荐 `SSE`，因为这里只需要服务端单向推送“图已更新”事件，不需要双向通信。这样比一开始上 WebSocket 更简单。

## 6. 前端架构

前端建议单独放在 `frontend/depgraph/`，使用 `Vite + Vue + TypeScript`。

### 6.1 目录建议

```text
frontend/depgraph/
  src/
    api/
    store/
    adapters/
    components/
    panels/
    controls/
    styles/
```

### 6.2 职责拆分

- `api/`
  - 负责获取 snapshot
  - 负责订阅 `SSE`
  - 不参与图布局和规则解释
- `store/`
  - 保存当前 snapshot、选中节点、筛选条件、视图模式
- `adapters/`
  - 把后端 `GraphSnapshot` 转成 Cytoscape 可渲染元素
  - 屏蔽第三方渲染库细节
- `components/`
  - 画布容器、页面外壳
- `panels/`
  - 节点详情、违规列表、图例、汇总信息
- `controls/`
  - 搜索、过滤、层级切换、视图切换

### 6.3 前端关键约束

- Vue 组件不直接认识 `grimp` / `import-linter`
- Vue 组件不直接持有规则判断逻辑
- Cytoscape 相关代码收敛在 adapter 或 canvas 封装里
- 侧边栏负责“解释”，图画布负责“关系”

## 7. 图渲染方案

前端图渲染建议使用 `Cytoscape.js`。

理由：

- 适合中小型交互式关系图
- 支持节点/边样式、高亮、布局、搜索、聚焦
- 比从零实现交互图更稳

第一版的默认交互建议如下：

- 默认展示包级总览
- 点击节点后可查看直接上游 / 下游
- 支持按层过滤
- 支持仅查看违规边
- 支持搜索文件或模块名
- 点击边后在侧边栏展示违规原因

## 8. 实施阶段

### Phase 1: Contract 与导出器

- 新建 `plhm/depgraph/contracts.py`
- 封装 `grimp` 获取基础依赖边
- 输出本地 `graph.json`
- 能在命令行导出一次完整快照

交付结果：

- 已有稳定 contract
- 已能导出图快照

### Phase 2: 规则与违规检测

- 引入 `import-linter` 或等价规则层
- 为当前 `PLHM` 分层定义一组明确规则
- 把违规边转为 contract 中的 `violations`

交付结果：

- 系统不止能“画图”，还能说明“哪条边坏了”

### Phase 3: 实时服务

- 增加文件监听
- 提供 snapshot 读取接口
- 提供 `SSE` 更新通知

交付结果：

- 文件变化后前端能自动看到新快照

### Phase 4: Vue 前端

- 用 `Vite + Vue` 建立独立 depgraph UI
- 接入 snapshot 拉取与 `SSE`
- 完成图画布、筛选、详情侧边栏、违规面板

交付结果：

- 浏览器里可用的实时依赖图页面

### Phase 5: 工程化收尾

- 增加启动命令
- 补充 README / 使用说明
- 在 CI 中加入依赖规则校验

交付结果：

- 本地可用、PR 可守门

## 9. 验收标准

达到以下条件可视为第一版完成：

- 修改任意受监控 Python 文件后，图能自动刷新
- 能在界面中定位某个文件的直接依赖关系
- 能清楚看到违规边及其原因
- 前端不依赖分析库原始格式
- 后端 contract 稳定，前端只依赖 contract

## 10. 当前推荐实现顺序

为了避免返工，建议严格按下面顺序推进：

1. 先写 contract
2. 再写导出器
3. 再补规则引擎
4. 再接实时服务
5. 最后接 Vue 前端

这样做的原因很简单：

- 如果 contract 不稳定，前端一定会反复返工
- 如果先画图再补规则，最后很容易只能“看”，不能“判断”
- 如果先做复杂实时协议，会在图数据还没稳定时引入额外复杂度

## 11. 当前结论

这个版本适合按“后端 contract 先行，前端消费快照”的模式推进。

对 `PLHM` 当前规模来说，这是一条足够清晰、实现成本可控、后续也容易继续扩展的路线。第一版只要把 Python import graph、违规边解释和 Vue 可视化做扎实，就已经有很强的实用价值。
