---
schema_version: "1.0"
artifact_type: design_plan
id: fol-class-diagram
status: proposed
method_conformance_receipt: docs/plans/fol-class-diagram.receipt.json
trace_review_criteria:
  - criterion_id: outcome
    expected_outcome: pass
goal:
  outcome: "Opening visualizer/class-diagram.html shows the 29 OMG Common Logic classes as a top-down clickable class diagram generated from generated/odm-cl-metamodel-ir.json, after a repo tidy-up."
  canonical_example: "Serve the repo root, open /visualizer/class-diagram.html: UniversalQuantification sits below QuantifiedSentence, below Sentence, below Phrase; clicking QuantifiedSentence lists body (Sentence) and binding (Binding, 0..*, ordered) and their associations; hovering any control shows a styled tooltip."
  forbidden_substitutes: "A hand-drawn or hard-coded tree; the old force layout restyled; a screenshot of a mock; a count of 24 edges without checking which pairs."
  boundaries: "This repository only. FLAMS server, FLAMS patch, upstream contributions, semantics layer and LATIN2 links are out of scope. Reset local main only after confirming 938307c is on origin/wip/main-20261002."
  done_when: "Tidy-up landed; diagram generated from the IR and rendered by the shared ELK viewer; unit test asserts the 24 named generalization pairs and the suite passes with counts and exit 0; the Playwright run output shows screenshot, hierarchy positions, click details and tooltip-on-every-control; merged to main, pushed, git status clean."
  do_not_gate_on: "Brian reviewing the diagram; Phase 2 (semantics) and Phase 3 (LATIN2 links); FLAMS."
---

# Clickable class diagram of first-order logic

Each section below answers the checklist items quoted in it; the gate judges only that
section's text. Replace every `TODO(answer ...)` line before running `cli.py check`. Quote
values in the front matter: an unquoted ` #` starts a YAML comment and cuts the value.

## Actor and result

> **CORE-ACTOR-RESULT-EXAMPLE** (blocking): The plan names the actor it serves, the desired result, and one stable, concrete, user-visible example of that result.

Actor: Brian, learning how first-order logic is built (his 2026-09-30 words: "the WebVOWL or TypeDB type diagram that I'm looking for").

Result: a page, `visualizer/class-diagram.html`, that draws the 29 classes of the OMG ODM Common Logic package as a top-down "is a kind of" hierarchy, generated from `generated/odm-cl-metamodel-ir.json` and rendered with the shared graph viewer (`representation-router/graph-viewer`, React Flow + ELK layered layout). Clicking a class shows its properties (name, type, multiplicity) and the associations they belong to, all taken from the XMI import.

Example: open the page; `UniversalQuantification` is drawn below `QuantifiedSentence`, below `Sentence`, below `Phrase`. Click `QuantifiedSentence`: the side panel lists `body : Sentence` (association QuantificationForSentence) and `binding : Binding [0..*] ordered` (association BindingSequenceForQuantifiedSentence).

Phase 0 tidy-up comes first: local main matches origin/main, DESIGN.md agrees with the README, `.github/workflows/` removed, README notes FLAMS is parked.

## Requirements

> **CORE-REQUIREMENTS-TRACED** (blocking): The plan lists its requirements: what was asked for, and what the delivered work's own claims imply. A claim here is what the work is presented as being or doing to its users, for example work presented as following a standard, schema or contract (which implies conformance to it) or an output labelled as showing something (which implies it shows it correctly); the plan's own format and front matter are not such claims, and the details a check examines (what a trace must show) belong to that check rather than being separate requirements. Each requirement names the check that verifies it (a test, script, gate step, or named review of a run) and its status: passing, failing, planned and not yet run, or deferred with a stated reason; deferred requirements are carried onto every release or completion record the plan names. A plan fails this item if it has no requirements list, if any requirement has neither a check nor an explicit deferral with its reason, or if the plan presents the work as following a named standard, schema or contract, or as having another property its users rely on, that its requirements list omits.

| # | Requirement | Check | Status |
|---|---|---|---|
| R1 | Local `main` equals `origin/main`; commit 938307c confirmed on `origin/wip/main-20261002` first | `git branch -r --contains 938307c` then `git rev-parse main origin/main` equal | planned |
| R2 | DESIGN.md agrees with README: `spec/fol.json` is a legacy fixture, generated IR is authoritative | named review of the DESIGN.md diff in the merge commit | planned |
| R3 | No GitHub-hosted CI: `.github/workflows/` removed | `git ls-files .github` empty | planned |
| R4 | README says FLAMS work is parked and points to its docs | named review of README diff | planned |
| R5 | Diagram is generated from the imported OMG ODM CL XMI IR, never hand-written (claim: the picture faithfully shows the standard's generalizations) | `tests/test_class_diagram.py`: every one of the 24 named (child, parent) generalization pairs from the IR appears as an edge, no extra generalization edges, all 29 classes present; and regenerating equals the checked-in file | planned |
| R6 | Layout is an off-the-shelf hierarchical layout (ELK layered via shared graph-viewer, direction DOWN) | Playwright run: bounding box of UniversalQuantification is below QuantifiedSentence, below Sentence, below Phrase | planned |
| R7 | Clicking a class shows its properties and associations from the XMI | Playwright run clicks QuantifiedSentence and finds `body` and `binding` with their types in the details panel | planned |
| R8 | Every visible control shows a styled tooltip on hover (policy ui-tooltips-default) | Playwright run hovers every visible button/link/node and fails if no tooltip element becomes visible | planned |
| R9 | Unit suite passes with counts | `python3 -m unittest discover -s tests -v` output shows counts and exit 0 | planned |
| R10 | Merged to main and pushed; working tree clean | `git log origin/main -1`, `git status --short` | planned |
| R11 | New page registered in the ecosystem UI index | `ui/registry.yaml` lists it | planned |

## Success and disproof

> **CORE-SUCCESS-DISPROOF** (blocking): The plan defines the evidence that would show success and a concrete condition that would disprove the approach. Each success measure is the property the plan claims, or a check that directly tests that property, not a stand-in for it: a count, a picture, a readability judgment, or the pipeline agreeing with itself (hashes, labels, byte equality) does not show correctness or conformance it does not test. A plan fails this item if it has no disproof condition, or if a success measure is such a stand-in for the claimed property and the plan names no direct check of that property.

> **CORE-TRACE-REVIEW** (blocking): Every success or acceptance criterion in the plan is judged from the full trace of a run, not only its final outcome: it names the run whose full trace is examined (for example the session, its tool and LLM calls, commits, check output, or messages), where that trace lives, and what must be seen in that trace beyond the final outcome. A criterion that names only an outcome, such as tests passing, a PR merged, a test fixture reproducing the journey, or a status reading succeeded, fails this item. A criterion for which no run exists, such as a pure document edit, passes only when the plan states that exemption and its reason explicitly.

Success is the claimed property checked directly: the 24 generalization pairs are compared by membership against the IR (not counted), the vertical order of four named classes is measured in the rendered page, the click is performed and the panel text is read, and every control is hovered.

Disproof: any of the 24 IR generalization pairs is missing from the diagram or an extra one appears; the rendered layout does not put children below parents (meaning the layered layout does not fit this data, and we would switch to another hierarchical layout); the details panel shows anything not present in the IR; or a control shows no tooltip.

Each criterion is judged from the trace of this Claude Code session (session https://claude.ai/code/session_01UWLqVtwEQ9x6YTEvprgzje), which records every tool call and its output:

- R1: the git command output in the session shows 938307c contained in origin/wip/main-20261002 before the reset and both hashes equal after.
- R2, R4: the session shows the diff text of DESIGN.md and README.md, read before commit.
- R3, R10, R11: the session shows `git ls-files .github`, `git status --short`, `git log origin/main -1` and the registry diff.
- R5, R9: the session shows the full verbose unittest output, including the named test `test_class_diagram` lines, the total count and the exit code; the test itself prints any missing or extra pair by name.
- R6, R7, R8: the Playwright script `tests/e2e/class_diagram_e2e.mjs` prints one line per check (each class's y position, the panel text found, each hovered control and whether its tooltip appeared) and writes a screenshot; the session shows that output and the screenshot is opened and looked at, not just produced.
- R2 and R4 are pure document edits with no run; they are judged by reading the diff in the session, stated here as the exemption.

## When a run fails or surprises us

> **CORE-TRACE-DEBUGGING** (blocking): The plan includes a separate When a run fails or surprises us procedure, distinct from anticipated failure modes. It requires preserving the failed run and its trace id; reading full inputs, prompts, each tool call arguments/results, intermediate stages and final output before selecting a fix; citing the observed divergence; classifying evidence absent, evidence returned but unused or contradicted, invalid expectation, or unresolved; and linking a targeted repair to a new traced verification run while retaining the original failure. Unresolved diagnoses permit investigation but cannot authorize a causal repair. Review completeness is separate from the run verdict.

This procedure is separate from the anticipated failure modes above. When a check fails or surprises us:

1. Keep the failed run: save its full output (unittest or Playwright log and screenshot) under `~/code/.scratch/fol-class-diagram/` with the session id and a timestamp, and do not overwrite it.
2. Read the whole trace before choosing a fix: the inputs (IR file, generated typed graph), every tool call's arguments and results, each intermediate stage (generated JSON, rendered DOM, console errors), and the final output.
3. Cite the exact divergence (for example: pair Equation->Atom absent from generated edges; or UniversalQuantification y=120 above Sentence y=300).
4. Classify it: evidence absent (data never produced), evidence returned but unused or contradicted (data present, page ignores it), invalid expectation (the check is wrong, for example the IR has different names), or unresolved.
5. Only a classified cause authorizes a targeted fix; an unresolved diagnosis allows further investigation but no causal repair.
6. Link the fix to a new traced run and keep the original failure log next to it.

Whether the trace review was complete is recorded separately from whether the run passed: a passing run whose trace was not read does not count as reviewed.

## System model

> **CORE-SYSTEM-MODEL** (blocking): The plan links the project's system model (a path such as docs/model/ODD.md) or carries the one-line exemption `System model: exempt -- <reason>`, which fits only a project with no stored state and no user-facing view. Unless exempt, the plan names each system-model element (entity, process, record or event, or view) that the work adds, changes, or relies on, and its trace review names, for each such element, what the examined run must show of it (for example an event of that record type with its id, or the view displaying that entity). A plan with neither a model link nor the exemption line fails this item, as does one that lists model elements without saying what the examined run must show of each, or one that names no element without stating that the work touches none and why. For a maintained repository, the plan also cites the documentation entry point from which the model is reachable; a shared model explicitly identifies this repository's scope. It names applicable source-linked views, explains material omissions without imposing a fixed diagram quota, names concrete model freshness or drift checks, and states how the model, view coverage and verification evidence will be reconciled in the same change (or gives a concrete reason each needs no update). A bare model path without these discovery, view, freshness and reconciliation obligations fails this item. Representation Router may render selected views but does not supply planning authority or prove executed behavior.

System model: `docs/standards-metamodel.md` (the layered model of standards IR, MMT corpus and bridges) together with the pipeline section of `README.md`. The repository's documentation entry point is `README.md` (pipeline section), with the standards layer described in `docs/standards-metamodel.md`; this repo's scope is the whole model (no shared model). Elements this work adds, changes or relies on, and what the examined run must show of each:

- Entity `generated/odm-cl-metamodel-ir.json` (standards IR, relied on): the unit test loads it and its output names the 29 classes and 24 pairs it read.
- Process `scripts/cl_class_diagram.py` (added): converts the IR to typed-graph/v1 plus a details file; the test run shows it regenerating byte-identical output.
- Record `generated/cl-class-diagram.json` (added, typed-graph/v1 plus details): the test shows it validates and contains the 24 pairs.
- View `visualizer/class-diagram.html` (added): the Playwright run shows it displaying the classes in hierarchy, the details panel and tooltips.
- View `visualizer/index.html` (existing force explorer): unchanged except a link to the new page; the Playwright run shows the link.

Source-linked views: README pipeline text and `docs/where-we-are.html` (status picture). No new diagram of the pipeline is needed; omission reason: the pipeline gains one step, described in README text.
Freshness/drift checks: the unit test regenerates the typed graph from the IR and fails if it differs from the checked-in file; it also fails if the IR's generalization pairs change.
Reconciliation: README pipeline section, `docs/where-we-are.html` phase status and the test are updated in the same change as the converter and page.

## Capability reuse

> **CORE-CAPABILITY-REUSE** (blocking): The plan answers capability reuse against the capability catalogue in agentic-capability-architecture-canonical, which has two files: `reuse_candidates.yml`, whose entries under `candidates:` are cross-project capabilities with their selected off-the-shelf implementations, each named by its `id` (for example `documents_to_text`) and marked candidate or promoted; and `capability_registry.yml`, whose entries under `capabilities:` are the packages that repository holds, each named by its key (for example `approvals`) with the capability ids it `provides` (for example `approval.resolve`). An entry from either file counts. The plan names each catalogue capability the work reuses, by its id, key or provided id; names each new capability the work adds together with its first consumer (the project, command or workflow in this plan that uses it); and, where no entry covers what the work needs, states `No catalogue entry fits, because <reason>`, the reason saying what the work needs that no entry provides. A plan may give more than one of these answers. A plan fails this item if it gives none of them, if it claims reuse without naming the catalogue entry or id reused (reusing code or a contract that is not a catalogue entry does not count), if it adds a capability without naming its first consumer, or if it says no entry fits without a reason.

No catalogue entry fits, because neither `reuse_candidates.yml` nor `capability_registry.yml` in agentic-capability-architecture-canonical lists a graph or diagram rendering capability (searched for graph/diagram/layout/viewer on 2026-10-10; the only hit is `graph_application_toolkit`, which is document ingestion, not rendering).

Outside the catalogue, the work reuses the shared graph viewer `representation-router/graph-viewer` 0.8.0 (React Flow + ELK, input `typed-graph/v1`), vendored as a pinned copy, rather than writing any layout code. It adds no new shared capability.

## Authority and non-goals

> **CORE-AUTHORITY-NONGOALS** (blocking): The plan states who holds authority over the work and what it explicitly will not do (non-goals).

Authority: Brian owns the repository (BrianMills2718/fol-operational-metamodel, normal_push per PROJECT_GRAPH.json) and approved this work on 2026-10-10 ("yes give me the /goal"). The agent merges after local checks per workspace policy.

Non-goals: no FLAMS server, patch or upstream contribution; no semantics layer (Phase 2); no LATIN2 links (Phase 3); no hand-written FOL taxonomy presented as standard fact; no changes to the shared graph viewer itself (a missing feature there is reported to its owner, not patched here); no deletion of the FLAMS code.

## Irreversible actions and spend

> **CORE-IRREVERSIBLE-SPEND** (blocking): For each irreversible action or spend the plan proposes, it names the boundary, who must authorize it, and how it is contained.

No spend. Two actions are treated as irreversible and declared so in the activation facts.

1. Pushing to the public GitHub repository (publication). Boundary: only code, docs, the vendored viewer and the public OMG-derived IR; no private data. Authorization: Brian's standing rule (workspace AGENTS.md, 2026-10-07: anything may be public unless it holds private data) plus his 2026-10-10 approval of this goal. Containment: a secret and email/phone pattern grep over the diff before push; a bad push is reverted by a follow-up commit, and nothing is announced.
2. The local main reset. The only near-irreversible action is resetting local `main`, which discards local commit 938307c from that branch. Boundary: run it only after `git branch -r --contains 938307c` lists `origin/wip/main-20261002`. Authorization: Brian's 2026-10-10 approval of Phase 0. Containment: the commit stays on the remote branch and in the reflog. Deleting `.github/workflows/` is a revertible commit. Pushing to the public repository publishes only code, docs and public standard data (no private data; checked with a secret-pattern grep before push).

## Uncertainties

> **CORE-UNCERTAINTIES** (blocking): The plan lists its material uncertainties, and each one has an owner or the evidence that would resolve it.

- Whether ELK layered with direction DOWN gives a readable tree for 29 classes with several isolated classes (Binding, Text, etc.). Resolved by the Playwright screenshot and position checks; owner: this session.
- Whether the shared viewer's zoom/fit controls (React Flow Controls) have styled tooltips; they appear to carry only native `title`. Resolved by the hover check; if missing, a page-level tooltip layer covers them here and the gap is reported to representation-router. Owner: this session.
- Whether every uml-property in the IR has a resolvable type and association. Resolved by the converter test listing any unresolved property by name. Owner: this session.

## Activation facts

> **CORE-ACTIVATION-FACTS** (blocking): No activation fact that the plan triggers is declared false. Declaring a fact true when the plan does not strictly need it is acceptable, because it only adds checks; judge only facts declared false. empirical_comparison_proposed is triggered when the plan proposes an A/B test, benchmark, bake-off, or other experiment comparing alternative designs, models, or candidates to choose among them; checking the built result against an expected outcome (an acceptance test, fixture replay, or regression check) is verification and does not trigger it. shared_mechanism is triggered by a new shared mechanism, contract, or algorithm; llm_central by behavior that centrally depends on LLM calls; irreversible_or_spend_action by a proposed irreversible action or spend. claims_external_standard is triggered when the plan claims, or presents its work as, following, implementing or conforming to a standard, schema or contract owned outside the repository being changed (for example a model presented as DM2, or output said to match a published schema); conforming to the repository's own contracts does not trigger it; aes_governed_target when the target repository is governed by an AES target (`.aes/target.yaml`). These two facts are optional: an undeclared one is shown as false and is judged like a declared false.

Declared: shared_mechanism=false (reuses an existing shared viewer, adds no shared contract); empirical_comparison_proposed=false (checks are acceptance tests, no bake-off); llm_central=false (no LLM calls); irreversible_or_spend_action=true (public push and local main reset; boundaries, authorization and containment in the section above; no money is spent).

crosses_system_boundary=true (the work is pushed to the public GitHub repository; see Irreversible actions and spend for boundary, authorization and containment).

claims_external_standard: the page presents its content as the OMG ODM Common Logic metamodel. That claim is checked directly by R5 (membership of every generalization pair against the imported XMI IR), so the fact is treated as triggered and covered.

## Standard conformance

Standard claimed: OMG Ontology Definition Metamodel (ODM) 1.1, Common Logic (`CL`) package, as published in the normative XMI `https://www.omg.org/spec/ODM/20131101/ODM-metamodels.xmi` (sha256 `3ea06c4d0fed8f796072b55cb4899ae7ed995c5de2d624b48ee625b198f5a56a`, imported by `scripts/import_standards.py` into `generated/odm-cl-metamodel-ir.json`).

Machine-readable rules the artifacts must satisfy (from the XMI): (1) every `uml:Class` in the CL package appears as a class box; (2) every UML `generalization` (child, general) in the package appears as exactly one parent-to-child line, and no other line is drawn as a generalization; (3) each class's owned properties are shown with the name, type and multiplicity the XMI gives, and the association each belongs to. The diagram presents nothing else as part of the standard.

Check in the merge gate: `tests/test_class_diagram.py`, run by `python3 -m unittest discover -s tests -v`, which is this repository's local merge gate (README "Run"). It compares the generated diagram file against the IR by membership for rules 1-3 and fails on any missing or extra item. Disproof: the diagram labelled as the ODM Common Logic metamodel violates one of these rules.

Extensions: plain-language one-line explanations shown as tooltips on classes are this project's annotations, not part of the standard; the page labels them "our note" and the generated file stores them in a separate field from the XMI data.

## Contracts and dependencies

Boundaries crossed and the contracts each uses:

1. Shared graph viewer to this repository. Contract: `typed-graph/v1`, owner representation-router (Brian), file `~/code/representation-router/schemas/typed-graph.schema.json`, implementation `representation-router/graph-viewer` 0.8.0 (commit a22006a), vendored as `visualizer/vendor/graph-viewer.js`. This plan uses it and does not change it. Producer: `scripts/cl_class_diagram.py` writes `generated/cl-class-diagram.json` conforming to it; consumer: `visualizer/class-diagram.html` through `GraphViewer.mount`.
2. OMG standard to this repository. Contracts: (a) the ODM 1.1 XMI at https://www.omg.org/spec/ODM/20131101/ODM-metamodels.xmi, owner OMG; producer OMG, consumer `scripts/import_standards.py`. (b) this repository's `standards-ir/v1` IR format, owner this repository (Brian), defined by `scripts/import_standards.py` and instantiated in `generated/odm-cl-metamodel-ir.json`; producer `scripts/import_standards.py`, consumer the new `scripts/cl_class_diagram.py`. Neither is changed.
3. This repository to GitHub (public push). Contract: the git remote https://github.com/BrianMills2718/fol-operational-metamodel.git, owner Brian; unchanged. Producer: this local checkout's `main`; consumers: anyone cloning or browsing the public repository, and this checkout's future sessions.
4. This repository to the ecosystem UI index. Contract: the per-repository `ui/registry.yaml` format, owner project-meta, whose daily generator writes `~/.local/share/ui-index/ecosystem_ui_index.yaml`. Producer: this repository's `ui/registry.yaml` (this plan adds the entry); consumer: project-meta's UI index generator and agents searching the index. This plan does not change the format.

Landing order so no consumer breaks: vendor the viewer file first; then the converter and its generated file with the unit test; then the page that reads them; then the link from the old explorer, the README and registry entry; the whole set merges as one commit series on one branch, so `main` never holds a page without its data.
