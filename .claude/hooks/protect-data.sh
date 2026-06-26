#!/bin/bash
# PreToolUse hook: keep data/ read-only.
#
# CLAUDE.md mandates "keep data/ as read-only inputs" — every claim number
# derives from those CSVs + the PDF, so an accidental Edit/Write to them would
# silently invalidate the whole reconciliation. This denies such writes.
#
# Input: PreToolUse JSON on stdin (tool_name = Edit|Write, tool_input.file_path).
# Output: permissionDecision "deny" if the target is under <project>/data/.
set -euo pipefail

input=$(cat)
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')

# No file path (shouldn't happen for Edit/Write) -> stay silent, normal flow.
[ -z "$file_path" ] && exit 0

project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Canonicalize both sides: collapse `..` and resolve symlinks so that paths
# like agent/../data/x.csv (which resolve INTO data/) can't slip past a naive
# string-prefix check. python3 is guaranteed available; realpath -m is not on
# macOS. os.path.realpath works even when the target file doesn't exist yet.
canon() { python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1" 2>/dev/null; }

data_dir="$(canon "$project_dir/data")/"

case "$file_path" in
  /*) abs="$file_path" ;;
  *)  abs="$project_dir/$file_path" ;;
esac
abs="$(canon "$abs")"
[ -z "$abs" ] && exit 0

case "$abs" in
  "$data_dir"*)
    jq -nc --arg f "$file_path" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ("data/ is read-only ground truth (per CLAUDE.md). Refusing to write \($f). If a source value is genuinely wrong, raise it with the user rather than editing the input.")
      }
    }'
    ;;
  *)
    exit 0
    ;;
esac
