#!/bin/bash
# =============================================================================
# GRR Reporter GUI Launcher
# =============================================================================
# Works on macOS / Linux / WSL. Auto-detects Python, checks dependencies,
# installs missing ones if needed.
# =============================================================================

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Suppress matplotlib font cache noise
export MPLCONFIGDIR="/tmp/mpl_grr"
mkdir -p "$MPLCONFIGDIR"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Auto-detect Python ----------------------------------------------------
PYTHON=""
if [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
    info "Using virtual environment: venv/"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
elif command -v python &>/dev/null; then
    PYTHON="$(command -v python)"
else
    error "Python 3 not found! Install from https://www.python.org/downloads/"
    exit 1
fi

info "Using Python: $PYTHON"

# --- Python version check --------------------------------------------------
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR="${PY_VER%%.*}"; PY_MINOR="${PY_VER#*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    error "Python $PY_VER is too old. Need ≥ 3.10."
    exit 1
fi

# --- Dependency check ------------------------------------------------------
info "Checking dependencies..."
MISSING=$("$PYTHON" -c "
import importlib.metadata as im
import sys
pkgs = im.packages_distributions()
required = ['pandas', 'numpy', 'scipy', 'matplotlib', 'reportlab']
for p in required:
    if p not in pkgs:
        print(p)
" 2>/dev/null)

if [ -n "$MISSING" ]; then
    warn "Missing: $MISSING"
    echo "  Installing with pip install -r requirements.txt..."
    "$PYTHON" -m pip install -r requirements.txt --quiet
    info "Dependencies installed!"
fi

# --- Launch ----------------------------------------------------------------
info "Starting GRR Reporter..."
exec "$PYTHON" grr_gui.py "$@"
