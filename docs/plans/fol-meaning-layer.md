---
schema_version: "1.0"
artifact_type: design_plan
id: fol-meaning-layer
status: proposed
method_conformance_receipt: docs/plans/fol-meaning-layer.receipt.json
trace_review_criteria:
  - criterion_id: outcome
    expected_outcome: pass
goal:
  outcome: "In the class diagram, each Common Logic connective and quantifier shows when it is true (quoted and cited from the public Common Logic draft), its truth table, and how it is rebuilt from the core pieces not, and, for every, with every rebuild checked by the program."
  canonical_example: "Click Conjunction: true when every component is true; table row (true, false) gives false; a core piece. Click Disjunction: true unless every component is false; row (true, false) gives true; rebuilt as not (not C1 and ... and not Cn), checked on all rows for 0-3 components."
  forbidden_substitutes: "Truth rules paraphrased without the cited source; a rebuild line that is displayed but not checked; truth tables typed by hand instead of computed from the rule; checks that only count rows."
  boundaries: "This repository only; hand-written content lives in one marked annotation file; FLAMS, LATIN2 links and other logics are out of scope; no licence agreement accepted on Brian's behalf."
  done_when: "Annotation file cites the draft row for each of 9 classes; checker verifies every rebuild (all rows, 0-3 components; quantifiers on every world of 1-3 things); unit tests and browser check pass with counts; merged and pushed; git status clean."
  do_not_gate_on: "Brian reviewing the page; the final ISO 2007/2018 text (licence-gated); Phase 3 LATIN2 links."
---

# Meaning layer: truth rules and core rebuilds

Each section below answers the checklist items quoted in it; the gate judges only that
section's text. Replace every `TODO(answer ...)` line before running `cli.py check`. Quote
values in the front matter: an unquoted ` #` starts a YAML comment and cuts the value.

## Actor and result

> **CORE-ACTOR-RESULT-EXAMPLE** (blocking): The plan names the actor it serves, the desired result, and one stable, concrete, user-visible example of that result.

Actor: Brian, learning how first-order logic is built. On 2026-10-10 he looked at the Phase 1 class diagram and said "conjunction and disjunciton both have the same informaiton. ther is notinfromation that allows you to disntiguish them", then approved ("ok i approve") the design: keep the standard's boxes, and give each box "true when" plus "rebuilt from the core pieces not, and, for every", with the program checking every rebuild.

Result: clicking a connective or quantifier in `visualizer/class-diagram.html` shows (1) its truth rule quoted from ISO/IEC FCD 24707 Common Logic, final committee draft dated 2005-12-10, document JTC1/SC32 N1377 (https://www.jtc1sc32.org/doc/N1351-1400/32N1377T-FCD24707_doc, sha256 b9a641f5a4e6dff854cc76f5d20c5693742426275338dff34f3e6dfd85eb3661), clause 6.2 Table 1 rows E9-E15, and clause 6.1 for component counts, with a plain-language line; (2) a truth table computed from that rule; (3) whether it is a core piece or how it is rebuilt from the core, with the check result.

Example: Conjunction shows "true if I(C1) = ... = I(Cn) = true, otherwise false" (E10), row (true, false) -> false, "core piece". Disjunction shows "false if I(C1) = ... = I(Cn) = false, otherwise true" (E11), row (true, false) -> true, "rebuilt as not (not C1 and ... and not Cn): checked, all rows agree for 0-3 components".

## Requirements

> **CORE-REQUIREMENTS-TRACED** (blocking): The plan lists its requirements: what was asked for, and what the delivered work's own claims imply. A claim here is what the work is presented as being or doing to its users, for example work presented as following a standard, schema or contract (which implies conformance to it) or an output labelled as showing something (which implies it shows it correctly); the plan's own format and front matter are not such claims, and the details a check examines (what a trace must show) belong to that check rather than being separate requirements. Each requirement names the check that verifies it (a test, script, gate step, or named review of a run) and its status: passing, failing, planned and not yet run, or deferred with a stated reason; deferred requirements are carried onto every release or completion record the plan names. A plan fails this item if it has no requirements list, if any requirement has neither a check nor an explicit deferral with its reason, or if the plan presents the work as following a named standard, schema or contract, or as having another property its users rely on, that its requirements list omits.

| # | Requirement | Check | Status |
|---|---|---|---|
| R1 | Each of Negation, Conjunction, Disjunction, Implication, Biconditional, UniversalQuantification, ExistentialQuantification, Equation, AtomicSentence carries a truth rule quoted from the draft with clause and row (claim: the rules are Common Logic's) | `tests/test_cl_meaning.py` asserts every listed class has a quote, row id and source; a named review compares each quote to `fcd.txt` lines 700-735 in this session | planned, not yet run |
| R2 | Truth tables are computed from an evaluator that implements Table 1 rows literally, not typed by hand | test asserts tables are generated by `scripts/cl_meaning.py` and match a fresh run | planned, not yet run |
| R3 | Core pieces are exactly not, and, for every; every other connective/quantifier has a rebuild using only core pieces | test parses each rebuild and fails on any non-core operator | planned, not yet run |
| R4 | Every rebuild is checked: connectives on all true/false rows for 0-3 components (fixed arity where the draft fixes it), existential on every world of 1-3 things and every choice of which things the body holds for | test re-runs the checker and asserts each rebuild agrees on every case, printing any counterexample | planned, not yet run |
| R5 | Conjunction and Disjunction are visibly distinguished (Brian's finding) | test asserts their tables differ on row (true,false); browser check clicks both and reads different results | planned, not yet run |
| R6 | Quantifier checks are labelled as checked on small worlds, not proven | test asserts the label text; browser check reads it | planned, not yet run |
| R7 | Hand-written content is marked as our annotation, separate from XMI facts | test asserts `annotation: true` on every meaning record; page shows "our note" label | planned, not yet run |
| R8 | Phase 1 behaviour still holds (hierarchy, click, tooltips on every control) | browser check `tests/e2e/class_diagram_e2e.mjs` | planned, not yet run |
| R9 | Suite passes with counts; merged, pushed, clean | unittest -v output, git log/status | planned, not yet run |

## Success and disproof

> **CORE-SUCCESS-DISPROOF** (blocking): The plan defines the evidence that would show success and a concrete condition that would disprove the approach. Each success measure is the property the plan claims, or a check that directly tests that property, not a stand-in for it: a count, a picture, a readability judgment, or the pipeline agreeing with itself (hashes, labels, byte equality) does not show correctness or conformance it does not test. A plan fails this item if it has no disproof condition, or if a success measure is such a stand-in for the claimed property and the plan names no direct check of that property.

> **CORE-TRACE-REVIEW** (blocking): Every success or acceptance criterion in the plan is judged from the full trace of a run, not only its final outcome: it names the run whose full trace is examined (for example the session, its tool and LLM calls, commits, check output, or messages), where that trace lives, and what must be seen in that trace beyond the final outcome. A criterion that names only an outcome, such as tests passing, a PR merged, a test fixture reproducing the journey, or a status reading succeeded, fails this item. A criterion for which no run exists, such as a pure document edit, passes only when the plan states that exemption and its reason explicitly.

Success is checked directly: each rebuild is evaluated against the literal Table 1 rule on every case in the stated range; Conjunction and Disjunction are compared on a named row; each quote is compared to the draft text.

Disproof: any rebuild disagrees with the official rule on any case (the core claim is false, or the rebuild is wrong); a quoted rule does not match the draft text; Conjunction and Disjunction still show the same information; or the page presents a hand-written line as XMI fact.

Each criterion is judged from the trace of this Claude Code session (https://claude.ai/code/session_01UWLqVtwEQ9x6YTEvprgzje), which records every tool call and output:

- R1: the session shows the draft text (`~/code/.scratch/fol-cl-std/fcd.txt` lines 700-735) next to each quote in `spec/cl-meaning.json`, compared in a read step.
- R2-R6: the session shows `python3 scripts/cl_meaning.py` output listing each rebuild with the number of cases checked and any counterexample, and the verbose unittest lines for each named test, total count and exit code.
- R5, R6, R8: the browser script prints the panel text for Conjunction and Disjunction, the small-world label, hierarchy positions and the tooltip tally, then `RESULT passed=N failed=M`; the screenshot is opened and looked at.
- R7: the session shows the rendered panel label and the JSON field.
- R9: the session shows `git log origin/main -1` and `git status --short`.
Quote comparison (R1) is a document review with no run; it is judged by reading both texts in the session, stated here as the exemption.

## When a run fails or surprises us

> **CORE-TRACE-DEBUGGING** (blocking): The plan includes a separate When a run fails or surprises us procedure, distinct from anticipated failure modes. It requires preserving the failed run and its trace id; reading full inputs, prompts, each tool call arguments/results, intermediate stages and final output before selecting a fix; citing the observed divergence; classifying evidence absent, evidence returned but unused or contradicted, invalid expectation, or unresolved; and linking a targeted repair to a new traced verification run while retaining the original failure. Unresolved diagnoses permit investigation but cannot authorize a causal repair. Review completeness is separate from the run verdict.

This procedure is separate from the anticipated failure modes above. When a check fails or surprises us:

1. Keep the failed run: save the full output (checker, unittest or browser log, screenshot) under `~/code/.scratch/fol-class-diagram/`, named with the trace id (this session id plus the tool-call timestamp) so the trace can be found again; do not overwrite it.
2. Read the whole trace before choosing a fix: inputs (annotation file, IR), every tool call's arguments and results, intermediate stages (each evaluated case, generated JSON, rendered DOM, console), and the final output.
3. Cite the exact divergence (for example: Implication rebuild gives true on (true,false) where E12 gives false).
4. Classify it: evidence absent, evidence returned but unused or contradicted, invalid expectation (for example our rebuild or test is wrong, not the rule), or unresolved.
5. Only a classified cause authorizes a targeted fix; an unresolved diagnosis allows investigation but no causal repair. A disagreement between a rebuild and the draft rule is never fixed by editing the rule quote.
6. Link the fix to a new traced verification run (same check, same inputs) and keep the original failure log and its trace id next to it.

Review completeness (was the trace read) is recorded separately from the run verdict (did it pass).

## System model

> **CORE-SYSTEM-MODEL** (blocking): The plan links the project's system model (a path such as docs/model/ODD.md) or carries the one-line exemption `System model: exempt -- <reason>`, which fits only a project with no stored state and no user-facing view. Unless exempt, the plan names each system-model element (entity, process, record or event, or view) that the work adds, changes, or relies on, and its trace review names, for each such element, what the examined run must show of it (for example an event of that record type with its id, or the view displaying that entity). A plan with neither a model link nor the exemption line fails this item, as does one that lists model elements without saying what the examined run must show of each, or one that names no element without stating that the work touches none and why. For a maintained repository, the plan also cites the documentation entry point from which the model is reachable; a shared model explicitly identifies this repository's scope. It names applicable source-linked views, explains material omissions without imposing a fixed diagram quota, names concrete model freshness or drift checks, and states how the model, view coverage and verification evidence will be reconciled in the same change (or gives a concrete reason each needs no update). A bare model path without these discovery, view, freshness and reconciliation obligations fails this item. Representation Router may render selected views but does not supply planning authority or prove executed behavior.

System model: `docs/standards-metamodel.md` (layers: standards IR, MMT corpus, bridges and annotations) with the README pipeline section; documentation entry point `wiki/index.md` -> README. This repository's scope is the whole model. Elements this work adds, changes or relies on, and what the examined run must show of each:

- Entity `generated/odm-cl-metamodel-ir.json` (relied on): the test shows every annotated class name exists in it.
- Record `spec/cl-meaning.json` (added; annotation layer, the "project annotation" kind in docs/standards-metamodel.md's bridge policy): the test shows each record's quote, row and `annotation: true`.
- Process `scripts/cl_meaning.py` (added): the run shows each rebuild and its case count.
- Record `generated/cl-meaning-checks.json` (added): the test shows it matches a fresh run.
- Process `scripts/cl_class_diagram.py` (changed: merges meaning into details): the test shows the merged details for Conjunction and Disjunction.
- View `visualizer/class-diagram.html` (changed: meaning section in the panel): the browser run shows it for Conjunction and Disjunction.

Material omissions: none; no new diagram of the pipeline is needed because it gains one script and one data file, described in README text, and the class diagram itself is the view of the model's content.

Source-linked views: README class-diagram section and `docs/standards-metamodel.md` (gets a line naming the annotation file); `docs/where-we-are.html` phase status. Freshness/drift checks: tests regenerate both generated files and fail on any difference. Reconciliation: README, standards-metamodel doc, status page and tests change in the same commit as the code.

## Capability reuse

> **CORE-CAPABILITY-REUSE** (blocking): The plan answers capability reuse against the capability catalogue in agentic-capability-architecture-canonical, which has two files: `reuse_candidates.yml`, whose entries under `candidates:` are cross-project capabilities with their selected off-the-shelf implementations, each named by its `id` (for example `documents_to_text`) and marked candidate or promoted; and `capability_registry.yml`, whose entries under `capabilities:` are the packages that repository holds, each named by its key (for example `approvals`) with the capability ids it `provides` (for example `approval.resolve`). An entry from either file counts. The plan names each catalogue capability the work reuses, by its id, key or provided id; names each new capability the work adds together with its first consumer (the project, command or workflow in this plan that uses it); and, where no entry covers what the work needs, states `No catalogue entry fits, because <reason>`, the reason saying what the work needs that no entry provides. A plan may give more than one of these answers. A plan fails this item if it gives none of them, if it claims reuse without naming the catalogue entry or id reused (reusing code or a contract that is not a catalogue entry does not count), if it adds a capability without naming its first consumer, or if it says no entry fits without a reason.

No catalogue entry fits, because neither `reuse_candidates.yml` nor `capability_registry.yml` in agentic-capability-architecture-canonical lists truth-table evaluation, logical-equivalence checking, or a diagram renderer (searched graph/diagram/layout/viewer on 2026-10-10; the only hit, `graph_application_toolkit`, is document ingestion).

Outside the catalogue it reuses this repository's Phase 1 pipeline and the vendored shared graph viewer (representation-router graph-viewer 0.8.0). The equivalence check is exhaustive enumeration over a few dozen cases in standard-library Python, so no solver dependency is warranted. It adds no new shared capability.

## Authority and non-goals

> **CORE-AUTHORITY-NONGOALS** (blocking): The plan states who holds authority over the work and what it explicitly will not do (non-goals).

Authority: Brian owns the repository (BrianMills2718/fol-operational-metamodel, normal_push) and approved this design on 2026-10-10 ("ok i approve"). The agent merges after local checks per workspace policy.

Non-goals: no other choice of core pieces offered as a toggle; no proofs for infinite worlds (quantifier rebuilds are checked on small worlds and labelled so); no sequence names or other Common Logic extensions beyond first-order; no LATIN2 links; no accepting the ISO licence to fetch the final standard; no change to the shared viewer.

## Irreversible actions and spend

> **CORE-IRREVERSIBLE-SPEND** (blocking): For each irreversible action or spend the plan proposes, it names the boundary, who must authorize it, and how it is contained.

No spend. Pushing to the public GitHub repository is treated as irreversible publication. Boundary: code, docs, the hand-written annotation file and short quoted rule lines from a publicly posted ISO committee draft, with citation; no private data. Authorization: Brian's standing rule (workspace AGENTS.md, 2026-10-07: anything may be public unless it holds private data) plus his 2026-10-10 approval. Containment: gitleaks and an email/phone/key pattern grep over the diff before push; quotes limited to the one-line truth conditions; a bad push is reverted by a follow-up commit and nothing is announced.

## Uncertainties

> **CORE-UNCERTAINTIES** (blocking): The plan lists its material uncertainties, and each one has an owner or the evidence that would resolve it.

- Whether the final ISO text (2007/2018) words or numbers Table 1 differently from the 2005 draft. Resolution would need the licence-gated final text; until then every citation names the draft explicitly. Owner: Brian, if he wants the final text fetched.
- Row numbering E9 (negation), E7/E8 (equation/atomic) is inferred from the label order, because 2-character labels were dropped by text extraction. Resolved by reading the table in a .doc renderer (LibreOffice) if available; otherwise cite as "Table 1, row for <type>". Owner: this session.
- Whether quantifier rebuilds checked on worlds of 1-3 things are convincing to a reader. Owner: Brian, as the reader. Evidence that resolves it: his reaction when he clicks ExistentialQuantification on the delivered page; if he finds it unconvincing, the follow-up is to cite the textbook proof (Enderton, A Mathematical Introduction to Logic, already in references/README.md).

## Activation facts

> **CORE-ACTIVATION-FACTS** (blocking): No activation fact that the plan triggers is declared false. Declaring a fact true when the plan does not strictly need it is acceptable, because it only adds checks; judge only facts declared false. empirical_comparison_proposed is triggered when the plan proposes an A/B test, benchmark, bake-off, or other experiment comparing alternative designs, models, or candidates to choose among them; checking the built result against an expected outcome (an acceptance test, fixture replay, or regression check) is verification and does not trigger it. shared_mechanism is triggered by a new shared mechanism, contract, or algorithm; llm_central by behavior that centrally depends on LLM calls; irreversible_or_spend_action by a proposed irreversible action or spend. claims_external_standard is triggered when the plan claims, or presents its work as, following, implementing or conforming to a standard, schema or contract owned outside the repository being changed (for example a model presented as DM2, or output said to match a published schema); conforming to the repository's own contracts does not trigger it; aes_governed_target when the target repository is governed by an AES target (`.aes/target.yaml`). These two facts are optional: an undeclared one is shown as false and is judged like a declared false.

Declared: shared_mechanism=true (the evaluator in `scripts/cl_meaning.py` is a new algorithm, and `spec/cl-meaning.json` plus the `meaning` field are new contracts between components of this repository; covered by the contracts section and tests); empirical_comparison_proposed=false (checks are acceptance tests); llm_central=false (no LLM calls); irreversible_or_spend_action=true (public push; see Irreversible actions and spend); crosses_system_boundary=true (public push); claims_external_standard=true (the rules are presented as Common Logic's; checked by R1 against the draft text).

## Standard conformance

Standard claimed: ISO/IEC 24707 Common Logic, as published in ISO/IEC FCD 24707 Common Logic, final committee draft dated 2005-12-10, document JTC1/SC32 N1377 (https://www.jtc1sc32.org/doc/N1351-1400/32N1377T-FCD24707_doc, sha256 b9a641f5a4e6dff854cc76f5d20c5693742426275338dff34f3e6dfd85eb3661), clause 6.2 Table 1 rows E9-E15, and clause 6.1 for component counts; and the OMG ODM Common Logic XMI already used in Phase 1. The draft is a Word document with no machine-readable rule set, so the check encodes its written rules: the evaluator in `scripts/cl_meaning.py` implements Table 1 rows for negation, conjunction, disjunction, implication, biconditional, universal and existential quantification literally, and component counts from clause 6.1 ("any number, any number, one, two and two components").

Rules the artifacts must satisfy: each displayed rule quote matches the draft text; each displayed truth table is produced by that evaluator; each rebuild agrees with the evaluator on every case checked.

Check in the merge gate: `tests/test_cl_meaning.py`, run by `python3 -m unittest discover -s tests -v`, the repository's local merge gate. Disproof: an artifact labelled as Common Logic's rule disagrees with the draft or with the evaluator.

Extensions: the plain-language lines, the choice of core pieces (not, and, for every) and the rebuild formulas are this project's annotations, labelled "our note" on the page and stored with `annotation: true`, never presented as part of the standard.

## Contracts and dependencies

Every boundary, with every contract used or changed there (owner; file or URL; changed by this plan?):

1. Public Common Logic draft -> annotation file. Uses: ISO/IEC FCD 24707 draft (owner ISO/IEC JTC1/SC32; https://www.jtc1sc32.org/doc/N1351-1400/32N1377T-FCD24707_doc; not changed). Producer SC32; consumer `spec/cl-meaning.json`.
2. Annotation file + IR -> checker. Uses: `spec/cl-meaning.json` format (owner this repository; file `spec/cl-meaning.json`; created by this plan) and `standards-ir/v1` (owner this repository; `generated/odm-cl-metamodel-ir.json`, defined by `scripts/import_standards.py`; not changed). Producer: the annotation file and the importer; consumer: `scripts/cl_meaning.py`.
3. Checker -> converter. Uses: `spec/cl-meaning.json` (as above) and the checker output `generated/cl-meaning-checks.json` (owner this repository; format defined by `scripts/cl_meaning.py`: per class truth-table rows, rebuild text, cases checked, all-agree flag, counterexamples; created by this plan), plus `standards-ir/v1` (not changed). Producer: `scripts/cl_meaning.py`; consumers: `scripts/cl_class_diagram.py`, `tests/test_cl_meaning.py`.
4. Converter -> page. Uses: `cl-class-diagram/v1` (owner this repository; file `generated/cl-class-diagram.json`, format defined by `scripts/cl_class_diagram.py`; changed: adds a `meaning` field per class) and `typed-graph/v1` (owner representation-router; `~/code/representation-router/schemas/typed-graph.schema.json`; not changed). The page fetches the JSON over HTTP from the same static server. Producer: `scripts/cl_class_diagram.py`; consumer: `visualizer/class-diagram.html`.
5. Page -> shared viewer. Uses: the `GraphViewer.mount` API of graph-viewer 0.8.0 (owner representation-router; `visualizer/vendor/graph-viewer.js`, README in representation-router/graph-viewer; not changed). Producer: representation-router; consumer: the page.
6. Repository -> GitHub. Uses: git remote https://github.com/BrianMills2718/fol-operational-metamodel.git (owner Brian; not changed). Producer: local `main`; consumers: readers of the public repository.

Landing order (producer before consumer), all in one branch merged to `main` by fast-forward so `main` only ever sees the finished set:
1. `spec/cl-meaning.json` (producer of the annotation contract).
2. `scripts/cl_meaning.py`, which reads it, and its output `generated/cl-meaning-checks.json`.
3. `scripts/cl_class_diagram.py` changed to read both, then `generated/cl-class-diagram.json` regenerated with the `meaning` field.
4. `tests/test_cl_meaning.py` and the updated browser check.
5. `visualizer/class-diagram.html`, the consumer, reading the `meaning` field; it ignores a missing field, so an older data file still renders.
6. README, `docs/standards-metamodel.md`, `docs/where-we-are.html`.

## Prior art and ownership

Ownership searched: `project-meta/PROJECT_GRAPH.json` lists this repository (`fol-operational-metamodel`) as the only owner of first-order-logic modelling, and `check_coordination_claims.py --check --project fol-operational-metamodel` returned "No active claims" on 2026-10-10. Prior art searched: this repository's history, the ecosystem project graph (`project-meta/PROJECT_GRAPH.json` one-liners for truth table, propositional, first-order, satisfaction: only this repository matches), and common external tools.

- Internal lineage: `tests/test_model.py` `eval_formula` evaluates formulas of the legacy hand-written `spec/fol.json` on one finite structure. Disposition: bounded exception, not reused, because it is tied to the legacy schema DESIGN.md now marks non-authoritative and does not implement Common Logic's Table 1 rules (n-ary conjunction, the draft's wording). Left unchanged.
- Common Logic draft (ISO/IEC FCD 24707, SC32 N1377): reuse, as the source of every truth rule.
- OMG ODM CL XMI and the Phase 1 pipeline: extend (add the meaning field).
- Shared graph viewer (representation-router graph-viewer 0.8.0): reuse unchanged.
- External search method: the need is "check that two propositional or finite first-order formulas agree on every case"; the standard tool classes for that are computer-algebra logic modules, SMT solvers and SAT solvers, represented by their most used Python packages (SymPy `sympy.logic`, Z3 `z3-solver`, PySAT). Truth-table generators (online calculators) and teaching tools (Tarski's World) cover display, not a reusable check, and are bounded exceptions for the same reason as below. This is the full set of candidate classes considered.
- SymPy logic module, Z3, PySAT (equivalence checking): bounded exception. Every check here is exhaustive enumeration of at most 16 truth-table rows or a few hundred tiny worlds, done in standard-library Python; a solver dependency adds install weight without changing any result, and finite-world quantifier checks are not their domain.
- LATIN2 model-theory formalizations: bounded exception for this phase (they encode semantics inside MMT's logical framework, not as Common Logic's Table 1; linking them is Phase 3's scope).
- Formal Concept Analysis libraries (for example `concepts`): bounded exception, not used; Brian chose the fixed core-pieces design on 2026-10-10, so no hierarchy is computed from attributes.
