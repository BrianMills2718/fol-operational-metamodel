"""The meaning layer: quoted Common Logic truth rules, computed truth tables, checked core rebuilds."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cl_meaning  # noqa: E402

SPEC = json.loads((ROOT / "spec" / "cl-meaning.json").read_text())
CHECKS = json.loads((ROOT / "generated" / "cl-meaning-checks.json").read_text())
DIAGRAM = json.loads((ROOT / "generated" / "cl-class-diagram.json").read_text())

EXPECTED_ROWS = {
    "Equation": "E6", "AtomicSentence": "E7", "Negation": "E8", "Conjunction": "E9", "Disjunction": "E10",
    "Implication": "E11", "Biconditional": "E12", "UniversalQuantification": "E13", "ExistentialQuantification": "E14",
}


class MeaningTests(unittest.TestCase):
    def test_every_covered_class_quotes_its_draft_row(self):
        self.assertEqual(set(SPEC["classes"]), set(EXPECTED_ROWS))
        for name, row in EXPECTED_ROWS.items():
            rec = SPEC["classes"][name]
            self.assertEqual(rec["row"], f"6.2 Table 1, {row}", name)
            self.assertTrue(rec["quote"] and rec["plain"], name)
        self.assertIn("jtc1sc32.org", SPEC["source"]["url"])
        self.assertIn("draft", SPEC["source"]["caveat"])

    def test_core_is_not_and_for_every(self):
        self.assertEqual(SPEC["core"], ["Negation", "Conjunction", "UniversalQuantification"])
        self.assertEqual({n for n, r in SPEC["classes"].items() if r["role"] == "core"}, set(SPEC["core"]))

    def test_every_rebuild_agrees_with_the_official_rule_on_every_case(self):
        rebuilt = {n: r for n, r in CHECKS["classes"].items() if r["role"] == "rebuilt"}
        self.assertEqual(set(rebuilt), {"Disjunction", "Implication", "Biconditional", "ExistentialQuantification"})
        for name, r in rebuilt.items():
            self.assertTrue(r["agrees"], f"{name}: counterexamples {r['counterexamples']}")
        # 2^0 + 2^1 + 2^2 + 2^3 assignments for 0-3 components; 2+4+8 small worlds.
        self.assertEqual(rebuilt["Disjunction"]["cases"], 15)
        self.assertEqual(rebuilt["ExistentialQuantification"]["cases"], 14)
        self.assertIn("not a proof", rebuilt["ExistentialQuantification"]["scope"])

    def test_checker_catches_a_wrong_rebuild(self):
        wrong = copy.deepcopy(SPEC)
        # "or" rebuilt as plain "and" must be caught.
        wrong["classes"]["Disjunction"]["rebuilt_as"] = {"op": "and_each", "each": "$c"}
        r = cl_meaning.check(wrong)["classes"]["Disjunction"]
        self.assertFalse(r["agrees"])
        self.assertIn(["true", "false"], r["counterexamples"])

    def test_checker_refuses_non_core_operations(self):
        wrong = copy.deepcopy(SPEC)
        wrong["classes"]["Implication"]["rebuilt_as"] = {"op": "or", "args": ["C1", "C2"]}
        with self.assertRaises(ValueError):
            cl_meaning.check(wrong)

    def test_conjunction_and_disjunction_differ_where_brian_looked(self):
        conj = {tuple(r[:2]): r[2] for r in CHECKS["classes"]["Conjunction"]["table"]["rows"]}
        disj = {tuple(r[:2]): r[2] for r in CHECKS["classes"]["Disjunction"]["table"]["rows"]}
        self.assertEqual((conj[("true", "false")], disj[("true", "false")]), ("false", "true"))
        self.assertEqual((conj[("true", "true")], disj[("false", "false")]), ("true", "false"))

    def test_diagram_carries_meaning_marked_as_annotation(self):
        for name in EXPECTED_ROWS:
            m = DIAGRAM["details"][name]["meaning"]
            self.assertTrue(m["annotation"], name)
            self.assertEqual(m["quote"], SPEC["classes"][name]["quote"])
        self.assertEqual(DIAGRAM["details"]["Disjunction"]["meaning"]["rebuilt_as"], "not (not C1 and … and not Cn)")

    def test_checked_in_checks_match_a_fresh_run(self):
        self.assertEqual(cl_meaning.check(SPEC), CHECKS, "run python3 scripts/cl_meaning.py")


if __name__ == "__main__":
    unittest.main()
