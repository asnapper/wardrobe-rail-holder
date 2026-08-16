# README SCAD Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the inaccurate README schematic with a faithful three-quarter assembly image rendered directly from the OpenSCAD model.

**Architecture:** OpenSCAD remains the single geometry source. A reproducible, documented CLI render produces `docs/bracket-render.png`; a focused documentation test validates the PNG header and dimensions, the README reference, and removal of the obsolete SVG.

**Tech Stack:** OpenSCAD 2021.01 CLI, Xvfb/software OpenGL, Python 3 standard-library `unittest`, Markdown.

## Global Constraints

- Render `part="assembly"` from `wardrobe_rail_bracket.scad`.
- Use an orthographic three-quarter view with the reference rail visible.
- Save a 1200 × 900 PNG at `docs/bracket-render.png`.
- Replace the README reference and remove `docs/bracket-arrangement.svg`.
- Do not hand-edit model geometry or the resulting bitmap.

---

### Task 1: Generate and install the faithful README render

**Files:**
- Create: `docs/bracket-render.png`
- Create: `tests/test_readme_render.py`
- Modify: `README.md:7`
- Delete: `docs/bracket-arrangement.svg`

**Interfaces:**
- Consumes: `wardrobe_rail_bracket.scad` with `part="assembly"` and its existing preview-only reference rail.
- Produces: a 1200 × 900 PNG referenced by the README and validated by `tests/test_readme_render.py`.

- [x] **Step 1: Write the failing documentation-asset test**

```python
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
        self.assertIn("![Rendered wardrobe rail bracket](docs/bracket-render.png)", readme)
        self.assertNotIn("docs/bracket-arrangement.svg", readme)
        self.assertFalse(OLD_SVG.exists())

    def test_render_is_a_1200_by_900_png(self):
        data = RENDER.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(data[12:16], b"IHDR")
        self.assertEqual(struct.unpack(">II", data[16:24]), (1200, 900))
```

- [x] **Step 2: Run the focused test to verify it fails**

Run: `python3 -m unittest tests.test_readme_render -v`

Expected: FAIL because `docs/bracket-render.png` does not exist and the README still references `docs/bracket-arrangement.svg`.

- [x] **Step 3: Render the assembly from OpenSCAD**

Run:

```bash
xvfb-run -a env LIBGL_ALWAYS_SOFTWARE=1 openscad \
  --preview \
  --imgsize=1200,900 \
  --projection=o \
  --camera=0,0,-24,110,0,35,250 \
  --autocenter \
  --colorscheme=Tomorrow \
  -D 'part="assembly"' \
  -o docs/bracket-render.png \
  wardrobe_rail_bracket.scad
```

Expected: OpenSCAD exits 0 and writes a 1200 × 900 PNG. Because PNG preview mode sets `$preview`, the translucent reference rail is present.

- [x] **Step 4: Visually inspect the generated image**

Open `docs/bracket-render.png` with the local image viewer. Confirm that the image shows the actual ceiling plate, upper saddle, removable cap, four bracket-bolt lugs, ceiling screw holes, and reference rail without clipping or excessive empty space. If framing is poor, adjust only the camera rotation/distance and rerender at the same output size.

- [x] **Step 5: Update the README and remove the obsolete SVG**

Change the README image line to:

```markdown
![Rendered wardrobe rail bracket](docs/bracket-render.png)
```

Delete `docs/bracket-arrangement.svg` with `apply_patch` after confirming no other tracked file references it.

- [x] **Step 6: Run focused and full verification**

Run:

```bash
python3 -m unittest tests.test_readme_render -v
python3 -m unittest discover -s tests -v
git diff --check
rg -n "bracket-arrangement\.svg|bracket-render\.png" README.md tests
```

Expected: the focused and full suites pass, `git diff --check` is silent, and only the new PNG path appears as an active README asset reference.

- [x] **Step 7: Commit the implementation**

```bash
git add README.md docs/bracket-render.png docs/bracket-arrangement.svg \
  docs/superpowers/plans/2026-08-16-readme-scad-render.md \
  tests/test_readme_render.py
git commit -m "docs: replace bracket schematic with SCAD render"
```
