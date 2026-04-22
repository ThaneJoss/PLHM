import cytoscape from "cytoscape";

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
