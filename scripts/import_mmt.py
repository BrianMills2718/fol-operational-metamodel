#!/usr/bin/env python3
"""Import MMT source or compiled OMDoc into a normalized graph IR.

OMDoc is preferred because it is produced by MMT after parsing/type-checking.
The source extractor remains a deliberately conservative fallback.
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "upstream/sources.json"
IR_PATH = ROOT / "generated/mmt-ir.json"
SEPARATOR = "❙"
END = "❚"
SOURCE_REF_REL = "http://cds.omdoc.org/mmt?metadata?sourceRef"


def source_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def bytes_sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _xml_fragment(element):
    if element is None:
        return None
    return ET.tostring(element, encoding="unicode")


def _child(element, local_name):
    return next((child for child in element if _local(child.tag) == local_name), None)


def _source_ref(element):
    for node in element.iter():
        if _local(node.tag) == "link" and node.attrib.get("rel") == SOURCE_REF_REL:
            return node.attrib.get("resource")
    return None


def _symbol_uri(oms):
    base = oms.attrib.get("base", "")
    module = oms.attrib.get("module")
    name = oms.attrib.get("name")
    if not name:
        return None
    if module:
        return f"{base}?{module}?{name}" if base else f"{module}?{name}"
    return f"{base}?{name}" if base else name


def _module_uri(element, inherited_base):
    base = element.attrib.get("base") or inherited_base
    name = element.attrib.get("name")
    explicit = element.attrib.get("uri")
    if explicit:
        return explicit
    if name:
        return f"{base}?{name}" if base else name
    return base


def _component_text(element, name):
    return _xml_fragment(_child(element, name))


def extract_omdoc(xml_text, source_uri, source_path, source_hash):
    """Extract explicit MMT structure from compiled OMDoc XML.

    This does not infer logical meaning from OpenMath terms or symbol names.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"invalid OMDoc XML: {exc}") from exc

    nodes, edges = [], []
    root_base = root.attrib.get("base") or source_uri
    document_id = source_uri
    nodes.append({
        "id": document_id, "uri": document_id, "name": Path(source_path).name,
        "kind": "document", "description": "Compiled OMDoc document.",
        "references": [], "source": {"uri": source_uri, "path": source_path}
    })

    def add_edge(source, target, kind):
        if source and target:
            edge = {"source": source, "target": target, "kind": kind}
            if edge not in edges:
                edges.append(edge)

    modules = [el for el in root.iter() if _local(el.tag) in {"theory", "view"}]
    for module in modules:
        kind = _local(module.tag)
        module_uri = _module_uri(module, root_base)
        if not module_uri:
            continue
        node = {
            "id": module_uri, "uri": module_uri,
            "name": module.attrib.get("name") or module_uri,
            "kind": kind,
            "description": f"MMT {kind} from compiled OMDoc.",
            "references": [],
            "source": {"uri": source_uri, "path": source_path, "source_ref": _source_ref(module)}
        }
        for key in ("meta", "from", "to", "implicit"):
            if module.attrib.get(key):
                node[key] = module.attrib[key]
        nodes.append(node)
        add_edge(document_id, module_uri, "contains-module")
        add_edge(module_uri, module.attrib.get("meta"), "meta-theory")
        if kind == "view":
            add_edge(module_uri, module.attrib.get("from"), "view-from")
            add_edge(module_uri, module.attrib.get("to"), "view-to")

        import_index = 0
        for child in module:
            child_kind = _local(child.tag)
            if child_kind == "constant":
                name = child.attrib.get("name")
                if not name:
                    continue
                decl_uri = f"{module_uri}?{name}"
                declaration = {
                    "id": decl_uri, "uri": decl_uri, "name": name, "kind": "constant",
                    "description": "MMT constant from compiled OMDoc.",
                    "references": [],
                    "source": {"uri": source_uri, "path": source_path, "source_ref": _source_ref(child)},
                    "type_xml": _component_text(child, "type"),
                    "definition_xml": _component_text(child, "definition"),
                    "role": child.attrib.get("role"),
                    "aliases": child.attrib.get("alias", "").split()
                }
                nodes.append(declaration)
                add_edge(module_uri, decl_uri, "declares")
                seen_refs = set()
                for desc in child.iter():
                    if _local(desc.tag) == "OMS":
                        target = _symbol_uri(desc)
                        if target and target != decl_uri and target not in seen_refs:
                            seen_refs.add(target)
                            declaration["references"].append(target)
                            add_edge(decl_uri, target, "uses-symbol")
            elif child_kind == "import":
                target = child.attrib.get("from")
                name = child.attrib.get("name")
                import_index += 1
                import_id = f"{module_uri}?@import-{import_index}"
                import_node = {
                    "id": import_id, "uri": import_id,
                    "name": name or (target.rsplit("?", 1)[-1] if target else f"import-{import_index}"),
                    "kind": "structure" if name else "include",
                    "description": "MMT structure/import from compiled OMDoc.",
                    "references": [target] if target else [],
                    "source": {"uri": source_uri, "path": source_path, "source_ref": _source_ref(child)},
                    "from": target, "implicit": child.attrib.get("implicit"), "total": child.attrib.get("total")
                }
                nodes.append(import_node)
                add_edge(module_uri, import_id, "declares")
                add_edge(import_id, target, "imports")
            elif child_kind == "derived":
                name = child.attrib.get("name")
                if name:
                    decl_uri = f"{module_uri}?{name}"
                    nodes.append({
                        "id": decl_uri, "uri": decl_uri, "name": name,
                        "kind": f"derived:{child.attrib.get('feature', 'unknown')}",
                        "description": "MMT derived declaration from compiled OMDoc.",
                        "references": [],
                        "source": {"uri": source_uri, "path": source_path, "source_ref": _source_ref(child)},
                        "type_xml": _component_text(child, "type"),
                        "definition_xml": _component_text(child, "definition")
                    })
                    add_edge(module_uri, decl_uri, "declares")

    return {
        "format": "mmt-ir/v2",
        "source": {
            "uri": source_uri, "path": source_path, "sha256": source_hash,
            "input_kind": "omdoc", "extractor": "omdoc-xml-structural"
        },
        "scope": "compiled OMDoc structure and explicit OpenMath symbol references; no semantic inference",
        "nodes": nodes, "edges": edges
    }



def extract_archivegraph(json_text, source_uri, source_path, source_hash):
    """Convert MMT :jgraph/json output into normalized graph IR.

    MMT's archivegraph endpoint already provides theory nodes and typed graph
    edges (e.g. meta/include/structure/view). We preserve those explicit styles
    without inferring additional semantics.
    """
    try:
        graph = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid archivegraph JSON: {exc}") from exc
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list) or not isinstance(graph.get("edges"), list):
        raise ValueError("archivegraph JSON must contain nodes and edges arrays")

    nodes, edges = [], []
    for item in graph["nodes"]:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        style = item.get("style") or "archive-node"
        kind = style if style in {"theory", "document"} else f"archive-node:{style}"
        node = {
            "id": item["id"],
            "uri": item.get("uri") or item["id"],
            "name": item.get("label") or item["id"].rsplit("?", 1)[-1],
            "kind": kind,
            "description": "MMT archive/theory graph node.",
            "references": [],
            "source": {"uri": source_uri, "path": source_path},
            "archivegraph_style": style,
        }
        if item.get("url"):
            node["mmt_url"] = item["url"]
        for key, value in item.items():
            if key not in {"id", "uri", "label", "style", "url"}:
                node.setdefault("archivegraph_data", {})[key] = value
        nodes.append(node)

    for item in graph["edges"]:
        if not isinstance(item, dict) or not item.get("from") or not item.get("to"):
            continue
        edge = {
            "source": item["from"],
            "target": item["to"],
            "kind": item.get("style") or "archive-edge",
        }
        if item.get("id"):
            edge["id"] = item["id"]
        if item.get("label"):
            edge["label"] = item["label"]
        if item.get("url"):
            edge["mmt_url"] = item["url"]
        extra = {k: v for k, v in item.items() if k not in {"from", "to", "style", "id", "label", "url"}}
        if extra:
            edge["archivegraph_data"] = extra
        edges.append(edge)

    return {
        "format": "mmt-ir/v2",
        "source": {
            "uri": source_uri,
            "path": source_path,
            "sha256": source_hash,
            "input_kind": "archivegraph",
            "extractor": "mmt-jgraph-structural",
        },
        "scope": "MMT-generated archive/theory graph only; declaration detail requires OMDoc",
        "nodes": nodes,
        "edges": edges,
    }


def merge_irs(irs, source_uri="merged://mmt-graph"):
    """Merge archive-level and declaration-level IR by stable MMT URI.

    Later IRs win scalar field conflicts, so callers should pass archivegraph
    first and OMDoc second when declaration-level detail should take priority.
    Provenance from all inputs is retained.
    """
    node_map = {}
    edge_map = {}
    input_sources = []

    for ir in irs:
        input_sources.append(ir.get("source", {}))
        for node in ir.get("nodes", []):
            node_id = node.get("id")
            if not node_id:
                continue
            if node_id not in node_map:
                node_map[node_id] = dict(node)
            else:
                previous = node_map[node_id]
                merged = dict(previous)
                merged.update({k: v for k, v in node.items() if v not in (None, "", [], {})})
                refs = list(dict.fromkeys((previous.get("references") or []) + (node.get("references") or [])))
                merged["references"] = refs
                provenance = []
                for src in previous.get("provenance", []):
                    if src not in provenance:
                        provenance.append(src)
                if previous.get("source") and previous["source"] not in provenance:
                    provenance.append(previous["source"])
                for src in node.get("provenance", []):
                    if src not in provenance:
                        provenance.append(src)
                if node.get("source") and node["source"] not in provenance:
                    provenance.append(node["source"])
                if provenance:
                    merged["provenance"] = provenance
                node_map[node_id] = merged

        for edge in ir.get("edges", []):
            if not edge.get("source") or not edge.get("target"):
                continue
            key = (
                edge.get("source"),
                edge.get("target"),
                edge.get("kind"),
                edge.get("id"),
                edge.get("label"),
            )
            edge_map.setdefault(key, dict(edge))

    digest_material = json.dumps(input_sources, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "format": "mmt-ir/v2",
        "source": {
            "uri": source_uri,
            "path": "merged",
            "sha256": hashlib.sha256(digest_material).hexdigest(),
            "input_kind": "merged",
            "extractor": "uri-merge",
            "inputs": input_sources,
        },
        "scope": "merged MMT archivegraph and declaration-level IR; no new semantic inference",
        "nodes": list(node_map.values()),
        "edges": list(edge_map.values()),
    }

def extract(text, source_uri, source_path, source_hash):
    """Fallback extractor for a conservative line-oriented subset of MMT source."""
    lines = text.splitlines()
    namespace = ""
    nodes, edges = [], []
    current_module = None
    module_re = re.compile(r"^\s*(theory|view)\s+([^\s:=]+)(?:\s*:\s*([^=]+))?\s*=\s*$")
    include_re = re.compile(r"^\s*include\s+(.+?)\s*$")
    constant_re = re.compile(r"^\s*([\w.'-]+)\s*:\s*(.+?)\s*$")

    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if line == END:
            current_module = None
            continue
        if not line or line.startswith("#"):
            continue
        if line.startswith("namespace "):
            namespace = line[len("namespace "):].split()[0]
            continue
        module = module_re.match(line)
        if module:
            kind, name, meta = module.groups()
            uri = f"{namespace}?{name}" if namespace else name
            current_module = {
                "id": uri, "uri": uri, "name": name, "kind": kind,
                "meta_theory": meta.strip() if meta else None,
                "description": f"MMT {kind} declaration imported from source.",
                "references": [],
                "source": {"uri": source_uri, "path": source_path, "line": number,
                           "column": len(raw) - len(raw.lstrip()) + 1}
            }
            nodes.append(current_module)
            if meta:
                edges.append({"source": uri, "target": meta.strip(), "kind": "meta-theory"})
            continue
        if line == SEPARATOR or current_module is None:
            continue
        include = include_re.match(line.rstrip(SEPARATOR))
        if include:
            target = include.group(1).strip()
            current_module["references"].append(target)
            edges.append({"source": current_module["id"], "target": target, "kind": "include"})
            continue
        declaration = constant_re.match(line.rstrip(SEPARATOR))
        if declaration:
            name, body = declaration.groups()
            uri = f"{current_module['uri']}?{name}"
            nodes.append({
                "id": uri, "uri": uri, "name": name, "kind": "constant",
                "type_surface": body.strip(),
                "description": "MMT constant; type surface retained without interpretation.",
                "references": [],
                "source": {"uri": source_uri, "path": source_path, "line": number,
                           "column": len(raw) - len(raw.lstrip()) + 1}
            })
            edges.append({"source": current_module["id"], "target": uri, "kind": "declares"})

    return {
        "format": "mmt-source-ir/v1",
        "source": {
            "uri": source_uri, "path": source_path, "sha256": source_hash,
            "input_kind": "mmt-source", "extractor": "conservative-line-extractor"
        },
        "scope": "surface declarations only; no MMT parsing, checking, elaboration, or semantic inference",
        "nodes": nodes, "edges": edges
    }


def manifest_source(source_id):
    manifest = json.loads(MANIFEST.read_text())
    item = next((source for source in manifest["sources"] if source["id"] == source_id), None)
    if item is None:
        raise ValueError(f"unknown upstream source: {source_id}")
    revision = item.get("revision")
    if not revision or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError(f"{source_id} has no immutable 40-character commit pin")
    if not item.get("sha256") and not item.get("git_blob_sha"):
        raise ValueError(f"{source_id} has no expected sha256 or git_blob_sha")
    return item


def source_download_url(item):
    repository = item["repository"].removesuffix(".git")
    parsed = urllib.parse.urlparse(repository)
    revision = item["revision"]
    path = urllib.parse.quote(item["path"], safe="/$.-_")
    if parsed.netloc == "github.com":
        owner_repo = parsed.path.strip("/")
        return f"https://raw.githubusercontent.com/{owner_repo}/{revision}/{path}"
    return f"{repository}/-/raw/{revision}/{path}"


def fetch(source_id, output):
    item = manifest_source(source_id)
    url = source_download_url(item)
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    if item.get("sha256"):
        actual = bytes_sha256(data)
        if actual != item["sha256"]:
            raise ValueError(f"download sha256 mismatch: expected {item['sha256']}, got {actual}")
    if item.get("git_blob_sha"):
        actual_blob = git_blob_sha(data)
        if actual_blob != item["git_blob_sha"]:
            raise ValueError(f"download git blob mismatch: expected {item['git_blob_sha']}, got {actual_blob}")
    Path(output).write_bytes(data)
    print(f"fetched {item['path']} at {item['revision']}")


def write_ir(ir, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ir, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {path}: {len(ir['nodes'])} nodes, {len(ir['edges'])} edges")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    p_fetch = commands.add_parser("fetch", help="download an immutable, integrity-checked upstream file")
    p_fetch.add_argument("source_id")
    p_fetch.add_argument("--output", required=True)

    p_extract = commands.add_parser("extract", help="fallback: extract conservative IR from local .mmt source")
    p_extract.add_argument("source")
    p_extract.add_argument("--uri", required=True)
    p_extract.add_argument("--source-path")
    p_extract.add_argument("--output", default=str(IR_PATH))

    p_omdoc = commands.add_parser("omdoc", help="preferred: extract structural IR from compiled OMDoc XML")
    p_omdoc.add_argument("source")
    p_omdoc.add_argument("--uri", required=True)
    p_omdoc.add_argument("--source-path")
    p_omdoc.add_argument("--output", default=str(IR_PATH))

    p_archive = commands.add_parser("archivegraph", help="import MMT :jgraph/json archivegraph output")
    p_archive.add_argument("source")
    p_archive.add_argument("--uri", required=True)
    p_archive.add_argument("--source-path")
    p_archive.add_argument("--output", default=str(IR_PATH))

    p_merge = commands.add_parser("merge", help="merge multiple normalized IR files by stable URI")
    p_merge.add_argument("sources", nargs="+")
    p_merge.add_argument("--uri", default="merged://mmt-graph")
    p_merge.add_argument("--output", default=str(IR_PATH))

    args = parser.parse_args()
    try:
        if args.command == "fetch":
            fetch(args.source_id, args.output)
        elif args.command == "merge":
            irs = [json.loads(Path(source).read_text(encoding="utf-8")) for source in args.sources]
            write_ir(merge_irs(irs, args.uri), args.output)
        else:
            path = Path(args.source)
            text = path.read_text(encoding="utf-8")
            source_path = args.source_path or path.as_posix()
            digest = source_sha256(text)
            if args.command == "omdoc":
                ir = extract_omdoc(text, args.uri, source_path, digest)
            elif args.command == "archivegraph":
                ir = extract_archivegraph(text, args.uri, source_path, digest)
            else:
                ir = extract(text, args.uri, source_path, digest)
            write_ir(ir, args.output)
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
