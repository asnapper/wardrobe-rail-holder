# Reproducible Release Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace obsolete pre-M6 model files with current portable STL/3MF releases and add a headless, reproducible OpenSCAD/OrcaSlicer build pipeline for every published artifact.

**Architecture:** OpenSCAD exports neutral geometry directly from the SCAD output modes. Focused POSIX shell scripts share dependency discovery and atomic-install helpers; OrcaSlicer 2.4+ consumes committed flattened P1S profiles only for the sliced two-bracket release. Tests run the real model exporter, inspect generated archives and meshes, and exercise dependency failures at process boundaries.

**Tech Stack:** OpenSCAD 2021.01+, POSIX shell, OrcaSlicer 2.4+, Python 3 standard-library `unittest`, STL parsing, XML, and ZIP inspection; optional Xvfb.

## Global Constraints

- Work directly on `master`, preserving unrelated user changes.
- `wardrobe_rail_bracket.scad` remains the authoritative geometry source.
- Mandatory model and slicing outputs must not require X11, Wayland, Xvfb, or OpenGL.
- Image generation may use Xvfb but must be optional in the aggregate build.
- Model files under `dist/models/` are geometry-only and contain no slicer settings or G-code.
- The P1S release contains two mains and two caps with 0.20 mm layers, 5 walls, 6 top/bottom layers, 40% gyroid, supports disabled, 5 mm outer brim, 0.1 mm brim gap, by-layer printing, 120 mm/s outer walls, and 200 mm/s inner walls/infill.
- Missing dependencies must name the executable, exit nonzero when required, preserve prior outputs, and provide an official installation link.
- Delete both obsolete root artifacts: tracked `wardrobe_rail_bracket.3mf` and ignored `wardrobe_rail_bracket.stl`.
- Do not claim that the M6 revision has been physically tested.

---

### Task 1: Neutral model export contract

**Files:**
- Create: `tests/test_release_scripts.py`
- Create: `scripts/lib/common.sh`
- Create: `scripts/build-models.sh`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: SCAD modes `main_print`, `cap_print`, and `print`.
- Produces: `scripts/build-models.sh [--output-dir DIR]` and helper functions `find_required_tool`, `new_build_dir`, `require_nonempty`, and `atomic_install`.

- [ ] **Step 1: Write failing integration tests for portable exports**

Add `ReleaseModelBuildTests` that runs `scripts/build-models.sh --output-dir <temp>`, expects the five literal filenames from the spec, parses the real STL and 3MF vertices, and asserts these hand-derived envelopes:

```python
EXPECTED = {
    "wardrobe_rail_bracket_main.stl": ((63.5, 75.0, 30.0), 1),
    "wardrobe_rail_bracket_cap.stl": ((63.5, 24.0, 15.7), 1),
    "wardrobe_rail_bracket_main.3mf": ((63.5, 75.0, 30.0), 1),
    "wardrobe_rail_bracket_cap.3mf": ((63.5, 24.0, 15.7), 1),
}
```

The 75 mm Y extent is the full ceiling plate; 24 mm is only the clamp depth.

For `wardrobe_rail_bracket_complete.3mf`, assert two disconnected printable volumes, nonnegative Z, no path ending in `.gcode`, and absence of `Metadata/project_settings.config`, `Metadata/model_settings.config`, and `Metadata/slice_info.config`.

- [ ] **Step 2: Run the model-script tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_release_scripts.ReleaseModelBuildTests -v
```

Expected: FAIL because `scripts/build-models.sh` does not exist.

- [ ] **Step 3: Write failing dependency and atomicity tests**

Run the missing script with `OPENSCAD_BIN=/definitely/missing/openscad` and a temporary output directory containing a sentinel file. Assert nonzero status, stderr containing `OpenSCAD` and `https://openscad.org/downloads.html`, the sentinel unchanged, and no release filenames created.

- [ ] **Step 4: Implement common helpers and the neutral exporter**

Implement executable resolution without `eval`:

```sh
find_required_tool() {
    override=$1 label=$2 url=$3
    shift 3
    if [ -n "$override" ]; then
        [ -x "$override" ] || die "$label executable not found: $override\nInstall: $url"
        printf '%s\n' "$override"
        return
    fi
    for candidate do
        if command -v "$candidate" >/dev/null 2>&1; then
            command -v "$candidate"
            return
        fi
    done
    die "$label is required but was not found. Install: $url"
}
```

`build-models.sh` resolves the repository root from its own path, accepts only `--output-dir DIR`, exports each requested SCAD mode into a private `mktemp -d` directory, checks every file is nonempty, then installs all five outputs only after all exports succeed. Use OpenSCAD itself for both STL and 3MF; do not route clean 3MF through a slicer.

- [ ] **Step 5: Allow deliberate release STLs and run GREEN**

Keep `*.stl` ignored and add:

```gitignore
!dist/models/
!dist/models/*.stl
```

Make scripts executable, rerun the focused tests, and expect PASS.

- [ ] **Step 6: Commit the neutral pipeline**

```bash
git add .gitignore scripts/lib/common.sh scripts/build-models.sh tests/test_release_scripts.py
git commit -m "build: add portable model export pipeline"
```

### Task 2: Current model artifacts and stale-file removal

**Files:**
- Modify: `tests/test_release_scripts.py`
- Create: `dist/models/wardrobe_rail_bracket_main.stl`
- Create: `dist/models/wardrobe_rail_bracket_cap.stl`
- Create: `dist/models/wardrobe_rail_bracket_main.3mf`
- Create: `dist/models/wardrobe_rail_bracket_cap.3mf`
- Create: `dist/models/wardrobe_rail_bracket_complete.3mf`
- Delete: `wardrobe_rail_bracket.3mf`
- Delete: `wardrobe_rail_bracket.stl`

**Interfaces:**
- Consumes: `scripts/build-models.sh` from Task 1.
- Produces: the clean, current M6 release set and the repository invariant that no root model artifact exists.

- [ ] **Step 1: Add a failing repository-hygiene test**

Add a test that asserts both exact root paths are absent. Name the break it catches: an obsolete or manually exported root file can be mistaken for the current M6 release.

- [ ] **Step 2: Verify RED against the two existing root artifacts**

Run the hygiene test and expect it to fail for both `wardrobe_rail_bracket.3mf` and `wardrobe_rail_bracket.stl`.

- [ ] **Step 3: Remove only the resolved obsolete targets**

Delete the two exact root files. Do not use a glob and do not remove anything under `dist/`.

- [ ] **Step 4: Generate and verify current portable releases**

Run:

```bash
scripts/build-models.sh
python3 -m unittest tests.test_release_scripts -v
```

Expected: all release-script tests PASS.

- [ ] **Step 5: Commit the artifact replacement**

```bash
git add -A wardrobe_rail_bracket.3mf dist/models
git add -f dist/models/*.stl
git commit -m "build: publish current M6 model files"
```

### Task 3: Versioned Orca P1S profiles and sliced build

**Files:**
- Create: `profiles/orca/p1s-0.4-machine.json`
- Create: `profiles/orca/pla-basic.json`
- Create: `profiles/orca/bracket-strength.json`
- Create: `scripts/build-p1s.sh`
- Modify: `scripts/lib/common.sh`
- Modify: `tests/test_release_scripts.py`
- Modify: `tests/test_3mf_project.py`

**Interfaces:**
- Consumes: OpenSCAD, OrcaSlicer CLI 2.4+, the SCAD `main_print` and `cap_print` modes, and the three flattened profile JSON files.
- Produces: `scripts/build-p1s.sh [--output FILE]` and a validated two-bracket `.gcode.3mf`.

- [ ] **Step 1: Write failing Orca dependency tests**

Invoke `build-p1s.sh --output <temp>/release.gcode.3mf` with `ORCASLICER_BIN=/definitely/missing/orca`. Assert nonzero status, `OrcaSlicer`, `https://github.com/OrcaSlicer/OrcaSlicer/releases`, no output, and an existing sentinel output remains byte-identical.

- [ ] **Step 2: Verify RED because the P1S script is absent**

Run the focused dependency test and confirm the expected missing-script failure.

- [ ] **Step 3: Commit flattened profile inputs**

Use the official OrcaSlicer 2.4.2 release profiles named `Bambu Lab P1S 0.4 nozzle`, `Bambu PLA Basic @BBL X1C`, and `0.20mm Standard @BBL X1C` as the source presets. Export their resolved CLI settings with OrcaSlicer rather than copying a user's preset directory. Split the resulting inputs into the committed machine and filament JSON files, then apply this literal process overlay in `bracket-strength.json`:

```json
{
  "layer_height": "0.2",
  "wall_loops": "5",
  "top_shell_layers": "6",
  "bottom_shell_layers": "6",
  "sparse_infill_density": "40%",
  "sparse_infill_pattern": "gyroid",
  "enable_support": "0",
  "brim_type": "outer_only",
  "brim_width": "5",
  "brim_object_gap": "0.1",
  "print_sequence": "by layer",
  "outer_wall_speed": "120",
  "inner_wall_speed": "200",
  "sparse_infill_speed": "200"
}
```

Validate the JSON with `python3 -m json.tool` and confirm the machine profile identifies `Bambu Lab P1S 0.4 nozzle` and the filament identifies Bambu PLA Basic.

- [ ] **Step 4: Implement version checking and atomic P1S generation**

Add `version_at_least 2 4 <detected>` to the shared helpers. Implement `build-p1s.sh` so it:

1. parses only `--output FILE`;
2. resolves OpenSCAD and OrcaSlicer, honoring environment overrides;
3. rejects OrcaSlicer versions before 2.4 with the official release URL;
4. exports two fresh STL source files into a private build directory;
5. supplies each STL twice to OrcaSlicer, loads the committed settings and filament JSON, arranges and ensures them on the bed, slices plate 0, exports slice data and `.gcode.3mf`;
6. checks the Orca exit code, nonempty archive, and `result.json` return code before atomic installation.

Use direct Orca execution by default. If `xvfb-run` is available, it may wrap Orca to enable thumbnails, but slicing correctness cannot depend on it.

- [ ] **Step 5: Run dependency tests GREEN, then run a real Orca build**

First rerun the missing-dependency test. Then, with OrcaSlicer 2.4.2 selected through `ORCASLICER_BIN`, run:

```bash
scripts/build-p1s.sh --output /tmp/wardrobe-release-test.gcode.3mf
```

Expected: Orca returns success and produces a valid archive containing four model objects and embedded G-code.

- [ ] **Step 6: Adapt P1S validation to Orca output**

Keep assertions on four objects, the hand-derived 63.5 mm part width, exact strength settings, supports disabled, no support toolpaths, and embedded G-code checksum. Remove the requirement that preview PNG members exist. Update estimate bounds only after reading the real Orca `result.json`; use narrow bounds around the observed result rather than copying the old Bambu estimate.

- [ ] **Step 7: Regenerate the published P1S artifact and run GREEN**

Run `scripts/build-p1s.sh`, then:

```bash
python3 -m unittest tests.test_release_scripts tests.test_3mf_project -v
```

Expected: PASS with the new Orca-generated artifact.

- [ ] **Step 8: Commit the Orca build pipeline**

```bash
git add profiles/orca scripts/build-p1s.sh scripts/lib/common.sh tests/test_release_scripts.py tests/test_3mf_project.py dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf
git commit -m "build: regenerate P1S release with OrcaSlicer"
```

### Task 4: Optional render and aggregate build

**Files:**
- Create: `scripts/build-render.sh`
- Create: `scripts/build-all.sh`
- Modify: `tests/test_release_scripts.py`

**Interfaces:**
- Consumes: common dependency helpers, OpenSCAD, optional `xvfb-run`, and the model/P1S scripts.
- Produces: explicit render regeneration and an aggregate release command that skips only images when Xvfb is absent.

- [ ] **Step 1: Write failing explicit-render dependency test**

Invoke `build-render.sh --output <temp>/render.png` with `XVFB_RUN_BIN=/definitely/missing/xvfb-run`. Assert nonzero status, `Xvfb`, `https://packages.ubuntu.com/search?keywords=xvfb`, no output, and no damage to an existing sentinel.

- [ ] **Step 2: Verify RED because the render script is absent**

Run the focused test and confirm the failure is caused by the absent entry point.

- [ ] **Step 3: Implement the render script**

Accept only `--output FILE`; default to `docs/bracket-render.png`. Reuse the established 1200x900 orthographic OpenSCAD assembly camera and `Tomorrow` color scheme. Render into a private directory via `xvfb-run`, check the PNG is nonempty, and install atomically.

- [ ] **Step 4: Implement aggregate orchestration**

`build-all.sh` invokes model and P1S scripts. It calls `build-render.sh` only if the explicit `XVFB_RUN_BIN` is executable or `xvfb-run` is on `PATH`; otherwise it emits `warning: Xvfb not found; keeping existing render` and exits successfully after mandatory outputs finish.

- [ ] **Step 5: Run render tests and regenerate the image**

Run the dependency test, then `scripts/build-render.sh`, followed by the existing render dimensions test. Expect PASS and a 1200x900 PNG.

- [ ] **Step 6: Commit optional rendering**

```bash
git add scripts/build-render.sh scripts/build-all.sh tests/test_release_scripts.py docs/bracket-render.png
git commit -m "build: add optional release render generation"
```

### Task 5: Documentation, final verification, and review

**Files:**
- Modify: `README.md`
- Inspect: `tests/test_readme_render.py` (no modification expected)

**Interfaces:**
- Consumes: all generated artifacts and script entry points.
- Produces: a publication-ready file guide and reproducible build instructions without physical-validation claims.

- [ ] **Step 1: Update release documentation**

Add a table covering each `dist/models` file and the P1S profile. Add commands for `build-models.sh`, `build-p1s.sh`, `build-render.sh`, and `build-all.sh`; document OpenSCAD, OrcaSlicer 2.4+, optional Xvfb, environment overrides, official installation URLs, and the fact that headless P1S output may omit thumbnails. Replace Bambu Studio generator/estimate text with observed OrcaSlicer values. State explicitly that the M6 revision still awaits physical fit, function, and load testing.

- [ ] **Step 2: Run the full verification suite from a clean command**

Run:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Also run `unzip -t` on all four 3MF release archives and render the two individual STLs with OpenSCAD to confirm they remain manifold.

- [ ] **Step 3: Request independent code review**

Use `superpowers:requesting-code-review` with base commit `b50b43c`. Require review of dependency behavior, atomic output safety, clean-3MF portability, P1S settings/toolpaths, stale-file removal, and README accuracy. Fix every Critical or Important finding with a failing test first.

- [ ] **Step 4: Commit documentation and review fixes**

```bash
git add README.md tests scripts profiles dist docs/bracket-render.png .gitignore
git commit -m "docs: document reproducible release builds"
```

- [ ] **Step 5: Verify the committed snapshot**

Rerun the full test suite, archive checks, `git diff --check`, and `git status --short`. The final status must be clean and `master` must contain every implementation commit.
