# Upstream provenance

`sources.json` records authoritative project URLs and the limits of what this checkout could inspect. It intentionally does not pretend that a branch name is an immutable revision. The runner requires a 40-character Git commit and expected SHA-256 before downloading any upstream source.

The MMT examples project publishes `source/tutorial/1-sfol.mmt`; the official MMT tutorial identifies it as the full FOL definition. Its GitLab file page was reachable through the web index, but its body and current commit were not. Direct Git access failed because this environment could not resolve `gl.mathhub.info`. No upstream source has been vendored.

The LATIN2 README says human-edited MMT files live under `source/`, and official LATIN materials identify the modular logic families PL, FOL, SFOL, and DFOL. A LATIN2-oriented MMT presentation names modules `TypedLogic`, `SFOLEQ`, and `RelativizedUniversalQuantification`; these are module names, not verified current file paths. The exact current `.mmt` paths for these modules remain unverified in this checkout. Do not treat the names as an exhaustive inventory until the repository can be cloned at a pinned revision.

The test input `tests/fixtures/sfol-mini.mmt` is a small local fixture using the documented MMT theory/declaration surface shape. It is pinned by its SHA-256 in `sources.json`, but is explicitly not represented as a verbatim upstream file. Once GitLab access is available, replace or supplement it with a byte-exact excerpt from `1-sfol.mmt`, pinning both repository commit and file hash.

## MMT-native extraction path

When an MMT installation and the archive are available, build the selected source through MMT rather than treating the Python extractor as a parser:

```text
build MMT/examples mmt-omdoc source/tutorial/1-sfol.mmt
```

The MMT tutorial documents `mmt-omdoc` as the source-to-OMDoc build target; it writes OMDoc content and relational indexes into the archive's generated `narration/`, `content/`, and `relational/` trees. The local IR does not yet consume OMDoc XML or MMT's relational store. A future native adapter should read the built OMDoc structural declarations (documents, theories/views, constants) or query the relational store, preserving MMT paths rather than reparsing surface text.

For a graph directly from a running MMT server, the MMT project documents this archive graph endpoint after loading/building an archive and starting the server:

```text
http://localhost:8081/:jgraph/json?key=archivegraph&uri=MMT/LATIN2
```

This endpoint is an alternate MMT-generated graph view, not currently an input format supported by `scripts/import_mmt.py`. MMT API docs describe structural elements as URI-bearing and distinguish modules (theories/views) from declarations (constants); the local IR's kinds follow that distinction. Sources: [MMT tutorial](https://uniformal.github.io/doc/tutorials/prototyping/), [MMT API overview](https://uniformal.github.io/apidoc/info/kwarc/mmt/api/ontology/index.html), [MMT archivegraph instructions](https://github.com/UniFormal/MMT/issues/525), [LATIN2 repository README](https://gl.mathhub.info/MMT/LATIN2/-/blob/devel/README.md).

## Current limitations

- Upstream commit revisions are unresolved and upstream fetch is intentionally blocked until both a full commit SHA and expected source SHA-256 are entered in `sources.json`.
- Current LATIN2 file paths for FOL/SFOL modules have not been verified; only module names and project-level scope are documented above.
- The extractor is a conservative line-oriented subset, not a complete MMT parser. Nested/inline declarations, multiline expressions, comments inside objects, aliases, assignments, structures, views beyond the header, and extension-defined syntax are not reliably represented.
- No term-level semantics, proofs, truth conditions, theorem validity, or type-checking are inferred by the IR.
- OMDoc XML and MMT relational JSON ingestion remain unimplemented; use `mmt-omdoc` and the archivegraph endpoint for native MMT inspection today.
