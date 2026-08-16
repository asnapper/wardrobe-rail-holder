# Task 4 report: optional render and aggregate build

## Scope

Task 4 adds explicit render regeneration through `scripts/build-render.sh` and
the aggregate release entry point `scripts/build-all.sh`. The render keeps the
established 1200 × 900 orthographic assembly camera and `Tomorrow` color scheme,
stages the PNG in a private build directory, and installs it atomically.

The aggregate command always runs the model and P1S builders. It runs the render
only when an executable explicit `XVFB_RUN_BIN` is available or `xvfb-run` is on
`PATH`; otherwise it warns and preserves the existing image.

## RED evidence

Added `RenderBuildTests.test_missing_xvfb_preserves_render_destination` to
`tests/test_release_scripts.py`. The test invokes:

```text
build-render.sh --output <temporary>/render.png
XVFB_RUN_BIN=/definitely/missing/xvfb-run
```

Before the implementation existed, the focused run failed at the intentional
entry-point assertion:

```text
FAIL ... scripts/build-render.sh is missing
```

This established that the test detected the missing production entry point.

## GREEN evidence

After implementing both scripts, the focused dependency test passed:

```text
python3 -m unittest tests.test_release_scripts.RenderBuildTests.test_missing_xvfb_preserves_render_destination -v
OK
```

The test verified that an invalid explicit Xvfb executable produces a nonzero
status, names `Xvfb`, includes the Ubuntu package URL, leaves no new output,
and preserves the existing sentinel bytes.

The real render command completed successfully:

```text
scripts/build-render.sh
python3 -m unittest tests.test_readme_render -v
Ran 2 tests ... OK
docs/bracket-render.png: PNG image data, 1200 x 900, 8-bit/color RGB, non-interlaced
```

An aggregate smoke test using isolated fake mandatory builders with
`XVFB_RUN_BIN=/definitely/missing/xvfb-run` returned status 0 and emitted:

```text
warning: Xvfb not found; keeping existing render
```

The tracked model and P1S artifacts were restored unchanged after that smoke
test; they are not part of this task's changes.

Final verification:

```text
sh -n scripts/build-render.sh scripts/build-all.sh
python3 -m unittest discover -s tests -v
Ran 34 tests in 53.863s
OK
git diff --check
```

The regenerated `docs/bracket-render.png` is a successful real OpenSCAD render
and remains 1200 × 900.

## Files changed

- `scripts/build-render.sh`
- `scripts/build-all.sh`
- `tests/test_release_scripts.py`
- `docs/bracket-render.png`
- this report

No SCAD source, profiles, neutral model exports, or sliced P1S artifact were
changed.

## Fix round 1: explicit Xvfb override precedence

### RED evidence

Added `AggregateBuildTests.test_invalid_explicit_xvfb_skips_render_even_when_path_has_xvfb`.
The isolated test copies `build-all.sh`, supplies fake model/P1S/render entry
points, places an executable fake `xvfb-run` on `PATH`, and sets
`XVFB_RUN_BIN=/definitely/missing/xvfb-run`. Against the previous aggregate
predicate, the focused test failed because the event log showed:

```text
['models', 'p1s', 'render']
```

This demonstrated that the invalid explicit override incorrectly fell through
to the PATH candidate and invoked rendering.

### GREEN evidence

`build-all.sh` now treats an explicitly set `XVFB_RUN_BIN` as authoritative:
only an executable override enables rendering; PATH lookup is used only when
the override is unset. The focused aggregate test and the direct-render strict
dependency test both pass:

```text
python3 -m unittest \
  tests.test_release_scripts.AggregateBuildTests.test_invalid_explicit_xvfb_skips_render_even_when_path_has_xvfb \
  tests.test_release_scripts.RenderBuildTests.test_missing_xvfb_preserves_render_destination -v
Ran 2 tests ... OK
```

The aggregate regression verifies mandatory builders run first, rendering is
not invoked, the exact warning is emitted, status is zero, and the existing
render sentinel remains byte-for-byte unchanged.
