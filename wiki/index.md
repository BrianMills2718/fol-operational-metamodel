# FOL Operational Metamodel: index

What this repo does: imports published formal sources about first-order logic
(OMG Common Logic and DOL metamodels, MMT/LATIN2 formalizations) into graph
files and draws them in a browser viewer. See the [README](../README.md).

## Purpose

Brian, 2026-10-10: learning checked visual models (metamodels, semantics, diagrams) in order to understand and steer his agent-built systems, starting with the observation-to-action repository. Rule carried forward: a picture is generated from the real source, anything hand-added is marked as a note, and a program checks its claims. Done for this repo: Common Logic syntax (class diagram) plus meaning (truth rules, checked core rebuilds). Next use of the pattern: other repositories, not more first-order logic here.

## Start here

- [Class diagram of first-order logic](../visualizer/class-diagram.html) (serve the repo root first; see README "Run").
- [Where we are, in pictures](../docs/where-we-are.html): status and phases (2026-10-10).
- [Standards-derived metamodel layers](../docs/standards-metamodel.md): which source is authoritative for what.
- [Design and contribution guide](../DESIGN.md)

## Plans

- [Goal: clickable class diagram](../docs/goals/fol-class-diagram.md)
- [Plan fol-class-diagram](../docs/plans/fol-class-diagram.md) and its [goal record](../docs/plans/fol-class-diagram.goal.md) (done)
- [Plan fol-meaning-layer](../docs/plans/fol-meaning-layer.md) and its [goal record](../docs/plans/fol-meaning-layer.goal.md): truth rules and core rebuilds (done)

## Parked: FLAMS live search

- [MMT to FLAMS RDF bridge](../docs/mmt-flams-rdf-bridge.md)
- [FLAMS external-archive RDF hook](../docs/flams-external-rdf-hook.md)
- [First FLAMS view query](../docs/first-flams-view.md)

## Provenance

- [Vendored shared graph viewer](../visualizer/vendor/README.md)
- [Upstream sources](../upstream/README.md)
- [Concept references](../references/README.md)
