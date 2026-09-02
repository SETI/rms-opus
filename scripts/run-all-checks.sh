#!/usr/bin/env bash
#
# rms-opus - Run All Checks Script
#
# This script runs linting, type checking, tests, Sphinx build, and
# Markdown lint as separate checks. In parallel mode all requested
# checks run concurrently.
#
# Usage:
#   ./scripts/run-all-checks.sh [options]
#
# Options:
#   -p, --parallel         Run all requested checks in parallel (default)
#   -s, --sequential       Run all requested checks sequentially
#   -w, --pytest-workers N Pytest workers: auto (default), 1 (serial), or N
#   -c, --code             Run all code checks (sets each RUN_* code flag true)
#   -d, --docs             Run Sphinx and PyMarkdown (RUN_SPHINX, RUN_PYMARKDOWN)
#   -m, --markdown         Run only PyMarkdown (RUN_PYMARKDOWN)
#   --ruff-check           Run ruff check only (may combine with other --* flags)
#   --ruff-format          Run ruff format --check only
#   --mypy                 Run mypy only
#   --pytest               Run pytest only
#   --pyroma               Run pyroma only
#   --bandit               Run bandit only
#   --vulture              Run vulture only
#   --sphinx               Run Sphinx build only
#   --pymarkdown           Run PyMarkdown scan only
#   --import-tests         ALSO run the import suite. Opt-in and never part of a
#                          default run: it needs a reachable MySQL server, which no
#                          other check does, and takes about two minutes. Combined
#                          with a --* flag it is added to that selection; on its own
#                          it is added to the full run.
#   -h, --help             Show this help message
#
# Environment:
#   VENV or VENV_PATH        Path to virtualenv (default: $PROJECT_ROOT/venv)
#   OPUS_TEST_DB_HOST/_USER/_PASSWORD   Where --import-tests finds MySQL. The suite
#                            reads them itself, defaulting to root with no password
#                            on 127.0.0.1.
#   CLEANUP_GRACE_PERIOD     Seconds to wait for graceful shutdown (default: 5)
#
#   Pytest coverage minimum: configure fail_under in coverage config (e.g.
#   pyproject.toml [tool.coverage.report] or .coveragerc [report]).
#
#   RUN_* (set by this script from CLI or full-run defaults): RUN_RUFF_CHECK,
#   RUN_RUFF_FORMAT, RUN_MYPY, RUN_PYTEST, RUN_PYROMA, RUN_BANDIT, RUN_VULTURE,
#   RUN_SPHINX, RUN_PYMARKDOWN
#
#   Per-check toggles (true/false). Each check runs only if both RUN_* and
#   ENABLE_* are true (RUN_* from CLI or defaults below; ENABLE_* from env or
#   the defaults block below). Every ENABLE_* default is true here:
#     ENABLE_RUFF_CHECK   (default: true)
#     ENABLE_RUFF_FORMAT  (default: true)
#     ENABLE_MYPY         (default: true)
#     ENABLE_PYTEST       (default: true)
#     ENABLE_PYROMA       (default: true)
#     ENABLE_BANDIT       (default: true)
#     ENABLE_VULTURE      (default: true)
#     ENABLE_SPHINX       (default: true)
#     ENABLE_PYMARKDOWN   PyMarkdown scan (default: true)
#     ENABLE_IMPORT_TESTS (default: true, but --import-tests must ask for it too)
#
# Checks (each run separately; -d runs both Sphinx and Markdown):
#   Code:     optional: ruff check, ruff format --check, mypy, pytest, pyroma,
#             bandit, vulture (see ENABLE_* above)
#   Sphinx:   make -C docs html (docs/Makefile passes -W and -n: warnings are
#             errors, and every unresolved cross-reference is a warning)
#   Markdown: pymarkdown scan docs/ .cursor/ README.md CONTRIBUTING.md
#
# Exit codes:
#   0 - All requested checks passed
#   1 - One or more checks failed
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Default options
PARALLEL=true
PYTEST_WORKERS=auto
RUN_RUFF_CHECK=false
RUN_RUFF_FORMAT=false
RUN_MYPY=false
RUN_PYTEST=false
RUN_PYROMA=false
RUN_BANDIT=false
RUN_VULTURE=false
RUN_SPHINX=false
RUN_PYMARKDOWN=false
RUN_IMPORT_TESTS=false
SCOPE_SPECIFIED=false

# Per-check defaults (override by exporting before invoking this script, or
# permanently change here).
#
# Every check is on. `ruff format` owns layout everywhere OPUS_RUFF_PATHS
# reaches, and mypy runs strict over the whole repository: [tool.mypy] silences
# no module wholesale, and its exclude and ignore_missing_imports carry the
# non-source paths and the untyped third-party packages.
: "${ENABLE_RUFF_CHECK:=true}"
: "${ENABLE_RUFF_FORMAT:=true}"
: "${ENABLE_MYPY:=true}"
: "${ENABLE_PYTEST:=true}"
: "${ENABLE_PYROMA:=true}"
: "${ENABLE_BANDIT:=true}"
: "${ENABLE_VULTURE:=true}"
: "${ENABLE_SPHINX:=true}"
: "${ENABLE_PYMARKDOWN:=true}"
: "${ENABLE_IMPORT_TESTS:=true}"

# The importable packages live under src/, with the live-DB suites in
# integration_tests/, the holdings-free import suite in import_tests/, the unit
# suite in tests/, the documentation build's own extensions in docs/ and
# manage.py at the root.
# Vulture scans the same code trees plus vulture_whitelist.py (so whitelisted
# names count as used); min-confidence/exclude come from [tool.vulture]. Bandit
# skips tests/ and import_tests/ but does scan integration_tests/, which drives a
# live server.
: "${OPUS_RUFF_PATHS:=src integration_tests import_tests tests docs manage.py}"
# mypy covers the same trees, and integration_tests/ is checked strictly like
# every other one: no tree is silenced wholesale.
: "${OPUS_MYPY_PATHS:=src integration_tests import_tests tests docs manage.py}"
: "${OPUS_BANDIT_PATHS:=src integration_tests manage.py}"
: "${OPUS_VULTURE_PATHS:=src integration_tests import_tests tests docs manage.py vulture_whitelist.py}"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="${VENV:-${VENV_PATH:-$PROJECT_ROOT/venv}}"

# OPUS has no default location for its configuration file, so anything that reads
# OPUS settings (pytest, mypy's django-stubs plugin and the Sphinx build) is given
# one. The checked-in dummy configuration holds dummy credentials and paths under
# /tmp. The path is made absolute for clarity rather than out of necessity: Sphinx
# evaluates docs/conf.py with the working directory set to docs/, and conf.py resolves
# a relative OPUS_CONFIG against the repository root itself, so either form works.
# Export an absolute OPUS_CONFIG before invoking this script to check against a
# real installation's configuration instead.
: "${OPUS_CONFIG:=$PROJECT_ROOT/tests/fixtures/opus_ci.toml}"
export OPUS_CONFIG

# Track failures and final exit code
FAILED_CHECKS=()
EXIT_CODE=0

# Temp directory for parallel output and status files
TEMP_DIR=$(mktemp -d)

# Grace period (seconds) before SIGKILL after SIGTERM
CLEANUP_GRACE_PERIOD=${CLEANUP_GRACE_PERIOD:-5}
if ! echo "$CLEANUP_GRACE_PERIOD" | grep -qE '^[0-9]+$'; then
    echo "Error: CLEANUP_GRACE_PERIOD must be a non-negative integer (got: $CLEANUP_GRACE_PERIOD)" >&2
    exit 1
fi

_wait_or_kill() {
    local pid=$1
    [ -z "$pid" ] && return 0
    kill -TERM "$pid" 2>/dev/null || true
    local waited=0
    while [ "$waited" -lt "$CLEANUP_GRACE_PERIOD" ]; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
        waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -KILL "$pid" 2>/dev/null || true
    fi
    wait "$pid" 2>/dev/null || true
    return 0
}

_cleanup() {
    rm -rf "$TEMP_DIR"
}

# On INT/TERM: kill all background check jobs with grace period, then exit
_cleanup_and_exit() {
    local sig_code=$1
    local pids
    pids=$(jobs -p)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            _wait_or_kill "$pid"
        done
    fi
    _cleanup
    exit "$sig_code"
}
trap '_cleanup_and_exit 130' SIGINT
trap '_cleanup_and_exit 143' SIGTERM
trap _cleanup EXIT

print_header() {
    echo -e "\n${BOLD}${BLUE}===================================================${RESET}"
    echo -e "${BOLD}${BLUE}  $1${RESET}"
    echo -e "${BOLD}${BLUE}===================================================${RESET}\n"
}

print_section() {
    echo -e "\n${BOLD}${YELLOW}>>> $1${RESET}\n"
}

print_success() {
    echo -e "${GREEN}✓${RESET} $1"
}

print_error() {
    echo -e "${RED}✗${RESET} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${RESET} $1"
}

show_usage() {
    sed -n '/^# Usage:/,/^# Exit codes:/p' "$0" | sed 's/^# //g' | sed 's/^#//g'
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -s|--sequential)
            PARALLEL=false
            shift
            ;;
        -w|--pytest-workers)
            if [[ -z "${2:-}" || "$2" =~ ^- ]]; then
                echo -e "${RED}Error: -w/--pytest-workers requires a value (auto, 1, 2, ...)${RESET}" >&2
                show_usage
                exit 1
            fi
            PYTEST_WORKERS="$2"
            shift 2
            ;;
        --pytest-workers=*)
            PYTEST_WORKERS="${1#*=}"
            shift
            ;;
        -c|--code)
            RUN_RUFF_CHECK=true
            RUN_RUFF_FORMAT=true
            RUN_MYPY=true
            RUN_PYTEST=true
            RUN_PYROMA=true
            RUN_BANDIT=true
            RUN_VULTURE=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        -d|--docs)
            RUN_SPHINX=true
            RUN_PYMARKDOWN=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        -m|--markdown)
            RUN_PYMARKDOWN=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --ruff-check)
            RUN_RUFF_CHECK=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --ruff-format)
            RUN_RUFF_FORMAT=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --mypy)
            RUN_MYPY=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --pytest)
            RUN_PYTEST=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --import-tests)
            # Deliberately does not set SCOPE_SPECIFIED: this flag *adds* the import
            # suite rather than narrowing the run to it. On its own it means the full
            # run plus the import suite; alongside another --* flag it is added to that
            # selection instead.
            RUN_IMPORT_TESTS=true
            shift
            ;;
        --pyroma)
            RUN_PYROMA=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --bandit)
            RUN_BANDIT=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --vulture)
            RUN_VULTURE=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --sphinx)
            RUN_SPHINX=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --pymarkdown)
            RUN_PYMARKDOWN=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${RESET}" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Default: run all checks (each RUN_* true; ENABLE_* still filters per repo)
if [ "$SCOPE_SPECIFIED" = false ]; then
    RUN_RUFF_CHECK=true
    RUN_RUFF_FORMAT=true
    RUN_MYPY=true
    RUN_PYTEST=true
    RUN_PYROMA=true
    RUN_BANDIT=true
    RUN_VULTURE=true
    RUN_SPHINX=true
    RUN_PYMARKDOWN=true
fi

START_TIME=$(date +%s)

print_header "rms-opus - Running All Checks"

if [ "$PARALLEL" = true ]; then
    print_info "Running checks in PARALLEL mode"
else
    print_info "Running checks in SEQUENTIAL mode"
fi
if [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ]; then
    print_info "Pytest workers: $PYTEST_WORKERS"
fi

# True if at least one code check is both selected (RUN_*) and enabled (ENABLE_*).
_code_checks_any_scheduled() {
    [ "$RUN_RUFF_CHECK" = true ] && [ "$ENABLE_RUFF_CHECK" = true ] && return 0
    [ "$RUN_RUFF_FORMAT" = true ] && [ "$ENABLE_RUFF_FORMAT" = true ] && return 0
    [ "$RUN_MYPY" = true ] && [ "$ENABLE_MYPY" = true ] && return 0
    [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ] && return 0
    [ "$RUN_PYROMA" = true ] && [ "$ENABLE_PYROMA" = true ] && return 0
    [ "$RUN_BANDIT" = true ] && [ "$ENABLE_BANDIT" = true ] && return 0
    [ "$RUN_VULTURE" = true ] && [ "$ENABLE_VULTURE" = true ] && return 0
    [ "$RUN_IMPORT_TESTS" = true ] && [ "$ENABLE_IMPORT_TESTS" = true ] && return 0
    return 1
}

# ---- Code checks (ruff, mypy, pytest, pyroma, bandit, vulture) ----
run_code_checks() {
    local output_file="${1:-}"
    local status_file="${2:-}"

    if [ -n "$output_file" ]; then
        exec > "$output_file" 2>&1
    fi

    print_section "Code Checks"

    cd "$PROJECT_ROOT" || exit 1

    if ! _code_checks_any_scheduled; then
        print_info "No code checks scheduled (RUN_* and ENABLE_*); skipping code checks"
        return 0
    fi

    if [ ! -f "$VENV/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV"
        [ -n "$status_file" ] && echo "Code - Virtual environment not found" >> "$status_file"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    local failed=false
    local failed_checks=""

    if [ "$RUN_RUFF_CHECK" = true ] && [ "$ENABLE_RUFF_CHECK" = true ]; then
        print_info "Running ruff check..."
        # shellcheck disable=SC2086  # word-splitting of the path list is intended
        if python -m ruff check $OPUS_RUFF_PATHS; then
            print_success "Ruff check passed"
        else
            print_error "Ruff check failed"
            failed=true
            failed_checks="${failed_checks}Code - Ruff check"$'\n'
        fi
    fi

    if [ "$RUN_RUFF_FORMAT" = true ] && [ "$ENABLE_RUFF_FORMAT" = true ]; then
        print_info "Running ruff format --check..."
        # shellcheck disable=SC2086  # word-splitting of the path list is intended
        if python -m ruff format --check $OPUS_RUFF_PATHS; then
            print_success "Ruff format check passed"
        else
            print_error "Ruff format check failed"
            failed=true
            failed_checks="${failed_checks}Code - Ruff format"$'\n'
        fi
    fi

    if [ "$RUN_MYPY" = true ] && [ "$ENABLE_MYPY" = true ]; then
        print_info "Running mypy..."
        # The source root and the strict settings come from pyproject.toml, which
        # silences no module wholesale; the paths match the CI lint job's MYPY_PATHS.
        # shellcheck disable=SC2086  # word-splitting of the path list is intended
        if python -m mypy $OPUS_MYPY_PATHS; then
            print_success "Mypy passed"
        else
            print_error "Mypy failed"
            failed=true
            failed_checks="${failed_checks}Code - Mypy"$'\n'
        fi
    fi

    # -n controls parallelism; --dist loadscope keeps each test module on one
    # worker to avoid time-mocking and fixture-isolation interference.
    # testpaths and the strict options come from pyproject.toml.
    #
    # No --cov here, and import_tests/ is not in this invocation. Exactly one
    # job measures coverage and exactly one number gates: the Import Tests job
    # in run-tests.yml runs `pytest import_tests --cov`, and
    # [tool.coverage.report] fail_under is that run's own floor. Measuring the
    # holdings-free unit suite alone against that floor would fail a healthy
    # tree, and this script has to stay runnable without a MySQL server, which
    # import_tests needs.
    if [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ]; then
        print_info "Running pytest (-n ${PYTEST_WORKERS})..."
        if python -m pytest -q -n "$PYTEST_WORKERS" --dist loadscope tests; then
            print_success "Pytest passed"
        else
            print_error "Pytest failed"
            failed=true
            failed_checks="${failed_checks}Code - Pytest"$'\n'
        fi
    fi

    # The import suite, opt-in because it is the one check needing a server. The bare
    # form, no coverage: that is the everyday one and about two minutes, and the coverage
    # form is two commands belonging to the Import Tests job. It reads
    # OPUS_TEST_DB_HOST/_USER/_PASSWORD itself.
    if [ "$RUN_IMPORT_TESTS" = true ] && [ "$ENABLE_IMPORT_TESTS" = true ]; then
        print_info "Running pytest import_tests (needs a reachable MySQL)..."
        if python -m pytest -q import_tests; then
            print_success "Import tests passed"
        else
            print_error "Import tests failed"
            failed=true
            failed_checks="${failed_checks}Code - Import tests"$'\n'
        fi
    fi

    if [ "$RUN_PYROMA" = true ] && [ "$ENABLE_PYROMA" = true ]; then
        print_info "Running pyroma (packaging metadata)..."
        if python -m pyroma .; then
            print_success "Pyroma passed"
        else
            print_error "Pyroma failed"
            failed=true
            failed_checks="${failed_checks}Code - Pyroma"$'\n'
        fi
    fi

    if [ "$RUN_BANDIT" = true ] && [ "$ENABLE_BANDIT" = true ]; then
        print_info "Running bandit..."
        # shellcheck disable=SC2086  # word-splitting of the path list is intended
        if python -m bandit -c pyproject.toml -r $OPUS_BANDIT_PATHS -q; then
            print_success "Bandit passed"
        else
            print_error "Bandit failed"
            failed=true
            failed_checks="${failed_checks}Code - Bandit"$'\n'
        fi
    fi

    if [ "$RUN_VULTURE" = true ] && [ "$ENABLE_VULTURE" = true ]; then
        print_info "Running vulture..."
        # shellcheck disable=SC2086  # word-splitting of the path list is intended
        if python -m vulture $OPUS_VULTURE_PATHS; then
            print_success "Vulture passed"
        else
            print_error "Vulture failed"
            failed=true
            failed_checks="${failed_checks}Code - Vulture"$'\n'
        fi
    fi

    deactivate 2>/dev/null || true

    if [ "$failed" = true ]; then
        [ -n "$status_file" ] && printf '%s' "$failed_checks" >> "$status_file"
        return 1
    fi
    return 0
}

# ---- Sphinx build only ----
run_sphinx_build() {
    local output_file="${1:-}"
    local status_file="${2:-}"

    if [ -n "$output_file" ]; then
        exec > "$output_file" 2>&1
    fi

    print_section "Sphinx Build"

    cd "$PROJECT_ROOT" || exit 1

    if [ ! -f "$VENV/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV"
        [ -n "$status_file" ] && echo "Sphinx - Virtual environment not found" >> "$status_file"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    # -W turns every warning into an error and -n reports every cross-reference that
    # does not resolve. docs/Makefile defaults to the same pair; they are named here
    # too so that the gate does not depend on that default.
    print_info "Building documentation (warnings are errors, nitpicky)..."
    if (cd docs && make clean && make html SPHINXOPTS="-W -n"); then
        print_success "Sphinx build passed"
        deactivate 2>/dev/null || true
        return 0
    else
        print_error "Sphinx build failed"
        [ -n "$status_file" ] && echo "Sphinx - Sphinx build" >> "$status_file"
        deactivate 2>/dev/null || true
        return 1
    fi
}

# ---- Markdown lint only (PyMarkdown) ----
run_markdown_checks() {
    local output_file="${1:-}"
    local status_file="${2:-}"

    if [ -n "$output_file" ]; then
        exec > "$output_file" 2>&1
    fi

    print_section "Markdown Lint (PyMarkdown)"

    cd "$PROJECT_ROOT" || exit 1

    if [ ! -f "$VENV/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV"
        [ -n "$status_file" ] && echo "Markdown - Virtual environment not found" >> "$status_file"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    print_info "Running PyMarkdown scan (docs/, .cursor/, root *.md)..."
    local scan_paths=()
    [ -d "docs/" ] && scan_paths+=("docs/")
    [ -d ".cursor/" ] && scan_paths+=(".cursor/")
    [ -f "README.md" ] && scan_paths+=("README.md")
    [ -f "CONTRIBUTING.md" ] && scan_paths+=("CONTRIBUTING.md")
    if [ ${#scan_paths[@]} -eq 0 ]; then
        print_info "No Markdown files/directories found to scan"
        deactivate 2>/dev/null || true
        return 0
    fi
    if python -m pymarkdown scan "${scan_paths[@]}"; then
        print_success "PyMarkdown scan passed"
        deactivate 2>/dev/null || true
        return 0
    else
        print_error "PyMarkdown scan failed"
        [ -n "$status_file" ] && echo "Markdown - PyMarkdown scan" >> "$status_file"
        deactivate 2>/dev/null || true
        return 1
    fi
}

# ---- Collect status from a status file into FAILED_CHECKS ----
_collect_status() {
    local status_file=$1
    if [ -f "$status_file" ]; then
        while IFS= read -r line; do
            [ -n "$line" ] && FAILED_CHECKS+=("$line")
        done < "$status_file"
    fi
}

# ---- Run requested checks ----
if [ "$PARALLEL" = true ]; then
    print_info "Running requested checks in parallel, please wait..."

    pids=()
    temp_files=()
    status_files=()

    if _code_checks_any_scheduled; then
        code_output="$TEMP_DIR/code.log"
        code_status="$TEMP_DIR/code.status"
        temp_files+=("$code_output")
        status_files+=("$code_status")
        run_code_checks "$code_output" "$code_status" &
        pids+=($!)
    fi

    if [ "$RUN_SPHINX" = true ] && [ "$ENABLE_SPHINX" = true ]; then
        sphinx_output="$TEMP_DIR/sphinx.log"
        sphinx_status="$TEMP_DIR/sphinx.status"
        temp_files+=("$sphinx_output")
        status_files+=("$sphinx_status")
        run_sphinx_build "$sphinx_output" "$sphinx_status" &
        pids+=($!)
    fi

    if [ "$RUN_PYMARKDOWN" = true ] && [ "$ENABLE_PYMARKDOWN" = true ]; then
        markdown_output="$TEMP_DIR/markdown.log"
        markdown_status="$TEMP_DIR/markdown.status"
        temp_files+=("$markdown_output")
        status_files+=("$markdown_status")
        run_markdown_checks "$markdown_output" "$markdown_status" &
        pids+=($!)
    fi

    # Wait for all jobs; any non-zero exit sets EXIT_CODE=1
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            EXIT_CODE=1
        fi
    done

    # Collect named failures from status files
    for status_file in "${status_files[@]}"; do
        _collect_status "$status_file"
    done

    # Safety net: if any status file had content, ensure EXIT_CODE reflects it
    [ ${#FAILED_CHECKS[@]} -gt 0 ] && EXIT_CODE=1

    # Print all outputs in a fixed order
    echo ""
    for log_file in "${temp_files[@]}"; do
        [ -f "$log_file" ] && cat "$log_file"
    done
else
    # Sequential — pass a status file so FAILED_CHECKS is populated
    if _code_checks_any_scheduled; then
        code_status="$TEMP_DIR/code.status"
        if ! run_code_checks "" "$code_status"; then
            EXIT_CODE=1
        fi
        _collect_status "$code_status"
    fi

    if [ "$RUN_SPHINX" = true ] && [ "$ENABLE_SPHINX" = true ]; then
        sphinx_status="$TEMP_DIR/sphinx.status"
        if ! run_sphinx_build "" "$sphinx_status"; then
            EXIT_CODE=1
        fi
        _collect_status "$sphinx_status"
    fi

    if [ "$RUN_PYMARKDOWN" = true ] && [ "$ENABLE_PYMARKDOWN" = true ]; then
        markdown_status="$TEMP_DIR/markdown.status"
        if ! run_markdown_checks "" "$markdown_status"; then
            EXIT_CODE=1
        fi
        _collect_status "$markdown_status"
    fi
fi

# ---- Summary ----
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
ELAPSED_SECONDS=$((ELAPSED % 60))

print_header "Summary"

if [ "$EXIT_CODE" -eq 0 ]; then
    print_success "All checks passed!"
    echo -e "${GREEN}${BOLD}✓ SUCCESS${RESET} - All checks completed successfully"
else
    print_error "Some checks failed:"
    if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
        echo -e "  ${RED}✗${RESET} One or more checks failed (see output above)"
    else
        for check in "${FAILED_CHECKS[@]}"; do
            echo -e "  ${RED}✗${RESET} $check"
        done
        echo -e "${RED}${BOLD}✗ FAILURE${RESET} - ${#FAILED_CHECKS[@]} check(s) failed"
    fi
fi

echo ""
print_info "Total time: ${MINUTES}m ${ELAPSED_SECONDS}s"
echo ""

exit "$EXIT_CODE"
