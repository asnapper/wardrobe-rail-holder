# 6 mm Nut Clearance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Increase the default captive-nut pocket from 5.3 mm to 6.3 mm so a 6 mm-high M6 nut fits with the existing 0.3 mm nominal print clearance, and refresh every published artifact derived from that geometry.

**Architecture:** `wardrobe_rail_bracket.scad` remains the authoritative geometry source. A real-geometry OpenSCAD intersection probe specifies the required nut fit, existing derived dimensions propagate the 1 mm increase through the lug and boss, and the established build scripts regenerate and validate neutral, rendered, and sliced releases.

**Tech Stack:** OpenSCAD, Python 3 `unittest`, POSIX shell build scripts, OrcaSlicer 2.4.2, Xvfb, STL/3MF/PNG release artifacts.

## Global Constraints

- Default nut hardware is 10 mm nominal across flats and 6 mm high.
- Preserve `nut_clearance = 0.3`, producing `nut_pocket_height = 6.3` mm.
- Preserve the pocket bottom, 2.5 mm bearing floor, 6 mm roof, loading direction, bolt axis, M6 x 12 mm button-head screws, and rail geometry.
- Recalibrate `minimum_bolt_projection` from 0.8 mm to 0 mm: the 12 mm bolt must reach the full 6.3 mm pocket, with nominal geometry extending 0.1 mm beyond the pocket and 0.4 mm beyond a seated 6 mm nut.
- Do not claim physical fit or load validation; the revised part remains unprinted and unverified.
- Regenerate all five neutral model releases, the 1200 x 900 README render, and the two-bracket P1S sliced project.
- Keep the existing external mesh-envelope contracts unless regenerated geometry proves an actual outer-bound change.

## File Map

- `wardrobe_rail_bracket.scad`: authoritative hardware parameter and derived pocket/lug geometry.
- `tests/test_scad_model.py`: real-geometry bolt and nut fit regression test.
- `README.md`: hardware contract and measured OrcaSlicer release estimates.
- `dist/models/*`: five regenerated neutral STL/3MF model releases.
- `docs/bracket-render.png`: regenerated assembly image.
- `dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf`: regenerated two-bracket P1S project.
- `tests/test_3mf_project.py`: plausibility contract for the regenerated sliced project's measured weight and time.

---

### Task 1: Specify and implement the 6.3 mm captive-nut pocket

**Files:**
- Modify: `tests/test_scad_model.py:240-267`
- Modify: `wardrobe_rail_bracket.scad:44-46`
- Modify: `README.md:9-13`

**Interfaces:**
- Consumes: `OpenScadRenderTests.render(output_mode, *definitions)` and `assert_probe_does_not_intersect(model_output, probe_body, message)`.
- Produces: default `clamp_nut_thickness = 6`, derived `nut_pocket_height = 6.3`, `minimum_bolt_projection = 0`, and a hardware-fit regression using a 5.96 mm geometric probe inset 0.02 mm from the nominal 6 mm faces to avoid coincident-surface ambiguity.

- [ ] **Step 1: Change the regression probe to represent a 6 mm-high nut**

In both nut solids inside `test_m6_button_head_bolt_and_standard_nut_fit_the_voids`, change only the heights from `4.96` to `5.96`:

```python
f" translate([{bolt_x}, 0, -27.48]) cylinder(h=5.96, r=10/sqrt(3), $fn=6);"
f" translate([{bolt_x - 10 / 3 ** 0.5}, -12.98, -27.48])"
f" cube([{20 / 3 ** 0.5}, 12.96, 5.96]);"
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python3 -m unittest tests.test_scad_model.OpenScadRenderTests.test_m6_button_head_bolt_and_standard_nut_fit_the_voids -v
```

Expected: FAIL for the standard-hex-nut subtests with `standard M6 nut cannot occupy or enter the captive pocket`, proving the current 5.3 mm pocket rejects the 6 mm nut probe.

- [ ] **Step 3: Make the minimal authoritative model change**

Change the public hardware dimension without changing the clearance formula:

```scad
clamp_nut_across_flats = 10;
clamp_nut_thickness = 6;
nut_clearance = 0.3;
minimum_bolt_projection = 0;
```

Leave these derived expressions and the full-pocket bolt-length assertion
unchanged:

```scad
nut_pocket_height = clamp_nut_thickness + nut_clearance;
assert(
    bolt_tip_z - nut_pocket_top_z >= minimum_bolt_projection,
    "clamp bolt is too short to engage the captive nut"
);
```

- [ ] **Step 4: Update the documented hardware contract**

Change the README hardware bullet to:

```markdown
- 2 × standard M6 hex nuts (10 mm nominal across flats, 6 mm thick)
```

- [ ] **Step 5: Run the focused test and SCAD regression suite to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_scad_model.OpenScadRenderTests.test_m6_button_head_bolt_and_standard_nut_fit_the_voids -v
python3 -m unittest tests.test_scad_model -v
```

Expected: the focused test passes for both nut pockets and all `test_scad_model` tests pass, including bolt engagement, support, topology, and envelope checks.

- [ ] **Step 6: Commit the tested source contract**

```bash
git add wardrobe_rail_bracket.scad tests/test_scad_model.py README.md
git commit -m "fix: fit 6 mm captive nuts"
```

---

### Task 2: Regenerate neutral models and the README render

**Files:**
- Modify: `dist/models/wardrobe_rail_bracket_main.stl`
- Modify: `dist/models/wardrobe_rail_bracket_cap.stl`
- Modify: `dist/models/wardrobe_rail_bracket_main.3mf`
- Modify: `dist/models/wardrobe_rail_bracket_cap.3mf`
- Modify: `dist/models/wardrobe_rail_bracket_complete.3mf`
- Modify: `docs/bracket-render.png`

**Interfaces:**
- Consumes: the default SCAD output modes `main_print`, `cap_print`, `print`, and `assembly`; `scripts/validate_release.py models DIRECTORY`.
- Produces: current neutral release geometry and a 1200 x 900 assembly PNG generated from the 6.3 mm-pocket source.

- [ ] **Step 1: Regenerate and validate all neutral model releases**

Run:

```bash
./scripts/build-models.sh
python3 scripts/validate_release.py models dist/models
```

Expected: both commands exit 0. The main, cap, and complete artifacts retain their existing 63.5 x 75.0 x 30.0, 63.5 x 24.0 x 15.7, and 133.5 x 75.0 x 30.0 envelope contracts respectively.

- [ ] **Step 2: Regenerate the README render from the changed source**

Run:

```bash
./scripts/build-render.sh
```

Expected: exit 0 and `docs/bracket-render.png` is replaced by a nonempty 1200 x 900 PNG.

- [ ] **Step 3: Verify the release builders and render contract**

Run:

```bash
python3 -m unittest tests.test_release_scripts tests.test_readme_render -v
```

Expected: all tests pass, including model topology, geometry-only 3MF contents, atomic publication behavior, and PNG dimensions.

- [ ] **Step 4: Review and commit generated neutral assets**

Run `git status --short` and confirm changes are limited to expected regenerated files. Git may omit byte-identical cap or render outputs; their successful build commands are the evidence that they were regenerated.

```bash
git add dist/models docs/bracket-render.png
git commit -m "build: refresh 6 mm nut model assets"
```

---

### Task 3: Regenerate the sliced P1S project and synchronize measured metadata

**Files:**
- Modify: `dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf`
- Modify: `README.md:30-35`
- Modify if measured estimates leave the current accepted ranges: `tests/test_3mf_project.py:109-128`

**Interfaces:**
- Consumes: current main/cap SCAD geometry, versioned P1S/PLA/strength profiles, and `scripts/validate_release.py p1s ARCHIVE`.
- Produces: a four-object sliced project with two main bodies, two caps, 150 support-free layers, valid embedded G-code checksum, and README/test estimates matching the regenerated archive.

- [ ] **Step 1: Regenerate and validate the P1S project**

Run:

```bash
./scripts/build-p1s.sh
python3 scripts/validate_release.py p1s dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf
```

Expected: both commands exit 0; validation confirms two main and two cap objects, correct 63.5 mm object widths, 150 support-free layers, expected profiles, and a matching embedded checksum.

- [ ] **Step 2: Read the regenerated weight and time from the archive**

Run:

```bash
python3 -c 'import zipfile,xml.etree.ElementTree as E; p="dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf"; z=zipfile.ZipFile(p); r=E.fromstring(z.read("Metadata/slice_info.config")); m={e.attrib.get("key"):e.attrib.get("value") for e in r.findall("./plate/metadata")}; print("weight_g="+m["weight"], "prediction_s="+m["prediction"])'
```

Expected: one `weight_g` value and one `prediction_s` value from OrcaSlicer. Convert seconds to rounded hours/minutes using integer division for the README parenthetical.

- [ ] **Step 3: Verify whether the old plausibility contract detects the changed sliced output**

Run:

```bash
python3 -m unittest tests.test_3mf_project.OrcaProjectTests.test_slice_is_support_free_and_has_plausible_estimates -v
```

Expected: either PASS if the reduced-material project remains inside both existing narrow ranges, or FAIL specifically on the weight/time range whose regenerated value moved outside it. Do not alter support, outside-bed, layer-count, or support-toolpath assertions.

- [ ] **Step 4: Synchronize README measurements and, only when needed, plausibility bounds**

Replace the README's `133.09 g`, `17,452 s`, and rounded duration with the values printed in Step 2, retaining `150 layers`.

If a Step 3 bound failed, replace only that pair of bounds with a narrow deterministic interval around the measured result:

- Weight: the immediately enclosing 0.2 g interval on one-decimal boundaries; for example, a measured 132.67 g uses `> 132.6` and `< 132.8`.
- Time: the immediately enclosing 100-second interval; for example, 17,389 s uses `> 17_300` and `< 17_400`.

This keeps the test independent of README formatting while allowing small deterministic slicer variation.

- [ ] **Step 5: Verify the sliced project and its documentation**

Run:

```bash
python3 -m unittest tests.test_3mf_project -v
python3 scripts/validate_release.py p1s dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf
```

Expected: all project tests pass and the release validator exits 0.

- [ ] **Step 6: Commit the regenerated sliced release and synchronized metadata**

```bash
git add dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf README.md tests/test_3mf_project.py
git commit -m "build: refresh 6 mm nut P1S project"
```

---

### Task 4: Full repository verification

**Files:**
- Verify only; modify a scoped source, test, documentation, or artifact file only if its corresponding verification exposes a requirement mismatch.

**Interfaces:**
- Consumes: all source, tests, generated artifacts, and validators updated in Tasks 1-3.
- Produces: fresh evidence that the repository is internally consistent and releasable.

- [ ] **Step 1: Run the complete automated test suite**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: all discovered tests pass with zero failures and zero errors.

- [ ] **Step 2: Re-run both release validators directly**

Run:

```bash
python3 scripts/validate_release.py models dist/models
python3 scripts/validate_release.py p1s dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf
```

Expected: both commands exit 0 without diagnostics.

- [ ] **Step 3: Check patch hygiene and scope**

Run:

```bash
git diff --check HEAD~3..HEAD
git status --short
```

Expected: no whitespace errors and no uncommitted changes. Review `git show --stat --oneline HEAD~3..HEAD` to confirm the implementation touched only the files listed in this plan.
