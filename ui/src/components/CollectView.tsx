/** Part two: get it into the Datalake, then let the agents clean and annotate it.
 *
 * Two panels, in the order the work happens:
 *
 *   Collect — download the selected candidates, index them, run the cleaning
 *   agent over the frames and the annotation agent over what survives. Every
 *   stage of every clip is streamed, because indexing takes minutes and a
 *   silent progress bar is not one.
 *
 *   Curate — grade a worklist that is already indexed: the hours ledger, the
 *   diversity checks, the duplicate groups, the batch grade.
 */

import { useRef, useState } from "react";

import { hours, percent, timecode } from "../lib/format";
import type { OwnKeys } from "../App";
import { streamRequest } from "../lib/sse";
import type { CurationResult, GateCheck, IngestClip } from "../lib/types";
import { AnnotationTreeFor } from "./AnnotationTree";
import { GateList } from "./GateList";
import { Empty, Field, Panel, Pill, Stat } from "./primitives";

const STAGES = [
  "probing",
  "downloading",
  "uploading",
  "indexing",
  "cleaning",
  "annotating",
] as const;

const TERMINAL: Record<string, string> = {
  accepted: "accepted",
  rejected: "rejected",
  skipped: "skipped",
  failed: "failed",
};

/** How far a clip actually got, which a terminal stage does not say by itself.
 *
 * A rejected clip stopped at cleaning and was never annotated; a skipped one
 * never got past the screen. Marking every stage done because the clip is
 * finished would claim work that did not happen.
 */
function furthestStage(clip: IngestClip): number {
  switch (clip.stage) {
    case "accepted":
      return STAGES.length - 1;
    case "rejected":
      return STAGES.indexOf("cleaning");
    case "skipped":
      return STAGES.indexOf("probing");
    case "failed":
      if (clip.video_id) return STAGES.indexOf("indexing");
      if (clip.size_mb) return STAGES.indexOf("downloading");
      return STAGES.indexOf("probing");
    default:
      return STAGES.indexOf(clip.stage as (typeof STAGES)[number]);
  }
}

function Journey({ clip }: { clip: IngestClip }) {
  const terminal = TERMINAL[clip.stage];
  const reached = furthestStage(clip);

  return (
    <div className="journey">
      {STAGES.map((stage, index) => {
        const done = index <= reached && (Boolean(terminal) || index < reached);
        const current = !terminal && index === reached;
        return (
          <span
            key={stage}
            className={
              current
                ? "journey__stage journey__stage--current"
                : done
                  ? "journey__stage journey__stage--done"
                  : "journey__stage"
            }
          >
            {stage}
          </span>
        );
      })}
      {terminal ? (
        <span
          className={
            terminal === "accepted"
              ? "journey__stage journey__stage--done"
              : "journey__stage journey__stage--rejected"
          }
        >
          {terminal}
        </span>
      ) : null}
    </div>
  );
}

/** Merge gate reports, keeping the last verdict for any id seen twice. */
function mergeChecks(...lists: Array<GateCheck[] | undefined>): GateCheck[] {
  const byId = new Map<string, GateCheck>();
  for (const list of lists) {
    for (const check of list ?? []) byId.set(check.id, check);
  }
  return [...byId.values()];
}

function ClipResult({ clip }: { clip: IngestClip }) {
  const [open, setOpen] = useState(false);
  const quality = clip.quality;
  const frame = clip.frame_check;

  return (
    <div className="clip">
      <div className="clip__head">
        <div>
          <h3 className="clip__title">{clip.title ?? clip.url}</h3>
          <span className="clip__url">{clip.url}</span>
        </div>
        <div className="row" style={{ gap: "var(--space-1)" }}>
          {clip.accepted ? <Pill tone="pass">accepted</Pill> : null}
          {clip.stage === "rejected" || clip.stage === "skipped" ? (
            <Pill tone="fail">{clip.stage}</Pill>
          ) : null}
          {clip.stage === "failed" ? <Pill tone="fail">failed</Pill> : null}
          {quality ? <Pill>grade {quality.grade}</Pill> : null}
          {clip.annotation_level ? <Pill>{clip.annotation_level}</Pill> : null}
          {frame ? (
            <Pill tone={frame.hands_visible ? "pass" : "fail"}>
              {frame.hands_visible ? "hands" : "no hands"}
            </Pill>
          ) : null}
        </div>
      </div>

      <Journey clip={clip} />

      {clip.rejection_reason ? (
        <div className="notice notice--error">{clip.rejection_reason}</div>
      ) : null}
      {clip.error ? <div className="notice notice--error">{clip.error}</div> : null}
      {clip.notes.length ? (
        <div className="notice">
          {clip.notes.map((note) => (
            <div key={note}>{note}</div>
          ))}
        </div>
      ) : null}

      <div className="card__meta">
        {clip.video_id ? <span>datalake {clip.video_id}</span> : null}
        {clip.duration_seconds ? <span>{timecode(clip.duration_seconds)}</span> : null}
        {clip.size_mb ? <span>{clip.size_mb} MB</span> : null}
        {quality ? <span>{quality.score}/100</span> : null}
        {quality?.idle_seconds ? <span>idle {timecode(quality.idle_seconds)}</span> : null}
        {clip.annotation ? (
          <span>survival {percent(clip.annotation.survival_rate)}</span>
        ) : null}
        {clip.tags_written.length ? <span>{clip.tags_written.length} tags</span> : null}
      </div>

      <button
        type="button"
        className="button button--small button--ghost"
        style={{ alignSelf: "flex-start" }}
        onClick={() => setOpen(!open)}
      >
        {open ? "Hide detail" : "Gates & annotation tree"}
      </button>

      {open ? (
        <>
          {/* The screen and the post-index gates overlap on G0-LIC; the later
              verdict is the one that counts, so the lists are merged by id. */}
          <GateList checks={mergeChecks(clip.screening?.checks, quality?.checks)} />
          {clip.segments?.length ? (
            <div className="tree">
              <span className="tree__branch">anchors</span>
              <div className="tree__node">
                {clip.segments.map((segment) => (
                  <div className="tree__leaf" key={segment.segment_id}>
                    <span className="tree__span">
                      {timecode(segment.span_start)}–{timecode(segment.span_end)}
                    </span>
                    <b>{segment.hier_level}</b>
                    <span>{segment.label ?? ""}</span>
                    {segment.evidence.length ? (
                      <span className="tree__tag">{segment.evidence.join(" · ")}</span>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {clip.annotation ? (
            <AnnotationTreeFor
              annotations={clip.annotation.annotations}
              caveat={clip.annotation.caveat}
            />
          ) : null}
          {clip.tags_written.length ? (
            <div className="tree__tags">
              {clip.tags_written.map((tag) => (
                <span className="tree__tag" key={tag}>
                  {tag}
                </span>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

export interface CollectViewProps {
  ownKeys: OwnKeys;
  apiKey: string;
  queuedUrls: string[];
  /** What the server accepts per request; the queue is sent in batches of it. */
  maxUrlsPerRequest: number;
}

export function CollectView({
  apiKey,
  ownKeys,
  queuedUrls,
  maxUrlsPerRequest,
}: CollectViewProps) {
  const [urlText, setUrlText] = useState(queuedUrls.join("\n"));
  const [requireHands, setRequireHands] = useState(true);
  const [viewpoint, setViewpoint] = useState("egocentric");
  const [minDuration, setMinDuration] = useState("");
  const [annotate, setAnnotate] = useState(true);

  const [collecting, setCollecting] = useState(false);
  const [batch, setBatch] = useState<{ index: number; total: number } | null>(null);
  const [clips, setClips] = useState<Record<string, IngestClip>>({});
  const [order, setOrder] = useState<string[]>([]);
  const [error, setError] = useState("");

  const [tag, setTag] = useState("clean_pass");
  const [curating, setCurating] = useState(false);
  const [curation, setCuration] = useState<CurationResult | null>(null);

  const controller = useRef<AbortController | null>(null);

  // The queue changes when part one sends a selection over; only adopt it while
  // the box is untouched, so a typed list is never overwritten.
  const queueSignature = queuedUrls.join("\n");
  const lastQueue = useRef(queueSignature);
  if (queueSignature !== lastQueue.current) {
    lastQueue.current = queueSignature;
    if (queueSignature) setUrlText(queueSignature);
  }

  const urls = urlText
    .split(/[\s,]+/)
    .map((value) => value.trim())
    .filter(Boolean);

  async function collect() {
    if (!urls.length || collecting) return;
    controller.current?.abort();
    controller.current = new AbortController();
    setCollecting(true);
    setError("");
    setClips({});
    setOrder([]);

    const record = (clip: IngestClip) => {
      setClips((current) => ({ ...current, [clip.url]: clip }));
      setOrder((current) => (current.includes(clip.url) ? current : [...current, clip.url]));
    };

    // The server caps how many clips one request may queue, because indexing is
    // billed per video-minute. Rather than refusing a longer queue — which is
    // what it used to do, at submit time, after you had already picked them —
    // the queue is sent in batches of that size.
    const batches: string[][] = [];
    for (let index = 0; index < urls.length; index += maxUrlsPerRequest) {
      batches.push(urls.slice(index, index + maxUrlsPerRequest));
    }

    for (const [index, group] of batches.entries()) {
      if (controller.current?.signal.aborted) break;
      setBatch({ index: index + 1, total: batches.length });

      await streamRequest(
        "/api/v1/collect/stream",
        {
          urls: group,
          require_hands: requireHands,
          viewpoint: viewpoint || undefined,
          min_duration_seconds: minDuration ? Number(minDuration) : undefined,
          annotate,
        },
        {
          onEvent: (event, data) => {
            if (event === "clip_stage" || event === "clip_done") {
              record(data.clip as unknown as IngestClip);
            } else if (event === "error") {
              setError(String(data.message ?? "Collection failed"));
            }
          },
          onError: setError,
        },
        { apiKey, keys: ownKeys, signal: controller.current.signal },
      );
    }

    setBatch(null);
    setCollecting(false);
  }

  async function curate() {
    if (curating) return;
    const indexed = order
      .map((url) => clips[url]?.video_id)
      .filter((value): value is string => Boolean(value));

    setCurating(true);
    setError("");
    await streamRequest(
      "/api/v1/curate/stream",
      indexed.length ? { video_ids: indexed, require_hands: requireHands } : { tag },
      {
        onEvent: (event, data) => {
          if (event === "complete") setCuration(data as unknown as CurationResult);
          else if (event === "error") setError(String(data.message ?? "Curation failed"));
        },
        onError: setError,
        onDone: () => setCurating(false),
      },
      { apiKey, keys: ownKeys },
    );
  }

  const results = order.map((url) => clips[url]).filter(Boolean);
  const accepted = results.filter((clip) => clip.accepted).length;

  return (
    <>
      <header className="page-head">
        <h1>Curate &amp; annotate</h1>
        <p>
          Download what the search found, index it into the Video Datalake, then let the cleaning
          agent judge the frames and the annotation agent write the task → action → event tree. A
          clip whose frames show no hands is dropped.
        </p>
      </header>

      <Panel
        title="Collect"
        meta={
          collecting
            ? batch
              ? `batch ${batch.index} of ${batch.total}`
              : "running"
            : `${urls.length} URL${urls.length === 1 ? "" : "s"} queued`
        }
      >
        <Field
          label={
            `Candidate URLs — one per line. This deployment indexes ` +
            `${maxUrlsPerRequest} per request; longer queues are sent in batches.`
          }
        >
          <textarea
            className="textarea"
            value={urlText}
            onChange={(event) => setUrlText(event.target.value)}
            placeholder="https://www.youtube.com/watch?v=…"
          />
        </Field>

        <div className="fields">
          <Field label="Viewpoint">
            <select
              className="select"
              value={viewpoint}
              onChange={(event) => setViewpoint(event.target.value)}
            >
              <option value="">Any</option>
              <option value="egocentric">Egocentric (first person)</option>
              <option value="exocentric">Exocentric (third person)</option>
            </select>
          </Field>
          <Field label="Minimum length (seconds)">
            <input
              className="input"
              type="number"
              min={0}
              step="any"
              value={minDuration}
              onChange={(event) => setMinDuration(event.target.value)}
              placeholder="300"
            />
          </Field>
        </div>

        <div className="row">
          <label className="checkbox">
            <input
              type="checkbox"
              checked={requireHands}
              onChange={(event) => setRequireHands(event.target.checked)}
            />
            <span>Hands must be visible</span>
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={annotate}
              onChange={(event) => setAnnotate(event.target.checked)}
            />
            <span>Annotate what survives</span>
          </label>
          <div className="row row--end" style={{ marginLeft: "auto" }}>
            {collecting ? (
              <button
                type="button"
                className="button button--ghost"
                onClick={() => controller.current?.abort()}
              >
                Stop
              </button>
            ) : null}
            <button
              type="button"
              className="button button--primary"
              disabled={collecting || !urls.length}
              onClick={collect}
            >
              {collecting ? "Collecting…" : "Download & index"}
            </button>
          </div>
        </div>
      </Panel>

      {error ? <div className="notice notice--error">{error}</div> : null}

      <Panel
        title="Clips"
        meta={results.length ? `${accepted} of ${results.length} accepted` : undefined}
      >
        {results.length ? (
          <div className="clip-list">
            {results.map((clip) => (
              <ClipResult clip={clip} key={clip.url} />
            ))}
          </div>
        ) : (
          <Empty>
            Queue candidates from the search, or paste URLs above. Every stage streams as it
            happens.
          </Empty>
        )}
      </Panel>

      <Panel
        title="Curate the set"
        action={
          <div className="row">
            <input
              className="input"
              style={{ width: "160px" }}
              value={tag}
              onChange={(event) => setTag(event.target.value)}
              placeholder="clean_pass"
              aria-label="Worklist tag"
            />
            <button
              type="button"
              className="button button--small button--primary"
              disabled={curating}
              onClick={curate}
            >
              {curating ? "Curating…" : "Grade the set"}
            </button>
          </div>
        }
      >
        {curation ? (
          <>
            <div className="stats">
              <Stat
                label="Batch grade"
                value={curation.batch_grade}
                note={`${curation.accepted_clips} of ${curation.total_clips} accepted`}
              />
              <Stat
                label="Delivered"
                value={hours(curation.hours.delivered_hours)}
                note="downloaded"
              />
              <Stat
                label="Accepted"
                value={hours(curation.hours.accepted_hours)}
                note={`media yield ${percent(curation.hours.media_yield)}`}
              />
              <Stat
                label="Accepted + labelled"
                value={hours(curation.hours.accepted_labeled_hours)}
                note="the only figure to quote"
              />
            </div>
            <div className="stats">
              <Stat
                label="Grades"
                value={Object.entries(curation.grades)
                  .map(([grade, count]) => `${grade} ${count}`)
                  .join(" · ")}
                small
              />
              <Stat
                label="Annotation depth"
                value={Object.entries(curation.annotation_levels)
                  .map(([level, count]) => `${level} ${count}`)
                  .join(" · ")}
                small
              />
              <Stat label="Duplicate groups" value={curation.duplicate_groups} small />
              <Stat label="Idle" value={hours(curation.hours.idle_hours)} small />
            </div>
            <GateList checks={curation.dataset_checks} />
            {curation.errors.length ? (
              <div className="notice">
                {curation.errors.map((message) => (
                  <div key={message}>{message}</div>
                ))}
              </div>
            ) : null}
          </>
        ) : (
          <Empty>
            Grade what is already indexed — by the ids just collected, or by a worklist tag. You get
            the four hour measures, the diversity checks and the batch grade.
          </Empty>
        )}
      </Panel>
    </>
  );
}
