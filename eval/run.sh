#!/usr/bin/env bash
# The one definition of how a measurement is taken.
#
# Every host that runs the eval calls this: the GitHub workflows, an always-on
# VM under systemd, a laptop. It exists because the invocation had already been
# written out twice in YAML (the slice job and the chunk job) and was about to
# be written a third time in a systemd unit — and a rule derived in two places
# eventually disagrees (docs/autoresearch/LEARNINGS.md L1). A chunk that forgot
# --resume, or a host that started the server differently, would bill again for
# queries already paid for and put two populations in one record file.
#
# Usage:
#   eval/run.sh [--limit N] [--resume] [--out PATH] [--per-query N]
#               [--queries PATH] [-- EXTRA ARGS FOR run_eval.py]
#
#   --limit N     run the first N of the frozen set (omit for the whole set)
#   --resume      skip queries already in --out instead of paying again
#   --out PATH    record file, default eval/results/slice.jsonl
#
# Environment:
#   PORT            port for the API this measures, default 8099
#   QA_DEPLOYMENT   set by this script from PORT unless already set
#   START_SERVER    0 to measure a server that is already running elsewhere
#
# It starts the API if nothing healthy is listening, waits for health, runs the
# eval, then scores the records — scoring is free and always runs, so a failed
# or interrupted run still leaves a readable scorecard beside its records.
set -euo pipefail

cd "$(dirname "$0")/.."

limit=""
resume=0
out="eval/results/slice.jsonl"
per_query="2"
queries="eval/queries-v1.1.json"
extra=()

while [ $# -gt 0 ]; do
  case "$1" in
    --limit) limit="$2"; shift 2 ;;
    --resume) resume=1; shift ;;
    --out) out="$2"; shift 2 ;;
    --per-query) per_query="$2"; shift 2 ;;
    --queries) queries="$2"; shift 2 ;;
    --) shift; extra=("$@"); break ;;
    *) echo "eval/run.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done

port="${PORT:-8099}"
export QA_DEPLOYMENT="${QA_DEPLOYMENT:-http://127.0.0.1:$port}"
health="$QA_DEPLOYMENT/api/v1/health"
mkdir -p "$(dirname "$out")"

# Keys, checked before anything is spent. Never printed — only named.
missing=""
for name in OPENROUTER_API_KEY GOOGLE_API_KEY YOUTUBE_API_KEY \
            MEMORIES_API_KEY APIFY_API_TOKEN; do
  [ -n "${!name:-}" ] || missing="$missing $name"
done
if [ -n "$missing" ]; then
  echo "eval/run.sh: missing required keys:$missing" >&2
  exit 1
fi

if [ "${START_SERVER:-1}" = "1" ] && ! curl -sf "$health" >/dev/null 2>&1; then
  echo "starting the API on port $port"
  nohup uv run uvicorn src.video_searching_agent.web.main:app \
    --host 127.0.0.1 --port "$port" > server.log 2>&1 &
  for _ in $(seq 1 90); do
    curl -sf "$health" >/dev/null 2>&1 && break
    sleep 1
  done
fi

if ! curl -sf "$health" >/dev/null 2>&1; then
  echo "eval/run.sh: the API never became healthy at $health" >&2
  [ -f server.log ] && tail -40 server.log >&2
  exit 1
fi

args=(--queries "$queries" --per-query "$per_query" --out "$out" --yes)
[ -n "$limit" ] && args+=(--limit "$limit")
[ "$resume" = 1 ] && args+=(--resume "$out")

before=0
[ -f "$out" ] && before=$(wc -l < "$out")
echo "records before this run: $before  ->  $out"

set +e
uv run python eval/run_eval.py "${args[@]}" ${extra[@]+"${extra[@]}"}
status=$?
set -e

# A completed run prints its own scorecard, so this is only for the run that
# died partway: free, and an interrupted run is still a datapoint. Skipped on
# success rather than printed twice.
if [ "$status" != 0 ]; then
  uv run python eval/run_eval.py --score-only "$out" || true
fi

after=0
[ -f "$out" ] && after=$(wc -l < "$out")
echo "records after this run: $after (added $((after - before)))"
exit "$status"
