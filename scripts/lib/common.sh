#!/usr/bin/env sh

die() {
    printf '%b\n' "$*" >&2
    exit 1
}

absolute_tool_path() {
    tool_path=$1
    case "$tool_path" in
        /*)
            printf '%s\n' "$tool_path"
            ;;
        *)
            tool_directory=$(dirname -- "$tool_path")
            tool_name=$(basename -- "$tool_path")
            absolute_tool_directory=$(CDPATH= cd -- "$tool_directory" && pwd) \
                || return 1
            printf '%s/%s\n' "$absolute_tool_directory" "$tool_name"
            ;;
    esac
}

find_required_tool() {
    override=$1 label=$2 url=$3
    shift 3
    if [ -n "$override" ]; then
        [ -x "$override" ] || die "$label executable not found: $override\nInstall: $url"
        absolute_tool_path "$override"
        return
    fi
    for candidate do
        if command -v "$candidate" >/dev/null 2>&1; then
            absolute_tool_path "$(command -v "$candidate")"
            return
        fi
    done
    die "$label is required but was not found. Install: $url"
}

find_python3() {
    python_url=https://www.python.org/downloads/
    python_executable=$(find_required_tool \
        "${PYTHON_BIN:-}" "Python 3" "$python_url" python3)
    "$python_executable" -c \
        'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)' \
        >/dev/null 2>&1 \
        || die "Python 3 is required but the selected executable is incompatible: $python_executable\nInstall: $python_url"
    printf '%s\n' "$python_executable"
}

new_build_dir() {
    mktemp -d "${TMPDIR:-/tmp}/wardrobe-rail-holder.XXXXXX" \
        || die "Unable to create a private build directory"
}

require_nonempty() {
    [ -s "$1" ] || die "Expected a nonempty file: $1"
}

version_at_least() {
    required_major=$1 required_minor=$2 detected_version=$3
    detected_major=${detected_version%%.*}
    if [ "$detected_major" = "$detected_version" ]; then
        detected_minor=0
    else
        detected_remainder=${detected_version#*.}
        detected_minor=${detected_remainder%%.*}
    fi

    case "$detected_major:$detected_minor" in
        *[!0-9:]* | :* | *:)
            return 1
            ;;
    esac

    [ "$detected_major" -gt "$required_major" ] || {
        [ "$detected_major" -eq "$required_major" ] \
            && [ "$detected_minor" -ge "$required_minor" ]
    }
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
