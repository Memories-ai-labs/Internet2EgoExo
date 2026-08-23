/** The small formatters, in one place so a number reads the same everywhere.
 *
 * Every one of them answers "unknown" with an em dash rather than a zero: a
 * clip whose duration nobody has is not a clip of zero length, and a cost
 * nobody measured is not free.
 */

export const DASH = "—";

/** Seconds as m:ss. */
export function timecode(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || !Number.isFinite(seconds)) return DASH;
  const whole = Math.max(Math.floor(seconds), 0);
  const minutes = Math.floor(whole / 60);
  const rest = whole % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

/** What a clip says its length is, preferring the platform's own string. */
export function durationLabel(clip: {
  duration?: string | null;
  duration_seconds?: number | null;
}): string {
  if (clip.duration) return clip.duration;
  if (clip.duration_seconds) return timecode(clip.duration_seconds);
  return DASH;
}

export function hours(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return DASH;
  return `${value.toFixed(digits)}h`;
}

export function money(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return DASH;
  return `$${value.toFixed(2)}`;
}

export function percent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return DASH;
  return `${Math.round(value * 100)}%`;
}

/** A count-per-key map as "egocentric 2 · exocentric 1", commonest first. */
export function mix(counts: Record<string, number> | null | undefined): string {
  const entries = Object.entries(counts ?? {}).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return DASH;
  return entries.map(([key, count]) => `${key} ${count}`).join(" · ");
}

/** A URL only if it is one, and only if it is http(s).
 *
 * Clip URLs come from whatever the platform or the open web handed back, so
 * `javascript:` and `data:` have to be turned away before they reach an href.
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

/** A tool name as prose: `youtube_search` → `youtube search`. */
export function toolLabel(tool: string): string {
  return tool.replace(/_/g, " ");
}
