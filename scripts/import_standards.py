#!/usr/bin/env python3
"""Import OMG UML/XMI metamodel packages into normalized graph IR."""

import argparse
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

XMI_NS = "http://www.omg.org/spec/XMI/20110701"
XMI_TYPE = f"{{{XMI_NS}}}type"
XMI_ID = f"{{{XMI_NS}}}id"
XMI_UUID = f"{{{XMI_NS}}}uuid"

ODM_XMI_URL = "https://www.omg.org/spec/ODM/20131101/ODM-metamodels.xmi"
DOL_XMI_URL = "https://www.omg.org/spec/DOL/20151109/DOL-metamodel.xmi"


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def xmi_attr(element, name):
    for key, value in element.attrib.items():
        if key == name or key.endswith("}" + name):
            return value
    return None


def xmi_type(element):
    return xmi_attr(element, "type") or ""


def stable_id(source_uri, xmi_id):
    return f"{source_uri}#{xmi_id}"


def multiplicity(prop):
    lower = None
    upper = None
    for child in prop:
        local = child.tag.rsplit("}", 1)[-1]
        if local == "lowerValue":
            lower = child.attrib.get("value", "0")
        elif local == "upperValue":
            upper = child.attrib.get("value", "1")
    return {"lower": lower, "upper": upper}


def find_package(root, package_name):
    matches = [
        e for e in root.iter()
        if xmi_type(e) == "uml:Package" and e.attrib.get("name") == package_name
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one UML package named {package_name!r}, found {len(matches)}")
    return matches[0]


def extract_package(xml_bytes, source_uri, package_name):
    root = ET.fromstring(xml_bytes)
    package = find_package(root, package_name)

    global_index = {
        xmi_attr(e, "id"): e
        for e in root.iter()
        if xmi_attr(e, "id")
    }

    package_id = xmi_attr(package, "id")
    package_node_id = stable_id(source_uri, package_id)
    nodes = [{
        "id": package_node_id,
        "uri": package_node_id,
        "name": package.attrib.get("name", package_name),
        "kind": "uml-package",
        "xmi_id": package_id,
        "xmi_uuid": package.attrib.get(XMI_UUID),
        "source": {"uri": source_uri},
    }]
    edges = []

    elements = [
        e for e in package
        if xmi_type(e) in {"uml:Class", "uml:Association"}
    ]

    for element in elements:
        xid = xmi_attr(element, "id")
        kind = "uml-class" if xmi_type(element) == "uml:Class" else "uml-association"
        node_id = stable_id(source_uri, xid)
        node = {
            "id": node_id,
            "uri": node_id,
            "name": element.attrib.get("name", xid),
            "kind": kind,
            "xmi_id": xid,
            "xmi_uuid": xmi_attr(element, "uuid"),
            "source": {"uri": source_uri, "package": package_name},
        }
        if element.attrib.get("isAbstract") == "true":
            node["abstract"] = True
        nodes.append(node)
        edges.append({"source": package_node_id, "target": node_id, "kind": "contains"})

        if kind == "uml-class":
            for child in element:
                local = child.tag.rsplit("}", 1)[-1]
                if local == "generalization" and child.attrib.get("general"):
                    target_xid = child.attrib["general"]
                    if target_xid in global_index:
                        edges.append({
                            "source": node_id,
                            "target": stable_id(source_uri, target_xid),
                            "kind": "generalizes-to",
                            "xmi_id": xmi_attr(child, "id"),
                        })

        properties = [
            child for child in element
            if xmi_type(child) == "uml:Property"
        ]
        for prop in properties:
            pid = xmi_attr(prop, "id")
            prop_id = stable_id(source_uri, pid)
            pnode = {
                "id": prop_id,
                "uri": prop_id,
                "name": prop.attrib.get("name", pid),
                "kind": "uml-property",
                "xmi_id": pid,
                "xmi_uuid": xmi_attr(prop, "uuid"),
                "source": {"uri": source_uri, "package": package_name},
                "multiplicity": multiplicity(prop),
            }
            if prop.attrib.get("isOrdered") == "true":
                pnode["ordered"] = True
            nodes.append(pnode)
            edges.append({"source": node_id, "target": prop_id, "kind": "owns-property"})
            target_xid = prop.attrib.get("type")
            if target_xid and target_xid in global_index:
                edges.append({
                    "source": prop_id,
                    "target": stable_id(source_uri, target_xid),
                    "kind": "typed-as",
                })

        if kind == "uml-association":
            for child in element:
                if child.tag.rsplit("}", 1)[-1] == "memberEnd" and xmi_attr(child, "idref"):
                    target_xid = xmi_attr(child, "idref")
                    if target_xid in global_index:
                        edges.append({
                            "source": node_id,
                            "target": stable_id(source_uri, target_xid),
                            "kind": "member-end",
                        })

    return {
        "format": "standards-ir/v1",
        "source": {
            "uri": source_uri,
            "sha256": sha256_bytes(xml_bytes),
            "input_kind": "omg-uml-xmi",
            "package": package_name,
        },
        "scope": "UML/XMI structure imported verbatim; no logical-semantic classifications inferred",
        "nodes": nodes,
        "edges": edges,
    }


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fol-operational-metamodel/1"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def write_ir(ir, output):
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ir, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    generic = sub.add_parser("xmi", help="import a UML package from OMG-style XMI")
    generic.add_argument("source")
    generic.add_argument("--uri", required=True)
    generic.add_argument("--package", required=True)
    generic.add_argument("--output", required=True)

    odm = sub.add_parser("odm-cl", help="import the normative ODM Common Logic metamodel")
    odm.add_argument("--source")
    odm.add_argument("--output", default="generated/odm-cl-metamodel-ir.json")

    dol = sub.add_parser("dol", help="import the normative DOL MOF metamodel package")
    dol.add_argument("--source")
    dol.add_argument("--package", required=True)
    dol.add_argument("--output", default="generated/dol-metamodel-ir.json")

    args = parser.parse_args()
    if args.command == "odm-cl":
        data = Path(args.source).read_bytes() if args.source else fetch(ODM_XMI_URL)
        ir = extract_package(data, ODM_XMI_URL, "CL")
    elif args.command == "dol":
        data = Path(args.source).read_bytes() if args.source else fetch(DOL_XMI_URL)
        ir = extract_package(data, DOL_XMI_URL, args.package)
    else:
        data = Path(args.source).read_bytes()
        ir = extract_package(data, args.uri, args.package)
    write_ir(ir, args.output)


if __name__ == "__main__":
    main()
