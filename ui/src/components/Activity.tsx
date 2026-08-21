/** The agent's activity, as it happens.
 *
 * A collection run makes a lot of calls and some of them fail; a run that shows
 * nothing until it finishes is indistinguishable from a hung one.
 */

import { useEffect, useRef } from "react";

import type { ActivityEntry } from "../lib/types";
import { Panel } from "./primitives";

export function Activity({ entries, running }: { entries: ActivityEntry[]; running: boolean }) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Pin to the newest line while the run is live.
    if (running && host.current) host.current.scrollTop = host.current.scrollHeight;
  }, [entries.length, running]);

  if (!entries.length) return null;

  return (
    <Panel title="Agent activity" meta={running ? "running" : `${entries.length} steps`}>
      <div className="activity" ref={host}>
        {entries.map((entry) => (
          <div
            className={entry.failed ? "activity__row activity__row--fail" : "activity__row"}
            key={entry.id}
          >
            <span className="activity__kind">{entry.kind}</span>
            <span>{entry.message}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
