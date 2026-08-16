#!/usr/bin/env sh

die() {
    printf '%b\n' "$*" >&2
    exit 1
}

find_required_tool() {
    override=$1 label=$2 url=$3
    shift 3
    if [ -n "$override" ]; then
        [ -x "$override" ] || die "$label executable not found: $override\nInstall: $url"
        printf '%s\n' "$override"
        return
    fi
    for candidate do
        if command -v "$candidate" >/dev/null 2>&1; then
            command -v "$candidate"
            return
        fi
    done
    die "$label is required but was not found. Install: $url"
}

new_build_dir() {
    mktemp -d "${TMPDIR:-/tmp}/wardrobe-rail-holder.XXXXXX" \
        || die "Unable to create a private build directory"
}

require_nonempty() {
    [ -s "$1" ] || die "Expected a nonempty file: $1"
}

atomic_install() {
    source_path=$1 destination_path=$2
    destination_directory=$(dirname "$destination_path")
    destination_name=$(basename "$destination_path")

    mkdir -p "$destination_directory" \
        || die "Unable to create output directory: $destination_directory"
    temporary_destination=$(mktemp "$destination_directory/.${destination_name}.XXXXXX") \
        || die "Unable to stage output: $destination_path"
    if ! cp "$source_path" "$temporary_destination"; then
        rm -f "$temporary_destination"
        die "Unable to stage output: $destination_path"
    fi
    mv -f "$temporary_destination" "$destination_path" \
        || die "Unable to install output: $destination_path"
}
