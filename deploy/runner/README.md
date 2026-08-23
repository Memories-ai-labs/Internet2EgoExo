# Standing up the runner without an SSH client

`bootstrap.sh` is the whole deployment, and it is idempotent — deploying a code
change is the same command again. What this file adds is the path in: the
first bootstrap of a fresh box, done from the provider's web console, by
someone who can reach the machine.

That constraint is not hypothetical. A Claude Code session's egress carries
443 and 80 and nothing else, so port 22 is unreachable from one, and the image
ships no `ssh` client — an agent cannot do this step no matter how the keys are
handed to it. Anything below is meant to be pasted into a console session on
the host.

## First bootstrap

Paste as root on a fresh Ubuntu box. The keys are the only part that needs
thought; everything after them is fixed.

```bash
install -d -m 700 /etc/egoexo
cat > /etc/egoexo/env <<'ENV'
OPENROUTER_API_KEY=sk-or-…
GOOGLE_API_KEY=…
YOUTUBE_API_KEY=…
MEMORIES_API_KEY=sk-mai-…
EXA_API_KEY=…
# Only if this host will be reachable from anywhere but itself — see below.
API_KEYS=
ENV
chmod 600 /etc/egoexo/env

git clone https://github.com/Memories-ai-labs/Internet2EgoExo /opt/egoexo/video-searching-agent
REPO=https://github.com/Memories-ai-labs/Internet2EgoExo \
  bash /opt/egoexo/video-searching-agent/deploy/runner/bootstrap.sh
```

`REPO` is passed explicitly because the script's default is the private
`video-searching-agent`, which clones only for someone holding credentials for
it. The public mirror is the same tree, and it clones unattended — which is
what a console paste needs.

`.env.example` lists every key the app reads; the five above are what a run
actually spends against. `bootstrap.sh` refuses to start without
`/etc/egoexo/env`, on purpose: it installs no secrets of its own.

It ends by waiting for the API's own health check, so a clean exit means the
service is up. If it exits complaining instead:

```bash
systemctl status egoexo-api --no-pager
journalctl -u egoexo-api -n 50 --no-pager
systemctl list-timers egoexo-eval.timer --no-pager
```

One host at a time: the GitHub `eval` workflow and `egoexo-eval.timer` both
fire at 06:50 UTC, and running both buys the same daily datapoint twice.
Disable the workflow's schedule when the VM takes over.

## Reaching it from somewhere else

`egoexo-api.service` binds `127.0.0.1:8099` deliberately. The runner exists to
measure the app on a schedule, and an eval does not need the port to be public
— so nothing above opens one.

Publishing it is a separate decision with a real cost attached: every endpoint
past `/ui/` and `/api/v1/health` spends the owner's OpenRouter and Datalake
credits, so an open port is an open tab. Set `API_KEYS` first — the middleware
turns auth on the moment it is non-empty, the UI then asks for the key in its
sidebar, and the health endpoint reports `auth_required: true`. The snippet
below refuses to run without one.

```bash
if ! grep -qE '^API_KEYS=.+' /etc/egoexo/env; then
  echo "set API_KEYS in /etc/egoexo/env first — this would publish an open API" >&2
else
apt-get install -y -qq --no-install-recommends nginx
cat > /etc/nginx/sites-available/egoexo <<'CONF'
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:8099;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        # The whole UI is server-sent events; buffering them turns a live run
        # into a five-minute pause followed by everything at once.
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
CONF
ln -sf /etc/nginx/sites-available/egoexo /etc/nginx/sites-enabled/egoexo
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
fi
```

The guard is an `if` rather than an `exit`, because this is meant to be pasted
into an interactive console and an `exit` there closes the session.

## Browser QA against the deployment

Once it answers on 80, the same walk that runs against a laptop runs against
the host — no SSH involved, which means a session that cannot reach port 22
can still test the real deployment:

```bash
cd ui && npm install
QA_BASE=http://<host>/ui/ QA_API_KEY=<one of API_KEYS> \
  node qa/flow.mjs qa/shots
```

`QA_API_KEY` is seeded into the same `localStorage` slot the sidebar writes, so
the run authenticates exactly as a person does. Without it the walk dies at the
first search with a 401 — which is the correct behaviour, not a bug in the run.
