---
name: video-searching
description: Run the Video Searching Agent with deterministic, concise chat UX for /video_searching using a pinned self-bootstrap runtime.
user-invocable: true
metadata: {"openclaw":{"os":["darwin","linux"],"homepage":"https://github.com/Memories-ai-labs/video-searching-agent","requires":{"bins":["git","uv"],"env":["GOOGLE_API_KEY","YOUTUBE_API_KEY"]}}}
---

# Video Searching Skill

Use this skill when the user asks to find, compare, or analyze social videos (YouTube, TikTok, Instagram, Twitter/X), or explicitly invokes `/video_searching`.

This workflow expects host runtime execution (sandbox mode off).
The runner auto-bootstraps a pinned runtime from `Memories-ai-labs/video-searching-agent@v0.2.5` when `VIDEO_SEARCHING_AGENT_ROOT` is not set.

## Triggering

Run this workflow when either condition is true:

1. Message starts with `/video_searching`.
2. The user asks for video searching/trend/creator/brand analysis and wants concrete video links.

If `/video_searching` is used with no query body, ask for the missing query.

## Execution contract

1. Resolve query text:
   - `/video_searching ...` => strip `/video_searching` and use remaining text.
   - Free-form => use user message as query.
2. Default to compact mode:
   - `--event-detail compact`
3. If user asks for debugging/raw payloads:
   - Switch to `--event-detail verbose`

### `/video_searching` deterministic path

1. Build command with required args:
   - `<skill_dir>/scripts/run_video_query.sh --query "<query>" --event-detail <compact|verbose> --ux-mode three_message --progress-gate-seconds 5`
2. Start with `exec` using `background: true` and explicit timeout:
   - `timeout: 420`
3. Poll with `process` using `action: "poll"` every 2-4 seconds until process exits.
4. Parse NDJSON output and render only these events, using your persona voice for all user-facing text:
   - `started` => send a brief message conveying that video searching has begun, written in your persona voice
   - `ux_progress` => read the `summary` field as structured status data and compose a concise,
     natural progress update in your persona voice (do not echo `summary` verbatim)
     Send each `ux_progress` as a separate assistant message in Telegram.
   - terminal event (`complete`, `clarification_needed`, `error`) => send final message as-is
5. Do not forward raw `progress`, `tool_call`, or `tool_result` events for `/video_searching`.
6. Preserve the user's existing OpenClaw personality behavior across all messages — progress and final alike.
7. Never launch a second run while a prior run session is still active.
   - If retrying, call `process` with `action: "kill"` for the prior `sessionId` first.
8. If process exits without a terminal event, send a concise fallback message that:
   - states run ended before completion,
   - includes one actionable next step,
   - does not start another run automatically.

Behavior target for `/video_searching`:

1. Fast run (<5s): 2 messages (`started`, terminal).
2. Longer run (>=5s): recurring throttled `ux_progress` updates, then terminal.

### Free-form path (non-strict)

1. Keep existing flexible behavior.
2. Build command without forcing `three_message` mode:
   - `<skill_dir>/scripts/run_video_query.sh --query "<query>" --event-detail <compact|verbose>`
3. Stream useful progress updates and final response naturally.

## Final response format

When terminal event is `complete`:

1. One short paragraph conclusion.
2. Top 3 video references only by default:
   - `title`
   - `url`
   - one-line relevance note
3. `Tools used: ...` with a compact status summary.

If fewer than 3 videos exist, show all available references.

When terminal event is `clarification_needed`:

1. Ask the clarification question directly.
2. Treat this as the final response for the current run.

When terminal event is `error`:

1. Send concise failure reason.
2. Include one actionable next step.

## Safety and fallback

1. If script fails due to missing env/tooling, explain exact missing piece (for example `VIDEO_SEARCHING_AGENT_ROOT`, `uv`, or API key env var).
2. If `VIDEO_SEARCHING_AGENT_ROOT` is unset, the runner uses managed path:
   - `~/.openclaw/data/video-searching-agent/v0.2.5`
3. `VIDEO_SEARCHING_AGENT_ROOT` remains an advanced override for local development.
4. Keep response concise and action-oriented.
5. Never fabricate video URLs or metrics.
