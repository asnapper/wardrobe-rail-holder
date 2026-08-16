# README SCAD render design

## Goal

Replace the inaccurate `docs/bracket-arrangement.svg` illustration with an
image rendered from the current OpenSCAD geometry.

## Design

- Render `part="assembly"` directly from `wardrobe_rail_bracket.scad`.
- Use an orthographic three-quarter camera angle that clearly shows the ceiling
  plate, upper body, removable cap, fastener locations, and reference rail.
- Use a neutral background and the model's existing material colors.
- Save the result as `docs/bracket-render.png` at a README-friendly resolution.
- Update the README image reference, then remove the obsolete SVG.

## Verification

- Visually inspect the rendered PNG against the SCAD assembly.
- Confirm the PNG is valid and sufficiently large for the README.
- Confirm the README references the new image and no tracked file references the
  removed SVG.
- Run the existing automated tests to ensure the documentation-only change does
  not disturb the model or packaged print project.
