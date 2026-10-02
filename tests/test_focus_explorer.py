import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class FocusExplorerTests(unittest.TestCase):
    def test_visualizer_exposes_focus_endpoint_and_layout_controls(self):
        html = (ROOT / "visualizer" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="focus"', html)
        self.assertIn('id="endpoint"', html)
        self.assertIn('id="load-focus"', html)
        self.assertIn('id="layout"', html)
        self.assertIn('value="layered"', html)
        self.assertIn('value="force"', html)

    def test_focus_mode_builds_sparql_over_named_graphs(self):
        js = (ROOT / "visualizer" / "app.js").read_text(encoding="utf-8")
        self.assertIn("SELECT DISTINCT ?direction ?predicate ?other ?otherType ?graph", js)
        self.assertIn("GRAPH ?graph", js)
        self.assertIn('decode_uris: "false"', js)
        self.assertIn("normalizeFocusRows(rows, focus)", js)
        self.assertIn('params.get("focus")', js)
        self.assertIn('params.get("endpoint")', js)

    def test_generated_ir_fallback_remains_available(self):
        js = (ROOT / "visualizer" / "app.js").read_text(encoding="utf-8")
        self.assertIn("../generated/pinned-fol-ir.json", js)
        self.assertIn("loadIr(dataFile)", js)

    def test_visualizer_javascript_parses(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed")
        subprocess.run(
            [node, "--check", str(ROOT / "visualizer" / "app.js")],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
