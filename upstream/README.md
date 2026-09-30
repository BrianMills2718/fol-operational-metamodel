# Upstream provenance

This repository is a projection layer over existing MMT formalizations. It does not attempt to redefine first-order logic independently.

## Verified upstream anchors

### Compiled MMT FOL OMDoc

The strongest current anchor is an actual compiled FOL OMDoc artifact already committed in the MMT repository:

- repository: `https://github.com/UniFormal/MMT.git`
- commit: `fca5d7e12db5b4e9d6329590f9d25380017981d8`
- path: `src/test/testarchive/content/http..mydomain.org/testarchive/mmt-example/$F$O$L.omdoc`
- Git blob SHA: `76ccd4bc3968272d2e16d4fc51d8950c6b28fbe7`

That artifact was inspected directly. It contains a theory `FOL` with meta-theory `http://cds.omdoc.org/urtheories?LF` and constants including `prop`, `true`, `false`, Boolean connectives, `sort`, `term`, equality, quantifiers, and `proof`.

This is the preferred regression target because MMT has already produced the OMDoc representation. The fetcher validates the downloaded bytes against the recorded Git blob SHA before accepting them.

### LATIN2

The public LATIN2 GitLab index exposes immutable revision:

`39dc7046f457ff02f695387a8ebd80366789a465`

LATIN2 is the larger modular logic atlas. Its README states that human-edited MMT sources are under `source/`. We have pinned the repository revision, but have not yet completed an inventory of the FOL/SFOL module file paths at that revision.

### MMT tutorial FOL source

The official MMT language-design tutorial identifies:

`MMT/examples/source/tutorial/1-sfol.mmt`

as the complete tutorial FOL definition. The path is verified, but an immutable commit for the examples repository has not yet been established in this project, so that source remains intentionally unpinned.

## Why OMDoc is preferred

MMT documents the `mmt-omdoc` build target as the path from MMT source to its internal OMDoc XML representation. The build produces content, narration, and relational indexes. That means OMDoc is downstream of MMT parsing/type-checking and is a better graph input than reimplementing the MMT parser.

Typical MMT workflow:

```text
build MMT/examples mmt-omdoc source/tutorial/1-sfol.mmt
```

The importer in this repository reads explicit OMDoc structure only. It currently recognizes:

- `theory` and `view` modules;
- module meta-theory/domain/codomain attributes;
- `constant` declarations;
- `import` elements as includes or named structures;
- `derived` declarations conservatively;
- source-reference metadata;
- type and definition XML;
- explicit OpenMath `OMS` references inside constants.

It does not infer logical semantics from names or OpenMath term shapes.

## MMT-native graph alternatives

MMT also documents an archive graph JSON endpoint after an archive is built and served:

```text
http://localhost:8081/:jgraph/json?key=archivegraph&uri=MMT/LATIN2
```

That graph is useful for archive/theory-level structure. It is complementary to the declaration-level OMDoc projection here. The repository now ingests this endpoint with `scripts/import_mmt.py archivegraph` and merges it with OMDoc IR using `scripts/import_mmt.py merge`. MMT's own graph styles (`meta`, `include`, `structure`, `view`) are preserved verbatim rather than reclassified.

MMT's relational indexes are another promising input because they already classify declaration and dependency relations. They should be preferred over name-based heuristics when we add richer classifications.

## Current limitations

- LATIN2 is pinned, but its exact FOL/SFOL source-module inventory is not yet captured here.
- The MMT examples tutorial FOL source path is known, but its repository commit is still unresolved.
- The OMDoc adapter is structural, not a complete semantic interpretation of OpenMath.
- MMT relational-store ingestion and `:jgraph/json` ingestion are not implemented yet.
- The checked-in OMDoc fixture is compact and representative; the real pinned FOL OMDoc should be fetched for full exploration.

## References

- MMT FOL tutorial: https://uniformal.github.io/doc/tutorials/prototyping/
- MMT build targets: https://uniformal.github.io/doc/archives/building
- MMT declaration format: https://uniformal.github.io/doc/language/declarations
- MMT archive graph instructions: https://github.com/UniFormal/MMT/issues/525
- LATIN2 repository: https://gl.mathhub.info/MMT/LATIN2
