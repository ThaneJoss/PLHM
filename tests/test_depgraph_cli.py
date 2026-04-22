from pathlib import Path
import unittest

from plhm.depgraph.cli import build_serve_message


class BuildServeMessageTestCase(unittest.TestCase):
    def test_localhost_message_mentions_port_forwarding(self) -> None:
        message = build_serve_message(Path("/tmp/PLHM"), "127.0.0.1", 8765)

        self.assertIn("Browser URL: http://127.0.0.1:8765", message)
        self.assertIn("does not render a UI in the terminal", message)
        self.assertIn("ssh -L 8765:127.0.0.1:8765 <remote-host>", message)

    def test_non_loopback_message_skips_port_forwarding_hint(self) -> None:
        message = build_serve_message(Path("/tmp/PLHM"), "0.0.0.0", 8765)

        self.assertIn("Browser URL: http://0.0.0.0:8765", message)
        self.assertNotIn("ssh -L", message)


if __name__ == "__main__":
    unittest.main()
