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


if __name__ == "__main__":
    unittest.main()
