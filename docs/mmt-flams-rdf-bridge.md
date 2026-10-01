# MMT → FLAMS RDF bridge

Current MMT and FLAMS already use the same Upper Library Ontology (ULO). The remaining incompatibility is serialization and archive layout:

- MMT v26+ writes one RDF4J Binary RDF (`.brf`) graph per built document under `relational/`.
- FLAMS loads standard RDF from per-document `index.ttl` files under its output tree.

`scripts/mmt_brf_to_flams_rdf.py` is deliberately **not an ontology converter**. It uses the official MMT jar's RDF4J parser to read each BRF graph and serializes the exact RDF statements as N-Triples syntax, which is valid Turtle.

The staging layout is:

```
<output>/<MMT relational document path without .brf>/index.ttl
```

This preserves graph boundaries and makes the output easy to inspect or feed to a standard RDF loader. It does **not** claim that the staging paths are native FLAMS `ArchiveUri/DocumentUri` paths; FLAMS derives named-graph identity from its own archive/output path conventions. That final path/identity mapping must come from a concrete FLAMS archive integration rather than a guessed filename transformation.

## Verified current-stack sample

With MMT v27 and current LATIN2, the 13 `logic/fol_like` BRF graphs contain 2,877 triples total. The bridge emitted 13 `index.ttl` files with exactly 2,877 statement lines. `fol.brf` contains 423 triples and the output retains, among others:

- `UniversalQuantification rdf:type ulo:theory`
- `UniversalQuantification?uforall rdf:type ulo:function`
- `FOL ulo:has-meta-theory LF`
- ULO include/specifies/uses relations.

## Requirements

The script needs:

- Python 3;
- a JDK (`java` and `javac`);
- an official MMT jar containing the RDF4J binary parser.

No Python RDF package and no project-authored ontology mapping are used.
