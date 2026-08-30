/** What the run actually collected — and which hour measure that is.
 *
 * The four hour figures are shown side by side on purpose. Quoting a delivered
 * hour as an accepted one overstates a set by a third, so the panel never
 * collapses them into a single "hours" number.
 */

import { hours, mix, money, percent } from "../lib/format";
import { manifestToCsv, manifestToJsonl, download } from "../lib/exports";
import type { Manifest } from "../lib/types";
import { Panel, Stat } from "./primitives";

export function DatasetPanel({ manifest }: { manifest: Manifest }) {
  const ledger = manifest.hours;
  const measured =
    ledger.accepted_labeled_hours || ledger.accepted_hours || manifest.total_hours;
  const target = manifest.target_hours;
  const progress = target ? Math.min((measured / target) * 100, 100) : 0;
  // Before the gates have run there is nothing accepted *yet* — which is not
  // the same as nothing being acceptable. A zero here would read as a verdict.
  const graded = manifest.accepted_clips > 0 || Object.keys(manifest.grades).length > 0;
  // What the searches turned up, before the pre-download look spent anything.
  const found = manifest.total_clips + manifest.excluded_clips;

  return (
    <Panel
      title="Dataset"
      action={
        <div className="row">
          <span className="panel__meta">
            {manifest.requested_viewpoint
              ? `${manifest.requested_viewpoint} requested`
              : "any viewpoint"}
          </span>
          <button
            type="button"
            className="button button--small button--ghost"
            onClick={() =>
              download("dataset.jsonl", manifestToJsonl(manifest), "application/x-ndjson")
            }
          >
            JSONL
          </button>
          <button
            type="button"
            className="button button--small button--ghost"
            onClick={() => download("dataset.csv", manifestToCsv(manifest), "text/csv")}
          >
            CSV
          </button>
        </div>
      }
    >
      <div className="stats">
        <Stat label="Clips" value={manifest.total_clips} note={`${manifest.accepted_clips} accepted`} />
        <Stat
          label="Delivered"
          value={hours(ledger.delivered_hours)}
          note="downloaded, before the gates"
        />
        <Stat
          label="Accepted"
          value={graded ? hours(ledger.accepted_hours) : "—"}
          note={graded ? `media yield ${percent(ledger.media_yield)}` : "not gated yet"}
        />
        <Stat
          label="Accepted + labelled"
          value={graded ? hours(ledger.accepted_labeled_hours) : "—"}
          note={graded ? "the only figure to quote" : "collect these clips to find out"}
        />
      </div>

      {target ? (
        <div className="progress">
          <span className="stat__label">
            {measured >= target ? "Target reached" : "Progress to target"} — {hours(measured)} of{" "}
            {hours(target)}
          </span>
          <div className="progress__bar">
            <div className="progress__fill" style={{ width: `${progress.toFixed(1)}%` }} />
          </div>
        </div>
      ) : null}

      <div className="stats">
        <Stat label="Viewpoint mix" value={mix(manifest.by_viewpoint)} small />
        <Stat label="Sources" value={mix(manifest.by_platform)} small />
        <Stat
          label="Reusable licence"
          value={`${manifest.reusable_license_clips}/${manifest.total_clips}`}
          small
        />
        {Object.keys(manifest.grades).length ? (
          <Stat label="Grades" value={mix(manifest.grades)} small />
        ) : null}
        {Object.keys(manifest.annotation_levels).length ? (
          <Stat label="Annotation depth" value={mix(manifest.annotation_levels)} small />
        ) : null}
      </div>

      {/* The screen is now the largest loss in the funnel, and "0 candidates"
          was being read as a failed search when it usually means the footage
          exists and is shot on a tripod. So it gets the arithmetic, not a
          footnote: found, kept, and why the rest went. */}
      {manifest.excluded_clips ? (
        <div className="funnel">
          <div className="funnel__line">
            <span className="funnel__n">{found}</span>
            <span className="funnel__label">found by the searches</span>
            <span className="funnel__arrow" aria-hidden="true">&rarr;</span>
            <span className="funnel__n">{manifest.total_clips}</span>
            <span className="funnel__label">
              survived the look{found ? ` (${percent(manifest.total_clips / found)})` : ""}
            </span>
          </div>
          <ul className="funnel__reasons">
            {Object.entries(manifest.exclusion_reasons)
              .sort((a, b) => b[1] - a[1])
              .map(([reason, count]) => (
                <li key={reason}>
                  <span className="funnel__count">{count}</span> {reason}
                </li>
              ))}
          </ul>
        </div>
      ) : null}

      {manifest.searches_run?.length ? (
        <div className="searches">
          <p className="searches__intro">
            Searched as, because footage is titled by whoever recorded it:
          </p>
          <ul className="searches__list">
            {manifest.searches_run.slice(0, 6).map((search) => (
              <li key={search.text} className="searches__item">
                {search.angle ? (
                  <span className="searches__angle">{search.angle}</span>
                ) : null}
                <span className="searches__text">{search.text}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {manifest.cost ? (
        <div className="stats">
          <Stat
            label="Per collected hour"
            value={money(manifest.cost.usd_per_collected_hour)}
            note={`${money(manifest.cost.total_usd)} total for ${hours(manifest.cost.hours)}`}
          />
          <Stat
            label="Per delivered hour"
            value={money(manifest.cost.usd_per_delivered_hour)}
            note={`at ${percent(manifest.cost.assumed_yield)} frame-check yield`}
          />
          <Stat
            label="Indexing"
            value={money(manifest.cost.indexing_usd)}
            note="dominates the bill"
            small
          />
          <Stat
            label="Discovery"
            value={money(manifest.cost.discovery_usd)}
            note="Gemini + search tools"
            small
          />
        </div>
      ) : null}

      {manifest.cost?.notes?.length ? (
        <div className="notice">
          {manifest.cost.notes.map((note) => (
            <div key={note}>{note}</div>
          ))}
        </div>
      ) : null}

    </Panel>
  );
}
