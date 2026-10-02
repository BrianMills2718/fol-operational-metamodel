const palette = {
  document: "#53b8db",
  theory: "#59c3a5",
  view: "#8b9cf4",
  function: "#e9ad59",
  constant: "#d99454",
  include: "#c27ce1",
  structure: "#ef7185",
  graph: "#7b8ca8",
  external: "#718096",
  other: "#ef7185"
};

const labels = {
  document: "Document",
  theory: "Theory",
  view: "View",
  function: "Function",
  constant: "Constant",
  include: "Include",
  structure: "Structure",
  graph: "Source graph",
  external: "External reference",
  other: "Other"
};

const ULO = "http://mathhub.info/ulo#";
const RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";

let viewSpecs = [];
let selectedView = null;
let currentIr = null;
let currentSimulation = null;
let liveMode = false;
let focusHistory = [];
let historyIndex = -1;

function shortName(uri) {
  if (!uri) return "external";
  const decoded = decodeURIComponent(uri);
  const pieces = decoded.split(/[?#/]/).filter(Boolean);
  return pieces[pieces.length - 1] || decoded;
}

function categoryFromTypes(types = []) {
  for (const type of types) {
    if (type.startsWith(ULO)) {
      const key = type.slice(ULO.length);
      if (palette[key]) return key;
    }
  }
  return "other";
}

function termValue(term) {
  if (term == null) return null;
  if (typeof term === "string") return term;
  if (typeof term.value === "string") return term.value;
  return null;
}

function resultBindings(payload) {
  if (Array.isArray(payload?.results?.bindings)) return payload.results.bindings;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.bindings)) return payload.bindings;
  if (Array.isArray(payload?.results?.results)) return payload.results.results;
  throw new Error("FLAMS returned an unfamiliar SPARQL result shape.");
}

function assertFocusIri(value) {
  const focus = value.trim();
  if (!focus.includes(":") || /[\s<>"{}|^\`]/.test(focus)) {
    throw new Error("Focus must be an absolute RDF IRI with no whitespace or angle brackets.");
  }
  return focus;
}

function predicateValues(predicates = []) {
  if (!predicates.length) return "";
  return "  VALUES ?predicate { " + predicates.map(p => `<${p}>`).join(" ") + " }\n";
}

function neighborhoodQuery(focus, spec) {
  return `PREFIX rdf: <${RDF_TYPE}>
PREFIX ulo: <${ULO}>

SELECT DISTINCT ?direction ?predicate ?other ?otherType ?graph
WHERE {
  VALUES ?focus { <${focus}> }
${predicateValues(spec.predicates)}
  GRAPH ?graph {
    {
      ?focus ?predicate ?other .
      BIND("out" AS ?direction)
    }
    UNION
    {
      ?other ?predicate ?focus .
      BIND("in" AS ?direction)
    }

    OPTIONAL { ?other rdf:type ?otherType . }
  }
}
ORDER BY ?direction ?predicate ?other ?otherType`;
}

function provenanceQuery(focus) {
  return `SELECT DISTINCT ?graph
WHERE {
  GRAPH ?graph {
    { <${focus}> ?p ?o . }
    UNION
    { ?s ?p <${focus}> . }
  }
}
ORDER BY ?graph`;
}

function queryForView(focus, spec) {
  return spec.mode === "provenance" ? provenanceQuery(focus) : neighborhoodQuery(focus, spec);
}

async function loadViewSpecs() {
  const response = await fetch("views.json");
  if (!response.ok) throw new Error(`Could not load semantic view definitions: ${response.status}`);
  const payload = await response.json();
  viewSpecs = payload.views || [];
  if (!viewSpecs.length) throw new Error("No semantic views are defined.");
  return viewSpecs;
}

function getView(id) {
  return viewSpecs.find(v => v.id === id) || viewSpecs[0];
}

async function queryFlams(endpoint, query) {
  const body = new URLSearchParams({query, decode_uris: "false"});
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
    body
  });
  if (!response.ok) {
    throw new Error(`FLAMS query failed: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadFlams(endpoint, focus, spec) {
  const payload = await queryFlams(endpoint, queryForView(focus, spec));
  const rows = resultBindings(payload);
  return spec.mode === "provenance"
    ? normalizeProvenanceRows(rows, focus, spec)
    : normalizeFocusRows(rows, focus, spec);
}

function baseFocusNode(focus) {
  return {
    id: focus,
    uri: focus,
    name: shortName(focus),
    types: [],
    provenance: [],
    category: "other",
    kind: "other",
    color: "#ffffff",
    focus: true
  };
}

function normalizeProvenanceRows(rows, focus, spec) {
  const focusNode = baseFocusNode(focus);
  const nodes = [focusNode];
  const edges = [];
  const seen = new Set();

  for (const row of rows) {
    const graph = termValue(row.graph);
    if (!graph || seen.has(graph)) continue;
    seen.add(graph);
    nodes.push({
      id: graph,
      uri: graph,
      name: shortName(graph),
      types: [],
      provenance: [graph],
      category: "graph",
      kind: "graph",
      color: palette.graph
    });
    edges.push({
      source: focus,
      target: graph,
      kind: "asserted-in",
      predicate: "derived:view/asserted-in",
      graphs: [graph],
      derived: true
    });
  }

  return {
    source: {sha256: "live-flams", input_kind: "FLAMS SPARQL / ULO"},
    scope: `${spec.label} view of ${focus}`,
    view: spec.id,
    nodes,
    edges,
    focus
  };
}

function normalizeFocusRows(rows, focus, spec) {
  const nodeMap = new Map();
  const edgeMap = new Map();

  const ensure = id => {
    if (!nodeMap.has(id)) {
      nodeMap.set(id, {
        id, uri: id, name: shortName(id),
        types: new Set(), provenance: new Set()
      });
    }
    return nodeMap.get(id);
  };

  const focusNode = ensure(focus);
  focusNode.focus = true;

  for (const row of rows) {
    const direction = termValue(row.direction);
    const predicate = termValue(row.predicate);
    const other = termValue(row.other);
    const otherType = termValue(row.otherType);
    const graph = termValue(row.graph);
    if (!direction || !predicate || !other) continue;

    const otherNode = ensure(other);
    if (otherType) otherNode.types.add(otherType);
    if (graph) {
      otherNode.provenance.add(graph);
      focusNode.provenance.add(graph);
    }

    if (predicate === RDF_TYPE && direction === "out") {
      focusNode.types.add(other);
    }

    const source = direction === "out" ? focus : other;
    const target = direction === "out" ? other : focus;
    const key = `${source}\n${predicate}\n${target}`;
    if (!edgeMap.has(key)) {
      edgeMap.set(key, {
        source,
        target,
        kind: shortName(predicate),
        predicate,
        graphs: new Set()
      });
    }
    if (graph) edgeMap.get(key).graphs.add(graph);
  }

  const nodes = [...nodeMap.values()].map(node => {
    const types = [...node.types];
    const category = categoryFromTypes(types);
    return {
      ...node,
      types,
      provenance: [...node.provenance],
      category,
      kind: category,
      color: node.focus ? "#ffffff" : (palette[category] || palette.other)
    };
  });

  const edges = [...edgeMap.values()].map(edge => ({
    ...edge,
    graphs: [...edge.graphs]
  }));

  return {
    source: {sha256: "live-flams", input_kind: "FLAMS SPARQL / ULO"},
    scope: `${spec.label} view of ${focus}`,
    view: spec.id,
    nodes,
    edges,
    focus
  };
}

async function loadIr(dataFile) {
  const response = await fetch(dataFile);
  if (!response.ok) throw new Error(`Could not load generated MMT IR: ${response.status}`);
  const ir = await response.json();
  const nodes = ir.nodes.map(item => ({
    ...item,
    category: palette[item.kind] ? item.kind : "other",
    color: palette[item.kind] || palette.other
  }));
  return {...ir, nodes};
}

function renderGraph(ir, layoutMode = "force", onRefocus = null) {
  const svg = d3.select("#graph");
  svg.selectAll("*").remove();

  const nodes = ir.nodes.map(d => ({...d}));
  const byId = new Map(nodes.map(node => [node.id, node]));

  for (const edge of ir.edges) {
    for (const id of [edge.source, edge.target]) {
      if (id && !byId.has(id)) {
        const external = {
          id, uri: id, name: shortName(id), kind: "external", category: "external",
          color: palette.external, description: "Referenced object outside the current projection.",
          external: true
        };
        nodes.push(external);
        byId.set(id, external);
      }
    }
  }

  const links = ir.edges.filter(edge => byId.has(edge.source) && byId.has(edge.target));
  const width = svg.node().clientWidth;
  const height = svg.node().clientHeight;
  const root = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.25, 4]).on("zoom", event => root.attr("transform", event.transform)));

  const link = root.append("g").selectAll("line").data(links).join("line")
    .attr("class", d => "link" + (d.derived ? " derived" : ""));
  const edgeLabel = root.append("g").selectAll("text").data(links).join("text")
    .attr("class", "edge-label").text(d => d.kind);

  const node = root.append("g").selectAll("g").data(nodes).join("g")
    .attr("class", d => "node" + (d.focus ? " focus" : ""))
    .call(d3.drag()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.25).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      }));

  node.append("circle")
    .attr("r", d => d.focus ? 11 : d.external ? 6 : 8)
    .attr("fill", d => d.color);
  node.append("text").attr("dx", 12).attr("dy", 4).text(d => d.name);

  node.on("click", (event, d) => {
    node.classed("selected", n => n.id === d.id);
    showDetail(d, links, byId);
    if (onRefocus && d.uri && d.uri !== ir.focus) {
      onRefocus(d.uri);
    }
  });

  const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(125))
    .force("charge", d3.forceManyBody().strength(-340))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(46));

  if (layoutMode === "layered" && ir.focus) {
    const focusId = ir.focus;
    simulation
      .force("x", d3.forceX(d => {
        if (d.id === focusId) return width / 2;
        const incoming = links.some(e => (e.target.id || e.target) === focusId && (e.source.id || e.source) === d.id);
        const outgoing = links.some(e => (e.source.id || e.source) === focusId && (e.target.id || e.target) === d.id);
        if (incoming && !outgoing) return width * 0.22;
        if (outgoing && !incoming) return width * 0.78;
        return width / 2;
      }).strength(0.65))
      .force("y", d3.forceY(height / 2).strength(0.08));
  }

  simulation.on("tick", () => {
    link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    edgeLabel.attr("x", d => (d.source.x + d.target.x) / 2)
      .attr("y", d => (d.source.y + d.target.y) / 2);
    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });

  populateCategoryFilter(nodes, links, node, link, edgeLabel);
  return simulation;
}

function showDetail(d, links, byId) {
  const aside = document.querySelector("#detail");
  aside.innerHTML =
    '<p class="eyebrow"></p><h2></h2><p class="description"></p>' +
    '<p class="types"></p><p class="refs"></p><p class="location"></p>' +
    '<pre class="type"></pre><pre class="definition"></pre>';
  aside.querySelector(".eyebrow").textContent =
    d.focus ? "FOCUS · " + (labels[d.category] || d.kind) : (labels[d.category] || d.kind);
  aside.querySelector("h2").textContent = d.name;
  aside.querySelector(".description").textContent = d.description || d.uri || "";
  aside.querySelector(".types").textContent =
    d.types?.length ? "Types: " + d.types.map(shortName).join(", ") : "";
  aside.querySelector(".refs").textContent =
    "Links: " + (links.filter(e =>
      (e.source.id || e.source) === d.id || (e.target.id || e.target) === d.id)
      .map(e => {
        const outbound = (e.source.id || e.source) === d.id;
        const otherId = outbound ? (e.target.id || e.target) : (e.source.id || e.source);
        const prefix = e.derived ? "derived " : "";
        return `${outbound ? "→" : "←"} ${prefix}${e.kind} ${byId.get(otherId)?.name || shortName(otherId)}`;
      }).join(", ") || "none");
  aside.querySelector(".location").textContent =
    d.provenance?.length ? "Graph: " + d.provenance.join(", ") :
      d.source?.source_ref || d.source?.path || d.uri || "";
  const type = d.type_surface || d.type_xml;
  if (type) aside.querySelector(".type").textContent = "type\n" + type;
  if (d.definition_xml) aside.querySelector(".definition").textContent =
    "definition\n" + d.definition_xml;
}

function populateCategoryFilter(nodes, links, node, link, edgeLabel) {
  const select = document.querySelector("#category");
  select.innerHTML = '<option value="all">all concepts</option>';
  [...new Set(nodes.map(item => item.category))].sort().forEach(key => {
    const option = document.createElement("option");
    option.value = key;
    option.textContent = labels[key] || key;
    select.append(option);
  });

  select.onchange = () => {
    const value = select.value;
    node.style("opacity", d => value === "all" || d.category === value ? 1 : 0.12);
    link.style("opacity", d =>
      value === "all" || d.source.category === value || d.target.category === value ? 0.55 : 0.04);
    edgeLabel.style("opacity", d =>
      value === "all" || d.source.category === value || d.target.category === value ? 0.7 : 0.03);
  };
}

function updateHistory(focus, replace = false) {
  if (!focus) return;
  if (replace && historyIndex >= 0) {
    focusHistory[historyIndex] = focus;
  } else if (focusHistory[historyIndex] !== focus) {
    focusHistory = focusHistory.slice(0, historyIndex + 1);
    focusHistory.push(focus);
    historyIndex = focusHistory.length - 1;
  }
  renderBreadcrumbs();
}

function renderBreadcrumbs() {
  const bar = document.querySelector("#breadcrumbs");
  bar.innerHTML = "";
  focusHistory.forEach((focus, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "crumb" + (index === historyIndex ? " active" : "");
    button.textContent = shortName(focus);
    button.title = focus;
    button.addEventListener("click", () => {
      historyIndex = index;
      document.querySelector("#focus").value = focus;
      renderBreadcrumbs();
      loadLive({pushHistory: false});
    });
    bar.append(button);
  });

  document.querySelector("#back").disabled = historyIndex <= 0;
  document.querySelector("#forward").disabled =
    historyIndex < 0 || historyIndex >= focusHistory.length - 1;
}

function updateUrl(focus, endpoint, viewId) {
  const url = new URL(window.location.href);
  url.searchParams.set("focus", focus);
  url.searchParams.set("endpoint", endpoint);
  url.searchParams.set("view", viewId);
  history.replaceState(null, "", url);
}

async function boot() {
  await loadViewSpecs();

  const params = new URLSearchParams(window.location.search);
  const focusInput = document.querySelector("#focus");
  const endpointInput = document.querySelector("#endpoint");
  const layoutSelect = document.querySelector("#layout");
  const viewSelect = document.querySelector("#semantic-view");

  const focusFromUrl = params.get("focus") || "";
  const endpointFromUrl = params.get("endpoint") || "/api/backend/query";
  const viewFromUrl = params.get("view") || "all";

  focusInput.value = focusFromUrl;
  endpointInput.value = endpointFromUrl;

  for (const spec of viewSpecs) {
    const option = document.createElement("option");
    option.value = spec.id;
    option.textContent = spec.label;
    viewSelect.append(option);
  }
  viewSelect.value = getView(viewFromUrl).id;
  selectedView = getView(viewSelect.value);

  window.loadLive = async ({pushHistory = true} = {}) => {
    try {
      document.querySelector("#description").textContent = "Loading…";
      const focus = assertFocusIri(focusInput.value);
      const endpoint = endpointInput.value.trim() || "/api/backend/query";
      selectedView = getView(viewSelect.value);
      currentIr = await loadFlams(endpoint, focus, selectedView);
      liveMode = true;
      document.querySelector("#version").textContent = "LIVE";
      document.querySelector("#description").textContent =
        `${selectedView.label}: ${currentIr.nodes.length} nodes · ${currentIr.edges.length} relations · ${selectedView.description}`;
      if (pushHistory) updateHistory(focus);
      updateUrl(focus, endpoint, selectedView.id);
      currentSimulation?.stop();
      currentSimulation = renderGraph(currentIr, layoutSelect.value, uri => {
        focusInput.value = uri;
        loadLive({pushHistory: true});
      });
    } catch (error) {
      document.querySelector("#description").textContent = error.message;
      console.error(error);
    }
  };

  async function loadInitial() {
    if (focusInput.value.trim()) {
      updateHistory(focusInput.value.trim());
      await loadLive({pushHistory: false});
      return;
    }
    const dataFile = params.get("data") || "../generated/pinned-fol-ir.json";
    currentIr = await loadIr(dataFile);
    liveMode = false;
    document.querySelector("#version").textContent =
      currentIr.source.sha256?.slice(0, 12) || "IR";
    document.querySelector("#description").textContent =
      `${currentIr.nodes.length} imported nodes from ${currentIr.source.input_kind || "unknown input"} · ${currentIr.scope}.`;
    currentSimulation?.stop();
    currentSimulation = renderGraph(currentIr, layoutSelect.value);
  }

  document.querySelector("#load-focus").addEventListener("click", () => loadLive());
  focusInput.addEventListener("keydown", event => {
    if (event.key === "Enter") loadLive();
  });
  viewSelect.addEventListener("change", () => {
    selectedView = getView(viewSelect.value);
    if (focusInput.value.trim()) loadLive({pushHistory: false});
  });
  layoutSelect.addEventListener("change", () => {
    if (!currentIr) return;
    currentSimulation?.stop();
    currentSimulation = renderGraph(
      currentIr,
      layoutSelect.value,
      liveMode ? uri => {
        focusInput.value = uri;
        loadLive({pushHistory: true});
      } : null
    );
  });

  document.querySelector("#back").addEventListener("click", () => {
    if (historyIndex <= 0) return;
    historyIndex -= 1;
    focusInput.value = focusHistory[historyIndex];
    renderBreadcrumbs();
    loadLive({pushHistory: false});
  });

  document.querySelector("#forward").addEventListener("click", () => {
    if (historyIndex >= focusHistory.length - 1) return;
    historyIndex += 1;
    focusInput.value = focusHistory[historyIndex];
    renderBreadcrumbs();
    loadLive({pushHistory: false});
  });

  renderBreadcrumbs();
  await loadInitial();
}

boot();
