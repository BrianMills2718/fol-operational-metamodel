---
description: What the FOL operational metamodel repository is for, the bet behind generating its pictures from published standards, and what would disprove it
---

# FOL Operational Metamodel: goal and thesis

## Introduction and Goals

### Requirements Overview

The repository turns published, machine-readable sources about first-order logic
into graph files and browser pictures a person can click through: the OMG ODM
Common Logic and DOL metamodels (imported verbatim from normative XMI), compiled
MMT/LATIN2 formalizations (imported from OMDoc, archivegraph and relational
indexes), and a marked annotation layer that quotes the Common Logic truth rules
and checks how each connective and quantifier is rebuilt from the core pieces.
The numbered requirements, each with a success criterion and a disproof, are in
[REQUIREMENTS.md](REQUIREMENTS.md); the rules that enforce them, with their owner
files and tests, are in the system model ([ARCHITECTURE.md](../model/ARCHITECTURE.md),
[trace.yaml](../model/trace.yaml)).

### Quality Goals

- Generated, not drawn: every class, generalization and property in a picture
  comes from an imported upstream file, and a test fails when the checked-in
  picture no longer matches a fresh generation.
- Additions are marked: anything the project adds beyond an upstream source (a
  plain-language note, a truth rule quoted from the draft, a bridge) carries an
  annotation mark and its citation, never presented as upstream fact
  ([Decision 0001](../decisions/0001-standards-are-the-authority.md)).
- Claims are checked by a program: each rebuild of a connective or quantifier is
  evaluated on every true/false combination (and every world of 1-3 things),
  not asserted.
- No dependencies to run: Python standard library and a browser; Node only for
  the optional browser check.

### Stakeholders

- Brian, who uses the pictures to learn checked visual models (metamodels,
  semantics, diagrams) so he can understand and steer agent-built systems.
- Coding agents that extend the importers and annotations, and that reuse the
  "generated picture plus checked claims" pattern in other repositories.

## North star (AES extension)

From the purpose recorded in `wiki/index.md` (Brian, 2026-10-10): a person can open
one page and see how first-order logic is built (its parts from the Common Logic
standard, and what each connective and quantifier means), where every element
on the page is generated from a real source, anything hand-added is visibly
marked, and a program has checked its claims; the same pattern then carries to
other repositories, starting with the observation-to-action repository.

## Thesis (AES extension)

A picture of a formal system can be trusted to teach when its truth lives where
it is edited (AES-CTX-004): the structure comes from the published standard or
compiled formal corpus that owns it, regenerated rather than redrawn, and the
project's own additions sit in one marked annotation file whose claims a program
re-checks on every test run. A hand-drawn or hand-maintained diagram drifts from
its source and cannot say which of its lines are fact and which are opinion.

## Thesis disproof (AES extension)

The approach is wrong if a reader of the class diagram still cannot tell which
statements are upstream fact and which are project annotation; or if keeping the
generated diagram and checks current costs more edits than redrawing it by hand
would (for example, the importer needs hand patches to match the XMI); or if a
checked rebuild agrees with the program while disagreeing with the quoted
Common Logic rule on some case a person finds.

## Non-goals

- Authoring the project's own ontology of first-order logic; `spec/fol.json`,
  `schema/fol.tql` and `examples/abc.json` are kept only as a legacy comparison
  fixture (`DESIGN.md`).
- Inferring categories (quantifier, connective, axiom) from names in the MMT
  corpus; richer classes come only from upstream roles or marked annotations.
- Live FLAMS search: parked since 2026-10-10 until a FLAMS server with the
  external-RDF patch exists.
- More first-order-logic depth here; the next use of the pattern is other
  repositories.

## Lineage (AES extension)

none -- original. The repository began 2026-09-30 ("Initialize operational FOL
metamodel"). The folder keeps a `-real` suffix only because an older local
duplicate checkout of the same GitHub repository was archived on 2026-10-02
(`project-meta/PROJECT_GRAPH.json` note); that was a copy, not a predecessor.
Drawn from: `README.md`, `DESIGN.md`, `wiki/index.md` (Purpose),
`docs/standards-metamodel.md`, `docs/goals/fol-class-diagram.md`,
`docs/plans/fol-meaning-layer.goal.md` and the git history.
