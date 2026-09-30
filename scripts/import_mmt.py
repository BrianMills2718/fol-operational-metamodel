#!/usr/bin/env python3
"""Conservative source-level MMT declaration extractor (not an MMT parser)."""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "upstream/sources.json"
IR_PATH = ROOT / "generated/mmt-ir.json"
SEPARATOR = "❙"
END = "❚"


def source_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract(text, source_uri, source_path, source_hash):
    """Extract namespace, theories/views, includes and simple named declarations.

    Deliberately does not parse MMT objects, validate terms, resolve names, or
    infer semantics. A declaration body is retained as surface text.
    """
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
            current_module = {"id": uri, "uri": uri, "name": name, "kind": kind,
                              "meta_theory": meta.strip() if meta else None,
                              "description": f"MMT {kind} declaration imported from source.",
                              "references": [], "source": {"uri": source_uri, "path": source_path,
                              "line": number, "column": len(raw) - len(raw.lstrip()) + 1}}
            nodes.append(current_module)
            if meta:
                edges.append({"source": uri, "target": meta.strip(), "kind": "meta-theory"})
            continue
        if line in (SEPARATOR,):
            continue
        if current_module is None:
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
            nodes.append({"id": uri, "uri": uri, "name": name, "kind": "constant",
                          "type_surface": body.strip(), "description": "MMT constant; type surface retained without interpretation.",
                          "references": [], "source": {"uri": source_uri, "path": source_path,
                          "line": number, "column": len(raw) - len(raw.lstrip()) + 1}})
            edges.append({"source": current_module["id"], "target": uri, "kind": "declares"})

    return {"format": "mmt-source-ir/v1", "source": {"uri": source_uri, "path": source_path,
            "sha256": source_hash, "extractor": "conservative-line-extractor"},
            "scope": "surface declarations only; no MMT parsing, checking, elaboration, or semantic inference",
            "nodes": nodes, "edges": edges}


def pinned_source(source_id):
    manifest = json.loads(MANIFEST.read_text())
    item = next((source for source in manifest["sources"] if source["id"] == source_id), None)
    if item is None:
        raise ValueError(f"unknown upstream source: {source_id}")
    revision, digest = item.get("revision"), item.get("sha256")
    if not revision or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError(f"{source_id} has no immutable 40-character commit pin")
    if not digest or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError(f"{source_id} has no expected SHA-256 pin")
    return item, revision, digest


def fetch(source_id, output):
    item, revision, digest = pinned_source(source_id)
    url = item["repository"].removesuffix(".git") + f"/-/raw/{revision}/{item['path']}"
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != digest:
        raise ValueError(f"download digest mismatch: expected {digest}, got {actual}")
    Path(output).write_bytes(data)
    print(f"fetched {item['path']} at {revision}; sha256={actual}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p_fetch = commands.add_parser("fetch", help="download an immutable, hash-checked source")
    p_fetch.add_argument("source_id")
    p_fetch.add_argument("--output", required=True)
    p_extract = commands.add_parser("extract", help="extract conservative IR from a local .mmt file")
    p_extract.add_argument("source")
    p_extract.add_argument("--uri", required=True)
    p_extract.add_argument("--source-path")
    p_extract.add_argument("--output", default=str(IR_PATH))
    args = parser.parse_args()
    try:
        if args.command == "fetch":
            fetch(args.source_id, args.output)
        else:
            path = Path(args.source)
            text = path.read_text(encoding="utf-8")
            ir = extract(text, args.uri, args.source_path or path.as_posix(), source_sha256(text))
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(ir, indent=2, ensure_ascii=False) + "\n")
            print(f"wrote {output}: {len(ir['nodes'])} nodes, {len(ir['edges'])} edges")
    except (OSError, ValueError, urllib.error.URLError) as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
