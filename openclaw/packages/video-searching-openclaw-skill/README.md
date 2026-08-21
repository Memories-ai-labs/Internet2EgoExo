# video-searching-openclaw-skill

Standalone OpenClaw skill package for deterministic self-bootstrap execution.

Default runtime source:

- `https://github.com/Memories-ai-labs/Internet-Video-Search`
- pinned tag: `v0.2.5`
- managed path: `~/.openclaw/data/video-searching-agent/v0.2.5`

`VIDEO_SEARCHING_AGENT_ROOT` is optional and only for local development override.

## Requirements

1. Host binaries on OpenClaw machine:
   - `git`
   - `uv`
2. Required API keys in OpenClaw global env:
   - `GOOGLE_API_KEY`
   - `YOUTUBE_API_KEY`
3. Sandbox off for host runtime flow.

## Install

1. Link or copy the skill folder to OpenClaw:

```bash
mkdir -p ~/.openclaw/skills
ln -sfn \
  /Users/samuelzhang/Documents/GitHub/video-searching-agent/openclaw/packages/video-searching-openclaw-skill/skills/video-searching \
  ~/.openclaw/skills/video-searching
```

2. Add env vars and enable skill in `~/.openclaw/openclaw.json`:

```json5
{
  env: {
    vars: {
      GOOGLE_API_KEY: "your_google_api_key",
      YOUTUBE_API_KEY: "your_youtube_data_api_key",
      MEMORIES_API_KEY: "optional_memories_key",
      EXA_API_KEY: "optional_exa_key",
      APIFY_API_TOKEN: "optional_apify_token",
    },
  },
  skills: {
    entries: {
      "video-searching": {
        enabled: true,
      },
    },
  },
}
```

3. Keep runtime tools allowlist compatible with this workflow:

```json5
{
  tools: {
    allow: ["exec", "process", "read", "memory_search"],
    deny: ["write", "edit", "apply_patch", "browser", "canvas", "cron", "gateway"],
  },
}
```

4. Ensure sandbox is disabled:

```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "off",
      },
    },
  },
}
```

5. Restart OpenClaw Gateway and use:

`/video_searching Find trending UGC videos for SaaS this week`

## Optional local override

Use this only if you want to run a local checkout instead of managed pinned runtime:

```json5
{
  skills: {
    entries: {
      "video-searching": {
        enabled: true,
        env: {
          VIDEO_SEARCHING_AGENT_ROOT: "/absolute/path/to/local/video-searching-agent",
        },
      },
    },
  },
}
```

## Runtime behavior

`/video_searching` deterministic runner mode:

1. Immediate start message.
2. Throttled progress updates after 5 seconds.
3. Final terminal result (`complete`, `clarification_needed`, `error`).
4. Runner command should set explicit timeout (`exec.timeout: 420`).
5. Kill prior process session before launching retries.

Free-form behavior remains non-strict.

## Typing indicator reliability

To reduce sticky Telegram `typing...` indicators during long polling loops:

```bash
openclaw config set agents.defaults.typingMode '"message"'
openclaw config set agents.defaults.typingIntervalSeconds 6
openclaw gateway restart
```

Expected behavior:

1. Start/progress/final messages still arrive normally.
2. Typing appears when text is actively emitted.
3. Typing clears shortly after terminal output (usually within 5-8 seconds).

## Troubleshooting

1. `Required binary not found on PATH: git` or `uv`
   - Install missing binaries on host.
2. `Required environment variable is not set: GOOGLE_API_KEY` / `YOUTUBE_API_KEY`
   - Add required keys in global env vars.
3. Clone/sync errors during first run
   - Confirm host can access GitHub and fetch tag `v0.2.5`.
4. No progress updates shown
   - Restart gateway and verify channel stream mode settings.
5. Typing indicator remains visible after final response
   - Set `agents.defaults.typingMode` to `"message"` and restart the gateway.
   - Fallback: `openclaw config set agents.defaults.typingMode '"never"'`.
   - Rollback: `openclaw config unset agents.defaults.typingMode` and `openclaw config unset agents.defaults.typingIntervalSeconds`.
