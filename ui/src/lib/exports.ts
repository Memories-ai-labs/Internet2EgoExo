/** The manifest, as a file someone can hand to a training pipeline.
 *
 * JSONL keeps every field, including the annotation tree; CSV is the flat view
 * for a spreadsheet and names its columns explicitly, so a new field in the
 * manifest cannot silently reorder somebody's importer.
 */

import type { Clip, Manifest } from "./types";

const COLUMNS: Array<[string, (clip: Clip) => string]> = [
  ["url", (clip) => clip.url],
  ["platform", (clip) => clip.platform],
  ["title", (clip) => clip.title ?? ""],
  ["creator", (clip) => clip.creator ?? ""],
  ["duration_seconds", (clip) => String(clip.duration_seconds ?? "")],
  ["viewpoint", (clip) => clip.viewpoint],
  ["viewpoint_confidence", (clip) => clip.viewpoint_confidence.toFixed(2)],
  ["license", (clip) => clip.license ?? ""],
  ["commercial_use_ok", (clip) => String(clip.commercial_use_ok ?? false)],
  ["usability_score", (clip) => clip.usability_score.toFixed(3)],
  ["quality_grade", (clip) => clip.quality_grade ?? ""],
  ["quality_score", (clip) => String(clip.quality_score ?? "")],
  ["annotation_level", (clip) => clip.annotation_level ?? ""],
  ["usable_seconds", (clip) => String(clip.usable_seconds ?? "")],
  ["idle_seconds", (clip) => String(clip.idle_seconds ?? "")],
  ["task_family", (clip) => clip.task_family ?? ""],
  ["dup_group_id", (clip) => clip.dup_group_id ?? ""],
  ["datalake_video_id", (clip) => clip.datalake_video_id ?? ""],
  ["annotations", (clip) => String(clip.annotations?.length ?? 0)],
];

function cell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

export function manifestToJsonl(manifest: Manifest): string {
  return manifest.clips.map((clip) => JSON.stringify(clip)).join("\n");
}

export function manifestToCsv(manifest: Manifest): string {
  const header = COLUMNS.map(([name]) => name).join(",");
  const rows = manifest.clips.map((clip) =>
    COLUMNS.map(([, read]) => cell(read(clip))).join(","),
  );
  return [header, ...rows].join("\n");
}

/** Hand the browser a file. No server round trip: the data is already here. */
export function download(filename: string, body: string, type: string): void {
  const blob = new Blob([body], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
