#!/usr/bin/env python3
"""Materialize MMT v26+ ULO .brf graphs as standard RDF N-Quads.

This adapter performs no ontology or semantic mapping. It delegates RDF4J
Binary RDF parsing to the official MMT jar and serializes the exact statements
as N-Quads, preserving each statement's RDF context / named-graph identity.

That context matters for FLAMS integration: current MMT already stores the
authoritative document graph URI inside each .brf file, so no filename-to-URI
reconstruction is necessary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile

JAVA_SOURCE = r"""
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.TreeSet;
import org.eclipse.rdf4j.rio.*;
import org.eclipse.rdf4j.rio.helpers.NTriplesUtil;

public class BrfToNQuads {
  public static void main(String[] a) throws Exception {
    var model = Rio.parse(new FileInputStream(a[0]), "", RDFFormat.BINARY);
    var contexts = new TreeSet<String>();
    try (var w = new BufferedWriter(new OutputStreamWriter(
        new FileOutputStream(a[1]), StandardCharsets.UTF_8))) {
      for (var st : model) {
        w.write(NTriplesUtil.toNTriplesString(st.getSubject())); w.write(" ");
        w.write(NTriplesUtil.toNTriplesString(st.getPredicate())); w.write(" ");
        w.write(NTriplesUtil.toNTriplesString(st.getObject()));
        var ctx = st.getContext();
        if (ctx != null) {
          w.write(" ");
          w.write(NTriplesUtil.toNTriplesString(ctx));
          contexts.add(ctx.stringValue());
        } else {
          contexts.add("<default>");
        }
        w.write(" .\n");
      }
    }
    System.out.println("statements=" + model.size());
    for (var ctx : contexts) System.out.println("context=" + ctx);
  }
}
"""


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compile_helper(
    java: str, javac: str, mmt_jar: pathlib.Path, work: pathlib.Path
) -> None:
    src = work / "BrfToNQuads.java"
    src.write_text(JAVA_SOURCE, encoding="utf-8")
    subprocess.run([java, "-version"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        [javac, "-cp", str(mmt_jar), str(src)],
        check=True,
        cwd=work,
    )


def convert_one(
    java: str,
    mmt_jar: pathlib.Path,
    classes: pathlib.Path,
    source: pathlib.Path,
    target: pathlib.Path,
) -> tuple[int, list[str]]:
    target.parent.mkdir(parents=True, exist_ok=True)
    cp = f"{mmt_jar}{';' if os.name == 'nt' else ':'}{classes}"
    proc = subprocess.run(
        [java, "-cp", cp, "BrfToNQuads", str(source), str(target)],
        check=True,
        text=True,
        capture_output=True,
    )
    statements = None
    contexts: list[str] = []
    for line in proc.stdout.splitlines():
        if line.startswith("statements="):
            statements = int(line.split("=", 1)[1])
        elif line.startswith("context="):
            contexts.append(line.split("=", 1)[1])
    if statements is None:
        raise RuntimeError(f"helper did not report statement count for {source}")
    return statements, contexts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmt-jar", type=pathlib.Path, required=True)
    ap.add_argument(
        "--relational",
        type=pathlib.Path,
        required=True,
        help="MMT archive relational/ directory",
    )
    ap.add_argument("--output", type=pathlib.Path, required=True)
    ap.add_argument("--java", default="java")
    ap.add_argument("--javac", default="javac")
    ap.add_argument("--manifest", type=pathlib.Path)
    args = ap.parse_args()

    brfs = sorted(args.relational.rglob("*.brf"))
    if not brfs:
        raise SystemExit(f"no .brf files under {args.relational}")

    rows = []
    with tempfile.TemporaryDirectory(prefix="mmt-flams-rdf-") as td:
        work = pathlib.Path(td)
        compile_helper(args.java, args.javac, args.mmt_jar, work)
        for source in brfs:
            rel = source.relative_to(args.relational).with_suffix("")
            target = (args.output / rel).with_suffix(".nq")
            statements, contexts = convert_one(
                args.java, args.mmt_jar, work, source, target
            )
            rows.append(
                {
                    "source": rel.as_posix() + ".brf",
                    "target": rel.as_posix() + ".nq",
                    "statements": statements,
                    "contexts": contexts,
                    "source_sha256": sha256(source),
                    "target_sha256": sha256(target),
                }
            )

    manifest = {
        "format": "mmt-flams-rdf-bridge/v2",
        "semantic_mapping": "none",
        "input_format": "RDF4J Binary RDF",
        "output_format": "N-Quads",
        "preserves_named_graph_context": True,
        "graphs": rows,
        "total_graphs": len(rows),
        "total_statements": sum(r["statements"] for r in rows),
    }
    text = json.dumps(manifest, indent=2) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
