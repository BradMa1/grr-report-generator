#!/bin/bash
# =============================================================================
# GRR Reporter Launcher — .app bundle wrapper
# =============================================================================
# This is the CFBundleExecutable for the .app bundle.
# It simply opens the .command file in Terminal, where the user can see output.
# If you prefer a direct terminal approach, use "GRR Reporter.command" instead.
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMMAND_FILE="$PROJECT_DIR/GRR Reporter.command"

if [ -f "$COMMAND_FILE" ]; then
    open "$COMMAND_FILE"
else
    # Fallback: run run.sh directly via Terminal
    RUN_SH="$PROJECT_DIR/run.sh"
    osascript -e "
    tell application \"Terminal\"
        activate
        do script \"clear && echo '=== GRR Reporter ===' && \\\"$RUN_SH\\\" && echo '' && echo 'Done - you can close this window'\"
    end tell
    "
fi

exit 0
