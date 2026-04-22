import { createApp, nextTick } from "vue";

import { fetchSnapshot, subscribeToSnapshotEvents } from "./api.js";
import { createGraphController } from "./graph.js";

createApp({
  data() {
    return {
      error: "",
      graphController: null,
      loading: true,
      selected: null,
      snapshot: null,
      filters: {
        layer: "all",
        search: "",
        viewMode: "package",
        violationsOnly: false,
      },
    };
  },
  computed: {
    layers() {
      if (!this.snapshot) {
        return [];
      }
      return Array.from(
        new Set(this.snapshot.nodes.map((node) => node.layer).filter((layer) => layer !== "unknown")),
      ).sort();
    },
    visibleViolations() {
      if (!this.snapshot) {
        return [];
      }
      return this.snapshot.violations.slice(0, 12);
    },
    selectedDetails() {
      if (!this.selected || !this.snapshot) {
        return null;
      }
      if (this.selected.type === "node") {
        return this.snapshot.nodes.find((node) => node.id === this.selected.data.id) ?? this.selected.data;
      }
      return this.snapshot.edges.find((edge) => edge.id === this.selected.data.id) ?? this.selected.data;
    },
  },
  watch: {
    filters: {
      deep: true,
      handler() {
        this.renderGraph();
      },
    },
    snapshot() {
      this.renderGraph();
    },
  },
  async mounted() {
    await this.loadSnapshot();
    this.unsubscribe = subscribeToSnapshotEvents(() => this.loadSnapshot());
  },
  beforeUnmount() {
    this.unsubscribe?.();
    this.graphController?.destroy();
  },
  methods: {
    async loadSnapshot() {
      this.loading = true;
      this.error = "";
      try {
        this.snapshot = await fetchSnapshot();
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
      } finally {
        this.loading = false;
      }
    },
    async renderGraph() {
      if (!this.snapshot) {
        return;
      }
      await nextTick();
      const container = this.$refs.canvas;
      if (!container) {
        return;
      }
      if (!this.graphController) {
        this.graphController = createGraphController(container, (selected) => {
          this.selected = selected;
        });
      }
      this.graphController.render(this.snapshot, this.filters);
    },
    formatReasons(reasons) {
      return (reasons ?? []).join(" ");
    },
    optimizeLayout() {
      this.graphController?.optimizeLayout(this.filters);
    },
  },
  template: `
    <main class="shell">
      <section class="masthead">
        <div>
          <p class="eyebrow">PLHM Dependency Graph</p>
          <h1>实时依赖图</h1>
          <p class="subtitle">
            用稳定的 GraphSnapshot contract 把包级 / 文件级依赖、层级违规和实时刷新收进一个观察面板。
          </p>
        </div>
        <div class="summary-card" v-if="snapshot">
          <div class="summary-item">
            <span>Nodes</span>
            <strong>{{ snapshot.summary.node_count }}</strong>
          </div>
          <div class="summary-item">
            <span>Edges</span>
            <strong>{{ snapshot.summary.edge_count }}</strong>
          </div>
          <div class="summary-item">
            <span>Violations</span>
            <strong>{{ snapshot.summary.violation_count }}</strong>
          </div>
          <div class="summary-item">
            <span>Cycles</span>
            <strong>{{ snapshot.summary.cycle_count }}</strong>
          </div>
        </div>
      </section>

      <section class="toolbar">
        <label>
          <span>视图</span>
          <select v-model="filters.viewMode">
            <option value="package">Package</option>
            <option value="file">File</option>
          </select>
        </label>
        <label>
          <span>层级</span>
          <select v-model="filters.layer">
            <option value="all">all</option>
            <option v-for="layer in layers" :key="layer" :value="layer">{{ layer }}</option>
          </select>
        </label>
        <label class="search">
          <span>搜索</span>
          <input v-model="filters.search" type="search" placeholder="module / path / label" />
        </label>
        <label class="checkbox">
          <input v-model="filters.violationsOnly" type="checkbox" />
          <span>只看违规边</span>
        </label>
        <button type="button" @click="loadSnapshot">手动刷新</button>
        <button type="button" @click="optimizeLayout">自动优化布局</button>
      </section>

      <section class="workspace">
        <article class="panel canvas-panel">
          <header>
            <h2>依赖关系</h2>
            <p v-if="snapshot">生成时间：{{ snapshot.generated_at }}</p>
          </header>
          <div v-if="loading" class="empty-state">正在读取 snapshot...</div>
          <div v-else-if="error" class="empty-state error">{{ error }}</div>
          <div ref="canvas" class="canvas"></div>
        </article>

        <aside class="panel inspector-panel">
          <header>
            <h2>详情</h2>
            <p>点击节点或边查看解释。</p>
          </header>
          <div v-if="!selectedDetails" class="empty-state">当前还没有选中内容。</div>
          <div v-else-if="selected?.type === 'node'" class="detail-list">
            <div class="detail-item"><span>ID</span><strong>{{ selectedDetails.id }}</strong></div>
            <div class="detail-item"><span>Module</span><strong>{{ selectedDetails.module }}</strong></div>
            <div class="detail-item"><span>Path</span><strong>{{ selectedDetails.path }}</strong></div>
            <div class="detail-item"><span>Layer</span><strong>{{ selectedDetails.layer }}</strong></div>
            <div class="detail-item"><span>Status</span><strong>{{ selectedDetails.status }}</strong></div>
            <div class="detail-item"><span>Kind</span><strong>{{ selectedDetails.kind }}</strong></div>
          </div>
          <div v-else class="detail-list">
            <div class="detail-item"><span>ID</span><strong>{{ selectedDetails.id }}</strong></div>
            <div class="detail-item"><span>Source</span><strong>{{ selectedDetails.source }}</strong></div>
            <div class="detail-item"><span>Target</span><strong>{{ selectedDetails.target }}</strong></div>
            <div class="detail-item"><span>Allowed</span><strong>{{ selectedDetails.allowed }}</strong></div>
            <div class="detail-item"><span>Imports</span><strong>{{ selectedDetails.import_count }}</strong></div>
            <div class="detail-item detail-reason">
              <span>Reasons</span>
              <strong>{{ formatReasons(selectedDetails.reasons) }}</strong>
            </div>
          </div>
        </aside>

        <aside class="panel violations-panel">
          <header>
            <h2>违规列表</h2>
            <p>优先把真正破坏层级的边挑出来。</p>
          </header>
          <div v-if="!snapshot || !visibleViolations.length" class="empty-state">没有检测到层级违规。</div>
          <ul v-else class="violation-list">
            <li v-for="violation in visibleViolations" :key="violation.id">
              <span class="severity">{{ violation.severity }}</span>
              <strong>{{ violation.rule_id }}</strong>
              <p>{{ violation.message }}</p>
            </li>
          </ul>
        </aside>
      </section>
    </main>
  `,
}).mount("#app");
