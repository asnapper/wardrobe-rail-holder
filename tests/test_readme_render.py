import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
RENDER = ROOT / "docs" / "bracket-render.png"
OLD_SVG = ROOT / "docs" / "bracket-arrangement.svg"


class ReadmeRenderTests(unittest.TestCase):
    def test_readme_uses_current_scad_render(self):
        readme = README.read_text(encoding="utf-8")
        self.assertIn(
            "![Rendered wardrobe rail bracket](docs/bracket-render.png)", readme
        )
        self.assertNotIn("docs/bracket-arrangement.svg", readme)
        self.assertFalse(OLD_SVG.exists())

    def test_render_is_a_1200_by_900_png(self):
        data = RENDER.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(struct.unpack(">II", data[16:24]), (1200, 900))


if __name__ == "__main__":
    unittest.main(verbosity=2)
