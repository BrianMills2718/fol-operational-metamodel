# Goal: a clickable class diagram of first-order logic

Profile: `continuous-light` (one writer, one repository, reversible).
Plan: `fol-class-diagram` (company-planning quick-adopt in this repository).
Picture of where things stand and the phases: [`docs/where-we-are.html`](../where-we-are.html).

## Mission

Brian asked (2026-09-30) for "the WebVOWL or TypeDB type diagram that I'm
looking for": a readable picture of how first-order logic is built. On
2026-10-10 he approved Phase 0 (tidy-up) and Phase 1 (the class diagram), with
the FLAMS live-search work parked.

The diagram is generated from the OMG ODM Common Logic XMI the repository
already imports (`generated/odm-cl-metamodel-ir.json`), not hand-drawn.

## Canonical example

Serve the repository root, open `/visualizer/` (or the new diagram page), and see
`UniversalQuantification` drawn as a box under `QuantifiedSentence`, which sits
under `Sentence`, which sits under `Phrase`: a top-down hierarchy, not a
force-directed tangle. Clicking `QuantifiedSentence` shows its properties and
"has a" associations from the XMI (for example its body and binding sequence),
and a tooltip appears on hover for every control.

The reference output is the 24-link "is a kind of" tree in `docs/where-we-are.html`
(derived from the XMI data and checked by hand on 2026-10-10). The diagram must contain
exactly those 24 generalization links, checked by membership, not by count.

## Increments

**Phase 0: tidy up**
1. Make local `main` match `origin/main` (the extra local commit `938307c` is
   already preserved on `origin/wip/main-20261002`; confirm before resetting).
2. Fix `DESIGN.md` so it agrees with the README: `spec/fol.json` is a legacy
   comparison fixture, not the canonical metamodel.
3. Remove `.github/workflows/*` (workspace rule: no GitHub-hosted CI); the
   local `python3 -m unittest discover -s tests -v` run is the merge gate.
4. Add a short "FLAMS work is parked" note to the README pointing at the FLAMS docs.
5. Register the viewer in `ui/registry.yaml` if it is not already in the
   ecosystem UI index.

**Phase 1: the class diagram**
1. Landscape check (short): pick an off-the-shelf hierarchical layout
   (for example ELK via elkjs, dagre, or Mermaid `classDiagram`) rather than
   writing a layout algorithm.
2. Render the Common Logic classes as a top-down class diagram: generalization
   edges as the tree, associations and properties shown on click.
3. Tooltips on every control (workspace policy `ui-tooltips-default`).
4. A test asserting the 24 expected generalization pairs are all present.

## Acceptance checks

- `python3 -m unittest discover -s tests -v` passes, with counts and exit 0 reported.
- A Playwright (or `agent-browser`) run against the served page that: screenshots the
  diagram, checks that `UniversalQuantification` is rendered below
  `QuantifiedSentence`, clicks one class and sees its details, and hovers every
  visible control and fails if any shows no tooltip.
- `git status --short` clean; work merged to `main` and pushed.

## Out of scope

- FLAMS server, its patch, upstream contribution to FLAMS (parked, Phase 4).
- The semantics layer (Phase 2) and links into LATIN2 (Phase 3).
- Any hand-written FOL taxonomy presented as standard fact.

## Stops

- Same reproduced blocker three times with no new evidence: stop, report it
  with owner and resume event.
- Revalidate after three increments or about four hours: compare visible
  diagram progress against tidy-up/process work.

## Non-gating next actions

- Brian looks at the diagram and says whether it is the picture he meant.
- Phase 2 (truth side) and Phase 3 (LATIN2 links) get their own goal afterwards.
