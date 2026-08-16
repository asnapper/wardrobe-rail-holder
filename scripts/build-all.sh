#!/usr/bin/env sh
set -eu

SCRIPT_DIRECTORY=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

usage() {
    printf '%s\n' "Usage: $0" >&2
    exit 2
}

[ "$#" -eq 0 ] || usage

"$SCRIPT_DIRECTORY/build-models.sh"
"$SCRIPT_DIRECTORY/build-p1s.sh"

if [ -n "${XVFB_RUN_BIN:-}" ]; then
    if [ -x "$XVFB_RUN_BIN" ]; then
        render_available=1
    else
        render_available=0
    fi
else
    render_available=0
    command -v xvfb-run >/dev/null 2>&1 && render_available=1
fi

if [ "$render_available" = 1 ]; then
    "$SCRIPT_DIRECTORY/build-render.sh"
else
    printf '%s\n' "warning: Xvfb not found; keeping existing render" >&2
fi
