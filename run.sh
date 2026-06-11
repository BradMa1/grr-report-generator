#!/bin/bash
# 启动 GRR GUI
# Usage: ./run.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

export MPLCONFIGDIR="/tmp/mpl_grr"
mkdir -p "$MPLCONFIGDIR"

# 优先用 python3，回退到 python
PY=$(command -v python3 || command -v python)

$PY grr_gui.py "$@"
