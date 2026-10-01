# MMT → FLAMS RDF bridge

Current MMT and FLAMS already use the same Upper Library Ontology (ULO). The remaining compatibility boundary is RDF serialization plus the FLAMS external-archive ingestion hook:

- MMT v26+ writes RDF4J Binary RDF (`.brf`) under `relational/`.
- FLAMS stores/query RDF in Oxigraph and natively loads Turtle from local FLAMS archives.
- A validated FLAMS prototype lets an `ExternalArchive` contribute authoritative named RDF graphs directly.

`scripts/mmt_brf_to_flams_rdf.py` is deliberately **not an ontology converter**. It uses the official MMT jar's RDF4J parser to read each BRF file and serializes the exact RDF statements as **N-Quads**.

## MMT already stores graph identity

A key current-stack finding is that MMT's BRF files already carry the authoritative RDF context. For current LATIN2:

```
fol.brf
  statements: 423
  named graph: latin:/source/logic/fol_like/fol.mmt
```

All 423 statements in that file carry that same graph URI. Therefore no filename-to-`DocumentUri` reconstruction is needed for an external-archive integration.

The bridge preserves that context:

```
<subject> <predicate> <object> <latin:/source/logic/fol_like/fol.mmt> .
```

The staging layout is simply:

```
<output>/<MMT relational path>.nq
```

It does not impersonate FLAMS' native `out/**/index.ttl` layout.

## Verified current-stack sample

With MMT v27 and current LATIN2, the 13 `logic/fol_like` BRF graphs contain 2,877 statements total. Earlier triple-only serialization verified the statement count; the context-preserving bridge now emits N-Quads.

For `fol.brf`, the graph contains 423 statements including:

- `UniversalQuantification rdf:type ulo:theory`
- `UniversalQuantification?uforall rdf:type ulo:function`
- `FOL ulo:has-meta-theory LF`
- ULO include/specifies/uses relations.

The real 423-statement FOL graph was then loaded through the validated FLAMS `ExternalArchive::relational_graphs` prototype. The RDF-enabled FLAMS test passed and preserved the graph URI `latin:/source/logic/fol_like/fol.mmt`.

## Requirements

The bridge needs:

- Python 3;
- a JDK (`java` and `javac`);
- an official MMT jar containing the RDF4J binary parser.

No Python RDF package and no project-authored ontology mapping are used.
