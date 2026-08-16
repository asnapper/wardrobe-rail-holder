#!/usr/bin/env sh
set -eu

SCRIPT_DIRECTORY=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIRECTORY/.." && pwd)
. "$SCRIPT_DIRECTORY/lib/common.sh"

usage() {
    die "Usage: $0 [--output-dir DIR]"
}

case $# in
    0)
        OUTPUT_DIRECTORY="$REPOSITORY_ROOT/dist/models"
        ;;
    2)
        [ "$1" = "--output-dir" ] && [ -n "$2" ] || usage
        OUTPUT_DIRECTORY=$2
        ;;
    *)
        usage
        ;;
esac

OPENSCAD=$(find_required_tool "${OPENSCAD_BIN:-}" "OpenSCAD" "https://openscad.org/downloads.html" openscad)
MODEL="$REPOSITORY_ROOT/wardrobe_rail_bracket.scad"
BUILD_DIRECTORY=$(new_build_dir)
trap 'rm -rf "$BUILD_DIRECTORY"' EXIT HUP INT TERM

export_stl() {
    mode=$1 output=$2
    "$OPENSCAD" --export-format binstl -o "$output" -D "part=\"$mode\"" "$MODEL"
    require_nonempty "$output"
}

export_3mf() {
    mode=$1 output=$2
    "$OPENSCAD" --export-format 3mf -o "$output" -D "part=\"$mode\"" "$MODEL"
    require_nonempty "$output"
}

export_stl main_print "$BUILD_DIRECTORY/wardrobe_rail_bracket_main.stl"
export_stl cap_print "$BUILD_DIRECTORY/wardrobe_rail_bracket_cap.stl"
export_3mf main_print "$BUILD_DIRECTORY/wardrobe_rail_bracket_main.3mf"
export_3mf cap_print "$BUILD_DIRECTORY/wardrobe_rail_bracket_cap.3mf"
export_3mf print "$BUILD_DIRECTORY/wardrobe_rail_bracket_complete.3mf"

for filename in \
    wardrobe_rail_bracket_main.stl \
    wardrobe_rail_bracket_cap.stl \
    wardrobe_rail_bracket_main.3mf \
    wardrobe_rail_bracket_cap.3mf \
    wardrobe_rail_bracket_complete.3mf
do
    atomic_install "$BUILD_DIRECTORY/$filename" "$OUTPUT_DIRECTORY/$filename"
done
