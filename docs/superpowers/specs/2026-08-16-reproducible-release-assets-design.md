# Reproducible Release Assets Design

**Status:** Approved for implementation on 2026-08-16

## Goal

Provide current M6 model files suitable for MakerWorld, Printables, and other
model hosts, and make every published artifact reproducible from
`wardrobe_rail_bracket.scad` with command-line scripts. Mandatory builds must
work without a display server. Image generation may use Xvfb when available,
but must remain optional.

## Current State

The parametric SCAD model is the authoritative source. The repository currently
publishes one Bambu P1S two-bracket `.gcode.3mf` under `dist/`, but it has no
current standalone main/cap model exports. The tracked root
`wardrobe_rail_bracket.3mf` predates the M6 redesign, and an ignored root
`wardrobe_rail_bracket.stl` is also obsolete. Both root artifacts can be
mistaken for the current release and must be removed.

The existing README render is current, but its generation previously required
a manually assembled OpenSCAD/Xvfb command. The new scripts must make that
operation discoverable and repeatable without making Xvfb a mandatory build
dependency.

## Selected Approach

OpenSCAD owns all portable geometry exports because it can generate STL and
standards-based geometry-only 3MF files directly from the SCAD source without a
display server. OrcaSlicer 2.4 or newer owns only the printer-specific P1S
`.gcode.3mf`. OpenSCAD running under Xvfb owns the optional README render.

This division keeps neutral model downloads independent of a slicer, avoids
slicer metadata in clean 3MF files, and provides a headless route for the
printer-specific artifact. It also keeps the SCAD output modes as the single
definition of print orientation.

## Artifact Contract

Generated release files live under `dist/`:

```text
dist/
|-- models/
|   |-- wardrobe_rail_bracket_main.stl
|   |-- wardrobe_rail_bracket_cap.stl
|   |-- wardrobe_rail_bracket_main.3mf
|   |-- wardrobe_rail_bracket_cap.3mf
|   `-- wardrobe_rail_bracket_complete.3mf
`-- wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf
```

The main and cap files use `part="main_print"` and `part="cap_print"`, so each
part sits on the build plate in its recommended orientation. The complete 3MF
uses `part="print"` and contains one main plus one cap in their recommended
layout. All three 3MF files under `dist/models/` are unsliced geometry-only
archives: they contain no G-code and no OrcaSlicer or Bambu Studio project
settings.

The P1S `.gcode.3mf` contains two complete brackets: two main bodies and two
caps. It preserves the agreed P1S, 0.4 mm nozzle, Bambu PLA Basic, and Textured
PEI configuration with these project settings:

- 0.20 mm layer height
- 5 walls
- 6 top layers and 6 bottom layers
- 40% gyroid infill
- supports disabled
- 5 mm outer brim with 0.1 mm object gap
- by-layer printing
- 120 mm/s outer walls and 200 mm/s inner walls/infill

The tracked pre-M6 root 3MF is deleted. The ignored pre-M6 root STL is removed
from the workspace. `.gitignore` continues to ignore incidental STL exports but
allows the five deliberate model releases under `dist/models/` to be tracked.

## Script Interfaces

The build interface consists of focused POSIX shell scripts:

```text
scripts/
|-- lib/common.sh
|-- build-models.sh
|-- build-p1s.sh
|-- build-render.sh
`-- build-all.sh
```

`scripts/lib/common.sh` resolves repository paths, locates executables, prints
consistent diagnostics, creates temporary working directories, and installs
completed artifacts atomically. It never deletes paths outside the known
release targets.

`scripts/build-models.sh` requires OpenSCAD and regenerates all five files under
`dist/models/`. It accepts an optional `--output-dir DIR` for tests and local
experiments; its default is the repository release directory.

`scripts/build-p1s.sh` requires OpenSCAD and OrcaSlicer 2.4 or newer. It first
exports fresh main/cap STL inputs into a temporary directory, loads the
repository's versioned Orca profiles, creates two copies of each part, arranges
them on one P1S plate, slices the plate, validates the result, and atomically
replaces the published `.gcode.3mf`. It accepts an optional `--output FILE` for
verification builds. It does not consume model files already present under
`dist/`, so a stale intermediate export cannot enter the sliced release.

`scripts/build-render.sh` explicitly regenerates
`docs/bracket-render.png`. It requires OpenSCAD and `xvfb-run`; when invoked
directly, a missing Xvfb dependency is an actionable error.

`scripts/build-all.sh` runs the neutral model and P1S builds. It then invokes
the render build only when `xvfb-run` is available. If Xvfb is absent, it emits
a warning, leaves the existing image unchanged, and completes successfully.

The Orca command runs directly in a headless environment. When `xvfb-run` is
available, the script may use it to enable embedded graphical previews. A
headless archive without embedded thumbnails remains valid; thumbnails are not
part of the mandatory P1S artifact contract.

## Slicer Profiles

Versioned, flattened CLI inputs live under `profiles/orca/`:

```text
profiles/orca/
|-- p1s-0.4-machine.json
|-- pla-basic.json
`-- bracket-strength.json
```

The files make the build independent of a user's OrcaSlicer presets and encode
the machine, filament, and project settings required by the artifact contract.
They are input data, not generated release outputs. OrcaSlicer records its
actual version in the exported project; the scripts reject versions older than
2.4 because reliable headless export is a design requirement.

## Dependency Discovery and Diagnostics

Executable lookup follows this order:

1. An explicit environment override.
2. Supported executable names on `PATH`.
3. Failure with a concise diagnostic and official installation link.

Supported overrides are `OPENSCAD_BIN`, `ORCASLICER_BIN`, and `XVFB_RUN_BIN`.
Orca lookup recognizes common names such as `orca-slicer`, `OrcaSlicer`, and
`orcaslicer`; an AppImage can be selected with `ORCASLICER_BIN=/path/to/file`.

Diagnostics identify which command is missing and point to:

- OpenSCAD downloads: <https://openscad.org/downloads.html>
- OrcaSlicer releases: <https://github.com/OrcaSlicer/OrcaSlicer/releases>
- Xvfb package information: <https://packages.ubuntu.com/search?keywords=xvfb>

Missing OpenSCAD stops every build that needs geometry. Missing OrcaSlicer
stops only the P1S and aggregate release builds. Missing Xvfb stops an explicit
render build but merely skips rendering in the aggregate build.

All scripts use a temporary directory and validate complete outputs before
moving them into place. A failed OpenSCAD render, failed slice, nonzero Orca
result, empty file, malformed ZIP archive, or missing expected payload exits
nonzero and leaves the previous published artifact untouched.

## Validation and Tests

Tests exercise observable build behavior rather than searching script source
for expected strings.

Model export integration tests run `build-models.sh` against a temporary output
directory and verify:

- all five artifacts exist and are nonempty;
- STL and 3MF meshes have the expected M6 model envelopes;
- individual parts are manifold and rest on the build plate;
- the complete 3MF contains both printable volumes;
- clean 3MF archives contain no G-code, slice information, or slicer-project
  configuration.

Dependency tests invoke scripts with deliberately unavailable executable
overrides and verify a nonzero exit, the missing dependency name, an official
installation URL, and the absence of partial output.

The existing P1S tests continue to verify four printable objects, valid embedded
G-code and checksum, exact strength settings, support-free toolpaths, plausible
material/time estimates, and current M6 geometry. Preview-image assertions are
relaxed so a valid headless Orca export is accepted. When OrcaSlicer is present,
a release smoke test regenerates the P1S artifact into a temporary path and
runs the same archive validation against it.

A repository hygiene test verifies that neither obsolete root model artifact
exists. The complete suite remains runnable with:

```bash
python3 -m unittest discover -s tests -v
```

## Documentation

The README gains a release-files table and a regeneration section that lists
each script, its output, its required dependencies, environment overrides, and
the optional Xvfb behavior. The ready-to-print section identifies OrcaSlicer as
the generator after migration and reports estimates obtained from the newly
generated artifact rather than retaining Bambu Studio values.

The documentation does not claim physical validation of the M6 revision. Fit,
function, sustained loading, and installation testing remain pending until the
part has been printed and mounted.

## Non-Goals

- Changing bracket geometry or hardware dimensions.
- Claiming verified fit, function, load capacity, or long-term material safety.
- Adding printer profiles other than the P1S 0.4 mm PLA release.
- Downloading or installing dependencies automatically.
- Requiring X11, Wayland, Xvfb, or OpenGL for mandatory model and slicing
  outputs.
- Guaranteeing byte-for-byte identical ZIP archives across slicer versions.
