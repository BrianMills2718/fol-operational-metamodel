# FOL Operational Metamodel

A compact, executable metamodel for classical first-order logic (FOL). The canonical JSON specification in `spec/fol.json` defines its vocabulary and rules. Validation examples, the TypeDB-like projection, and the interactive graph are derived or checked against that file.

## Run

Requirements: Python 3.10+ for the standard-library validator and a modern browser. The visualizer uses D3 v7 from its public CDN.

```sh
python3 -m unittest discover -s tests -v
python3 -m http.server 8000
```

Then open <http://localhost:8000/visualizer/>. Serve the repository root so the app can fetch `spec/fol.json`; opening the HTML directly does not allow that fetch. No Python packages or build step are needed.

## Layout

- `spec/fol.json` — canonical, versioned JSON model and schema.
- `schema/fol.tql` — initial TypeDB-like entity/relation projection.
- `examples/abc.json` — signature, structure, assignments, and evaluated formulas for Alice, Bob, and Carol.
- `visualizer/` — static D3 graph generated from the canonical model at runtime.
- `tests/` — checks of vocabulary/schema consistency, formation, truth evaluation, satisfaction, and consequence.
- `references/` — concise concept mapping and bibliography.
- `DESIGN.md` — source-of-truth and extension rules.

The model is intentionally classical and many-sorted only through explicit sorts in a signature; the running example uses one sort. Its evaluator handles terms, atomic formulas, Boolean connectives, and quantifiers over finite structures. This is an executable teaching and design baseline, not a complete proof assistant or an implementation of every logical framework.
