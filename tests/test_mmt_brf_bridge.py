import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mmt_brf_to_flams_rdf", ROOT / "scripts" / "mmt_brf_to_flams_rdf.py"
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(mod)


class MmtBrfBridgeTests(unittest.TestCase):
    def test_java_helper_is_semantics_free_serialization(self):
        src = mod.JAVA_SOURCE
        self.assertIn("RDFFormat.BINARY", src)
        self.assertIn("NTriplesUtil.toNTriplesString", src)
        self.assertIn("st.getContext()", src)
        self.assertNotIn("mathhub.info/ulo", src)
        self.assertNotIn("replace(", src)

    def test_manifest_declares_no_semantic_mapping_and_context_preservation(self):
        # Guard the architectural contract: this script must remain a
        # serialization bridge, not grow an ontology mapping table.
        source = (ROOT / "scripts" / "mmt_brf_to_flams_rdf.py").read_text()
        self.assertIn('"semantic_mapping": "none"', source)
        self.assertIn('"input_format": "RDF4J Binary RDF"', source)
        self.assertIn('"output_format": "N-Quads"', source)
        self.assertIn('"preserves_named_graph_context": True', source)

    def test_staging_extension_is_nquads_not_fake_flams_layout(self):
        source = (ROOT / "scripts" / "mmt_brf_to_flams_rdf.py").read_text()
        self.assertIn('with_suffix(".nq")', source)
        self.assertNotIn('"index.ttl"', source)


if __name__ == "__main__":
    unittest.main()
