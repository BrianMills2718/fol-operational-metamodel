import json
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class FocusExplorerTests(unittest.TestCase):
    def test_visualizer_exposes_focus_view_layout_and_history_controls(self):
        html = (ROOT / "visualizer" / "index.html").read_text(encoding="utf-8")
        for element_id in [
            "focus",
            "semantic-view",
            "endpoint",
            "load-focus",
            "layout",
            "category",
            "breadcrumbs",
            "back",
            "forward",
        ]:
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn('value="layered"', html)
        self.assertIn('value="force"', html)

    def test_semantic_views_are_data_not_hard_coded_ui_options(self):
        payload = json.loads(
            (ROOT / "visualizer" / "views.json").read_text(encoding="utf-8")
        )
        views = {view["id"]: view for view in payload["views"]}
        self.assertEqual(
            {"all", "structure", "declarations", "dependencies", "morphisms", "provenance"},
            set(views),
        )
        self.assertEqual(views["provenance"]["mode"], "provenance")
        self.assertIn("http://mathhub.info/ulo#include", views["structure"]["predicates"])
        self.assertIn("http://mathhub.info/ulo#uses", views["dependencies"]["predicates"])
        self.assertEqual(
            {
                "http://mathhub.info/ulo#domain",
                "http://mathhub.info/ulo#codomain",
            },
            set(views["morphisms"]["predicates"]),
        )

    def test_focus_mode_builds_view_specific_sparql_over_named_graphs(self):
        js = (ROOT / "visualizer" / "app.js").read_text(encoding="utf-8")
        self.assertIn("queryForView(focus, spec)", js)
        self.assertIn("predicateValues(spec.predicates)", js)
        self.assertIn("GRAPH ?graph", js)
        self.assertIn("provenanceQuery(focus)", js)
        self.assertIn('decode_uris: "false"', js)
        self.assertIn("normalizeFocusRows(rows, focus, spec)", js)
        self.assertIn("normalizeProvenanceRows(rows, focus, spec)", js)

    def test_click_refocus_and_history_preserve_selected_view(self):
        js = (ROOT / "visualizer" / "app.js").read_text(encoding="utf-8")
        self.assertIn("onRefocus(d.uri)", js)
        self.assertIn("focusHistory", js)
        self.assertIn("historyIndex", js)
        self.assertIn("renderBreadcrumbs()", js)
        self.assertIn("selectedView = getView(viewSelect.value)", js)
        self.assertIn('url.searchParams.set("view", viewId)', js)
        self.assertIn("loadLive({pushHistory: false})", js)

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
