from pathlib import Path
import unittest


class DepgraphFrontendImportMapTestCase(unittest.TestCase):
    def test_depgraph_index_uses_compiler_enabled_vue_build(self) -> None:
        index_html = Path("frontend/depgraph/index.html").read_text(encoding="utf-8")

        self.assertIn(
            '"vue": "https://esm.sh/vue@3.5.13/dist/vue.esm-browser.js"',
            index_html,
        )


if __name__ == "__main__":
    unittest.main()
