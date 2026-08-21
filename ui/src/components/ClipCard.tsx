/** One candidate clip. Training-data facts only — no engagement metrics.
 *
 * The card carries a checkbox because the next step in the flow is "send these
 * to the Datalake": selecting here is what fills the collection queue.
 */

import { useState } from "react";

import { durationLabel, safeUrl } from "../lib/format";
import type { Clip } from "../lib/types";
import { AnnotationTree } from "./AnnotationTree";
import { Pill } from "./primitives";

const REUSABLE = new Set(["creativecommon", "creative_commons", "cc-by", "cc0", "public"]);

export function ClipCard({
  clip,
  selected,
  onToggleSelected,
}: {
  clip: Clip;
  selected: boolean;
  onToggleSelected: () => void;
}) {
  const [open, setOpen] = useState(false);
  const href = safeUrl(clip.url);
  const thumb = safeUrl(clip.thumbnail_url);
  const licence = String(clip.license ?? "").toLowerCase().replace(/\s+/g, "");
  const reusable = REUSABLE.has(licence);

  return (
    <article className={open ? "card card--open" : "card"}>
      {thumb ? (
        <div className="card__thumb">
          <img src={thumb} alt="" loading="lazy" referrerPolicy="no-referrer" />
          <span className="card__badge">{clip.platform}</span>
          {durationLabel(clip) !== "—" ? (
            <span className="card__duration">{durationLabel(clip)}</span>
          ) : null}
        </div>
      ) : (
        // No preview to show: a strip with the same facts beats 11rem of grey.
        <div className="card__strip">
          <span>{clip.platform}</span>
          <span className="mono">{durationLabel(clip)}</span>
        </div>
      )}

      <div className="card__body">
        <h3 className="card__title">
          {href ? (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {clip.title ?? clip.url}
            </a>
          ) : (
            (clip.title ?? clip.url)
          )}
        </h3>

        <div className="row" style={{ gap: "var(--space-1)" }}>
          <Pill tone={clip.viewpoint === "unknown" ? "muted" : "plain"}>
            {clip.viewpoint}
            {clip.viewpoint_confidence > 0 ? ` ${clip.viewpoint_confidence.toFixed(2)}` : ""}
          </Pill>
          {clip.license ? (
            <Pill tone={reusable ? "pass" : "muted"}>{reusable ? "reusable" : clip.license}</Pill>
          ) : null}
          {clip.quality_grade ? <Pill tone="plain">grade {clip.quality_grade}</Pill> : null}
          {clip.annotation_level ? <Pill tone="plain">{clip.annotation_level}</Pill> : null}
        </div>

        {clip.creator ? <span className="card__meta">{clip.creator}</span> : null}
        {clip.relevance_note ? <p className="card__note">{clip.relevance_note}</p> : null}

        <div className="card__meta">
          {clip.usability_score > 0 ? <span>usability {clip.usability_score.toFixed(2)}</span> : null}
          {clip.datalake_video_id ? <span>indexed</span> : null}
        </div>
      </div>

      <div className="card__foot">
        <label className="checkbox">
          <input type="checkbox" checked={selected} onChange={onToggleSelected} />
          <span>Collect</span>
        </label>
        <button type="button" className="button button--small button--ghost" onClick={() => setOpen(!open)}>
          {open ? "Hide tree" : "Annotation tree"}
        </button>
      </div>

      {open ? (
        <div className="card__tree">
          <AnnotationTree clip={clip} />
        </div>
      ) : null}
    </article>
  );
}
