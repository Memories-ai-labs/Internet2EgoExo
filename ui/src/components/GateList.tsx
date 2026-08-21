/** A gate report, rendered as it is meant to be read.
 *
 * Three states, not two: passed, failed, and *not measured*. An unmeasured
 * check is not a pass — it is a number nobody has, and it says so, because the
 * scoring excludes it rather than assuming it.
 */

import type { GateCheck } from "../lib/types";
import { Pill } from "./primitives";

function value(check: GateCheck): string {
  if (check.value === null || check.value === undefined || check.value === "") return "";
  if (typeof check.value === "number") return String(check.value);
  return String(check.value);
}

export function GateList({ checks }: { checks: GateCheck[] }) {
  if (!checks.length) return null;

  return (
    <div className="gates">
      {checks.map((check) => {
        const tone = !check.measured ? "muted" : check.passed ? "pass" : check.blocking ? "fail" : "warn";
        const label = !check.measured ? "not measured" : check.passed ? "pass" : check.blocking ? "blocked" : "flagged";
        return (
          <div className="gate" key={check.id}>
            <span className="gate__id">{check.id}</span>
            <span>
              {check.name}
              {value(check) ? <span className="gate__detail"> — {value(check)}</span> : null}
              {check.detail ? <span className="gate__detail"> — {check.detail}</span> : null}
              {check.threshold && !check.detail ? (
                <span className="gate__detail"> (needs {check.threshold})</span>
              ) : null}
            </span>
            <Pill tone={tone}>{label}</Pill>
          </div>
        );
      })}
    </div>
  );
}
