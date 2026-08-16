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
        OUTPUT_FILE="$REPOSITORY_ROOT/docs/bracket-render.png"
        ;;
    2)
        [ "$1" = "--output" ] && [ -n "$2" ] || usage
        OUTPUT_FILE=$2
        ;;
    *)
        usage
        ;;
esac

XVFB_RUN=$(find_required_tool \
    "${XVFB_RUN_BIN:-}" \
    "Xvfb" \
    "https://packages.ubuntu.com/search?keywords=xvfb" \
    xvfb-run)
OPENSCAD=$(find_required_tool \
    "${OPENSCAD_BIN:-}" \
    "OpenSCAD" \
    "https://openscad.org/downloads.html" \
    openscad)

MODEL="$REPOSITORY_ROOT/wardrobe_rail_bracket.scad"
BUILD_DIRECTORY=$(new_build_dir)
trap 'rm -rf "$BUILD_DIRECTORY"' EXIT HUP INT TERM

RENDER="$BUILD_DIRECTORY/bracket-render.png"
"$XVFB_RUN" -a env LIBGL_ALWAYS_SOFTWARE=1 "$OPENSCAD" \
    --preview \
    --imgsize=1200,900 \
    --projection=o \
    --camera=0,0,-24,110,0,35,250 \
    --autocenter \
    --colorscheme=Tomorrow \
    -D 'part="assembly"' \
    -o "$RENDER" \
    "$MODEL"
require_nonempty "$RENDER"
atomic_install "$RENDER" "$OUTPUT_FILE"
