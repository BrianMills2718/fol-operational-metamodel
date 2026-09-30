const colors = {entity_types: "#59c3a5", relations: "#e9ad59", constructors: "#8b9cf4", judgments: "#ef7185", semantic_rules: "#c27ce1", satisfaction: "#53b8db", theory: "#e88750", semantic_consequence: "#b3cf67"};
const labels = {entity_types: "Entities", relations: "Relations", constructors: "Constructors", judgments: "Judgments", semantic_rules: "Semantic rules", satisfaction: "Satisfaction", theory: "Theory", semantic_consequence: "Semantic consequence"};

fetch("../spec/fol.json").then(response => { if (!response.ok) throw new Error(`Could not load spec: ${response.status}`); return response.json(); }).then(spec => {
  document.querySelector("#version").textContent = `v${spec.schema_version}`;
  document.querySelector("#description").textContent = spec.description;
  const categories = spec.schema.collections;
  const select = document.querySelector("#category");
  categories.forEach(key => { const option = document.createElement("option"); option.value = key; option.textContent = labels[key] || key; select.append(option); });
  const nodes = categories.flatMap(category => spec.model[category].map(item => ({...item, category, color: colors[category]})));
  const ids = new Set(nodes.map(node => node.id));
  const links = nodes.flatMap(source => source.references.filter(id => ids.has(id)).map(target => ({source: source.id, target})));
  const svg = d3.select("#graph"), width = svg.node().clientWidth, height = svg.node().clientHeight;
  const root = svg.append("g");
  svg.call(d3.zoom().scaleExtent([.35, 3]).on("zoom", event => root.attr("transform", event.transform)));
  const link = root.append("g").selectAll("line").data(links).join("line").attr("class", "link");
  const node = root.append("g").selectAll("g").data(nodes).join("g").attr("class", "node").call(d3.drag().on("start", (event,d) => { if (!event.active) simulation.alphaTarget(.25).restart(); d.fx=d.x; d.fy=d.y; }).on("drag",(event,d)=>{d.fx=event.x;d.fy=event.y;}).on("end",(event,d)=>{if(!event.active)simulation.alphaTarget(0);d.fx=null;d.fy=null;}));
  node.append("circle").attr("r", 8).attr("fill", d => d.color);
  node.append("text").attr("dx", 12).attr("dy", 4).text(d => d.name);
  node.on("click", (event, d) => { node.classed("selected", n => n.id === d.id); const aside = document.querySelector("#detail"); aside.innerHTML = `<p class="eyebrow">${labels[d.category] || d.category}</p><h2></h2><p></p><p class="refs"></p>`; aside.querySelector("h2").textContent=d.name; aside.querySelectorAll("p")[1].textContent=d.description; aside.querySelector(".refs").textContent=`References: ${d.references.map(id=>nodes.find(n=>n.id===id)?.name || id).join(", ") || "none"}`; });
  const simulation = d3.forceSimulation(nodes).force("link", d3.forceLink(links).id(d=>d.id).distance(105)).force("charge", d3.forceManyBody().strength(-260)).force("center",d3.forceCenter(width/2,height/2)).force("collide",d3.forceCollide(38)).on("tick",()=>{link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);node.attr("transform",d=>`translate(${d.x},${d.y})`);});
  select.addEventListener("change", () => { const value=select.value; node.style("opacity",d=>value==="all"||d.category===value?1:.12); link.style("opacity",d=>value==="all"||d.source.category===value||d.target.category===value?.55:.04); });
}).catch(error => { document.querySelector("#description").textContent = error.message; console.error(error); });
