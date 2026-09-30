# FOL Operational Metamodel

A generated graph projection over existing MMT formalizations of first-order logic. The project does **not** treat its own hand-written FOL schema as the authority.

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

## Import the real pinned MMT FOL artifact

The upstream manifest pins a compiled FOL OMDoc artifact from the MMT repository by both immutable Git commit and Git blob SHA.

```sh
mkdir -p upstream/cache
python3 scripts/import_mmt.py fetch mmt-compiled-fol-omdoc \
  --output upstream/cache/FOL.omdoc

python3 scripts/import_mmt.py omdoc upstream/cache/FOL.omdoc \
  --uri "https://github.com/UniFormal/MMT/blob/fca5d7e12db5b4e9d6329590f9d25380017981d8/src/test/testarchive/content/http..mydomain.org/testarchive/mmt-example/%24F%24O%24L.omdoc" \
  --output generated/mmt-ir.json
```

Reload the visualizer after regeneration. The graph will contain the imported FOL theory, its constants, explicit OpenMath symbol dependencies, its LF meta-theory, and any structures/imports present in the OMDoc.

The checked-in `generated/mmt-ir.json` is deliberately generated from a small fixture so tests and the initial UI stay compact. It is not the formal authority.

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
- `scripts/import_mmt.py` — verified fetcher, OMDoc structural importer, and fallback source extractor.
- `generated/mmt-ir.json` — derived graph IR consumed by the visualizer.
- `tests/fixtures/fol-compiled.omdoc` — compact representative compiled-OMDoc fixture.
- `tests/fixtures/sfol-mini.mmt` — reduced fallback-source fixture.
- `spec/fol.json` — legacy comparison fixture only; not formal authority.
- `schema/fol.tql` — legacy TypeDB-like comparison projection.
- `examples/abc.json` — legacy finite-structure teaching example.
- `visualizer/` — graph explorer generated from IR.
- `tests/` — importer and regression tests.

## Scope

The OMDoc adapter extracts explicit structural facts: documents, theories/views, constants, imports/structures, meta-theory/view links, source references, type/definition XML, roles/aliases, and explicit OpenMath `OMS` symbol dependencies.

It intentionally does **not** infer that a constant is a quantifier, connective, axiom, proof rule, semantic clause, etc. Those classifications should come from MMT roles/relational indexes or a separately provenance-marked annotation layer, not from guessing based on names.
