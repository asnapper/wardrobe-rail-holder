# Ceiling wardrobe rail bracket

Parametric OpenSCAD model for mounting a vertical 30 × 15 mm rounded-rectangle
wardrobe rail to a ceiling. The rail has 7 mm corner radii and is captured by a
removable lower cap.

![Rendered wardrobe rail bracket](docs/bracket-render.png)

## Hardware for one bracket

- 2 × M6 × 12 mm button-head socket screws
- 2 × standard M6 hex nuts (10 mm nominal across flats, 6 mm thick)
- 2 × 4 mm countersunk ceiling screws
- Ceiling anchors appropriate for the ceiling construction and intended load

Do not select ceiling anchors by screw size alone. Plasterboard, masonry,
concrete, timber, and suspended ceilings require different fastening methods.

## Release files

| File | Contents and intended use |
| --- | --- |
| [`dist/models/wardrobe_rail_bracket_main.stl`](dist/models/wardrobe_rail_bracket_main.stl) | Main body in its recommended print orientation; use with any slicer. |
| [`dist/models/wardrobe_rail_bracket_cap.stl`](dist/models/wardrobe_rail_bracket_cap.stl) | Cap in its recommended print orientation; use with any slicer. |
| [`dist/models/wardrobe_rail_bracket_main.3mf`](dist/models/wardrobe_rail_bracket_main.3mf) | Neutral, portable 3MF containing the main body only. |
| [`dist/models/wardrobe_rail_bracket_cap.3mf`](dist/models/wardrobe_rail_bracket_cap.3mf) | Neutral, portable 3MF containing the cap only. |
| [`dist/models/wardrobe_rail_bracket_complete.3mf`](dist/models/wardrobe_rail_bracket_complete.3mf) | Neutral, portable print layout containing one main body and one cap. |
| [`dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf`](dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf) | Ready-to-print Bambu Lab P1S project for two complete brackets, with models, project settings, and printer toolpaths. |

The P1S project was sliced with OrcaSlicer 2.4.2 for a P1S with a 0.4 mm
nozzle, Textured PEI Plate, and Bambu PLA Basic. It contains four objects: two
main bodies and two caps. Its embedded profile uses 0.20 mm layers, 5 walls, 6
top and bottom layers, 40% gyroid infill, a 5 mm outer brim with a 0.1 mm gap,
and no supports. OrcaSlicer reports 150 layers, 133.10 g of filament, and
17,454 s (about 4 h 51 min) estimated print time.

The headless P1S build is intended to reproduce the project settings and
toolpaths; embedded thumbnails are not guaranteed. Review the selected filament
and build plate in OrcaSlicer before sending it to the printer.

OrcaSlicer retains its standard enclosed-printer PLA advisory because the stock
Textured PEI profile uses a 55 °C bed. For this long PLA print, open the P1S
front door and/or remove the upper glass so chamber heat does not soften the
filament and cause an extruder clog. The advisory is intentionally retained; the
material heat limit and official bed temperature have not been falsified to hide
it.

## Reproducing release assets

Install [Python 3](https://www.python.org/downloads/),
[OpenSCAD](https://openscad.org/downloads.html), and
[OrcaSlicer 2.4 or later](https://github.com/OrcaSlicer/OrcaSlicer/releases).
Python 3 runs the standard-library artifact validator that checks every staged
model and sliced project before any release file is replaced.
[`xvfb-run`](https://packages.ubuntu.com/search?keywords=xvfb) is optional for
the aggregate release build: without it, `build-all.sh` still builds the models
and P1S project but preserves the existing render. It is required whenever
`build-render.sh` regenerates the PNG, including on a machine with a display.

Run the individual builders from the repository root:

```bash
./scripts/build-models.sh  # neutral STL and 3MF files in dist/models
./scripts/build-p1s.sh     # sliced P1S .gcode.3mf in dist
./scripts/build-render.sh  # regenerates docs/bracket-render.png; requires Xvfb
./scripts/build-all.sh     # models and P1S project; regenerates render if Xvfb is available
```

The builders locate `python3`, `openscad`, `orca-slicer` (also `orcaslicer` or
`OrcaSlicer`), and `xvfb-run` on `PATH`. Set `PYTHON_BIN`, `OPENSCAD_BIN`,
`ORCASLICER_BIN`, or `XVFB_RUN_BIN` to executable paths to override those
selections, for example:

```bash
PYTHON_BIN=/opt/python/bin/python3 ./scripts/build-models.sh
OPENSCAD_BIN=/opt/OpenSCAD/openscad ./scripts/build-models.sh
ORCASLICER_BIN=/opt/OrcaSlicer/orca-slicer ./scripts/build-p1s.sh
XVFB_RUN_BIN=/usr/bin/xvfb-run ./scripts/build-render.sh
```

`build-models.sh` accepts `--output-dir DIR`; `build-p1s.sh` and
`build-render.sh` accept `--output FILE`. `build-all.sh` has no arguments. If
Xvfb is unavailable, `build-all.sh` warns and keeps the existing render rather
than replacing it.

## Exporting the parts

Open `wardrobe_rail_bracket.scad` in OpenSCAD and set `part` near the top of the
file:

```scad
part = "main_print"; // main part in its recommended print orientation
part = "cap_print";  // cap in its recommended print orientation
```

The default `part = "print"` places both pieces on the build plate in their
recommended orientations. `part = "assembly"` shows the installed arrangement;
OpenSCAD preview also displays a translucent reference rail.

Command-line export is supported:

```bash
openscad -o wardrobe-bracket-main.stl -D 'part="main_print"' wardrobe_rail_bracket.scad
openscad -o wardrobe-bracket-cap.stl -D 'part="cap_print"' wardrobe_rail_bracket.scad
```

The `main` and `cap` modes retain the installed assembly coordinates and are
useful for CAD inspection rather than direct slicing.

All principal dimensions are top-level parameters. The default rail socket is
30.6 × 15.6 mm with a 7.3 mm radius, providing 0.3 mm nominal clearance on each
side. Print a short fit sample or adjust `rail_clearance` if the printer or rail
needs a different tolerance.

## Suggested PLA print settings

- 0.2 mm layer height or finer
- At least 5 perimeters/walls
- At least 6 top and bottom layers
- 40–60% cubic or gyroid infill
- No supports should be required in the supplied print layout; inspect the
  preview for the selected printer and slicer

The main part prints with its ceiling-contact face on the bed. The cap has a
flattened exterior face for bed adhesion; its downward-facing bolt-head recesses
start at that face and print upward from the build plate. Avoid changing these
orientations casually: layer direction is part of the load-bearing design.

PETG or another tougher, more creep-resistant material is preferable for warm
locations or long-term heavy loading. If using a material other than PLA,
re-check hole and rail clearances with a fit sample.

## Assembly

1. Slide one standard M6 nut into each side-loading hexagonal pocket in the
   main body.
2. Fasten the main body to structural ceiling material using both countersunk
   holes and suitable anchors.
3. Lift the rail into the downward-facing upper saddle.
4. Place the lower cap around the rail, with its bolt-head recesses facing down.
5. Insert the two M6 × 12 mm button-head bolts and tighten them evenly. Stop
   once the cap is secure; do not crush the rail or strip the printed part.

The 0.6 mm gap between the body and cap provides take-up for tolerance. A small
visible gap after tightening is normal.

## Safety and loading

This M6 revision has **not yet been physically printed or verified** for fit,
function, or load. A 20 kg static load is a design target only, not a validated
capacity or safety claim. It is **not structurally certified**. Capacity depends
on filament quality and age, print temperature, layer adhesion, bracket spacing,
rail span, ambient heat, ceiling construction, screws, and anchors. PLA also
creeps under sustained load.

Use multiple brackets, keep people clear during testing, and proof-load the
installed rail gradually with a non-fragile load before hanging clothes. Inspect
the brackets periodically for cracks, loosening, distortion, or cap movement.
Do not use the model where failure could injure someone or for human-supporting,
overhead lifting, or safety-critical applications.

## Verification

Run the automated render checks with:

```bash
python3 -m unittest discover -s tests -v
```

The tests compile every output mode with OpenSCAD, inspect the binary STL
envelopes and screw-access paths, exercise custom rail dimensions, verify
invalid geometry is rejected, and validate the embedded P1S settings and G-code
checksum in the ready-to-print project.
