/** Turning numbers into something readable, and nothing into an em dash.
 *
 * Every formatter here returns `DASH` for a value that is absent or not
 * finite, rather than "0" or "—" spelled differently in nine places. The
 * distinction is load-bearing in this UI: a zero is a measurement and a dash is
 * the absence of one, and a panel that renders them the same way invites
 * somebody to quote an unmeasured figure.
 */

import type { Clip } from "./types";

export const DASH = "—";

/** Seconds as `m:ss`. Negative and fractional values are floored, not rounded. */
export function timecode(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return DASH;
  const whole = Math.max(Math.floor(seconds), 0);
  const minutes = Math.floor(whole / 60);
  const rest = whole % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

/** A clip's length: whatever the platform already formatted, else the seconds. */
export function durationLabel(clip: Clip): string {
  if (clip.duration) return clip.duration;
  if (clip.duration_seconds) return timecode(clip.duration_seconds);
  return DASH;
}

export function hours(value: number | null | undefined, places = 2): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return `${value.toFixed(places)}h`;
}

export function money(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return `$${value.toFixed(2)}`;
}

export function percent(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return DASH;
  return `${Math.round(value * 100)}%`;
}

/** A count map as `label n · label n`, biggest first. */
export function mix(counts: Record<string, number> | null | undefined): string {
  const entries = Object.entries(counts ?? {}).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return DASH;
  return entries.map(([name, count]) => `${name} ${count}`).join(" · ");
}

/** An href only if it is one, and only http(s).
 *
 * Search results carry URLs from other people's pages; rendering one into an
 * anchor without checking the scheme is how a `javascript:` href gets clicked.
 */
export function safeUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : null;
  } catch {
    return null;
  }
}

/** A tool name as prose: `youtube_search` reads as `youtube search`. */
export function toolLabel(name: string): string {
  return name.replace(/_/g, " ");
}
