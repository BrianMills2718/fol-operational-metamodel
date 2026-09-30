const colors = {theory: "#59c3a5", view: "#8b9cf4", constant: "#e9ad59", other: "#ef7185"};
const labels = {theory: "Theory", view: "View", constant: "Constant", other: "Other"};

fetch("../generated/mmt-ir.json").then(response => { if (!response.ok) throw new Error(`Could not load generated MMT IR: ${response.status}. Run scripts/import_mmt.py extract.`); return response.json(); }).then(ir => {
  document.querySelector("#version").textContent = ir.source.sha256.slice(0, 12);
  document.querySelector("#description").textContent = `${ir.nodes.length} declarations extracted from ${ir.source.path}. ${ir.scope}.`;
  const categories = [...new Set(ir.nodes.map(item => colors[item.kind] ? item.kind : "other"))];
  const select = document.querySelector("#category");
  categories.forEach(key => { const option = document.createElement("option"); option.value = key; option.textContent = labels[key] || key; select.append(option); });
  const nodes = ir.nodes.map(item => ({...item, category: colors[item.kind] ? item.kind : "other", color: colors[item.kind] || colors.other}));
  const ids = new Set(nodes.map(node => node.id));
  const links = ir.edges.filter(edge => ids.has(edge.source) && ids.has(edge.target));
  const svg = d3.select("#graph"), width = svg.node().clientWidth, height = svg.node().clientHeight;
  const root = svg.append("g");
  svg.call(d3.zoom().scaleExtent([.35, 3]).on("zoom", event => root.attr("transform", event.transform)));
  const link = root.append("g").selectAll("line").data(links).join("line").attr("class", "link");
  const node = root.append("g").selectAll("g").data(nodes).join("g").attr("class", "node").call(d3.drag().on("start", (event,d) => { if (!event.active) simulation.alphaTarget(.25).restart(); d.fx=d.x; d.fy=d.y; }).on("drag",(event,d)=>{d.fx=event.x;d.fy=event.y;}).on("end",(event,d)=>{if(!event.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;}));
  node.append("circle").attr("r", 8).attr("fill", d => d.color);
  node.append("text").attr("dx", 12).attr("dy", 4).text(d => d.name);
  node.on("click", (event, d) => { node.classed("selected", n => n.id === d.id); const aside = document.querySelector("#detail"); aside.innerHTML = `<p class="eyebrow">${labels[d.category] || d.category}</p><h2></h2><p class="description"></p><p class="refs"></p><p class="location"></p><code class="type"></code>`; aside.querySelector("h2").textContent=d.name; aside.querySelector(".description").textContent=d.description; aside.querySelector(".refs").textContent=`Links: ${ir.edges.filter(e=>e.source===d.id).map(e=>`${e.kind} → ${nodes.find(n=>n.id===e.target)?.name || e.target}`).join(", ") || "none"}`; aside.querySelector(".location").textContent=`${d.source.path}:${d.source.line} · ${d.uri}`; if(d.type_surface) aside.querySelector(".type").textContent=d.type_surface; });
  const simulation = d3.forceSimulation(nodes).force("link", d3.forceLink(links).id(d=>d.id).distance(105)).force("charge", d3.forceManyBody().strength(-260)).force("center",d3.forceCenter(width/2,height/2)).force("collide",d3.forceCollide(38)).on("tick",()=>{link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);node.attr("transform",d=>`translate(${d.x},${d.y})`);});
  select.addEventListener("change", () => { const value=select.value; node.style("opacity",d=>value==="all"||d.category===value?1:.12); link.style("opacity",d=>value==="all"||d.source.category===value||d.target.category===value?.55:.04); });
}).catch(error => { document.querySelector("#description").textContent = error.message; console.error(error); });
