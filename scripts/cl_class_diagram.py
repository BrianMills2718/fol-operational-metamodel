#!/usr/bin/env python3
"""Turn the imported OMG ODM Common Logic IR into a class diagram for the shared graph viewer.

Input: generated/odm-cl-metamodel-ir.json (standards-ir/v1, written by import_standards.py).
Output: generated/cl-class-diagram.json with
  - "graph": a typed-graph/v1 document (representation-router/graph-viewer): one node per
    uml-class, one parent-to-child edge per UML generalization, laid out top-down;
  - "details": per class, its parents, children, owned properties (name, type, multiplicity,
    association) and the properties of other classes typed as it.
Everything is read from the IR; nothing about logic is added here.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "generated" / "odm-cl-metamodel-ir.json"
DEFAULT_OUTPUT = ROOT / "generated" / "cl-class-diagram.json"


def multiplicity_text(prop: dict) -> str:
    m = prop.get("multiplicity") or {}
    lower, upper = m.get("lower"), m.get("upper")
    if lower is None and upper is None:
        return "1 (not stated; UML default)"
    lower = "1" if lower is None else lower
    upper = "1" if upper is None else upper
    return lower if lower == upper else f"{lower}..{upper}"


def build(ir: dict) -> dict:
    nodes = {n["id"]: n for n in ir["nodes"]}
    classes = {i: n for i, n in nodes.items() if n["kind"] == "uml-class"}
    names = {i: n["name"] for i, n in classes.items()}
    if len(set(names.values())) != len(names):
        raise ValueError("class names are not unique in this package")

    out_edges: dict[str, list[dict]] = {}
    for e in ir["edges"]:
        out_edges.setdefault(e["source"], []).append(e)

    generalizations = [(e["source"], e["target"]) for e in ir["edges"]
                       if e["kind"] == "generalizes-to" and e["source"] in classes and e["target"] in classes]

    def prop_record(owner_id: str, prop_id: str) -> dict:
        prop = nodes[prop_id]
        type_ids = [e["target"] for e in out_edges.get(prop_id, []) if e["kind"] == "typed-as"]
        assoc = [nodes[e["source"]]["name"] for e in ir["edges"]
                 if e["kind"] == "member-end" and e["target"] == prop_id]
        return {
            "name": prop["name"],
            "owner": names[owner_id],
            "type": names.get(type_ids[0], nodes.get(type_ids[0], {}).get("name")) if type_ids else None,
            "multiplicity": multiplicity_text(prop),
            "ordered": bool(prop.get("ordered")),
            "association": assoc[0] if assoc else None,
            "xmi_id": prop.get("xmi_id"),
        }

    details = {}
    for cid, cls in classes.items():
        props = [prop_record(cid, e["target"]) for e in out_edges.get(cid, []) if e["kind"] == "owns-property"]
        details[names[cid]] = {
            "abstract": bool(cls.get("abstract")),
            "xmi_id": cls.get("xmi_id"),
            "parents": sorted(names[p] for c, p in generalizations if c == cid),
            "children": sorted(names[c] for c, p in generalizations if p == cid),
            "properties": sorted(props, key=lambda p: p["name"]),
            "used_by": [],
        }
    for d in details.values():
        for prop in d["properties"]:
            if prop["type"] in details:
                details[prop["type"]]["used_by"].append({"owner": prop["owner"], "property": prop["name"],
                                                        "association": prop["association"]})
    for d in details.values():
        d["used_by"].sort(key=lambda u: (u["owner"], u["property"]))

    def explain(name: str) -> str:
        d = details[name]
        parts = ["Abstract class" if d["abstract"] else "Class"]
        parts.append(f"kind of {', '.join(d['parents'])}" if d["parents"] else "top of a hierarchy")
        n = len(d["properties"])
        parts.append(f"{n} propert{'y' if n == 1 else 'ies'}" + (f": {', '.join(p['name'] for p in d['properties'])}" if n else ""))
        return "; ".join(parts) + ". Click for details."

    graph = {
        "schema": "typed-graph/v1",
        "kinds": {
            "abstract": {"label": "abstract class", "color": "#7fb0ff",
                         "explain": "A UML abstract class: only its subclasses have direct instances."},
            "class": {"label": "class", "color": "#f0a25a",
                      "explain": "A UML class with direct instances."},
        },
        "nodes": [{"id": name, "label": name, "kind": "abstract" if details[name]["abstract"] else "class",
                   "explain": explain(name)} for name in sorted(details)],
        "edges": [{"id": f"gen:{names[c]}->{names[p]}", "source": names[p], "target": names[c]}
                  for c, p in sorted(generalizations, key=lambda cp: (names[cp[1]], names[cp[0]]))],
        "layout": {"direction": "DOWN", "algorithm": "layered"},
    }
    return {
        "format": "cl-class-diagram/v1",
        "source": ir["source"],
        "generated_by": "scripts/cl_class_diagram.py",
        "note": "Every class, generalization and property comes from the OMG ODM Common Logic XMI import; tooltips summarise those facts and add no others.",
        "graph": graph,
        "details": details,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    result = build(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    g = result["graph"]
    print(f"wrote {args.output}: {len(g['nodes'])} classes, {len(g['edges'])} generalizations")


if __name__ == "__main__":
    main()
