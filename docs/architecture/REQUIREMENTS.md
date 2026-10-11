---
description: Numbered requirements of the FOL metamodel repository, each with the observable success criterion and the condition that would disprove it
---

# Requirements

Drawn from the behaviour the code and tests already enforce (`README.md`,
`DESIGN.md`, `docs/goals/fol-class-diagram.md`, `docs/plans/fol-meaning-layer.md`).
Rule IDs refer to [trace.yaml](../model/trace.yaml).

## REQ-STANDARDS-IMPORT: standards metamodels are imported verbatim

The OMG ODM Common Logic package and the DOL `oms` package are read from their
normative XMI into graph IR without adding categories inferred from names
(RULE-STANDARDS-VERBATIM).

Success: `generated/odm-cl-metamodel-ir.json` contains the 29 UML classes of the CL
package, including `Sentence`, `QuantifiedSentence` and `UniversalQuantification`,
and `tests/test_standards.py` passes on a fresh run.

Disproof: an element in the IR has no counterpart `xmi:id` in the source XMI, or a
class of the package is missing from the IR.

## REQ-MMT-PINNED: the formal corpus is pinned and verified

Every downloaded MMT artifact is checked against the SHA-256 or Git blob hash
pinned in `upstream/sources.json` before it is imported, and the importer keeps
only explicit structure (RULE-MMT-PINNED, RULE-MMT-EXPLICIT-ONLY).

Success: `tests/test_model.py::ModelTests::test_pinned_real_fol_snapshot_matches_upstream_artifact`
passes, and `scripts/import_mmt.py fetch` raises on a hash mismatch.

Disproof: `generated/pinned-fol-ir.json` records a hash other than the pinned
artifact's, or a node kind appears that no OMDoc element or relational predicate
supplied.

## REQ-CLASS-DIAGRAM: the class diagram is generated from the standard

`visualizer/class-diagram.html` draws the Common Logic classes top-down with one
line per UML generalization and nothing else, and shows each class's properties
and associations on click (RULE-DIAGRAM-GENERATED).

Success: `tests/test_class_diagram.py` passes (every expected generalization pair
present by membership, no extra line, checked-in diagram equals a fresh
generation), and `npm run e2e -- http://127.0.0.1:8000` prints
`RESULT passed=N failed=0`.

Disproof: a generalization in the XMI has no line on the page, a line appears with
no generalization behind it, or the checked-in `generated/cl-class-diagram.json`
differs from running `scripts/cl_class_diagram.py`.

## REQ-MEANING-CHECKED: truth rules are quoted and every rebuild is checked

Each connective and quantifier shows its truth rule quoted from the public Common
Logic draft (ISO/IEC FCD 24707, clause 6.2 Table 1) with its row cited, a computed
truth table, and either "core piece" (not, and, for every) or a rebuild from the
core pieces that the program has checked (RULE-MEANING-CHECKED,
RULE-ANNOTATION-MARKED).

Success: `scripts/cl_meaning.py` reports every rebuild agreeing on every true/false
combination for 0-3 components and every world of 1-3 things, and
`tests/test_cl_meaning.py` passes, including the seeded wrong rebuild being caught.

Disproof: a rebuild disagrees with the quoted rule on some case, a rebuild uses an
operation other than the three core pieces, or a meaning record on the diagram is
not marked as annotation.
