#!/usr/bin/env python3
"""Materialize MMT v26+ ULO .brf graphs as FLAMS-loadable Turtle.

This adapter performs no ontology or semantic mapping. It delegates BRF parsing
to the official MMT jar (RDF4J) and writes the exact RDF statements as
N-Triples, which is a valid subset of Turtle. Each MMT relational document is
kept separate.

The output layout is intentionally explicit rather than pretending to be a
native FLAMS archive: <output>/<relative-document>/index.ttl. A later ingestion
step may either load these files directly or reshape document names according
to a concrete FLAMS ArchiveUri/DocumentUri mapping.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile

JAVA_SOURCE = r"""
import java.io.*;
import java.nio.charset.StandardCharsets;
import org.eclipse.rdf4j.rio.*;
import org.eclipse.rdf4j.rio.helpers.NTriplesUtil;

public class BrfToTurtle {
  public static void main(String[] a) throws Exception {
    var model = Rio.parse(new FileInputStream(a[0]), "", RDFFormat.BINARY);
    try (var w = new BufferedWriter(new OutputStreamWriter(
        new FileOutputStream(a[1]), StandardCharsets.UTF_8))) {
      for (var st : model) {
        w.write(NTriplesUtil.toNTriplesString(st.getSubject())); w.write(" ");
        w.write(NTriplesUtil.toNTriplesString(st.getPredicate())); w.write(" ");
        w.write(NTriplesUtil.toNTriplesString(st.getObject())); w.write(" .\n");
      }
    }
    System.out.println(model.size());
  }
}
"""


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compile_helper(java: str, javac: str, mmt_jar: pathlib.Path, work: pathlib.Path) -> None:
    src = work / "BrfToTurtle.java"
    src.write_text(JAVA_SOURCE, encoding="utf-8")
    subprocess.run([java, "-version"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        [javac, "-cp", str(mmt_jar), str(src)],
        check=True,
        cwd=work,
    )


def convert_one(java: str, mmt_jar: pathlib.Path, classes: pathlib.Path,
                source: pathlib.Path, target: pathlib.Path) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    cp = f"{mmt_jar}{';' if __import__('os').name == 'nt' else ':'}{classes}"
    proc = subprocess.run(
        [java, "-cp", cp, "BrfToTurtle", str(source), str(target)],
        check=True, text=True, capture_output=True,
    )
    return int(proc.stdout.strip().splitlines()[-1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmt-jar", type=pathlib.Path, required=True)
    ap.add_argument("--relational", type=pathlib.Path, required=True,
                    help="MMT archive relational/ directory")
    ap.add_argument("--output", type=pathlib.Path, required=True)
    ap.add_argument("--java", default="java")\n    ap.add_argument("--javac", default="javac")
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
            target = args.output / rel / "index.ttl"
            triples = convert_one(args.java, args.mmt_jar, work, source, target)
            rows.append({
                "source": rel.as_posix() + ".brf",
                "target": (rel / "index.ttl").as_posix(),
                "triples": triples,
                "source_sha256": sha256(source),
                "target_sha256": sha256(target),
            })

    manifest = {
        "format": "mmt-flams-rdf-bridge/v1",
        "semantic_mapping": "none",
        "input_format": "RDF4J Binary RDF",
        "output_format": "N-Triples syntax (valid Turtle)",
        "graphs": rows,
        "total_graphs": len(rows),
        "total_triples": sum(r["triples"] for r in rows),
    }
    text = json.dumps(manifest, indent=2) + "\n"
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
