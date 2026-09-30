import json
import re
import unittest
from pathlib import Path

from scripts.import_mmt import (
    assemble_archive,
    extract,
    extract_archivegraph,
    extract_omdoc,
    extract_omdoc_directory,
    merge_irs,
    source_download_url,
    source_sha256,
)

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
        values = tuple(
            structure["constants"][arg["const"]] if "const" in arg else env[arg["var"]][1]
            for arg in args
        )
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
            values = [
                eval_formula(formula["body"], example, {**env, variable: (sort, value)})
                for value in domain
            ]
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
                kind = (
                    "entity"
                    if category == "entity_types"
                    or item["id"] in {"function-symbol", "predicate-symbol", "sentence"}
                    else "relation"
                )
                self.assertRegex(schema, rf"(?m)^\s*{re.escape(item['id'])} sub {kind},")

    def test_running_example_semantics_and_satisfaction(self):
        for case in EXAMPLE["cases"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(eval_formula(case["formula"], EXAMPLE), case["expected"])

    def test_formation_rejects_arity_and_sort_errors(self):
        bad_predicate = {
            "pred": "Sibling",
            "args": [{"const": "A"}, {"const": "A"}, {"const": "B"}],
        }
        with self.assertRaisesRegex(ValueError, "arity mismatch"):
            eval_formula(bad_predicate, EXAMPLE)
        wrong_sort_example = json.loads(json.dumps(EXAMPLE))
        wrong_sort_example["signature"]["constants"]["A"] = "Place"
        with self.assertRaisesRegex(ValueError, "sort mismatch"):
            eval_formula(
                {"pred": "Sibling", "args": [{"const": "A"}, {"const": "B"}]},
                wrong_sort_example,
            )

    def test_finite_structure_does_not_establish_semantic_consequence(self):
        premise = EXAMPLE["cases"][0]["formula"]
        conclusion = EXAMPLE["cases"][1]["formula"]
        self.assertTrue(eval_formula(premise, EXAMPLE))
        self.assertFalse(eval_formula(conclusion, EXAMPLE))

    def test_mmt_fixture_extracts_stable_uris_kinds_and_locations(self):
        path = ROOT / "tests/fixtures/sfol-mini.mmt"
        source = path.read_text(encoding="utf-8")
        ir = extract(
            source,
            "https://example.org/fixture.mmt",
            path.relative_to(ROOT).as_posix(),
            source_sha256(source),
        )
        by_name = {item["name"]: item for item in ir["nodes"]}
        self.assertEqual(by_name["FOL"]["kind"], "theory")
        self.assertEqual(by_name["forall"]["kind"], "constant")
        self.assertEqual(
            by_name["forall"]["uri"],
            "https://example.org/fol-operational-metamodel/fixture?FOL?forall",
        )
        self.assertEqual(by_name["forall"]["source"]["line"], 6)
        self.assertTrue(
            any(
                edge["kind"] == "declares" and edge["target"] == by_name["forall"]["id"]
                for edge in ir["edges"]
            )
        )
        self.assertIn("no MMT parsing", ir["scope"])

    def test_omdoc_fixture_extracts_mmt_structure_and_symbol_dependencies(self):
        path = ROOT / "tests/fixtures/fol-compiled.omdoc"
        source = path.read_text(encoding="utf-8")
        ir = extract_omdoc(
            source,
            "https://example.org/fol-compiled.omdoc",
            path.relative_to(ROOT).as_posix(),
            source_sha256(source),
        )
        by_name = {item["name"]: item for item in ir["nodes"]}
        self.assertEqual(ir["format"], "mmt-ir/v2")
        self.assertEqual(ir["source"]["input_kind"], "omdoc")
        self.assertEqual(by_name["FOL"]["kind"], "theory")
        self.assertEqual(by_name["prop"]["kind"], "constant")
        self.assertEqual(by_name["Logic"]["kind"], "include")
        self.assertEqual(
            by_name["prop"]["source"]["source_ref"],
            "http://mydomain.org/testarchive/fol.mmt#108.4.0:122.4.14",
        )
        self.assertTrue(
            any(
                edge["kind"] == "meta-theory"
                and edge["target"] == "http://cds.omdoc.org/urtheories?LF"
                for edge in ir["edges"]
            )
        )
        self.assertTrue(
            any(
                edge["kind"] == "imports"
                and edge["target"] == "http://mydomain.org/testarchive/mmt-example?Logic"
                for edge in ir["edges"]
            )
        )
        self.assertTrue(
            any(
                edge["kind"] == "uses-symbol"
                and edge["source"].endswith("?prop")
                and edge["target"] == "http://cds.omdoc.org/urtheories?Typed?type"
                for edge in ir["edges"]
            )
        )

    def test_fixture_checksums_are_pinned_in_upstream_manifest(self):
        manifest = json.loads((ROOT / "upstream/sources.json").read_text())
        fixture = ROOT / manifest["test_fixture"]["path"]
        self.assertEqual(
            source_sha256(fixture.read_text(encoding="utf-8")),
            manifest["test_fixture"]["sha256"],
        )
        omdoc_fixture = ROOT / manifest["omdoc_test_fixture"]["path"]
        self.assertEqual(
            source_sha256(omdoc_fixture.read_text(encoding="utf-8")),
            manifest["omdoc_test_fixture"]["sha256"],
        )

    def test_upstream_manifest_pins_real_mmt_and_latin_revisions(self):
        manifest = json.loads((ROOT / "upstream/sources.json").read_text())
        by_id = {item["id"]: item for item in manifest["sources"]}
        compiled = by_id["mmt-compiled-fol-omdoc"]
        self.assertEqual(
            compiled["revision"],
            "fca5d7e12db5b4e9d6329590f9d25380017981d8",
        )
        self.assertEqual(
            compiled["git_blob_sha"],
            "76ccd4bc3968272d2e16d4fc51d8950c6b28fbe7",
        )
        self.assertIn(
            "raw.githubusercontent.com/UniFormal/MMT/",
            source_download_url(compiled),
        )
        self.assertEqual(
            by_id["mmt-latin2"]["revision"],
            "39dc7046f457ff02f695387a8ebd80366789a465",
        )


    def test_archivegraph_fixture_preserves_mmt_graph_styles(self):
        path = ROOT / "tests/fixtures/archivegraph.json"
        source = path.read_text(encoding="utf-8")
        ir = extract_archivegraph(
            source,
            "http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2",
            path.relative_to(ROOT).as_posix(),
            source_sha256(source),
        )
        by_name = {item["name"]: item for item in ir["nodes"]}
        self.assertEqual(ir["source"]["input_kind"], "archivegraph")
        self.assertEqual(by_name["FOL"]["kind"], "theory")
        self.assertEqual(by_name["FOLEQ"]["archivegraph_style"], "theory")
        self.assertTrue(
            any(
                edge["kind"] == "include"
                and edge["source"].endswith("?FOL")
                and edge["target"].endswith("?FOLEQ")
                for edge in ir["edges"]
            )
        )
        self.assertTrue(any(edge["kind"] == "view" and edge["label"] == "fol-to-foleq" for edge in ir["edges"]))

    def test_merge_prefers_omdoc_detail_for_shared_theory_uri(self):
        omdoc_path = ROOT / "tests/fixtures/fol-compiled.omdoc"
        omdoc_text = omdoc_path.read_text(encoding="utf-8")
        omdoc_ir = extract_omdoc(
            omdoc_text,
            "https://example.org/fol-compiled.omdoc",
            omdoc_path.relative_to(ROOT).as_posix(),
            source_sha256(omdoc_text),
        )
        archive_path = ROOT / "tests/fixtures/archivegraph.json"
        archive_text = archive_path.read_text(encoding="utf-8")
        archive_ir = extract_archivegraph(
            archive_text,
            "http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2",
            archive_path.relative_to(ROOT).as_posix(),
            source_sha256(archive_text),
        )
        merged = merge_irs([archive_ir, omdoc_ir])
        ids = [item["id"] for item in merged["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))
        fol = next(item for item in merged["nodes"] if item["id"] == "http://mydomain.org/testarchive/mmt-example?FOL")
        self.assertEqual(fol["kind"], "theory")
        self.assertEqual(fol["source"]["source_ref"], "http://mydomain.org/testarchive/fol.mmt#57.2.0:746.27.1")
        self.assertIn("provenance", fol)
        self.assertTrue(any(edge["kind"] == "declares" and edge["source"] == fol["id"] for edge in merged["edges"]))
        self.assertTrue(any(edge["kind"] == "view" for edge in merged["edges"]))


    def test_omdoc_directory_imports_every_module_recursively(self):
        directory = ROOT / "tests/fixtures/omdoc-archive"
        ir = extract_omdoc_directory(directory, "mmt://fixture-content")
        by_id = {item["id"]: item for item in ir["nodes"]}
        self.assertEqual(ir["source"]["input_kind"], "omdoc-directory")
        self.assertEqual(len(ir["source"]["files"]), 2)
        fol_id = "http://mydomain.org/testarchive/mmt-example?FOL"
        foleq_id = "http://mydomain.org/testarchive/mmt-example?FOLEQ"
        equal_id = "http://mydomain.org/testarchive/mmt-example?FOLEQ?equal"
        self.assertEqual(by_id[fol_id]["kind"], "theory")
        self.assertEqual(by_id[foleq_id]["kind"], "theory")
        self.assertEqual(by_id[equal_id]["role"], "Eq")
        self.assertTrue(
            any(
                edge["kind"] == "imports"
                and edge["source"].startswith("http://mydomain.org/testarchive/mmt-example?FOLEQ?@import-")
                and edge["target"] == "http://mydomain.org/testarchive/mmt-example?FOL"
                for edge in ir["edges"]
            )
        )

    def test_assemble_combines_archivegraph_and_whole_content_directory(self):
        archive_path = ROOT / "tests/fixtures/archivegraph.json"
        archive_text = archive_path.read_text(encoding="utf-8")
        ir = assemble_archive(
            archive_text,
            "http://localhost:8080/:jgraph/json?key=archivegraph&uri=MMT/LATIN2",
            archive_path.relative_to(ROOT).as_posix(),
            source_sha256(archive_text),
            ROOT / "tests/fixtures/omdoc-archive",
            "mmt://fixture-content",
        )
        self.assertEqual(ir["source"]["input_kind"], "assembled-archive")
        ids = [item["id"] for item in ir["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))
        fol = next(item for item in ir["nodes"] if item["id"] == "http://mydomain.org/testarchive/mmt-example?FOL")
        foleq = next(item for item in ir["nodes"] if item["id"] == "http://mydomain.org/testarchive/mmt-example?FOLEQ")
        self.assertEqual(fol["kind"], "theory")
        self.assertEqual(foleq["kind"], "theory")
        self.assertTrue(any(edge["kind"] == "include" for edge in ir["edges"]))
        self.assertTrue(any(edge["kind"] == "declares" and edge["source"] == foleq["id"] for edge in ir["edges"]))

    def test_latin2_inventory_records_confirmed_fol_paths_at_pinned_revision(self):
        inventory = json.loads((ROOT / "upstream/latin2-fol-inventory.json").read_text())
        self.assertEqual(
            inventory["revision"],
            "39dc7046f457ff02f695387a8ebd80366789a465",
        )
        paths = {item["path"] for item in inventory["confirmed_paths"]}
        self.assertEqual(
            paths,
            {
                "source/logic/fol_like/fol.mmt",
                "source/logic/fol_like/fol_derived.mmt",
                "source/fundamentals/equality.mmt",
            },
        )
        self.assertIn("SFOLEQ", inventory["observed_theories"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
