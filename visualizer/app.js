const colors = {
  document: "#53b8db",
  theory: "#59c3a5",
  view: "#8b9cf4",
  constant: "#e9ad59",
  include: "#c27ce1",
  structure: "#ef7185",
  external: "#718096",
  other: "#ef7185"
};
const labels = {
  document: "Document",
  theory: "Theory",
  view: "View",
  constant: "Constant",
  include: "Include",
  structure: "Structure",
  external: "External reference",
  other: "Other"
};

function shortName(uri) {
  if (!uri) return "external";
  const pieces = uri.split(/[?#/]/).filter(Boolean);
  return pieces[pieces.length - 1] || uri;
}

const dataFile = new URLSearchParams(window.location.search).get("data") || "../generated/pinned-fol-ir.json";

fetch(dataFile)
  .then(response => {
    if (!response.ok) throw new Error(`Could not load generated MMT IR: ${response.status}`);
    return response.json();
  })
  .then(ir => {
    document.querySelector("#version").textContent = ir.source.sha256.slice(0, 12);
    document.querySelector("#description").textContent =
      `${ir.nodes.length} imported nodes from ${ir.source.input_kind || "unknown input"} · ${ir.scope}.`;

    const nodes = ir.nodes.map(item => ({
      ...item,
      category: colors[item.kind] ? item.kind : item.kind?.startsWith("derived:") ? "other" : "other",
      color: colors[item.kind] || colors.other
    }));

    const byId = new Map(nodes.map(node => [node.id, node]));
    for (const edge of ir.edges) {
      for (const id of [edge.source, edge.target]) {
        if (id && !byId.has(id)) {
          const external = {
            id,
            uri: id,
            name: shortName(id),
            kind: "external",
            category: "external",
            color: colors.external,
            description: "Referenced MMT/OMDoc object outside the imported document.",
            references: [],
            external: true
          };
          nodes.push(external);
          byId.set(id, external);
        }
      }
    }

    const categories = [...new Set(nodes.map(item => item.category))];
    const select = document.querySelector("#category");
    categories.forEach(key => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = labels[key] || key;
      select.append(option);
    });

    const links = ir.edges.filter(edge => byId.has(edge.source) && byId.has(edge.target));
    const svg = d3.select("#graph");
    const width = svg.node().clientWidth;
    const height = svg.node().clientHeight;
    const root = svg.append("g");
    svg.call(d3.zoom().scaleExtent([0.35, 3]).on("zoom", event => root.attr("transform", event.transform)));

    const link = root.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "link");

    const edgeLabel = root.append("g")
      .selectAll("text")
      .data(links)
      .join("text")
      .attr("class", "edge-label")
      .text(d => d.kind);

    const node = root.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("class", "node")
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
      .attr("r", d => d.external ? 6 : 8)
      .attr("fill", d => d.color);

    node.append("text")
      .attr("dx", 12)
      .attr("dy", 4)
      .text(d => d.name);

    node.on("click", (event, d) => {
      node.classed("selected", n => n.id === d.id);
      const aside = document.querySelector("#detail");
      aside.innerHTML =
        '<p class="eyebrow"></p><h2></h2><p class="description"></p><p class="classifications"></p><p class="refs"></p>' +
        '<p class="location"></p><pre class="type"></pre><pre class="definition"></pre>';
      aside.querySelector(".eyebrow").textContent = labels[d.category] || d.kind;
      aside.querySelector("h2").textContent = d.name;
      aside.querySelector(".description").textContent = d.description || "";
      aside.querySelector(".classifications").textContent =
        d.mmt_predicates?.length ? "MMT classifications: " + d.mmt_predicates.join(", ") : "";
      aside.querySelector(".refs").textContent =
        "Links: " + (links.filter(e => e.source.id === d.id || e.source === d.id)
          .map(e => `${e.kind} → ${byId.get(e.target.id || e.target)?.name || e.target.id || e.target}`)
          .join(", ") || "none");
      const source = d.source || {};
      aside.querySelector(".location").textContent =
        source.source_ref || (source.path ? `${source.path}${source.line ? ":" + source.line : ""}` : d.uri || "");
      const type = d.type_surface || d.type_xml;
      if (type) aside.querySelector(".type").textContent = "type\n" + type;
      const definition = d.definition_xml;
      if (definition) aside.querySelector(".definition").textContent = "definition\n" + definition;
    });

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(d => d.id).distance(d => d.kind === "uses-symbol" ? 135 : 105))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(42))
      .on("tick", () => {
        link
          .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
        edgeLabel
          .attr("x", d => (d.source.x + d.target.x) / 2)
          .attr("y", d => (d.source.y + d.target.y) / 2);
        node.attr("transform", d => `translate(${d.x},${d.y})`);
      });

    select.addEventListener("change", () => {
      const value = select.value;
      node.style("opacity", d => value === "all" || d.category === value ? 1 : 0.12);
      link.style("opacity", d =>
        value === "all" || d.source.category === value || d.target.category === value ? 0.55 : 0.04);
      edgeLabel.style("opacity", d =>
        value === "all" || d.source.category === value || d.target.category === value ? 0.7 : 0.03);
    });
  })
  .catch(error => {
    document.querySelector("#description").textContent = error.message;
    console.error(error);
  });
