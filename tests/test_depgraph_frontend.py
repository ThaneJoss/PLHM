from pathlib import Path
import unittest


class DepgraphFrontendImportMapTestCase(unittest.TestCase):
    def test_depgraph_index_uses_compiler_enabled_vue_build(self) -> None:
        index_html = Path("frontend/depgraph/index.html").read_text(encoding="utf-8")

        self.assertIn(
            '"vue": "https://esm.sh/vue@3.5.13/dist/vue.esm-browser.js"',
            index_html,
        )

    def test_depgraph_canvas_container_is_not_gated_behind_v_else(self) -> None:
        app_js = Path("frontend/depgraph/app.js").read_text(encoding="utf-8")

        self.assertIn('<div ref="canvas" class="canvas"></div>', app_js)
        self.assertNotIn('v-else ref="canvas"', app_js)
        self.assertIn("const container = this.$refs.canvas;", app_js)

    def test_depgraph_app_exposes_optimize_layout_button(self) -> None:
        app_js = Path("frontend/depgraph/app.js").read_text(encoding="utf-8")
        graph_js = Path("frontend/depgraph/graph.js").read_text(encoding="utf-8")

        self.assertIn('@click="optimizeLayout"', app_js)
        self.assertIn("this.graphController?.optimizeLayout(this.filters);", app_js)
        self.assertIn("optimizeLayout(filters) {", graph_js)
        self.assertIn("cy.layout(buildLayoutOptions(filters, true)).run();", graph_js)

    def test_depgraph_app_defaults_to_plhm_view(self) -> None:
        app_js = Path("frontend/depgraph/app.js").read_text(encoding="utf-8")

        self.assertIn('viewMode: "plhm"', app_js)
        self.assertIn('<option value="plhm">PLHM</option>', app_js)

    def test_depgraph_graph_builds_plhm_four_way_design_view(self) -> None:
        graph_js = Path("frontend/depgraph/graph.js").read_text(encoding="utf-8")

        self.assertIn('const PLHM_ROOT = {', graph_js)
        self.assertIn('id: "design:P"', graph_js)
        self.assertIn('id: "design:L"', graph_js)
        self.assertIn('id: "design:H"', graph_js)
        self.assertIn('id: "design:M"', graph_js)
        self.assertIn('return buildPlhmDesignElements(snapshot, filters);', graph_js)
        self.assertIn('name: "preset"', graph_js)


if __name__ == "__main__":
    unittest.main()
