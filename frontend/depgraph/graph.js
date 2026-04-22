import cytoscape from "cytoscape";

const PLHM_BRANCHES = [
  {
    id: "design:P",
    label: "P / PyTorch",
    module: "PLHM.P",
    path: "plhm/pytorch",
    layer: "core",
    x: -480,
    y: 180,
  },
  {
    id: "design:L",
    label: "L / Lightning",
    module: "PLHM.L",
    path: "plhm/lightning",
    layer: "adapter",
    x: -160,
    y: 180,
  },
  {
    id: "design:H",
    label: "H / Hydra",
    module: "PLHM.H",
    path: "plhm/hydra_loader.py",
    layer: "entry",
    x: 160,
    y: 180,
  },
  {
    id: "design:M",
    label: "M / MLflow",
    module: "PLHM.M",
    path: "plhm/mlflow.py",
    layer: "support",
    x: 480,
    y: 180,
  },
];

const PLHM_ROOT = {
  id: "design:main",
  label: "main",
  module: "main",
  path: "main.py",
  layer: "entry",
  x: 0,
  y: 0,
};

const PLHM_LEAVES = [
  {
    id: "design:plhm.app",
    label: "Composition Root",
    module: "plhm.app",
    path: "plhm/app.py",
    layer: "entry",
    branchId: "design:H",
    prefixes: ["plhm.app"],
    x: 160,
    y: 320,
  },
  {
    id: "design:plhm.hydra_loader",
    label: "Hydra Loader",
    module: "plhm.hydra_loader",
    path: "plhm/hydra_loader.py",
    layer: "entry",
    branchId: "design:H",
    prefixes: ["plhm.hydra_loader"],
    x: 160,
    y: 470,
  },
  {
    id: "design:plhm.settings",
    label: "Settings / Runtime",
    module: "plhm.settings",
    path: "plhm/settings.py",
    layer: "core",
    branchId: "design:H",
    prefixes: ["plhm.settings", "plhm.runtime"],
    x: 160,
    y: 620,
  },
  {
    id: "design:plhm.pytorch",
    label: "PyTorch Core",
    module: "plhm.pytorch",
    path: "plhm/pytorch",
    layer: "core",
    branchId: "design:P",
    prefixes: ["plhm.pytorch"],
    x: -480,
    y: 360,
  },
  {
    id: "design:plhm.lightning",
    label: "Lightning Loop",
    module: "plhm.lightning",
    path: "plhm/lightning",
    layer: "adapter",
    branchId: "design:L",
    prefixes: ["plhm.lightning"],
    x: -160,
    y: 360,
  },
  {
    id: "design:plhm.mlflow",
    label: "MLflow Setup",
    module: "plhm.mlflow",
    path: "plhm/mlflow.py",
    layer: "support",
    branchId: "design:M",
    prefixes: ["plhm.mlflow"],
    x: 480,
    y: 320,
  },
  {
    id: "design:plhm.integrations",
    label: "Lightning <-> MLflow",
    module: "plhm.integrations",
    path: "plhm/integrations",
    layer: "adapter",
    branchId: "design:M",
    prefixes: ["plhm.integrations"],
    x: 480,
    y: 470,
  },
  {
    id: "design:plhm.reporting",
    label: "Reporting",
    module: "plhm.reporting",
    path: "plhm/reporting.py",
    layer: "adapter",
    branchId: "design:M",
    prefixes: ["plhm.reporting"],
    x: 480,
    y: 620,
  },
];

export function createGraphController(container, onSelect) {
  const cy = cytoscape({
    container,
    elements: [],
    style: [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "font-family": "'IBM Plex Sans', 'Noto Sans SC', sans-serif",
          "font-size": 11,
          color: "#0f172a",
          "background-color": "#dbe4f0",
          "border-width": 2,
          "border-color": "#7890ab",
          padding: "12px",
          "text-wrap": "wrap",
          "text-max-width": 90,
        },
      },
      {
        selector: "node[kind = 'package']",
        style: {
          shape: "round-rectangle",
          "background-color": "#eef4fb",
          "border-color": "#4b6682",
          "font-weight": 700,
        },
      },
      {
        selector: "node[kind = 'design-root']",
        style: {
          shape: "round-rectangle",
          "background-color": "#112033",
          "border-color": "#112033",
          color: "#fffdf9",
          "font-size": 18,
          "font-weight": 800,
          "text-max-width": 140,
          padding: "18px",
        },
      },
      {
        selector: "node[kind = 'design-branch']",
        style: {
          shape: "round-rectangle",
          "background-color": "#eef4fb",
          "border-color": "#4b6682",
          "font-size": 14,
          "font-weight": 800,
          "text-max-width": 150,
          padding: "16px",
        },
      },
      {
        selector: "node[kind = 'design-leaf']",
        style: {
          shape: "round-rectangle",
          "background-color": "#fffaf1",
          "border-color": "#8e6b4a",
          "text-max-width": 140,
          padding: "14px",
        },
      },
      {
        selector: "node[status = 'warning']",
        style: {
          "border-color": "#f59e0b",
          "background-color": "#fff2cf",
        },
      },
      {
        selector: "node[status = 'error']",
        style: {
          "border-color": "#dc2626",
          "background-color": "#fee2e2",
        },
      },
      {
        selector: "edge",
        style: {
          width: "mapData(weight, 1, 8, 2, 8)",
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          "line-color": "#7794b2",
          "target-arrow-color": "#7794b2",
          opacity: 0.85,
        },
      },
      {
        selector: "edge[allowed = 0]",
        style: {
          "line-color": "#dc2626",
          "target-arrow-color": "#dc2626",
          width: 5,
        },
      },
      {
        selector: "edge[kind = 'design-tree']",
        style: {
          width: 2,
          "curve-style": "straight",
          "line-style": "dashed",
          "line-color": "#b8c6d6",
          "target-arrow-shape": "none",
          opacity: 0.8,
        },
      },
      {
        selector: ":selected",
        style: {
          "overlay-color": "#f97316",
          "overlay-opacity": 0.14,
          "overlay-padding": 12,
        },
      },
    ],
    layout: {
      name: "breadthfirst",
      directed: true,
      padding: 32,
      spacingFactor: 1.35,
    },
  });

  cy.on("tap", "node", (event) => {
    onSelect({
      type: "node",
      data: event.target.data(),
    });
  });

  cy.on("tap", "edge", (event) => {
    onSelect({
      type: "edge",
      data: event.target.data(),
    });
  });

  cy.on("tap", (event) => {
    if (event.target === cy) {
      onSelect(null);
    }
  });

  return {
    render(snapshot, filters) {
      const elements = buildElements(snapshot, filters);
      cy.elements().remove();
      cy.add(elements);
      cy.layout(buildLayoutOptions(filters, false)).run();
    },
    destroy() {
      cy.destroy();
    },
    optimizeLayout(filters) {
      cy.layout(buildLayoutOptions(filters, true)).run();
    },
  };
}

function buildLayoutOptions(filters, animate) {
  if (filters.viewMode === "plhm") {
    return {
      name: "preset",
      animate,
      fit: true,
      padding: 48,
    };
  }

  if (filters.viewMode === "package") {
    return {
      name: "breadthfirst",
      directed: true,
      padding: 32,
      spacingFactor: 1.5,
      animate,
      fit: true,
    };
  }

  return {
    name: "cose",
    animate,
    fit: true,
    padding: 32,
    randomize: false,
    componentSpacing: 120,
    nodeRepulsion: 140000,
    idealEdgeLength: 90,
    edgeElasticity: 180,
    nestingFactor: 0.85,
    gravity: 1,
    numIter: 1600,
  };
}

export function buildElements(snapshot, filters) {
  if (filters.viewMode === "plhm") {
    return buildPlhmDesignElements(snapshot, filters);
  }

  const nodeById = new Map(snapshot.nodes.map((node) => [node.id, node]));
  const hasNodeFilters = filters.layer !== "all" || filters.search.trim() !== "";
  const edgeSet = filters.viewMode === "package"
    ? buildPackageEdges(snapshot, nodeById)
    : snapshot.edges.map((edge) => ({
        ...edge,
        sourceNode: nodeById.get(edge.source),
        targetNode: nodeById.get(edge.target),
        weight: edge.import_count,
      }));

  const matchingNodes = new Set();
  const search = filters.search.trim().toLowerCase();
  for (const node of snapshot.nodes) {
    if (filters.viewMode === "package" && node.kind === "file" && node.parent_id) {
      continue;
    }
    if (filters.layer !== "all" && node.layer !== filters.layer) {
      continue;
    }
    if (search && !matchesNode(node, search)) {
      continue;
    }
    matchingNodes.add(node.id);
  }

  const visibleEdges = edgeSet.filter((edge) => {
    if (filters.violationsOnly && edge.allowed) {
      return false;
    }
    if (!hasNodeFilters) {
      return true;
    }
    return matchingNodes.has(edge.source) || matchingNodes.has(edge.target);
  });

  const visibleNodeIds = new Set(matchingNodes);
  for (const edge of visibleEdges) {
    visibleNodeIds.add(edge.source);
    visibleNodeIds.add(edge.target);
  }
  if (filters.viewMode === "file") {
    for (const nodeId of Array.from(visibleNodeIds)) {
      const node = nodeById.get(nodeId);
      if (node?.parent_id) {
        visibleNodeIds.add(node.parent_id);
      }
    }
  }

  const elements = [];
  for (const node of snapshot.nodes) {
    if (!visibleNodeIds.has(node.id)) {
      continue;
    }
    if (filters.viewMode === "package" && node.kind === "file" && node.parent_id) {
      continue;
    }
    if (node.kind === "package" && !visibleNodeIds.has(node.id)) {
      continue;
    }
    elements.push({
      data: {
        ...node,
        parent: filters.viewMode === "file" ? node.parent_id : undefined,
      },
      classes: node.kind,
    });
  }

  for (const edge of visibleEdges) {
    elements.push({
      data: {
        ...edge,
        weight: edge.weight ?? edge.import_count ?? 1,
        allowed: edge.allowed ? 1 : 0,
      },
    });
  }

  return elements;
}

function buildPackageEdges(snapshot, nodeById) {
  const aggregated = new Map();
  for (const edge of snapshot.edges) {
    const sourceNode = nodeById.get(edge.source);
    const targetNode = nodeById.get(edge.target);
    if (!sourceNode || !targetNode) {
      continue;
    }
    const source = sourceNode.parent_id || sourceNode.id;
    const target = targetNode.parent_id || targetNode.id;
    const key = `${source}->${target}`;
    const current = aggregated.get(key) ?? {
      id: `package:${key}`,
      source,
      target,
      kind: "import",
      allowed: true,
      reasons: [],
      import_count: 0,
      weight: 0,
    };
    current.allowed = current.allowed && edge.allowed;
    current.import_count += edge.import_count;
    current.weight += edge.import_count;
    current.reasons = Array.from(new Set([...current.reasons, ...edge.reasons]));
    aggregated.set(key, current);
  }
  return Array.from(aggregated.values());
}

function matchesNode(node, search) {
  return [node.label, node.module, node.path]
    .filter(Boolean)
    .some((value) => value.toLowerCase().includes(search));
}

function buildPlhmDesignElements(snapshot, filters) {
  const search = filters.search.trim().toLowerCase();
  const visibleLeafIds = new Set();
  const leafStatuses = new Map(PLHM_LEAVES.map((leaf) => [leaf.id, "normal"]));

  for (const node of snapshot.nodes) {
    const leafId = resolvePlhmDesignLeafId(node.module);
    if (!leafId) {
      continue;
    }

    if (node.status === "error") {
      leafStatuses.set(leafId, "error");
    } else if (node.status === "warning" && leafStatuses.get(leafId) !== "error") {
      leafStatuses.set(leafId, "warning");
    }
  }

  for (const leaf of PLHM_LEAVES) {
    if (filters.layer !== "all" && leaf.layer !== filters.layer) {
      continue;
    }
    if (search && !matchesNode(leaf, search)) {
      continue;
    }
    visibleLeafIds.add(leaf.id);
  }

  const dependencyEdges = aggregatePlhmDesignEdges(snapshot, visibleLeafIds, filters.violationsOnly);
  for (const edge of dependencyEdges) {
    visibleLeafIds.add(edge.source);
    visibleLeafIds.add(edge.target);
  }

  if (!visibleLeafIds.size && !search && filters.layer === "all") {
    for (const leaf of PLHM_LEAVES) {
      visibleLeafIds.add(leaf.id);
    }
  }

  const visibleBranchIds = new Set();
  for (const leaf of PLHM_LEAVES) {
    if (visibleLeafIds.has(leaf.id)) {
      visibleBranchIds.add(leaf.branchId);
    }
  }

  const elements = [
    {
      data: {
        ...PLHM_ROOT,
        kind: "design-root",
        status: "normal",
      },
      position: { x: PLHM_ROOT.x, y: PLHM_ROOT.y },
    },
  ];

  for (const branch of PLHM_BRANCHES) {
    if (!visibleBranchIds.has(branch.id)) {
      continue;
    }
    elements.push({
      data: {
        ...branch,
        kind: "design-branch",
        status: "normal",
      },
      position: { x: branch.x, y: branch.y },
    });
    elements.push({
      data: {
        id: `edge:${PLHM_ROOT.id}->${branch.id}`,
        source: PLHM_ROOT.id,
        target: branch.id,
        kind: "design-tree",
        allowed: true,
        reasons: ["PLHM top-level design tree."],
        import_count: 0,
      },
    });
  }

  for (const leaf of PLHM_LEAVES) {
    if (!visibleLeafIds.has(leaf.id)) {
      continue;
    }
    elements.push({
      data: {
        id: leaf.id,
        label: leaf.label,
        module: leaf.module,
        path: leaf.path,
        kind: "design-leaf",
        layer: leaf.layer,
        status: leafStatuses.get(leaf.id) ?? "normal",
        parent_id: leaf.branchId,
      },
      position: { x: leaf.x, y: leaf.y },
    });
    elements.push({
      data: {
        id: `edge:${leaf.branchId}->${leaf.id}`,
        source: leaf.branchId,
        target: leaf.id,
        kind: "design-tree",
        allowed: true,
        reasons: ["PLHM branch membership."],
        import_count: 0,
      },
    });
  }

  for (const edge of dependencyEdges) {
    elements.push({ data: edge });
  }

  return elements;
}

function aggregatePlhmDesignEdges(snapshot, visibleLeafIds, violationsOnly) {
  const aggregated = new Map();

  for (const edge of snapshot.edges) {
    const sourceModule = sourceModuleFromNodeId(edge.source);
    const targetModule = sourceModuleFromNodeId(edge.target);
    const source = resolvePlhmDesignLeafId(sourceModule);
    const target = resolvePlhmDesignLeafId(targetModule);
    if (!source || !target || source === target) {
      continue;
    }
    if (visibleLeafIds.size && (!isVisiblePlhmDesignNode(source, visibleLeafIds) || !isVisiblePlhmDesignNode(target, visibleLeafIds))) {
      continue;
    }
    if (violationsOnly && edge.allowed) {
      continue;
    }
    const key = `${source}->${target}`;
    const current = aggregated.get(key) ?? {
      id: `design-dependency:${key}`,
      source,
      target,
      kind: "import",
      allowed: true,
      reasons: [],
      import_count: 0,
      weight: 0,
    };
    current.allowed = current.allowed && edge.allowed;
    current.import_count += edge.import_count;
    current.weight += edge.import_count;
    current.reasons = Array.from(new Set([...current.reasons, ...edge.reasons]));
    aggregated.set(key, current);
  }

  return Array.from(aggregated.values());
}

function resolvePlhmDesignLeafId(module) {
  if (module === "main") {
    return PLHM_ROOT.id;
  }

  for (const leaf of PLHM_LEAVES) {
    if (leaf.prefixes.some((prefix) => module === prefix || module.startsWith(`${prefix}.`))) {
      return leaf.id;
    }
  }

  return null;
}

function sourceModuleFromNodeId(nodeId) {
  return nodeId.startsWith("file:") ? nodeId.slice(5) : nodeId;
}

function isVisiblePlhmDesignNode(nodeId, visibleLeafIds) {
  return nodeId === PLHM_ROOT.id || visibleLeafIds.has(nodeId);
}
