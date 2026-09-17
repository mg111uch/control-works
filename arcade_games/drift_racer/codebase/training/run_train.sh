#!/bin/bash
# Detached training launcher: unbuffered file logging, survives tool timeouts.
# Usage (from codebase/):  LOG=/tmp/opencode/p3.log ./training/run_train.sh --fresh --generations 30
# Default writes to training/models/ (single canonical dir). Custom dirs only for smoke:
# LOG=/tmp/opencode/smoke.log ./training/run_train.sh --pop-size 4 --episodes 1 --generations 1 --fresh --model-dir /tmp/opencode/smoke --proc-tracks 0 --tracks simple_oval
# Follow: tail -f <log> | Check: ps -p <pid>
# NEVER launch without the user's explicit permission (see README guardrail).
set -e
cd "$(dirname "$0")/.."
LOG="${LOG:-/tmp/opencode/drift_train.log}"
mkdir -p "$(dirname "$LOG")"
if pgrep -f "training/train_nn.py" > /dev/null; then
  echo "REFUSING: a train_nn.py process is already running:"
  pgrep -af "training/train_nn.py"
  exit 1
fi
PYTHONUNBUFFERED=1 nohup conda run --no-capture-output -n myenv python -u training/train_nn.py "$@" > "$LOG" 2>&1 &
echo "PID $!  LOG $LOG"
