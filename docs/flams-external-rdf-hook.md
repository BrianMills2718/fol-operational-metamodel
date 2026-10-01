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

It has **not been claimed as validated** because Brian's Windows host does not have a Rust toolchain and the guarded WSL coding-agent invocation failed before compilation. The prototype was not pushed upstream.

## Prior-art check

No existing FLAMS implementation or issue was found for:

- RDF supplied by `ExternalArchive`;
- MMT archive integration;
- RDF4J Binary RDF loading.

Current FLAMS does already have a generic RDF source/build target for Turtle files, but that still uses the local archive/output machinery and does not solve external archive graph identity.

## Recommended next step

Validate the small FLAMS hook in a Rust-capable environment. If it compiles cleanly, propose it upstream independently of MMT: it is a general capability for any external archive that can supply semantic RDF.

Only after that should an MMT-specific `ArchiveKind` be implemented.
