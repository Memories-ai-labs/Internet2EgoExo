/** Browsing the clean clips: the footage from the Datalake, the tree from the store.
 *
 * The other two views are a pipeline — find candidates, then collect them. This
 * one is the result: everything that survived, searchable by what is *in* it.
 * A search for "fold" finds a clip whose action is folding even when its title
 * never says so, which is only possible because the tree is rows in a database
 * rather than a blob hanging off a video record.
 */

import { useCallback, useEffect, useState } from "react";
import { Panel, Stat } from "./primitives";

type Segment = {
  segment_id: string;
  parent_segment_id: string | null;
  hier_level: string;
  span_start: number;
  span_end: number;
  seconds: number;
  label: string | null;
  narration: string | null;
  hands_visible: boolean | null;
  left_hand: string | null;
  right_hand: string | null;
  objects: string[];
  evidence: string[];
};

type ClipRow = {
  video_id: string;
  collection_id: string;
  source_video_id: string;
  source_start: number | null;
  source_end: number | null;
  title: string;
  duration_seconds: number | null;
  viewpoint: string;
  grade: string;
  annotation_level: string;
  accepted: boolean;
  segment_count: number;
  action_count: number;
};

/** Where in the Datalake this clip came from, said in full.
 *
 * The ids are the whole point of the panel and they were abbreviated to their
 * last eight characters, which is enough to recognise a clip you already know
 * and not enough to go and find it. Anyone checking a delivered clip needs the
 * id they can paste into the Datalake and the two timestamps it was cut
 * between — so both are shown whole, and both are selectable.
 */
function Provenance({ clip }: { clip: ClipRow }) {
  const span =
    clip.source_start !== null && clip.source_end !== null
      ? `${clip.source_start.toFixed(1)}s – ${clip.source_end.toFixed(1)}s`
      : "span not recorded";
  return (
    <dl className="prov">
      <div className="prov__row">
        <dt>clip</dt>
        <dd className="mono">{clip.video_id}</dd>
      </div>
      <div className="prov__row">
        <dt>cut from</dt>
        <dd className="mono">{clip.source_video_id || "—"}</dd>
      </div>
      <div className="prov__row">
        <dt>at</dt>
        <dd className="mono">{span}</dd>
      </div>
      {clip.collection_id ? (
        <div className="prov__row">
          <dt>collection</dt>
          <dd className="mono">{clip.collection_id}</dd>
        </div>
      ) : null}
    </dl>
  );
}

/** A still from the clip itself.
 *
 * Rendered server-side and cached, so this is one cheap GET. A clip whose
 * still could not be made shows the placeholder rather than a broken image
 * icon: "no thumbnail" is a fact about this host, not about the footage.
 */
function Thumb({ apiBase, videoId }: { apiBase: string; videoId: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) return <div className="thumb thumb--empty" aria-hidden="true" />;
  return (
    <img
      className="thumb"
      src={`${apiBase}/api/v1/clips/${videoId}/thumbnail`}
      alt=""
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}

type ClipDetail = ClipRow & {
  segments: Segment[];
  playback?: { url: string | null; status?: string; tags?: string[]; error?: string };
};

type Facets = {
  totals: {
    clips: number;
    accepted_clips: number;
    hours: number;
    action_segments: number;
    by_viewpoint: Record<string, number>;
  };
  action_labels: { label: string; segments: number; clips: number }[];
  objects?: { object: string; segments: number; clips: number }[];
};

const PAGE = 24;

export function LibraryView({ apiBase }: { apiBase: string }) {
  const [query, setQuery] = useState("");
  // The deliverable is first-person, so that is what the library opens on.
  // Everything the gate refused is still here and still reachable — a rejected
  // clip is how you check the gate was right — but it is not what somebody
  // browsing the corpus should be handed by default.
  const [viewpoint, setViewpoint] = useState("egocentric");
  const [handsOnly, setHandsOnly] = useState(false);
  const [clips, setClips] = useState<ClipRow[]>([]);
  const [total, setTotal] = useState(0);
  const [persists, setPersists] = useState(true);
  const [facets, setFacets] = useState<Facets | null>(null);
  const [selected, setSelected] = useState<ClipDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ limit: String(PAGE) });
      if (query.trim()) params.set("q", query.trim());
      if (viewpoint) params.set("viewpoint", viewpoint);
      if (handsOnly) params.set("hands_only", "true");
      const [listing, facetPayload] = await Promise.all([
        fetch(`${apiBase}/api/v1/clips?${params}`).then((r) => r.json()),
        fetch(`${apiBase}/api/v1/clips/facets`).then((r) => r.json()),
      ]);
      setClips(listing.clips ?? []);
      setTotal(listing.total ?? 0);
      setPersists(listing.store?.persists !== false);
      setFacets(facetPayload);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "could not read the library");
    } finally {
      setLoading(false);
    }
  }, [apiBase, query, viewpoint, handsOnly]);

  useEffect(() => {
    void load();
  }, [load]);

  const open = async (videoId: string) => {
    setSelected(null);
    try {
      const detail = await fetch(`${apiBase}/api/v1/clips/${videoId}`).then((r) => r.json());
      setSelected(detail);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "could not open that clip");
    }
  };

  const totals = facets?.totals;

  return (
    <div className="library">
      <Panel
        title="Clean clips"
        action={
          <span className="panel__meta">
            {loading ? "reading…" : `${total} match${total === 1 ? "" : "es"}`}
          </span>
        }
      >
        {/* A store that forgets between requests is not an empty corpus, and a
            reader deserves to be able to tell the two apart. */}
        {!persists ? (
          <p className="library__warning">
            This host has nowhere to keep the library, so it holds only what this
            request put there. Set <code>ANNOTATION_STORE_PATH</code> to somewhere
            that persists.
          </p>
        ) : null}

        {totals ? (
          <div className="stats">
            <Stat label="Clips" value={String(totals.clips)} />
            <Stat
              label="Accepted"
              value={`${totals.accepted_clips}/${totals.clips}`}
              small
            />
            <Stat label="Hours" value={totals.hours.toFixed(3)} small />
            <Stat label="Action anchors" value={String(totals.action_segments)} small />
            <Stat
              label="Viewpoint"
              value={
                Object.entries(totals.by_viewpoint)
                  .map(([name, n]) => `${name} ${n}`)
                  .join(" · ") || "—"
              }
              small
            />
          </div>
        ) : null}

        <div className="library__controls">
          <input
            className="input"
            type="search"
            value={query}
            placeholder="Search a title, an action, an object or what a hand did"
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Search the clean clips"
          />
          <select
            className="input input--select"
            value={viewpoint}
            onChange={(event) => setViewpoint(event.target.value)}
            aria-label="Viewpoint"
          >
            <option value="egocentric">egocentric — the deliverable</option>
            <option value="">any viewpoint</option>
            <option value="exocentric">exocentric</option>
            <option value="unknown">unknown</option>
          </select>
          <label className="library__toggle">
            <input
              type="checkbox"
              checked={handsOnly}
              onChange={(event) => setHandsOnly(event.target.checked)}
            />
            hands in frame
          </label>
        </div>

        {/* Offered from what the store actually holds, so a filter never
            promises a label nothing has. */}
        {facets?.action_labels?.length ? (
          <div className="library__labels">
            {facets.action_labels.slice(0, 12).map((row) => (
              <button
                key={row.label}
                type="button"
                className="chip"
                onClick={() => setQuery(row.label)}
              >
                {row.label}
                <span className="chip__count">{row.clips}</span>
              </button>
            ))}
          </div>
        ) : totals && totals.clips > 0 ? (
          <p className="library__note">
            These clips have spans but no labels yet — they were cut and cleaned,
            not annotated. Searching matches titles until the labelling pass runs
            over this collection.
          </p>
        ) : null}

        {/* What was actually handled. The facet a buyer reaches for first:
            they ask for footage of a drill, not for footage labelled
            "drive-the-screw". */}
        {facets?.objects?.length ? (
          <div className="library__labels">
            <span className="library__facetLabel">Objects</span>
            {facets.objects.slice(0, 12).map((row) => (
              <button
                key={row.object}
                type="button"
                className="chip"
                onClick={() => setQuery(row.object)}
              >
                {row.object}
                <span className="chip__count">{row.clips}</span>
              </button>
            ))}
          </div>
        ) : null}

        {/* Naming what the filter is holding back, rather than leaving the
            reader to notice the count is short. Split by what the frames said,
            because "run the gate" and "this footage is wrong" are different
            problems. */}
        {viewpoint === "egocentric" && totals ? (
          (() => {
            const held = Object.entries(totals.by_viewpoint).filter(([name]) => name !== "egocentric");
            const n = held.reduce((sum, [, count]) => sum + count, 0);
            if (!n) return null;
            return (
              <p className="library__note">
                {n} more clip{n === 1 ? "" : "s"} in the store {n === 1 ? "is" : "are"} not
                first-person and {n === 1 ? "is" : "are"} held out of the deliverable (
                {held.map(([name, count]) => `${count} ${name}`).join(", ")}). Switch the
                viewpoint filter to see {n === 1 ? "it" : "them"}.
              </p>
            );
          })()
        ) : null}

        {error ? <p className="library__warning">{error}</p> : null}

        {!loading && clips.length === 0 ? (
          <p className="library__note">
            Nothing here yet. Clips arrive when the refinement step cuts accepted
            anchors and uploads them to the clean collection.
          </p>
        ) : null}

        <ul className="library__list">
          {clips.map((clip) => (
            <li key={clip.video_id}>
              <button
                type="button"
                className={`clipRow${
                  selected?.video_id === clip.video_id ? " clipRow--open" : ""
                }`}
                onClick={() => void open(clip.video_id)}
              >
                <Thumb apiBase={apiBase} videoId={clip.video_id} />
                <span className="clipRow__body">
                  <span className="clipRow__title">{clip.title || clip.video_id}</span>
                  <span className="clipRow__meta">
                    {clip.duration_seconds ? `${clip.duration_seconds.toFixed(0)}s` : "—"}
                    {clip.viewpoint ? ` · ${clip.viewpoint}` : ""}
                    {clip.grade ? ` · ${clip.grade}` : ""}
                    {clip.action_count ? ` · ${clip.action_count} action` : ""}
                  </span>
                  <span className="clipRow__source mono">
                    {clip.source_video_id || "source unknown"}
                    {clip.source_start !== null && clip.source_end !== null
                      ? ` @ ${clip.source_start.toFixed(1)}–${clip.source_end.toFixed(1)}s`
                      : ""}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </Panel>

      {selected ? (
        <Panel
          title={selected.title || selected.video_id}
          action={
            <span className="panel__meta">
              {selected.grade ? `grade ${selected.grade} · ` : ""}
              {selected.annotation_level || "no tree"} · {selected.action_count} action
              {selected.action_count === 1 ? "" : "s"}
            </span>
          }
        >
          <Provenance clip={selected} />

          {selected.playback?.url ? (
            <video
              className="library__video"
              src={selected.playback.url}
              controls
              preload="metadata"
            />
          ) : (
            <p className="library__note">
              No playable URL right now
              {selected.playback?.error ? ` (${selected.playback.error})` : ""}.
            </p>
          )}

          {selected.playback?.tags?.length ? (
            <div className="library__labels">
              {selected.playback.tags.slice(0, 10).map((tag) => (
                <span key={tag} className="chip chip--static">
                  {tag}
                </span>
              ))}
            </div>
          ) : null}

          {/* The spans are rebased onto this clip's own timeline, because an
              offset from the 400-second source is useless to somebody scrubbing
              a 22-second clip. */}
          <ul className="ltree">
            {selected.segments.map((segment) => (
              <li
                key={segment.segment_id}
                className={`ltree__node ltree__node--${segment.hier_level}`}
              >
                <span className="ltree__span">
                  {segment.span_start.toFixed(0)}–{segment.span_end.toFixed(0)}s
                </span>
                <span className="ltree__level">{segment.hier_level}</span>
                <span className="ltree__label">
                  {segment.label ?? <em>unlabelled</em>}
                </span>
                {segment.narration ? (
                  <span className="ltree__narration">{segment.narration}</span>
                ) : null}
                {segment.left_hand || segment.right_hand ? (
                  <span className="ltree__hands">
                    {segment.left_hand ? `L: ${segment.left_hand}` : ""}
                    {segment.left_hand && segment.right_hand ? " · " : ""}
                    {segment.right_hand ? `R: ${segment.right_hand}` : ""}
                  </span>
                ) : null}
                {segment.objects?.length ? (
                  <span className="ltree__objects">{segment.objects.join(" · ")}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </Panel>
      ) : null}
    </div>
  );
}
