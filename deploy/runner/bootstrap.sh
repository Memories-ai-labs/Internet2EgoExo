#!/usr/bin/env bash
# Turn a plain Ubuntu VM into the always-on runner. Idempotent: safe to re-run
# after a code change, which is the normal way to deploy here.
#
# Platform-neutral on purpose. GCE, EC2, Azure and Hetzner differ in how you get
# a shell and what you pay; none of them differ in anything below, so the choice
# of provider does not fork this script. The team already has a GCE instance
# (`video-searching-api`, us-central1-a) that deploy.sh talks to — that is the
# cheapest host to try first, because it exists.
#
#   1. create /etc/egoexo/env with the keys (see .env.example), chmod 600
#   2. sudo bash deploy/runner/bootstrap.sh
#
# What it does NOT do: put keys anywhere. /etc/egoexo/env is written by hand,
# read only by root and the service user, and never committed.
#
# Once there is a checkout, deploy/runner/remote.sh drives all of this over SSH.
set -euo pipefail

# The public mirror, not the private video-searching-agent this code started in.
# The clone below carries no credentials — by design, since the script's whole
# stance is that it installs no secrets — so a private URL fails here on a fresh
# VM, and fails at the one moment there is no checkout to read this comment
# from. Both hold the same tree; only this one clones unattended.
REPO="${REPO:-https://github.com/Memories-ai-labs/Internet2EgoExo}"
BRANCH="${BRANCH:-main}"
ROOT=/opt/egoexo/video-searching-agent
UNITS="$(cd "$(dirname "$0")" && pwd)"

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }
[ -f /etc/egoexo/env ] || {
  echo "create /etc/egoexo/env first (keys, one KEY=value per line, chmod 600)" >&2
  exit 1
}
chmod 600 /etc/egoexo/env

apt-get update -qq
apt-get install -y -qq --no-install-recommends git curl ca-certificates

id egoexo >/dev/null 2>&1 || useradd --system --create-home --shell /bin/bash egoexo
chown -R egoexo:egoexo /etc/egoexo

# uv, installed to a path both the units and a human shell can see.
if ! [ -x /usr/local/bin/uv ]; then
  curl -fsSL https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh
fi

mkdir -p "$(dirname "$ROOT")"
if [ -d "$ROOT/.git" ]; then
  git -C "$ROOT" fetch origin "$BRANCH"
  git -C "$ROOT" checkout -B "$BRANCH" "origin/$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO" "$ROOT"
fi
chown -R egoexo:egoexo "$ROOT"

sudo -u egoexo env PATH=/usr/local/bin:/usr/bin:/bin \
  sh -c "cd '$ROOT' && uv sync --all-extras"

install -m 644 "$UNITS"/egoexo-api.service /etc/systemd/system/
install -m 644 "$UNITS"/egoexo-eval.service /etc/systemd/system/
install -m 644 "$UNITS"/egoexo-eval.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now egoexo-api.service
systemctl enable --now egoexo-eval.timer

for _ in $(seq 1 60); do
  curl -sf http://127.0.0.1:8099/api/v1/health >/dev/null && break
  sleep 1
done
curl -sf http://127.0.0.1:8099/api/v1/health >/dev/null || {
  echo "the API did not come up; journalctl -u egoexo-api -n 50" >&2
  exit 1
}

echo "runner up. next eval: $(systemctl show -p NextElapseUSecRealtime --value egoexo-eval.timer)"
echo "run one now:  systemctl start egoexo-eval.service"
echo "watch it:     journalctl -u egoexo-eval -f"
