#!/usr/bin/env sh
set -eu

SCRIPT_DIRECTORY=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIRECTORY/.." && pwd)
. "$SCRIPT_DIRECTORY/lib/common.sh"

usage() {
    die "Usage: $0 [--output FILE]"
}

case $# in
    0)
        OUTPUT_FILE="$REPOSITORY_ROOT/dist/wardrobe_rail_bracket_P1S_0.4_PLA_2x.gcode.3mf"
        ;;
    2)
        [ "$1" = "--output" ] && [ -n "$2" ] || usage
        OUTPUT_FILE=$2
        ;;
    *)
        usage
        ;;
esac

PYTHON=$(find_python3)
ORCA_RELEASE_URL=https://github.com/OrcaSlicer/OrcaSlicer/releases
ORCASLICER=$(find_required_tool \
    "${ORCASLICER_BIN:-}" \
    "OrcaSlicer" \
    "$ORCA_RELEASE_URL" \
    orca-slicer orcaslicer OrcaSlicer)

VERSION_DIRECTORY=$(new_build_dir)
BUILD_DIRECTORY=$(new_build_dir)
trap 'rm -rf "$VERSION_DIRECTORY" "$BUILD_DIRECTORY"' EXIT HUP INT TERM

ORCA_HELP=$(CDPATH= cd -- "$VERSION_DIRECTORY" && "$ORCASLICER" --help 2>&1) \
    || die "Unable to read the OrcaSlicer version. Install: $ORCA_RELEASE_URL"
ORCA_VERSION=$(printf '%s\n' "$ORCA_HELP" \
    | sed -n 's/^OrcaSlicer-\([0-9][0-9.]*\):.*$/\1/p' \
    | sed -n '1p')
[ -n "$ORCA_VERSION" ] \
    || die "Unable to read the OrcaSlicer version. Install: $ORCA_RELEASE_URL"
version_at_least 2 4 "$ORCA_VERSION" \
    || die "OrcaSlicer 2.4 or newer is required (found $ORCA_VERSION). Install: $ORCA_RELEASE_URL"

OPENSCAD=$(find_required_tool \
    "${OPENSCAD_BIN:-}" \
    "OpenSCAD" \
    "https://openscad.org/downloads.html" \
    openscad)

MODEL="$REPOSITORY_ROOT/wardrobe_rail_bracket.scad"
MACHINE_PROFILE="$REPOSITORY_ROOT/profiles/orca/p1s-0.4-machine.json"
FILAMENT_PROFILE="$REPOSITORY_ROOT/profiles/orca/pla-basic.json"
PROCESS_PROFILE="$REPOSITORY_ROOT/profiles/orca/bracket-strength.json"
VALIDATOR="$REPOSITORY_ROOT/scripts/validate_release.py"

export_stl() {
    mode=$1 output=$2
    QT_QPA_PLATFORM=offscreen "$OPENSCAD" --export-format binstl \
        -o "$output" -D "part=\"$mode\"" "$MODEL"
    require_nonempty "$output"
}

export_stl main_print "$BUILD_DIRECTORY/main_print.stl"
export_stl cap_print "$BUILD_DIRECTORY/cap_print.stl"

for profile in "$MACHINE_PROFILE" "$FILAMENT_PROFILE" "$PROCESS_PROFILE"
do
    require_nonempty "$profile"
done

ARCHIVE_NAME=release.gcode.3mf
if "$ORCASLICER" \
    --datadir "$BUILD_DIRECTORY/orca-data" \
    --logfile "$BUILD_DIRECTORY/orca.log" \
    --outputdir "$BUILD_DIRECTORY" \
    --load-settings "$MACHINE_PROFILE;$PROCESS_PROFILE" \
    --load-filaments "$FILAMENT_PROFILE" \
    --arrange 1 \
    --ensure-on-bed \
    --slice 0 \
    --export-slicedata "$BUILD_DIRECTORY/slicedata" \
    --export-3mf "$ARCHIVE_NAME" \
    "$BUILD_DIRECTORY/main_print.stl" \
    "$BUILD_DIRECTORY/main_print.stl" \
    "$BUILD_DIRECTORY/cap_print.stl" \
    "$BUILD_DIRECTORY/cap_print.stl"
then
    :
else
    orca_status=$?
    die "OrcaSlicer failed with exit code $orca_status"
fi

ARCHIVE="$BUILD_DIRECTORY/$ARCHIVE_NAME"
RESULT="$BUILD_DIRECTORY/result.json"
require_nonempty "$ARCHIVE"
require_nonempty "$RESULT"
result_return_code=$(sed -n \
    's/.*"return_code"[[:space:]]*:[[:space:]]*\(-\{0,1\}[0-9][0-9]*\).*/\1/p' \
    "$RESULT" | sed -n '1p')
[ -n "$result_return_code" ] \
    || die "OrcaSlicer result.json has no numeric return_code"
[ "$result_return_code" -eq 0 ] \
    || die "OrcaSlicer result.json reports return_code $result_return_code"

"$PYTHON" "$VALIDATOR" p1s "$ARCHIVE"

atomic_install "$ARCHIVE" "$OUTPUT_FILE"
