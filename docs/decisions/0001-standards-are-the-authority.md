---
description: Decision that upstream standards and the compiled MMT corpus are the authority for every picture, and project additions are marked annotations
---

# 0001: Upstream sources are the authority; project additions are marked annotations

Governs: RULE-STANDARDS-VERBATIM, RULE-MMT-PINNED, RULE-MMT-EXPLICIT-ONLY, RULE-MEANING-CHECKED, RULE-DIAGRAM-GENERATED, RULE-ANNOTATION-MARKED

Status: accepted, 2026-10-10 (recorded 2026-10-11 from commit `d576e67`, "Phase 0: fix DESIGN.md authority", and the fol-meaning-layer plan).

## Context

The repository started (2026-09-30) with a hand-written FOL schema (`spec/fol.json`,
`schema/fol.tql`, `examples/abc.json`), and `DESIGN.md` called it the canonical
metamodel while the README already said the opposite. Published, machine-readable
sources exist for every layer it wanted to show: the OMG ODM Common Logic XMI for
abstract syntax, DOL for the logic-interoperability layer, compiled MMT/LATIN2 for
formal instances, and the public Common Logic draft for the truth rules.

## Decision

Formal structure comes only from imported upstream sources, regenerated rather than
edited (`generated/` is never hand-edited). The hand-written schema stays only as a
legacy comparison fixture for its finite-semantics tests. Anything the project adds
(a plain-language note, a truth rule quoted from the draft, a bridge between a
standard class and an MMT declaration) lives in a marked annotation file with a
citation, and a program checks its claims; the bridge policy is in
`docs/standards-metamodel.md`.

## Consequences

Each picture can say which statements are upstream fact and which are annotation,
and a test fails when a checked-in picture drifts from its source. The cost: a layer
with no machine-readable source (the final ISO 2007/2018 text, which is licence-gated)
can only be shown as quoted, cited annotation.

## Wrong when

A reader of `visualizer/class-diagram.html` cannot tell an annotation from an
upstream fact, or the importer needs a hand patch to the generated IR to match its
source; either means generation is not carrying the authority and the decision
should be revisited.
