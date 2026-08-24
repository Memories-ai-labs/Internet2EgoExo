/** The manifest, in the two shapes something downstream can read.
 *
 * JSONL because an ingest pipeline reads a clip per line and never has to hold
 * the whole set in memory; CSV because a spreadsheet is still how most people
 * check a dataset before they trust it.
 *
 * The column list is explicit rather than derived from the object's keys. A
 * derived header changes silently when the API adds a field, which breaks
 * whatever was parsing yesterday's file — and it would emit the nested
 * annotations as `[object Object]`.
 */

import type { Clip, Manifest } from "./types";

const COLUMNS: [string, (clip: Clip) => string][] = [
  ["url", (c) => c.url],
  ["platform", (c) => c.platform],
  ["title", (c) => c.title ?? ""],
  ["creator", (c) => c.creator ?? ""],
  ["duration_seconds", (c) => String(c.duration_seconds ?? "")],
  ["viewpoint", (c) => c.viewpoint],
  ["viewpoint_confidence", (c) => c.viewpoint_confidence.toFixed(2)],
  ["license", (c) => c.license ?? ""],
  ["commercial_use_ok", (c) => String(c.commercial_use_ok ?? false)],
  ["usability_score", (c) => c.usability_score.toFixed(3)],
  ["quality_grade", (c) => c.quality_grade ?? ""],
  ["quality_score", (c) => String(c.quality_score ?? "")],
  ["annotation_level", (c) => c.annotation_level ?? ""],
  ["usable_seconds", (c) => String(c.usable_seconds ?? "")],
  ["idle_seconds", (c) => String(c.idle_seconds ?? "")],
  ["task_family", (c) => c.task_family ?? ""],
  ["dup_group_id", (c) => c.dup_group_id ?? ""],
  ["datalake_video_id", (c) => c.datalake_video_id ?? ""],
  ["annotations", (c) => String(c.annotations?.length ?? 0)],
];

/** Quote a cell only when it needs it, doubling any quote inside. */
function cell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

/** One clip per line, whole — for an ingest pipeline. */
export function manifestToJsonl(manifest: Manifest): string {
  return manifest.clips.map((clip) => JSON.stringify(clip)).join("\n");
}

/** The flat columns, for a spreadsheet. */
export function manifestToCsv(manifest: Manifest): string {
  const header = COLUMNS.map(([name]) => name).join(",");
  const rows = manifest.clips.map((clip) =>
    COLUMNS.map(([, read]) => cell(read(clip))).join(","),
  );
  return [header, ...rows].join("\n");
}

/** Hand the browser a file. Revoked immediately: the click already happened. */
export function download(filename: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const href = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = href;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(href);
}
