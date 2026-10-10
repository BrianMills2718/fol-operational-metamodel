# Design and contribution guide

## Authority and generated views

This repository does not author its own account of first-order logic. Formal
authority comes from upstream sources, imported as generated graph IR:

- `generated/odm-cl-metamodel-ir.json` and `generated/dol-oms-metamodel-ir.json`:
  OMG ODM Common Logic and DOL metamodels, imported verbatim from normative XMI
  by `scripts/import_standards.py` (see `docs/standards-metamodel.md`).
- `generated/pinned-fol-ir.json` and other MMT IR: compiled MMT OMDoc,
  archivegraph and relational indexes, imported by `scripts/import_mmt.py`
  (see `upstream/README.md`).

`spec/fol.json`, `schema/fol.tql` and `examples/abc.json` are a legacy,
hand-written comparison fixture. They are kept for their finite-semantics
tests, not as the canonical metamodel. Do not hand-edit generated IR or
duplicate graph structure in JavaScript; regenerate from the upstream source.

Anything the project adds beyond an upstream source (a plain-language note, a
link between a standard class and an MMT declaration) is a marked annotation,
never presented as upstream fact (bridge policy in `docs/standards-metamodel.md`).

## Extending

1. Add or change an importer or converter under `scripts/`, and regenerate its
   output under `generated/`.
2. Add a test that compares the output with the upstream input by membership
   (which items are present), not by count.
3. Run `python3 -m unittest discover -s tests -v` locally; that run is the
   merge gate (no GitHub-hosted CI). Serve the repository root with
   `python3 -m http.server 8000` and check the page in a browser.

JSON is used so files parse with Python's standard library and in browsers
without extra dependencies.
