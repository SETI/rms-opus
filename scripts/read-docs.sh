#!/usr/bin/env bash
#
# rms-opus - Build Sphinx documentation and open the HTML index
#
# Runs `make html` in docs/ with SPHINXOPTS="-W -n" -- warnings are errors and
# every unresolved cross-reference is a warning -- then opens
# docs/_build/html/index.html using the platform default handler.
#
# A developer convenience with no CI role: the `Docs` job in run-tests.yml and
# scripts/run-all-checks.sh are what gate the documentation.
#
# The pair is named here rather than left to docs/Makefile because passing
# SPHINXOPTS on the `make` command line OVERRIDES the Makefile's `?=` default
# instead of adding to it. (docs/conf.py sets nitpicky = True, so dropping -n
# would in fact change nothing today -- which is a reason to state the pair, not
# a reason to make the next reader re-derive that.)
#
# Usage:
#   ./scripts/read-docs.sh
#
# Environment:
#   VENV or VENV_PATH    Path to virtualenv (default: $PROJECT_ROOT/venv)
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="${VENV:-${VENV_PATH:-$PROJECT_ROOT/venv}}"
DOCS_DIR="$PROJECT_ROOT/docs"
HTML_INDEX="$DOCS_DIR/_build/html/index.html"

cd "$PROJECT_ROOT"

if [ ! -d "$DOCS_DIR" ]; then
    echo "Error: docs directory not found at $DOCS_DIR" >&2
    exit 1
fi

if [ ! -f "$VENV/bin/activate" ]; then
    echo "Error: virtual environment not found at $VENV" >&2
    exit 1
fi

# shellcheck source=/dev/null
source "$VENV/bin/activate"

echo "Building documentation (warnings are errors, nitpicky)..."
make -C "$DOCS_DIR" html SPHINXOPTS="-W -n"

if [ ! -f "$HTML_INDEX" ]; then
    echo "Error: built HTML not found at $HTML_INDEX" >&2
    exit 1
fi

open_html() {
    local path=$1
    case "$(uname -s)" in
        Linux)
            xdg-open "$path"
            ;;
        Darwin)
            open "$path"
            ;;
        CYGWIN* | MINGW* | MSYS*)
            if command -v cygpath >/dev/null 2>&1; then
                MSYS_NO_PATHCONV=1 cmd.exe //C start "" "$(cygpath -w "$path")"
            else
                cmd.exe //C start "" "$path"
            fi
            ;;
        *)
            echo "Error: unsupported platform $(uname -s). Open this file manually:" >&2
            echo "  $path" >&2
            exit 1
            ;;
    esac
}

echo "Opening $HTML_INDEX"
open_html "$HTML_INDEX"
