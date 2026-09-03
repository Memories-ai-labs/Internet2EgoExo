#!/usr/bin/env bash
# Drive the always-on runner from a laptop, over SSH.
#
# bootstrap.sh is what runs *on* the VM; this is how you reach it. The two are
# separate on purpose — bootstrap is idempotent and knows nothing about who
# invoked it, so it stays runnable from a console session when SSH is the thing
# that is broken.
#
# The host is not committed. It is one line of infrastructure that changes when
# the VM is rebuilt, and this repo is public, so it comes from the environment
# the same way deploy.sh resolves its VM address at call time rather than
# hardcoding one:
#
#   export EGOEXO_RUNNER_HOST=root@<vm-ip>
#   deploy/runner/remote.sh status
#
# EGOEXO_RUNNER_KEY overrides the key path (default ~/.ssh/egoexo).
#
# Note for agent sessions: an egress proxy that only forwards HTTPS cannot carry
# SSH, and the failure looks like the VM is down — a CONNECT succeeds and then
# no banner arrives. Test github.com:22 before blaming the host; if that is also
# silent, the session cannot reach any SSH server and this script will not work
# from it.
set -euo pipefail

host="${EGOEXO_RUNNER_HOST:-}"
key="${EGOEXO_RUNNER_KEY:-$HOME/.ssh/egoexo}"
root=/opt/egoexo/video-searching-agent
cmd="${1:-help}"

# Usage before configuration: the first thing somebody runs is `remote.sh` with
# no arguments, and answering that with "set EGOEXO_RUNNER_HOST" hides the list
# of verbs they are trying to read.
case "$cmd" in
  help|-h|--help)
    # The header comment, however long it grows — a fixed line range silently
    # starts printing code the moment somebody adds a paragraph to it.
    awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"
    echo
    echo "  status              units, next timer fire, API health"
    echo "  deploy [BRANCH]     re-run bootstrap.sh on BRANCH (default main)"
    echo "  eval-now            start one eval slice and follow it"
    echo "  logs [UNIT] [N]     last N lines of egoexo-UNIT (eval|api)"
    echo "  follow [UNIT]       tail -f that unit"
    echo "  shell               interactive session on the runner"
    exit 0
    ;;
esac

[ -n "$host" ] || {
  echo "set EGOEXO_RUNNER_HOST=root@<vm-ip> first" >&2
  exit 2
}
[ -f "$key" ] || {
  echo "no key at $key (set EGOEXO_RUNNER_KEY, or write the key there chmod 600)" >&2
  exit 2
}

run() { ssh -i "$key" -o StrictHostKeyChecking=accept-new "$host" "$@"; }

case "$cmd" in
  # Everything the runner is meant to be doing, in one screen: both units, the
  # timer's next fire, and whether the API the eval measures actually answers.
  status)
    run 'systemctl --no-pager status egoexo-api.service egoexo-eval.service || true
         systemctl list-timers --no-pager egoexo-eval.timer || true
         echo "--- health ---"
         curl -sf http://127.0.0.1:8099/api/v1/health || echo "API not answering"'
    ;;

  # Re-run bootstrap against a branch. This is the deploy: bootstrap itself
  # fetches, checks out, re-syncs dependencies, reinstalls the units and
  # health-checks. Safe to repeat, which is why there is no separate "update".
  #
  # The first bootstrap on a bare VM is not this — it needs /etc/egoexo/env
  # written by hand before anything can start, so it happens once from a console
  # session (see bootstrap.sh). After that the checkout exists and this works.
  deploy)
    branch="${2:-main}"
    run "test -x '$root/deploy/runner/bootstrap.sh'" || {
      echo "no checkout at $root — do the first bootstrap from a console session" >&2
      echo "(it needs /etc/egoexo/env written first; see deploy/runner/bootstrap.sh)" >&2
      exit 1
    }
    run "BRANCH='$branch' bash '$root/deploy/runner/bootstrap.sh'"
    ;;

  # One measurement now, outside the timer. It writes to the same dated file the
  # timer uses, so --resume in the unit still sees it and the day stays one
  # datapoint rather than two half-populations.
  eval-now)  run 'systemctl start egoexo-eval.service && journalctl -u egoexo-eval -f' ;;

  logs)      run "journalctl -u egoexo-${2:-eval} -n ${3:-200} --no-pager" ;;
  follow)    run "journalctl -u egoexo-${2:-eval} -f" ;;
  shell)     run ;;

  *)
    echo "unknown command: $cmd (try: $0 help)" >&2
    exit 2
    ;;
esac
