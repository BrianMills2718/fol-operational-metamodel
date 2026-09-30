import json
import unittest
from pathlib import Path

from scripts.import_standards import extract_package

ROOT = Path(__file__).resolve().parents[1]


class StandardsImportTests(unittest.TestCase):
    def test_minimal_xmi_preserves_structure(self):
        path = ROOT / "tests/fixtures/standards-mini.xmi"
        ir = extract_package(path.read_bytes(), "fixture://standards-mini", "Demo")
        by_name = {node["name"]: node for node in ir["nodes"]}
        self.assertEqual(by_name["Expression"]["kind"], "uml-class")
        self.assertEqual(by_name["Term"]["kind"], "uml-class")
        self.assertEqual(by_name["Parts"]["kind"], "uml-association")
        self.assertTrue(any(
            edge["kind"] == "generalizes-to"
            and edge["source"] == by_name["Term"]["id"]
            and edge["target"] == by_name["Expression"]["id"]
            for edge in ir["edges"]
        ))
        self.assertTrue(any(edge["kind"] == "typed-as" for edge in ir["edges"]))
        self.assertTrue(any(edge["kind"] == "member-end" for edge in ir["edges"]))

    def test_normative_odm_common_logic_snapshot_shape(self):
        ir = json.loads((ROOT / "generated/odm-cl-metamodel-ir.json").read_text(encoding="utf-8"))
        classes = {n["name"] for n in ir["nodes"] if n["kind"] == "uml-class"}
        associations = {n["name"] for n in ir["nodes"] if n["kind"] == "uml-association"}
        self.assertEqual(len(classes), 29)
        self.assertEqual(len(associations), 27)
        self.assertTrue({
            "Sentence", "Term", "Name", "AtomicSentence", "QuantifiedSentence",
            "UniversalQuantification", "ExistentialQuantification",
            "FunctionalTerm", "Module", "Text",
        } <= classes)
        self.assertEqual(ir["source"]["package"], "CL")
        self.assertEqual(ir["source"]["input_kind"], "omg-uml-xmi")

    def test_dol_oms_snapshot_is_standards_derived(self):
        ir = json.loads((ROOT / "generated/dol-oms-metamodel-ir.json").read_text(encoding="utf-8"))
        classes = {n["name"] for n in ir["nodes"] if n["kind"] == "uml-class"}
        self.assertIn("OMS", classes)
        self.assertIn("TranslationOMS", classes)
        self.assertIn("ReductionOMS", classes)
        self.assertEqual(ir["source"]["package"], "oms")


if __name__ == "__main__":
    unittest.main()
