# FOL Operational Metamodel

A generated graph projection over existing standards and MMT formalizations of first-order logic. The project does **not** treat its own hand-written FOL schema as the authority.

The conceptual/metamodel layer is also standards-derived. OMG ODM's normative Common Logic XMI supplies the abstract-syntax metamodel; Common Logic supplies the model-theoretic semantics; OMG DOL/institution theory supplies the logic/interoperability layer; and MMT/LATIN2 supplies the mechanized formal instances. See `docs/standards-metamodel.md`.

The preferred pipeline is:

```text
MMT source
  -> MMT mmt-omdoc build/type-check
  -> compiled OMDoc
  -> scripts/import_mmt.py omdoc
  -> normalized graph IR
  -> D3 explorer
```

MMT's compiled OMDoc is the primary interchange format because MMT has already parsed and elaborated the source. The older line-oriented `.mmt` extractor remains only as a conservative fallback.

## Run

Requirements: Python 3.10+ and a modern browser. No Python packages are required.

```sh
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```

Then open <http://localhost:8000/visualizer/>.

### Live FLAMS focus mode

The same visualizer can now query a FLAMS SPARQL endpoint directly instead of loading the generated IR. Supply a formal focus URI and endpoint:

`visualizer/?focus=latin:/?UniversalQuantification%23&endpoint=http://localhost:3000/api/backend/query`

The browser constructs a one-hop ULO SPARQL projection around the focus, keeps the authoritative RDF named-graph provenance, and lets the same semantic view switch between a force layout and a focus-layered layout. Leave the focus blank to use the generated-IR fallback.


## Import standards metamodels

```sh
python3 scripts/import_standards.py odm-cl \
  --output generated/odm-cl-metamodel-ir.json

python3 scripts/import_standards.py dol --package oms \
  --output generated/dol-oms-metamodel-ir.json
```

These commands import normative OMG XMI directly. They do not infer additional FOL categories from names.

## Import the real pinned MMT FOL artifact

The upstream manifest pins a compiled FOL OMDoc artifact from the MMT repository by both immutable Git commit and Git blob SHA.

```sh
mkdir -p upstream/cache
python3 scripts/import_mmt.py fetch mmt-compiled-fol-omdoc \
  --output upstream/cache/FOL.omdoc

python3 scripts/import_mmt.py omdoc upstream/cache/FOL.omdoc \
  --uri "https://github.com/UniFormal/MMT/blob/fca5d7e12db5b4e9d6329590f9d25380017981d8/src/test/testarchive/content/http..mydomain.org/testarchive/mmt-example/%24F%24O%24L.omdoc" \
  --output generated/pinned-fol-ir.json
```

Reload the visualizer after regeneration. The graph will contain the imported FOL theory, its constants, explicit OpenMath symbol dependencies, its LF meta-theory, and any structures/imports present in the OMDoc.

The visualizer defaults to the checked-in `generated/pinned-fol-ir.json`, which is generated from that exact pinned upstream artifact. It currently contains 16 imported nodes and 58 edges. Other generated datasets can be opened with the `data` query parameter, for example `/visualizer/?data=../generated/mmt-ir.json`.

## Add the LATIN2 archive/theory layer

MMT's `:jgraph/json` endpoint emits the archive/theory graph as JSON with `nodes` and `edges`. The importer preserves MMT's explicit edge styles such as `meta`, `include`, `structure`, and `view`.

After building/loading LATIN2 in MMT and starting its server:

```sh
curl 'http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2' \
  -o upstream/cache/latin2-archivegraph.json

python3 scripts/import_mmt.py archivegraph upstream/cache/latin2-archivegraph.json \
  --uri 'http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2' \
  --output generated/latin2-archive-ir.json
```

Then import one or more compiled OMDoc files and merge by stable MMT URI:

```sh
python3 scripts/import_mmt.py omdoc upstream/cache/FOL.omdoc \
  --uri 'mmt://compiled/FOL.omdoc' \
  --output generated/fol-omdoc-ir.json

python3 scripts/import_mmt.py merge \
  generated/latin2-archive-ir.json generated/fol-omdoc-ir.json \
  --output generated/mmt-ir.json
```

The archive graph supplies the large-scale theory/morphism topology; OMDoc supplies declaration-level detail. The merge does not invent additional semantic relations.

## Ingest a complete built LATIN2 archive

MMT's `mmt-omdoc` target writes one compiled OMDoc file per module into the archive's `content/` directory, with relational indexes alongside it. For LATIN2, prefer importing that whole generated directory instead of maintaining a manual list of logic files.

```sh
python3 scripts/import_mmt.py omdoc-dir /path/to/LATIN2/content \
  --uri 'mmt://MMT/LATIN2/content' \
  --output generated/latin2-content-ir.json
```

If an MMT server is running, save its archivegraph and assemble both layers in one command:

```sh
curl 'http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2' \
  -o upstream/cache/latin2-archivegraph.json

python3 scripts/import_mmt.py assemble \
  --archivegraph upstream/cache/latin2-archivegraph.json \
  --content /path/to/LATIN2/content \
  --archive-uri 'http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2' \
  --content-uri 'mmt://MMT/LATIN2/content' \
  --output generated/mmt-ir.json
```

This is the preferred large-scale workflow: MMT supplies the theory/morphism graph and all compiled module content; this repository only normalizes and joins those existing structures by MMT URI.

A small evidence-backed source inventory remains in `upstream/latin2-fol-inventory.json` for orientation, but it is not used as the formal authority.

## Add MMT's relational ontology layer

MMT also builds a `relational/` dimension. Its ABox XML records unary classifications such as `theory`, `view`, `structure`, `constant`, `rule`, and `judgementconstructor`, plus binary relations such as `has meta-theory`, `includes`, `has domain`, `has codomain`, `contains declaration of`, and `refers to`.

Import one relational file:

```sh
python3 scripts/import_mmt.py relational /path/to/file.xml \
  --uri 'mmt://MMT/LATIN2/relational/file.xml' \
  --output generated/latin2-relational-ir.json
```

Or recursively import an archive's whole relational directory:

```sh
python3 scripts/import_mmt.py relational-dir /path/to/LATIN2/relational \
  --uri 'mmt://MMT/LATIN2/relational' \
  --output generated/latin2-relational-ir.json
```

For the richest graph, include all three generated layers in one assembly:

```sh
python3 scripts/import_mmt.py assemble \
  --archivegraph upstream/cache/latin2-archivegraph.json \
  --content /path/to/LATIN2/content \
  --relational /path/to/LATIN2/relational \
  --archive-uri 'http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2' \
  --content-uri 'mmt://MMT/LATIN2/content' \
  --relational-uri 'mmt://MMT/LATIN2/relational' \
  --output generated/mmt-ir.json
```

This preserves MMT's own ontology predicates on nodes and edges instead of inferring categories from names.

## Reproduced historical LATIN2 atlas

The pinned 2022 LATIN2 stack has now been rebuilt end-to-end. The assembled graph contains 6,482 nodes and 46,782 edges from 798 compiled OMDoc modules and 891 relational files. Exact revisions, hashes, build notes, and output counts are recorded in `upstream/latin2-reproduction.json`.

Historical MMT compatibility is supported directly: 2022 archives use compressed `.omdoc.xz` content and line-based `.rel` relational indexes, while newer MMT archives use the newer formats already supported by this importer. The reproducible 39.7 MB full IR is not committed by default; its SHA-256 is pinned in the reproduction manifest.

## Fallback source extraction

When compiled OMDoc is unavailable:

```sh
python3 scripts/import_mmt.py extract some-file.mmt \
  --uri https://example.org/source.mmt \
  --output generated/mmt-ir.json
```

That mode only recognizes a small source-level subset and does not replace MMT parsing/type-checking.

## Layout

- `upstream/sources.json` — immutable upstream provenance where verified.
- `upstream/README.md` — provenance, evidence, and unresolved source boundaries.
- `upstream/latin2-fol-inventory.json` — partial evidence-backed orientation to confirmed FOL files/theories at the pinned LATIN2 revision.
- `scripts/import_mmt.py` — verified fetcher plus archivegraph, relational-ABox, OMDoc, whole-archive, merge, and fallback-source importers.
- `generated/pinned-fol-ir.json` — reproducible snapshot generated from the pinned real MMT FOL OMDoc; default visualizer dataset.
- `generated/mmt-ir.json` — workspace output for assembled or experimental graph IR.
- `tests/fixtures/fol-compiled.omdoc` — compact representative compiled-OMDoc fixture.
- `tests/fixtures/sfol-mini.mmt` — reduced fallback-source fixture.
- `spec/fol.json` — legacy comparison fixture only; not formal authority.
- `schema/fol.tql` — legacy TypeDB-like comparison projection.
- `examples/abc.json` — legacy finite-structure teaching example.
- `visualizer/` — graph explorer generated from IR.
- `tests/` — importer and regression tests.

## Scope

The OMDoc adapter extracts explicit structural facts: documents, theories/views, constants, imports/structures, meta-theory/view links, source references, type/definition XML, roles/aliases, and explicit OpenMath `OMS` symbol dependencies. The relational adapter separately preserves MMT's own unary and binary ontology predicates.

It intentionally does **not** infer that a constant is a quantifier, connective, axiom, proof rule, semantic clause, etc. Richer classifications come from MMT roles/relational indexes or a separately provenance-marked annotation layer, not from guessing based on names.
