import json
import re
import unittest
from pathlib import Path
from scripts.import_mmt import extract, source_sha256

ROOT = Path(__file__).resolve().parents[1]
MODEL = json.loads((ROOT / "spec/fol.json").read_text())
EXAMPLE = json.loads((ROOT / "examples/abc.json").read_text())
COLLECTIONS = MODEL["schema"]["collections"]


def declarations():
    return [item for collection in COLLECTIONS for item in MODEL["model"][collection]]


def term_type(term, example, env):
    sig = example["signature"]
    if "var" in term:
        if term["var"] not in env:
            raise ValueError(f"unbound variable {term['var']}")
        return env[term["var"]][0]
    if "const" in term:
        try:
            return sig["constants"][term["const"]]
        except KeyError as exc:
            raise ValueError(f"unknown constant {term['const']}") from exc
    raise ValueError("unsupported term")


def eval_formula(formula, example, env=None):
    env = dict(env or {})
    structure = example["structure"]
    if "pred" in formula:
        pred = formula["pred"]
        try:
            arg_sorts = example["signature"]["predicates"][pred]["arguments"]
        except KeyError as exc:
            raise ValueError(f"unknown predicate {pred}") from exc
        args = formula["args"]
        if len(args) != len(arg_sorts):
            raise ValueError(f"arity mismatch for {pred}")
        for arg, expected_sort in zip(args, arg_sorts):
            if term_type(arg, example, env) != expected_sort:
                raise ValueError(f"sort mismatch for {pred}")
        values = tuple(structure["constants"][arg["const"]] if "const" in arg else env[arg["var"]][1] for arg in args)
        return values in list(map(tuple, structure["predicates"].get(pred, [])))
    if "not" in formula:
        return not eval_formula(formula["not"], example, env)
    if "and" in formula:
        return all(eval_formula(part, example, env) for part in formula["and"])
    if "or" in formula:
        return any(eval_formula(part, example, env) for part in formula["or"])
    if "implies" in formula:
        left, right = formula["implies"]
        return (not eval_formula(left, example, env)) or eval_formula(right, example, env)
    for quantifier in ("forall", "exists"):
        if quantifier in formula:
            variable, sort = formula[quantifier], formula["sort"]
            domain = structure["domains"][sort]
            values = [eval_formula(formula["body"], example, {**env, variable: (sort, value)}) for value in domain]
            return all(values) if quantifier == "forall" else any(values)
    raise ValueError("unsupported formula")


class ModelTests(unittest.TestCase):
    def test_declarations_have_unique_ids_and_resolvable_references(self):
        items = declarations()
        ids = [item["id"] for item in items]
        self.assertEqual(len(ids), len(set(ids)), "declaration IDs must be globally unique")
        known = set(ids)
        for item in items:
            self.assertRegex(item["id"], MODEL["schema"]["declaration_fields"]["id_pattern"])
            for field in MODEL["schema"]["declaration_fields"]["required"]:
                self.assertIn(field, item, f"{item['id']} lacks {field}")
            self.assertTrue(set(item["references"]) <= known, item["id"])

    def test_typedb_projection_covers_entity_and_relation_names(self):
        schema = (ROOT / "schema/fol.tql").read_text()
        for category in ("entity_types", "relations"):
            for item in MODEL["model"][category]:
                kind = "entity" if category == "entity_types" or item["id"] in {"function-symbol", "predicate-symbol", "sentence"} else "relation"
                self.assertRegex(schema, rf"(?m)^\s*{re.escape(item['id'])} sub {kind},")

    def test_running_example_semantics_and_satisfaction(self):
        for case in EXAMPLE["cases"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(eval_formula(case["formula"], EXAMPLE), case["expected"])

    def test_formation_rejects_arity_and_sort_errors(self):
        bad_predicate = {"pred": "Sibling", "args": [{"const": "A"}, {"const": "A"}, {"const": "B"}]}
        with self.assertRaisesRegex(ValueError, "arity mismatch"):
            eval_formula(bad_predicate, EXAMPLE)
        wrong_sort_example = json.loads(json.dumps(EXAMPLE))
        wrong_sort_example["signature"]["constants"]["A"] = "Place"
        with self.assertRaisesRegex(ValueError, "sort mismatch"):
            eval_formula({"pred": "Sibling", "args": [{"const": "A"}, {"const": "B"}]}, wrong_sort_example)

    def test_finite_structure_does_not_establish_semantic_consequence(self):
        # This structure witnesses that the premise is true and the conclusion
        # false. One countermodel refutes consequence; a finite pass never proves it.
        premise = EXAMPLE["cases"][0]["formula"]
        conclusion = EXAMPLE["cases"][1]["formula"]
        self.assertTrue(eval_formula(premise, EXAMPLE))
        self.assertFalse(eval_formula(conclusion, EXAMPLE))

    def test_mmt_fixture_extracts_stable_uris_kinds_and_locations(self):
        path = ROOT / "tests/fixtures/sfol-mini.mmt"
        source = path.read_text(encoding="utf-8")
        ir = extract(source, "https://example.org/fixture.mmt", path.relative_to(ROOT).as_posix(), source_sha256(source))
        by_name = {item["name"]: item for item in ir["nodes"]}
        self.assertEqual(by_name["FOL"]["kind"], "theory")
        self.assertEqual(by_name["forall"]["kind"], "constant")
        self.assertEqual(by_name["forall"]["uri"], "https://example.org/fol-operational-metamodel/fixture?FOL?forall")
        self.assertEqual(by_name["forall"]["source"]["line"], 6)
        self.assertTrue(any(edge["kind"] == "declares" and edge["target"] == by_name["forall"]["id"] for edge in ir["edges"]))
        self.assertIn("no MMT parsing", ir["scope"])

    def test_fixture_checksum_is_pinned_in_upstream_manifest(self):
        manifest = json.loads((ROOT / "upstream/sources.json").read_text())
        fixture = ROOT / manifest["test_fixture"]["path"]
        self.assertEqual(source_sha256(fixture.read_text(encoding="utf-8")), manifest["test_fixture"]["sha256"])
        self.assertIn("not a byte-for-byte upstream copy", manifest["test_fixture"]["status"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
