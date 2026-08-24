/** Part one: find the footage.
 *
 * A query, the requirements it has to satisfy, and the candidates that came
 * back — each with the evidence behind its viewpoint verdict, so a wrong call
 * can be seen rather than guessed at. Selecting cards here fills the
 * collection queue in part two.
 */

import { useRef, useState } from "react";

import type { OwnKeys } from "../App";
import { toolLabel } from "../lib/format";
import { streamRequest } from "../lib/sse";
import type { ActivityEntry, AgentResponse, Clip, Manifest } from "../lib/types";
import { Activity } from "./Activity";
import { ClipCard } from "./ClipCard";
import { DatasetPanel } from "./DatasetPanel";
import { Chip, Empty, Field, Panel } from "./primitives";

const SOURCES = [
  ["youtube", "YouTube"],
  ["tiktok", "TikTok"],
  ["instagram", "Instagram"],
  ["twitter", "X"],
  ["web", "Open web"],
] as const;

export interface SearchViewProps {
  ownKeys: OwnKeys;
  apiKey: string;
  selected: string[];
  onToggleSelected: (url: string) => void;
  onSelectAll: (urls: string[]) => void;
  onClearSelection: () => void;
  /** The viewpoint the search ran with, so part two knows what was checked. */
  onSendToCollection: (checkedViewpoint: string) => void;
}

export function SearchView({
  apiKey,
  ownKeys,
  selected,
  onToggleSelected,
  onSelectAll,
  onClearSelection,
  onSendToCollection,
}: SearchViewProps) {
  const [query, setQuery] = useState("first-person cooking videos, hands visible");
  const [sources, setSources] = useState<string[]>([]);
  const [viewpoint, setViewpoint] = useState("egocentric");
  const [minDuration, setMinDuration] = useState("");
  const [licenceOnly, setLicenceOnly] = useState(false);
  const [targetHours, setTargetHours] = useState("");
  // How many candidates the loop must see pass the frames before it stops.
  // Empty means one search and no second attempt.
  const [keepUntil, setKeepUntil] = useState("");

  const [running, setRunning] = useState(false);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [clarification, setClarification] = useState<{
    question: string;
    options: string[];
  } | null>(null);

  const controller = useRef<AbortController | null>(null);
  const nextId = useRef(0);

  const log = (kind: string, message: string, failed = false) =>
    setActivity((entries) => [...entries, { id: nextId.current++, kind, message, failed }]);

  const toggleSource = (source: string) =>
    setSources((current) =>
      current.includes(source) ? current.filter((item) => item !== source) : [...current, source],
    );

  /** Search, screen, learn from what the frames said, search again.
   *
   * One search is a guess about vocabulary — `POV bike repair` returns
   * action-camera mount reviews, and no amount of rephrasing that finds a
   * workshop. The loop shows each round's verdict as it lands, because the
   * reasons are the useful part: "everything this phrasing found was a fixed
   * camera" is what tells you the angle is wrong rather than the request.
   */
  async function runLoop() {
    const target = Number(keepUntil);
    if (!query.trim() || running || !Number.isFinite(target) || target < 1) return;

    controller.current?.abort();
    controller.current = new AbortController();
    setRunning(true);
    setError("");
    setClarification(null);
    setActivity([]);
    setClips([]);
    setManifest(null);
    setAnswer("");

    await streamRequest(
      "/api/v1/search-loop/stream",
      {
        query: query.trim(),
        viewpoint: viewpoint || "egocentric",
        target,
        min_duration_seconds: minDuration ? Number(minDuration) : undefined,
      },
      {
        onEvent: (event, data) => {
          switch (event) {
            case "started":
              log("start", `looking for ${target} × ${String(data.viewpoint ?? "")}`);
              break;
            case "round": {
              const text = String(data.observation ?? "");
              log("round", `round ${data.round} — ${data.found}/${data.screened} screened`);
              // The observation is several lines and every one of them is a
              // reason; flattening it to a summary throws away the part worth
              // reading.
              for (const line of text.split("\n").slice(1)) {
                if (line.trim()) log("saw", line.trim());
              }
              break;
            }
            case "complete": {
              const found = Number(data.found ?? 0);
              const rows = (data.candidates as Clip[]) ?? [];
              setClips(rows);
              setAnswer(
                `${found} of ${data.target} passed the frames in ${data.rounds} round(s), ` +
                  `${data.screened} screened for $${Number(data.cost_usd ?? 0).toFixed(3)}. ` +
                  `Stopped: ${data.stopped_because}.` +
                  (data.what_worked ? `\n\nWorked: ${data.what_worked}` : "") +
                  (data.what_did_not ? `\n\nDid not: ${data.what_did_not}` : ""),
              );
              log("done", `${found} found, ${data.stopped_because}`);
              break;
            }
            case "error":
              setError(String(data.message ?? "The search loop failed"));
              break;
          }
        },
        onError: setError,
        onDone: () => setRunning(false),
      },
      { apiKey, keys: ownKeys, signal: controller.current.signal },
    );
  }

  async function run(answerToClarification?: string) {
    if (!query.trim() || running) return;

    controller.current?.abort();
    controller.current = new AbortController();
    setRunning(true);
    setError("");
    setClarification(null);
    if (!answerToClarification) {
      setActivity([]);
      setClips([]);
      setManifest(null);
      setAnswer("");
    }

    await streamRequest(
      "/api/v1/queries/stream",
      {
        query: query.trim(),
        clarification: answerToClarification,
        sources: sources.length ? sources : undefined,
        viewpoint: viewpoint || undefined,
        min_duration_seconds: minDuration ? Number(minDuration) : undefined,
        license_filter: licenceOnly ? "reusable" : undefined,
        target_hours: targetHours ? Number(targetHours) : undefined,
      },
      {
        onEvent: (event, data) => {
          switch (event) {
            case "started":
              log("start", `session ${String(data.session_id ?? "").slice(0, 8)}`);
              break;
            case "progress":
              log("progress", String(data.message ?? ""));
              break;
            case "tool_call":
              log("tool", toolLabel(String(data.tool ?? "tool")));
              break;
            case "tool_result": {
              const label = toolLabel(String(data.tool ?? "tool"));
              if (data.success === false) {
                log("failed", `${label} — ${String(data.error ?? "no result")}`, true);
              } else {
                const found = data.videos_found ?? data.moments_found;
                log("result", found !== undefined ? `${label} → ${found}` : label);
              }
              break;
            }
            case "clarification_needed":
              setClarification({
                question: String(data.question ?? ""),
                options: (data.options as string[]) ?? [],
              });
              break;
            case "complete": {
              const response = data as unknown as AgentResponse;
              setClips(response.video_references ?? []);
              setManifest(response.dataset ?? null);
              setAnswer(response.answer ?? "");
              log(
                "done",
                `${response.steps_taken} steps · ${response.total_videos_analyzed} candidates · ` +
                  `${response.execution_time_seconds.toFixed(1)}s`,
              );
              break;
            }
            case "error":
              setError(String(data.message ?? "Unknown error"));
              break;
          }
        },
        onError: setError,
        onDone: () => setRunning(false),
      },
      { apiKey, keys: ownKeys, signal: controller.current.signal },
    );
  }

  const allSelected =
    clips.length > 0 && clips.every((clip) => selected.includes(clip.url));

  return (
    <>
      <header className="page-head">
        <h1>Search &amp; scrape</h1>
        <p>
          Find egocentric or exocentric footage across YouTube, TikTok, Instagram, X and the open
          web. Candidates are ranked by viewpoint match, length and licence — never by views.
        </p>
      </header>

      <Panel title="What are you collecting?" meta={running ? "running" : undefined}>
        <Field label="Query">
          <textarea
            className="textarea"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="first-person bike repair, long continuous takes"
          />
        </Field>

        <div className="field">
          <span className="field__label">Sources — none selected means auto</span>
          <div className="chips">
            {SOURCES.map(([value, label]) => (
              <Chip key={value} active={sources.includes(value)} onClick={() => toggleSource(value)}>
                {label}
              </Chip>
            ))}
          </div>
        </div>

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
          <Field label="Target hours">
            <input
              className="input"
              type="number"
              min={0}
              step="any"
              value={targetHours}
              onChange={(event) => setTargetHours(event.target.value)}
              placeholder="2"
            />
          </Field>
        </div>

        <div className="row">
          <label className="checkbox">
            <input
              type="checkbox"
              checked={licenceOnly}
              onChange={(event) => setLicenceOnly(event.target.checked)}
            />
            <span>Reusable licences only</span>
          </label>
          <div className="row row--end" style={{ marginLeft: "auto" }}>
            {running ? (
              <button
                type="button"
                className="button button--ghost"
                onClick={() => controller.current?.abort()}
              >
                Stop
              </button>
            ) : null}
            {/* One search, or as many as it takes. The second is a different
                promise, so it is a different button rather than a mode. */}
            <label className="field field--inline">
              <span className="field__label">Keep searching until</span>
              <input
                className="input input--tiny"
                type="number"
                min={1}
                max={25}
                value={keepUntil}
                placeholder="—"
                onChange={(event) => setKeepUntil(event.target.value)}
                aria-label="Candidates that must pass the frames"
              />
            </label>
            <button
              type="button"
              className="button button--ghost"
              disabled={running || !query.trim() || !Number(keepUntil)}
              onClick={() => void runLoop()}
              title="Search, screen on frames, learn from the rejections, search again"
            >
              Keep searching
            </button>
            <button
              type="button"
              className="button button--primary"
              disabled={running || !query.trim()}
              onClick={() => run()}
            >
              {running ? "Searching…" : "Search"}
            </button>
          </div>
        </div>
      </Panel>

      {error ? <div className="notice notice--error">{error}</div> : null}

      {clarification ? (
        <Panel title="One more thing">
          <p>{clarification.question}</p>
          <div className="chips">
            {clarification.options.map((option) => (
              <Chip key={option} active={false} onClick={() => run(option)}>
                {option}
              </Chip>
            ))}
          </div>
        </Panel>
      ) : null}

      <Activity entries={activity} running={running} />

      {answer ? (
        <Panel title="What the agent found">
          <p className="answer">{answer}</p>
        </Panel>
      ) : null}

      {manifest ? <DatasetPanel manifest={manifest} /> : null}

      <Panel
        title="Candidates"
        action={
          <div className="row">
            <span className="panel__meta">
              {selected.length ? `${selected.length} of ${clips.length} selected` : `${clips.length} found`}
            </span>
            {clips.length ? (
              <button
                type="button"
                className="button button--small button--ghost"
                onClick={() =>
                  allSelected ? onClearSelection() : onSelectAll(clips.map((clip) => clip.url))
                }
              >
                {allSelected ? "Clear" : "Select all"}
              </button>
            ) : null}
            <button
              type="button"
              className="button button--small button--primary"
              disabled={!selected.length}
              onClick={() => onSendToCollection(viewpoint)}
            >
              Send to the Datalake
            </button>
          </div>
        }
      >
        {clips.length ? (
          <div className="cards">
            {clips.map((clip) => (
              <ClipCard
                key={clip.url}
                clip={manifest?.clips.find((entry) => entry.url === clip.url) ?? clip}
                selected={selected.includes(clip.url)}
                onToggleSelected={() => onToggleSelected(clip.url)}
              />
            ))}
          </div>
        ) : (
          <Empty>
            {running ? "Searching…" : "Run a search to see candidates and their annotation trees."}
          </Empty>
        )}
      </Panel>
    </>
  );
}
