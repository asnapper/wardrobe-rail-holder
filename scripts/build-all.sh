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

if {
    [ -n "${XVFB_RUN_BIN:-}" ] && [ -x "$XVFB_RUN_BIN" ]
} || command -v xvfb-run >/dev/null 2>&1
then
    "$SCRIPT_DIRECTORY/build-render.sh"
else
    printf '%s\n' "warning: Xvfb not found; keeping existing render" >&2
fi
