# 6 mm Nut Clearance Design

**Status:** Approved for implementation on 2026-08-17

## Goal

Fit the user's 6 mm-high M6 hex nuts in the main body's side-loading captive
nut pockets while preserving the model's existing 0.3 mm nominal print
clearance.

## Selected Approach

Change the authoritative `clamp_nut_thickness` parameter from 5 mm to 6 mm and
leave `nut_clearance` at 0.3 mm. The derived `nut_pocket_height` therefore
changes from 5.3 mm to 6.3 mm. This represents the real hardware dimension and
keeps custom parameter behavior predictable.

The pocket bottom, bearing floor, roof thickness, across-flats dimension, and
lateral clearance remain unchanged. The pocket top, main lug top, and tapered
boss support adjust through the existing derived dimensions, raising the
pocket roof by exactly 1 mm without reducing the 2.5 mm nut floor or 6 mm nut
roof.

The M6 x 12 mm clamp screws remain unchanged at the user's request. With the
taller pocket, a nominal screw reaches 0.1 mm beyond the pocket top and 0.4 mm
beyond a 6 mm nut seated on the pocket floor. Recalibrate
`minimum_bolt_projection` from 0.8 mm to 0 mm so the model requires the screw
to reach the full pocket height without claiming a protrusion margin that the
selected hardware cannot provide.

## Model and Hardware Contract

- Default hardware uses two M6 hex nuts measuring 10 mm nominal across flats
  and 6 mm high.
- Each captive pocket is 6.3 mm high: 6 mm nominal hardware plus 0.3 mm
  clearance.
- The existing M6 x 12 mm button-head screws, pocket loading direction, bolt
  axis, and rail geometry remain unchanged.
- The bolt-length assertion requires the screw to reach the full pocket height;
  it does not require additional projection beyond the 6.3 mm pocket.
- Existing structural assertions must still pass with the raised pocket roof.

## Tests

Update the real-geometry hardware fit test before changing the model so its
6 mm nut probe fails against the current 5.3 mm pocket. After the parameter
change, the same probe must occupy and enter each pocket without intersecting
the main body. The existing short-bolt rejection must still prove that an
undersized screw cannot reach the full pocket. Existing rendering, topology,
envelope, support, and invalid-parameter tests remain regression coverage.

Run the complete unit-test suite after rebuilding release artifacts. Validate
the neutral models and sliced P1S project with the repository's release
validator.

## Documentation and Release Artifacts

Update the README hardware list to specify 6 mm-high nuts. Regenerate all five
neutral model releases, the README render, and the two-bracket P1S sliced
project from the changed SCAD source. Update documented slicer layer, material,
and time estimates if the regenerated project reports different values.

The neutral model envelope contract is expected to remain unchanged because
the extra pocket height removes internal material without changing the outer
part bounds. Any actual regenerated envelope or slicer metadata changes must be
reflected in their validators and documentation rather than waived.

## Non-Goals

- Increasing clearance beyond the existing 0.3 mm allowance.
- Changing nut width, the selected M6 x 12 mm bolts, rail fit, or bracket
  exterior geometry.
- Claiming physical fit or load validation before the revised model is printed
  and tested.
