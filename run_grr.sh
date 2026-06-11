#!/bin/bash
# 启动 GRR GUI
# Usage: ./run_grr.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

export MPLCONFIGDIR="/tmp/mpl_grr"
mkdir -p "$MPLCONFIGDIR"

PY=$(command -v python3 || command -v python)
$PY grr_gui.py "$@"
