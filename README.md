# FOL Operational Metamodel

A small importer and graph projection for first-order logic formalizations in MMT. Upstream MMT source is the formal authority; `generated/mmt-ir.json` is a derived source projection. The former hand-authored `spec/fol.json` is retained only as a legacy comparison fixture.

## Run

Requirements: Python 3.10+ and a modern browser. The visualizer uses D3 v7 from its public CDN.

```sh
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```

Then open <http://localhost:8000/visualizer/>. Serve the repository root so the app can fetch `generated/mmt-ir.json`; opening the HTML directly does not allow that fetch. To regenerate the checked-in demonstration IR, run `python3 scripts/import_mmt.py extract tests/fixtures/sfol-mini.mmt --uri https://example.org/fixture.mmt --output generated/mmt-ir.json`.

## Layout

- `upstream/sources.json` — authoritative repository URLs, immutable-pin state, and fixture checksum.
- `upstream/README.md` — provenance, inspected sources, and access limitations.
- `scripts/import_mmt.py` — hash-checked fetch and conservative source extractor.
- `generated/mmt-ir.json` — generated declaration graph consumed by the visualizer.
- `tests/fixtures/sfol-mini.mmt` — local reduced MMT-shaped fixture; not claimed to be a verbatim upstream copy.
- `spec/fol.json` — legacy comparison fixture only; not formal authority.
- `schema/fol.tql` — legacy comparison projection, not derived from MMT.
- `examples/abc.json` — legacy finite-structure evaluation example, not upstream formal content.
- `visualizer/` — static D3 graph loaded from generated MMT IR at runtime.
- `tests/` — importer checks plus regression checks for the legacy evaluator and projections.
- `references/` — concise concept mapping and bibliography.

The extractor recognizes only simple line-oriented namespace, theory/view, include, and constant declarations using visible MMT separators. It preserves declaration surface text, URIs, paths, and line numbers. It is not an MMT parser: it does not parse arbitrary object syntax, type-check, elaborate, resolve imports, or establish semantics. See `upstream/README.md` for the verified source boundary and the documented MMT/OMDoc path.
