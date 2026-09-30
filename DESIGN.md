# Design and contribution guide

## Authority and generated views

`spec/fol.json` is the only canonical metamodel. Its top-level `schema` defines the data shape; `model` lists entity types, relations, constructors, judgments, semantic rules, satisfaction, theories, and semantic consequence. Stable string IDs connect those declarations. The D3 app reads this file directly and constructs graph nodes and edges from those declarations and their `references` fields. Do not hand-edit a graph export or duplicate graph structure in JavaScript.

`schema/fol.tql` is an initial TypeDB-like projection for conceptual comparison. It is not a second authority: keep its entity and relation names aligned with the canonical model, and extend `tests/test_model.py` when either representation changes. The test suite checks the shared names and exercises the concrete semantics; it is intentionally dependency-free.

## Extending the model

1. Add or revise a declaration in `spec/fol.json`, with a stable ID, description, and references to related declarations.
2. If the change affects the TypeDB-like view, update `schema/fol.tql` in the same change.
3. Add a small running example or test that distinguishes the intended rule from an incorrect implementation.
4. Check that the graph remains useful: graph edges represent declared references, not inferred claims.
5. Run `python3 -m unittest discover -s tests -v` and serve the repository root with `python3 -m http.server 8000` to inspect the visualizer.

JSON is used instead of YAML so the canonical file is directly parseable by both Python's standard library and browsers without a dependency or custom YAML subset. Keep the schema embedded in the canonical file and maintain `schema_version` when its structure changes.
