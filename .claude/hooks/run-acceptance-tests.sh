#!/bin/bash
# Stop hook: run the acceptance suite when agent/ or tests/ changed this turn.
#
# The headline numbers in the deliverables (€6,203 owed, recovery rate, per-
# supplier claims) are asserted in tests/test_acceptance.py. This guards against
# silently editing the engine and shipping docs whose numbers no longer hold.
#
# Behaviour:
#   - Hashes agent/*.py + tests/*.py. If unchanged since the last check, exits
#     silently (so it does NOT run on every turn, only after engine edits).
#   - On change, runs the zero-dependency test runner.
#       * pass  -> silent (systemMessage note to the user only).
#       * fail  -> injects the failing output as additionalContext so Claude
#                  fixes it before the work is considered done.
#   - The hash gate guarantees at most one re-run per distinct code state, so
#     a no-edit re-stop is allowed through and a runaway loop is impossible.
set -uo pipefail
shopt -s nullglob   # a non-matching *.py glob expands to nothing, not a literal

input=$(cat)
project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$project_dir" || exit 0

# Nothing to test if the engine/tests aren't present.
[ -d agent ] || exit 0
[ -f tests/test_acceptance.py ] || exit 0

state_file=".claude/.acceptance-state"
current_hash=$(cat agent/*.py tests/*.py 2>/dev/null | shasum | awk '{print $1}')
prev_hash=""
[ -f "$state_file" ] && prev_hash=$(cat "$state_file" 2>/dev/null)

# No engine/test change since the last run -> let Claude stop quietly.
if [ "$current_hash" = "$prev_hash" ]; then
  exit 0
fi

# Record the hash up front so a later no-op Stop won't re-run the suite.
mkdir -p "$(dirname "$state_file")"
printf '%s' "$current_hash" > "$state_file"

output=$(python3 tests/test_acceptance.py 2>&1)
status=$?

if [ "$status" -eq 0 ]; then
  summary=$(printf '%s' "$output" | tail -n 1)
  jq -nc --arg s "$summary" '{
    suppressOutput: true,
    systemMessage: ("Acceptance tests green after engine change — " + $s)
  }'
  exit 0
fi

jq -nc --arg out "$output" '{
  decision: "block",
  reason: ("Acceptance tests FAILED after an agent/ or tests/ change. The deliverable numbers are no longer backed by the suite. Fix before finishing:\n\n" + $out)
}'
