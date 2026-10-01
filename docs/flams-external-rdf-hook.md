# FLAMS external-archive RDF integration audit

Audited against FLAMS commit `b4f5a758ba66b716b7ac22ed5a23a94db3a1f4c5`.

## Finding

FLAMS has a genuine extension mechanism for non-native archives:

- `ArchiveKind` registers archive implementations;
- a manifest can select one with `kind: ...`;
- `ExternalArchive` abstracts module/document loading and can optionally expose local/buildable output.

However, the RDF subsystem does **not** currently use that extension point.

`RDFStore::load_archives` explicitly keeps only `Archive::Local` when discovering relational data and ignores `Archive::Ext`. For local archives it walks the native FLAMS `out/` tree, finds `index.ttl`, and derives the named graph / `DocumentUri` from that path.

Therefore an MMT `ExternalArchive` cannot currently contribute its ULO graphs to the global SPARQL store, even though current MMT and FLAMS already share ULO.

## Why fake `out/` paths are the wrong workaround

FLAMS' `get_iri` derives semantic document identity from the physical output path. Reshaping MMT relational files into a guessed FLAMS directory structure would therefore assert document identities rather than merely adapt serialization.

The MMT→FLAMS staging bridge in this repository intentionally does not do that.

## Smallest upstream-quality extension

The natural FLAMS change is to let `ExternalArchive` optionally provide relational named graphs directly, with a default empty implementation. Conceptually:

```rust
trait ExternalArchive {
    // existing methods ...

    #[cfg(feature = "rdf")]
    fn relational_graphs(
        &self,
    ) -> Iterator<Item = (NamedNode, Iterator<Item = Triple>)> {
        empty()
    }
}
```

Then `RDFStore::load_archives` would:

1. retain its existing `index.ttl` path for `Archive::Local`;
2. ask each `Archive::Ext` for authoritative named graphs;
3. insert those triples with the graph names supplied by the external archive.

This preserves the key boundary: **the external archive owns its URI/document identity; the RDF store owns storage/querying**.

An MMT archive kind could then parse or receive MMT's already-ULO RDF and supply each document graph under its actual MMT document IRI, without filename-derived semantic guesses.

## Prototype status

A two-file local prototype was prepared against the audited FLAMS commit:

- add a default-empty `ExternalArchive::relational_graphs` hook;
- consume it in `RDFStore::load_archives` before the existing local-archive loader.

The prototype has now been **validated in a containerized Rust environment without installing Rust on Brian's machine**:

- `cargo check -p flams-math-archives` passes;
- with the `rdf` feature enabled, a targeted unit test creates a fake `ExternalArchive` supplying one authoritative named RDF graph;
- `RDFStore::load_archives` loads the triple and preserves the supplied graph name;
- result: **1 test passed, 0 failed**.

The exact tested patch is checked in at `upstream/patches/flams-external-rdf.patch`.

An attempt to create an upstream FLAMS GitHub issue through the connected GitHub integration was rejected with HTTP 403 (`Resource not accessible by integration`), so no upstream issue or PR is claimed to have been created.

## Prior-art check

No existing FLAMS implementation or issue was found for:

- RDF supplied by `ExternalArchive`;
- MMT archive integration;
- RDF4J Binary RDF loading.

Current FLAMS does already have a generic RDF source/build target for Turtle files, but that still uses the local archive/output machinery and does not solve external archive graph identity.

## Real MMT graph validation

The hook was also tested with the actual current LATIN2 FOL relational graph.

MMT's `fol.brf` contains **423 statements** and already carries one authoritative RDF context on every statement:

`latin:/source/logic/fol_like/fol.mmt`

That BRF graph was losslessly serialized to N-Quads with the context intact, parsed by Oxigraph, supplied through a test `ExternalArchive`, and loaded by `RDFStore::load_archives`.

Result:

- source statements: **423**;
- loaded statements: **423**;
- graph URI preserved: **yes**;
- targeted RDF-enabled FLAMS test: **1 passed, 0 failed**.

Therefore an MMT integration does not need to infer graph identity from filenames or FLAMS output paths. The identity is already present in MMT's RDF.

## Recommended next step

Propose the validated generic hook upstream independently of MMT. After that, implement an MMT-specific `ArchiveKind` that reads MMT's already-ULO relational graphs and returns their embedded graph contexts.

The connected GitHub integration cannot create issues in the FLAMS repository (HTTP 403), so the tested patch and issue rationale are retained here for manual/upstream submission.
