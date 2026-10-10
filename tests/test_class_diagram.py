"""The Common Logic class diagram must show exactly the standard's classes and generalizations."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cl_class_diagram  # noqa: E402

IR = ROOT / "generated" / "odm-cl-metamodel-ir.json"
DIAGRAM = ROOT / "generated" / "cl-class-diagram.json"

# (child, parent) generalizations in the OMG ODM 1.1 Common Logic XMI package, listed by name
# so a change in the import or the converter names the pair that moved.
EXPECTED_GENERALIZATIONS = {
    ("CommentedTerm", "Term"), ("Disjunction", "BooleanSentence"), ("Importation", "Phrase"),
    ("BooleanSentence", "Sentence"), ("Biconditional", "BooleanSentence"),
    ("QuantifiedSentence", "Sentence"), ("CommentedSentence", "Sentence"),
    ("ExistentialQuantification", "QuantifiedSentence"), ("Negation", "BooleanSentence"),
    ("Conjunction", "BooleanSentence"), ("SequenceMarker", "Argument"), ("Sentence", "Phrase"),
    ("Module", "Phrase"), ("Comment", "Phrase"), ("Equation", "Atom"),
    ("Implication", "BooleanSentence"), ("UniversalQuantification", "QuantifiedSentence"),
    ("Identifier", "Name"), ("FunctionalTerm", "Term"), ("IrregularSentence", "Sentence"),
    ("Atom", "Sentence"), ("AtomicSentence", "Atom"), ("Term", "Argument"), ("Name", "Term"),
}


class ClassDiagramTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ir = json.loads(IR.read_text())
        cls.diagram = json.loads(DIAGRAM.read_text())
        nodes = {n["id"]: n for n in cls.ir["nodes"]}
        cls.ir_classes = {n["name"] for n in cls.ir["nodes"] if n["kind"] == "uml-class"}
        cls.ir_pairs = {(nodes[e["source"]]["name"], nodes[e["target"]]["name"])
                        for e in cls.ir["edges"] if e["kind"] == "generalizes-to"}

    def test_expected_pairs_are_the_imported_standard(self):
        self.assertEqual(self.ir_pairs, EXPECTED_GENERALIZATIONS,
                         f"missing from IR: {sorted(EXPECTED_GENERALIZATIONS - self.ir_pairs)}; "
                         f"unexpected in IR: {sorted(self.ir_pairs - EXPECTED_GENERALIZATIONS)}")

    def test_diagram_draws_every_generalization_and_no_other_line(self):
        g = self.diagram["graph"]
        drawn = {(e["target"], e["source"]) for e in g["edges"]}  # drawn parent -> child
        self.assertEqual(drawn, EXPECTED_GENERALIZATIONS,
                         f"missing: {sorted(EXPECTED_GENERALIZATIONS - drawn)}; extra: {sorted(drawn - EXPECTED_GENERALIZATIONS)}")
        self.assertEqual(len(g["edges"]), len(drawn), "a generalization is drawn twice")

    def test_diagram_has_every_class_of_the_package(self):
        drawn = {n["id"] for n in self.diagram["graph"]["nodes"]}
        self.assertEqual(drawn, self.ir_classes)
        self.assertEqual(set(self.diagram["details"]), self.ir_classes)

    def test_layout_is_top_down_layered_typed_graph(self):
        g = self.diagram["graph"]
        self.assertEqual(g["schema"], "typed-graph/v1")
        self.assertEqual(g["layout"], {"direction": "DOWN", "algorithm": "layered"})

    def test_quantified_sentence_properties_come_from_the_xmi(self):
        d = self.diagram["details"]["QuantifiedSentence"]
        props = {p["name"]: p for p in d["properties"]}
        self.assertEqual(set(props), {"body", "binding"})
        self.assertEqual((props["body"]["type"], props["body"]["association"]), ("Sentence", "QuantificationForSentence"))
        self.assertEqual((props["binding"]["type"], props["binding"]["multiplicity"], props["binding"]["ordered"],
                          props["binding"]["association"]),
                         ("Binding", "0..*", True, "BindingSequenceForQuantifiedSentence"))
        self.assertTrue(d["abstract"])
        self.assertEqual(d["children"], ["ExistentialQuantification", "UniversalQuantification"])

    def test_checked_in_diagram_matches_a_fresh_generation(self):
        self.assertEqual(cl_class_diagram.build(self.ir), self.diagram,
                         "generated/cl-class-diagram.json is stale: run python3 scripts/cl_class_diagram.py")


if __name__ == "__main__":
    unittest.main()
