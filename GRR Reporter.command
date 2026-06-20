#!/bin/bash
# =============================================================================
# GRR Reporter — macOS double-click launcher
# =============================================================================
# Save this file and double-click it in Finder to launch (Terminal opens automatically).
# This is the simplest way to run GRR Reporter on macOS.
# =============================================================================

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
./run.sh
