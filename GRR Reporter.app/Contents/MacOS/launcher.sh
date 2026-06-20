#!/bin/bash
# =============================================================================
# GRR Reporter Launcher — Generic Version
# =============================================================================
# Works on any macOS system with Python 3.10+. Auto-detects Python environment,
# checks dependencies, and activates virtual environment if present.
# =============================================================================

# --- Locate project root ---------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_DIR" || {
    echo "[ERROR] Failed to cd to project directory: $PROJECT_DIR"
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
}

# --- Suppress matplotlib font cache noise — unique per instance ----------
export MPLCONFIGDIR="/tmp/mpl_grr_$$"
mkdir -p "$MPLCONFIGDIR" 2>/dev/null

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Auto-detect Python ----------------------------------------------------
PYTHON=""
if [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
    info "Using virtual environment: venv/"
elif [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON="/opt/homebrew/bin/python3"
elif [ -x "/usr/local/bin/python3" ]; then
    PYTHON="/usr/local/bin/python3"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
else
    error "Python 3 not found!"
    echo ""
    echo "  Install from: https://www.python.org/downloads/"
    echo "  Or via Homebrew: brew install python@3.13"
    echo ""
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

info "Using Python: $PYTHON"

# --- Check Python version (require ≥ 3.10) ---------------------------------
PY_VER="$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)"
if [ -z "$PY_VER" ]; then
    error "Failed to get Python version!"
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

PY_MAJOR="${PY_VER%%.*}"; PY_MINOR="${PY_VER#*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    error "Python $PY_VER is too old. Need ≥ 3.10."
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

# --- Check / auto-install dependencies -------------------------------------
info "Checking dependencies..."
MISSING=$("$PYTHON" -c "
import importlib.metadata as im
required = ['pandas', 'numpy', 'scipy', 'matplotlib', 'reportlab']
for p in required:
    if p not in im.packages_distributions():
        print(p)
" 2>/dev/null)

if [ -n "$MISSING" ]; then
    warn "Installing: $MISSING"
    echo ""
    "$PYTHON" -m pip install -r requirements.txt --quiet
    if [ $? -ne 0 ]; then
        error "Failed to install dependencies!"
        echo "  Try manually: pip install -r requirements.txt"
        read -n 1 -s -r -p "Press any key to close..."
        exit 1
    fi
    info "Dependencies installed!"
fi

# --- Launch GUI ------------------------------------------------------------
info "Starting GRR Reporter..."
echo ""

"$PYTHON" grr_gui.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    error "GRR Reporter exited with code $EXIT_CODE"
    echo "  If this keeps happening, try running from Terminal:"
    echo "    cd $(pwd) && ./run.sh"
    echo ""
    read -n 1 -s -r -p "Press any key to close..."
fi
