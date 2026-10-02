const palette = {
  document: "#53b8db",
  theory: "#59c3a5",
  view: "#8b9cf4",
  function: "#e9ad59",
  constant: "#d99454",
  include: "#c27ce1",
  structure: "#ef7185",
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
  external: "External reference",
  other: "Other"
};

const ULO = "http://mathhub.info/ulo#";
const RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";

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

function focusQuery(focus) {
  return `PREFIX rdf: <${RDF_TYPE}>
PREFIX ulo: <${ULO}>

SELECT DISTINCT ?direction ?predicate ?other ?otherType ?graph
WHERE {
  VALUES ?focus { <${focus}> }

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

async function loadFlams(endpoint, focus) {
  const body = new URLSearchParams({
    query: focusQuery(focus),
    decode_uris: "false"
  });
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
    body
  });
  if (!response.ok) {
    throw new Error(`FLAMS query failed: ${response.status} ${response.statusText}`);
  }
  const payload = await response.json();
  const rows = resultBindings(payload);
  return normalizeFocusRows(rows, focus);
}

function normalizeFocusRows(rows, focus) {
  const nodeMap = new Map();
  const edgeMap = new Map();

  const ensure = id => {
    if (!nodeMap.has(id)) {
      nodeMap.set(id, {id, uri: id, name: shortName(id), types: new Set(), provenance: new Set()});
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
    scope: `one-hop semantic neighborhood of ${focus}`,
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

function renderGraph(ir, layoutMode = "force") {
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

  const link = root.append("g").selectAll("line").data(links).join("line").attr("class", "link");
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

  node.append("circle").attr("r", d => d.focus ? 11 : d.external ? 6 : 8).attr("fill", d => d.color);
  node.append("text").attr("dx", 12).attr("dy", 4).text(d => d.name);

  node.on("click", (event, d) => {
    node.classed("selected", n => n.id === d.id);
    showDetail(d, links, byId);
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
        const incoming = links.some(e => e.target === focusId && e.source === d.id);
        const outgoing = links.some(e => e.source === focusId && e.target === d.id);
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
  aside.querySelector(".eyebrow").textContent = d.focus ? "FOCUS · " + (labels[d.category] || d.kind) : (labels[d.category] || d.kind);
  aside.querySelector("h2").textContent = d.name;
  aside.querySelector(".description").textContent = d.description || d.uri || "";
  aside.querySelector(".types").textContent = d.types?.length ? "Types: " + d.types.map(shortName).join(", ") : "";
  aside.querySelector(".refs").textContent =
    "Links: " + (links.filter(e => (e.source.id || e.source) === d.id || (e.target.id || e.target) === d.id)
      .map(e => {
        const outbound = (e.source.id || e.source) === d.id;
        const otherId = outbound ? (e.target.id || e.target) : (e.source.id || e.source);
        return `${outbound ? "→" : "←"} ${e.kind} ${byId.get(otherId)?.name || shortName(otherId)}`;
      }).join(", ") || "none");
  aside.querySelector(".location").textContent =
    d.provenance?.length ? "Graph: " + d.provenance.join(", ") :
      d.source?.source_ref || d.source?.path || d.uri || "";
  const type = d.type_surface || d.type_xml;
  if (type) aside.querySelector(".type").textContent = "type\n" + type;
  if (d.definition_xml) aside.querySelector(".definition").textContent = "definition\n" + d.definition_xml;
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

let currentIr = null;
let currentSimulation = null;

async function boot() {
  const params = new URLSearchParams(window.location.search);
  const focusInput = document.querySelector("#focus");
  const endpointInput = document.querySelector("#endpoint");
  const layoutSelect = document.querySelector("#layout");
  const focusFromUrl = params.get("focus") || "";
  const endpointFromUrl = params.get("endpoint") || "/api/backend/query";
  focusInput.value = focusFromUrl;
  endpointInput.value = endpointFromUrl;

  async function load() {
    try {
      document.querySelector("#description").textContent = "Loading…";
      const focusValue = focusInput.value.trim();
      if (focusValue) {
        const focus = assertFocusIri(focusValue);
        currentIr = await loadFlams(endpointInput.value.trim() || "/api/backend/query", focus);
        document.querySelector("#version").textContent = "LIVE";
        document.querySelector("#description").textContent =
          `${currentIr.nodes.length} nodes · ${currentIr.edges.length} explicit ULO relations · ${currentIr.scope}`;
        const url = new URL(window.location.href);
        url.searchParams.set("focus", focus);
        url.searchParams.set("endpoint", endpointInput.value.trim() || "/api/backend/query");
        history.replaceState(null, "", url);
      } else {
        const dataFile = params.get("data") || "../generated/pinned-fol-ir.json";
        currentIr = await loadIr(dataFile);
        document.querySelector("#version").textContent = currentIr.source.sha256?.slice(0, 12) || "IR";
        document.querySelector("#description").textContent =
          `${currentIr.nodes.length} imported nodes from ${currentIr.source.input_kind || "unknown input"} · ${currentIr.scope}.`;
      }
      currentSimulation?.stop();
      currentSimulation = renderGraph(currentIr, layoutSelect.value);
    } catch (error) {
      document.querySelector("#description").textContent = error.message;
      console.error(error);
    }
  }

  document.querySelector("#load-focus").addEventListener("click", load);
  focusInput.addEventListener("keydown", event => { if (event.key === "Enter") load(); });
  layoutSelect.addEventListener("change", () => {
    if (!currentIr) return;
    currentSimulation?.stop();
    currentSimulation = renderGraph(currentIr, layoutSelect.value);
  });

  await load();
}

boot();
