"""The recurring report: one run's numbers, and how they moved.

A scorecard says what one run produced. That is not what somebody watching the
pipeline improve needs — they need to know whether today is better than
yesterday, and whether the difference is real. Which needs three things a
single scorecard cannot give:

* **An interval, not a point.** The recurring run is a 12-query slice, because
  the full set costs hours and money and cannot run three times a day. Twelve
  clips put a ±25-point band around an acceptance rate. Reporting `58%` from
  twelve clips as though it were a measurement is how a trend line becomes
  noise somebody acts on, so every rate here carries its Wilson interval and
  its denominator.
* **A rolling window.** One tick cannot resolve a small improvement; nine of
  them — about three days, a hundred-odd clips — can. So the report carries
  both: the tick, and the window it sits in.
* **A record of what was measured.** The pipeline under test is a deployment,
  not this checkout, and its behaviour depends on settings that change without
  a commit (`viewpoint_check`, the model). Every snapshot records the
  deployment's own health payload alongside the commit of `main` the harness
  ran from, so a step in the trend can be attributed to something.

`eval/history.jsonl` is the record, one snapshot per line, append-only. It is
committed: it *is* the trend, and a trend that lives in a build artifact is a
trend nobody can look at.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from math import sqrt
from pathlib import Path
from typing import Any

from video_searching_agent.evaluation.metrics import GRADES, Scorecard
from video_searching_agent.evaluation.scorecard import render

# The README carries the latest numbers between these markers, so the block can
# be rewritten without a template engine and a human edit outside them survives.
README_START = "<!-- performance-metrics:start -->"
README_END = "<!-- performance-metrics:end -->"

# Ticks in the rolling window: three a day, so nine is about three days.
WINDOW = 9

# Rows in the trend table.
TREND_ROWS = 12


@dataclass
class Snapshot:
    """One run, reduced to the numbers worth keeping forever."""

    ran_at: str = ""
    eval_version: str = ""
    slice_name: str = "core"
    commit: str = ""
    deployment: str = ""
    build: dict[str, Any] = field(default_factory=dict)

    queries: int = 0
    queries_with_candidates: int = 0
    queries_screened_to_nothing: int = 0
    found: int = 0
    screened_out: int = 0
    candidates: int = 0
    indexed: int = 0
    graded: int = 0
    accepted: int = 0
    high_quality: int = 0
    action_anchors: int = 0
    delivered_hours: float = 0.0
    usable_hours: float = 0.0
    total_usd: float = 0.0
    grades: dict[str, int] = field(default_factory=dict)
    usd_per_grade: dict[str, float] = field(default_factory=dict)
    contradictions: int = 0
    errors: int = 0

    # --- the rates, all of them with a denominator to hand ---------------
    @property
    def acceptance_rate(self) -> float:
        return _ratio(self.accepted, self.graded)

    @property
    def high_quality_rate(self) -> float:
        return _ratio(self.high_quality, self.graded)

    @property
    def screen_survival_rate(self) -> float:
        """Of what the search found, how much the pre-download screen let through.

        The first ratio in the funnel and, on a robot-derived query set, the
        smallest: the footage of a named task usually exists and is usually shot
        on a tripod. Worth its own trend line — a change here is a change in the
        screen or in what the search brings back, and neither is visible in the
        acceptance rate.
        """
        return _ratio(self.candidates, self.found)

    @property
    def screen_measured(self) -> bool:
        """Whether this run recorded what the screen dropped.

        Runs from before the funnel counted it carry `found = 0` with candidates
        of their own, and `66/0` is not a ratio. Those report the screen as
        unmeasured rather than as 0%.
        """
        return self.found > 0

    @property
    def usable_time_ratio(self) -> float:
        return _ratio(self.usable_hours, self.delivered_hours)

    @property
    def usd_per_usable_hour(self) -> float:
        return _ratio(self.total_usd, self.usable_hours)

    @property
    def usd_per_accepted_clip(self) -> float:
        return _ratio(self.total_usd, self.accepted)

    @property
    def day(self) -> str:
        return self.ran_at[:10]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def snapshot_of(
    card: Scorecard,
    *,
    ran_at: datetime | None = None,
    slice_name: str = "core",
    commit: str = "",
    deployment: str = "",
    build: dict[str, Any] | None = None,
) -> Snapshot:
    """Reduce a scorecard to the row that goes in the history."""
    chain = card.chain
    moment = ran_at or datetime.now(UTC)
    return Snapshot(
        ran_at=moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
        eval_version=card.eval_version,
        slice_name=slice_name,
        commit=commit,
        deployment=deployment,
        build=dict(build or {}),
        queries=chain.queries,
        queries_with_candidates=chain.queries_with_candidates,
        queries_screened_to_nothing=chain.queries_screened_to_nothing,
        found=chain.found,
        screened_out=chain.screened_out,
        candidates=chain.candidates,
        indexed=chain.indexed,
        graded=chain.graded,
        accepted=chain.accepted,
        high_quality=chain.high_quality,
        action_anchors=chain.action_anchors,
        delivered_hours=round(chain.delivered_hours, 4),
        usable_hours=round(chain.usable_hours, 4),
        total_usd=round(card.cost.total_usd, 4),
        grades={grade: card.band(grade).clips for grade in GRADES},
        usd_per_grade={
            grade: round(card.band(grade).usd_per_clip_obtained, 4) for grade in GRADES
        },
        contradictions=len(card.contradictions),
        errors=len(card.errors),
    )


def same_slice(history: list[Snapshot], slice_name: str) -> list[Snapshot]:
    """Only the ticks that ran the same queries.

    Pooling a 12-query `core` tick with a 200-query full run, or with a replay
    of some other slice, produces a window that is neither. Every comparison —
    the previous tick, the rolling window, 24 hours ago — is drawn from this
    lineage. The trend table is the one place all slices appear, and it labels
    them.
    """
    return [snapshot for snapshot in history if snapshot.slice_name == slice_name]


def load_history(path: Path) -> list[Snapshot]:
    """Read the append-only history, oldest first, skipping anything unreadable."""
    if not path.exists():
        return []
    known = set(Snapshot.__dataclass_fields__)
    snapshots: list[Snapshot] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        snapshots.append(Snapshot(**{k: v for k, v in data.items() if k in known}))
    return sorted(snapshots, key=lambda s: s.ran_at)


def append_history(path: Path, snapshot: Snapshot) -> None:
    """Add one snapshot. Append-only: a rewritten history is not a record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot.as_dict(), ensure_ascii=False) + "\n")


def wilson(successes: int, total: int) -> tuple[float, float]:
    """A 95% Wilson score interval for a proportion.

    Wilson rather than the textbook normal approximation because the counts
    here are small and the rates near the ends: at 1 of 12, the normal interval
    reaches below zero, which is not an interval anybody should print.
    """
    if total <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    phat = successes / total
    denominator = 1 + z * z / total
    centre = (phat + z * z / (2 * total)) / denominator
    spread = (z / denominator) * sqrt(phat * (1 - phat) / total + z * z / (4 * total * total))
    return (max(centre - spread, 0.0), min(centre + spread, 1.0))


@dataclass
class Window:
    """Several ticks pooled, because one tick cannot resolve a small change."""

    ticks: int = 0
    found: int = 0
    candidates: int = 0
    graded: int = 0
    accepted: int = 0
    high_quality: int = 0
    usable_hours: float = 0.0
    delivered_hours: float = 0.0
    total_usd: float = 0.0
    since: str = ""
    until: str = ""

    @property
    def screen_survival_rate(self) -> float:
        return _ratio(self.candidates, self.found)

    @property
    def screen_measured(self) -> bool:
        return self.found > 0

    @property
    def acceptance_rate(self) -> float:
        return _ratio(self.accepted, self.graded)

    @property
    def high_quality_rate(self) -> float:
        return _ratio(self.high_quality, self.graded)

    @property
    def usd_per_usable_hour(self) -> float:
        return _ratio(self.total_usd, self.usable_hours)


def pool(snapshots: list[Snapshot]) -> Window:
    """Pool snapshots into one window. Counts are summed, never rates averaged.

    Averaging three rates computed over 4, 12 and 30 clips weights the four-clip
    run as heavily as the thirty-clip one. Summing the numerators and the
    denominators does not.
    """
    window = Window(ticks=len(snapshots))
    for snapshot in snapshots:
        window.found += snapshot.found
        window.candidates += snapshot.candidates
        window.graded += snapshot.graded
        window.accepted += snapshot.accepted
        window.high_quality += snapshot.high_quality
        window.usable_hours += snapshot.usable_hours
        window.delivered_hours += snapshot.delivered_hours
        window.total_usd += snapshot.total_usd
    if snapshots:
        window.since = snapshots[0].ran_at
        window.until = snapshots[-1].ran_at
    return window


def render_report(
    card: Scorecard,
    snapshot: Snapshot,
    history: list[Snapshot],
) -> str:
    """The dated report: this tick, how it moved, and the full scorecard."""
    # `history` includes this snapshot as its last entry.
    lineage = same_slice(history, snapshot.slice_name)
    previous = lineage[-2] if len(lineage) > 1 else None
    window = pool(lineage[-WINDOW:])
    earlier = pool(lineage[-2 * WINDOW : -WINDOW]) if len(lineage) > WINDOW else None

    low, high = wilson(snapshot.accepted, snapshot.graded)
    build = snapshot.build or {}

    lines = [
        f"# Performance report — {snapshot.ran_at}",
        "",
        f"Eval set `{snapshot.eval_version}` · `{snapshot.slice_name}` slice · "
        f"{snapshot.queries} queries · {snapshot.graded} clips graded",
        "",
        "| what was measured | |",
        "| --- | --- |",
        f"| deployment | {snapshot.deployment or '—'} |",
        f"| build | version `{build.get('version', '—')}`, "
        f"model `{build.get('model', '—')}`, "
        f"viewpoint check `{build.get('viewpoint_check', '—')}` |",
        f"| harness commit | `{(snapshot.commit or '—')[:12]}` |",
        f"| spent | ${snapshot.total_usd:.2f} |",
        "",
        "## Headline",
        "",
        "| metric | this run | 95% interval | previous | window "
        f"({window.ticks} {_ticks(window.ticks)}, {window.graded} clips) |",
        "| --- | --- | --- | --- | --- |",
        f"| survived the screen | {_screen(snapshot)} | "
        f"{_interval(snapshot.candidates, snapshot.found)} | "
        f"{_screen(previous)}{_screen_move(snapshot, previous)} | "
        f"{_screen(window)} |",
        f"| acceptance rate | {_pct(snapshot.acceptance_rate)} "
        f"({snapshot.accepted}/{snapshot.graded}) | "
        f"{_pct(low)}–{_pct(high)} | "
        f"{_pct(previous.acceptance_rate) if previous else '—'}"
        f"{_delta(snapshot.acceptance_rate, previous.acceptance_rate) if previous else ''} | "
        f"{_pct(window.acceptance_rate)} |",
        f"| A or B share | {_pct(snapshot.high_quality_rate)} "
        f"({snapshot.high_quality}/{snapshot.graded}) | "
        f"{_interval(snapshot.high_quality, snapshot.graded)} | "
        f"{_pct(previous.high_quality_rate) if previous else '—'}"
        f"{_delta(snapshot.high_quality_rate, previous.high_quality_rate) if previous else ''} | "
        f"{_pct(window.high_quality_rate)} |",
        f"| usable time ratio | {_pct(snapshot.usable_time_ratio)} | — | "
        f"{_pct(previous.usable_time_ratio) if previous else '—'} | "
        f"{_pct(_ratio(window.usable_hours, window.delivered_hours))} |",
        f"| $ / usable hour | {_usd(snapshot.usd_per_usable_hour, snapshot.usable_hours)} | "
        f"— | {_usd(previous.usd_per_usable_hour, previous.usable_hours) if previous else '—'} | "
        f"{_usd(window.usd_per_usable_hour, window.usable_hours)} |",
        f"| $ / accepted clip | {_usd(snapshot.usd_per_accepted_clip, snapshot.accepted)} | "
        f"— | {_usd(previous.usd_per_accepted_clip, previous.accepted) if previous else '—'} | "
        f"{_usd(_ratio(window.total_usd, window.accepted), window.accepted)} |",
        "",
    ]

    if earlier:
        lines += [
            f"Against the {earlier.ticks} {_ticks(earlier.ticks)} before this window "
            f"({earlier.graded} clips): acceptance "
            f"{_pct(earlier.acceptance_rate)} → {_pct(window.acceptance_rate)}"
            f"{_delta(window.acceptance_rate, earlier.acceptance_rate)}, "
            f"A-or-B {_pct(earlier.high_quality_rate)} → "
            f"{_pct(window.high_quality_rate)}"
            f"{_delta(window.high_quality_rate, earlier.high_quality_rate)}.",
            "",
        ]

    lines += [
        _sample_caveat(snapshot, low, high),
        "",
        "## Grades",
        "",
        "| grade | clips | $ to obtain one |",
        "| --- | --- | --- |",
    ]
    for grade in GRADES:
        clips = snapshot.grades.get(grade, 0)
        lines.append(
            f"| {grade} | {clips} | {_usd(snapshot.usd_per_grade.get(grade, 0.0), clips)} |"
        )

    lines += ["", "## Trend", "", *trend_table(history), ""]
    lines += ["## Full scorecard", "", render(card, title="This run, in full").split("\n", 1)[1]]
    return "\n".join(lines).rstrip() + "\n"


def trend_table(history: list[Snapshot], rows: int = TREND_ROWS) -> list[str]:
    """The last few ticks, newest first."""
    table = [
        "| ran at | slice | clips | accepted | A+B | usable h | $ | $/usable h |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for snapshot in reversed(history[-rows:]):
        table.append(
            f"| {snapshot.ran_at} | {snapshot.slice_name} | {snapshot.graded} | "
            f"{snapshot.accepted} ({_pct(snapshot.acceptance_rate)}) | "
            f"{snapshot.high_quality} ({_pct(snapshot.high_quality_rate)}) | "
            f"{snapshot.usable_hours:.2f} | ${snapshot.total_usd:.2f} | "
            f"{_usd(snapshot.usd_per_usable_hour, snapshot.usable_hours)} |"
        )
    return table


def render_readme_block(history: list[Snapshot]) -> str:
    """The block the README carries, between the markers.

    Deliberately small: the latest tick, the window it sits in, and enough of a
    caveat that nobody quotes a twelve-clip percentage as a measurement. The
    full report is a link away.
    """
    if not history:
        return (
            f"{README_START}\n"
            "_No recurring run has reported yet._\n"
            f"{README_END}"
        )

    latest = history[-1]
    lineage = same_slice(history, latest.slice_name)
    window = pool(lineage[-WINDOW:])
    low, high = wilson(latest.accepted, latest.graded)
    day_ago = _closest_before(lineage, latest, hours=24)
    week_ago = _closest_before(lineage, latest, hours=24 * 7)

    lines = [
        README_START,
        f"**Latest run — {latest.ran_at}** · eval set `{latest.eval_version}` · "
        f"`{latest.slice_name}` slice, {latest.queries} queries, "
        f"{latest.graded} clips graded, ${latest.total_usd:.2f} spent",
        "",
        "| metric | latest | 95% interval | 24h ago | 7d ago | "
        f"rolling {window.ticks} {_runs(window.ticks)} ({window.graded} clips) |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| survived the screen | **{_screen(latest)}** | "
        f"{_interval(latest.candidates, latest.found)} | "
        f"{_screen(day_ago)} | {_screen(week_ago)} | "
        f"{_screen(window)} |",
        f"| accepted | **{_pct(latest.acceptance_rate)}** "
        f"({latest.accepted}/{latest.graded}) | {_pct(low)}–{_pct(high)} | "
        f"{_was(day_ago, 'acceptance_rate')} | {_was(week_ago, 'acceptance_rate')} | "
        f"{_pct(window.acceptance_rate)} |",
        f"| A or B | **{_pct(latest.high_quality_rate)}** "
        f"({latest.high_quality}/{latest.graded}) | "
        f"{_interval(latest.high_quality, latest.graded)} | "
        f"{_was(day_ago, 'high_quality_rate')} | {_was(week_ago, 'high_quality_rate')} | "
        f"{_pct(window.high_quality_rate)} |",
        f"| usable time | **{_pct(latest.usable_time_ratio)}** | — | "
        f"{_was(day_ago, 'usable_time_ratio')} | {_was(week_ago, 'usable_time_ratio')} | "
        f"{_pct(_ratio(window.usable_hours, window.delivered_hours))} |",
        f"| $ / usable hour | "
        f"**{_usd(latest.usd_per_usable_hour, latest.usable_hours)}** | — | "
        f"{_was(day_ago, 'usd_per_usable_hour', money=True)} | "
        f"{_was(week_ago, 'usd_per_usable_hour', money=True)} | "
        f"{_usd(window.usd_per_usable_hour, window.usable_hours)} |",
        "",
        "Grades this run: "
        + " · ".join(f"**{grade}** {latest.grades.get(grade, 0)}" for grade in GRADES)
        + f" · anchors {latest.action_anchors}"
        + (
            f" · ⚠️ {latest.contradictions} contradiction(s) with the standard"
            if latest.contradictions
            else ""
        ),
        "",
        "Runs every eight hours on a fixed slice of the eval set, so the numbers "
        "are comparable day to day, and small enough that one tick cannot "
        "resolve a small change on its own — read the interval and the rolling "
        "column, and quote a full 200-query run rather than a tick. Reports: "
        "[`eval/reports/`](eval/reports/) · latest: "
        "[`eval/REPORT.md`](eval/REPORT.md) · history: "
        "[`eval/history.jsonl`](eval/history.jsonl).",
        README_END,
    ]
    return "\n".join(lines)


def update_readme(text: str, block: str) -> str:
    """Replace the block between the markers, leaving everything else alone."""
    start = text.find(README_START)
    end = text.find(README_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError(
            f"README is missing the {README_START} / {README_END} markers; "
            "add them where the metrics should appear"
        )
    return text[:start] + block + text[end + len(README_END) :]


# --- formatting ---------------------------------------------------------------


def _sample_caveat(snapshot: Snapshot, low: float, high: float) -> str:
    """Say in words how much this tick can and cannot show."""
    if not snapshot.graded:
        return (
            "> ⚠️ Nothing was graded this run, so every rate above is undefined "
            "rather than zero. Check the errors in the scorecard below."
        )
    width = high - low
    return (
        f"> The acceptance rate here is {snapshot.accepted} of {snapshot.graded} clips, "
        f"so its 95% interval spans {100 * width:.0f} points. A change smaller than "
        f"that is not visible in one tick — the rolling column is the one to read, "
        f"and the full 200-query run is the number to quote."
    )


def _closest_before(
    history: list[Snapshot], latest: Snapshot, *, hours: int
) -> Snapshot | None:
    """The most recent snapshot at least `hours` before the latest one."""
    cutoff = _parse(latest.ran_at)
    if cutoff is None:
        return None
    earlier = [
        snapshot
        for snapshot in history
        if (moment := _parse(snapshot.ran_at)) is not None
        and (cutoff - moment).total_seconds() >= hours * 3600
    ]
    return earlier[-1] if earlier else None


def _parse(stamp: str) -> datetime | None:
    try:
        return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def _was(snapshot: Snapshot | None, attribute: str, *, money: bool = False) -> str:
    """A past value, with the movement since, or an em dash if there is no past."""
    if snapshot is None:
        return "—"
    value = getattr(snapshot, attribute)
    if money:
        return f"${value:.2f}" if value else "—"
    return _pct(value)


def _screen_move(now: Snapshot, previous: Snapshot | None) -> str:
    """Movement in the screen's survival rate, only when both ends measured it."""
    if previous is None or not (now.screen_measured and previous.screen_measured):
        return ""
    return _delta(now.screen_survival_rate, previous.screen_survival_rate)


def _screen(source: Snapshot | Window | None) -> str:
    """The screen's survival rate with its denominator, or an honest dash.

    A run recorded before the funnel counted what the screen dropped has no
    denominator here, and reporting that as 0% would read as "the screen threw
    everything away" — the opposite of "we did not measure it".
    """
    if source is None or not source.screen_measured:
        return "—"
    return f"{_pct(source.screen_survival_rate)} ({source.candidates}/{source.found})"


def _move(now: float, previous: Snapshot | None, attribute: str = "") -> str:
    """The movement against a previous snapshot, or nothing if there isn't one."""
    if previous is None:
        return ""
    return _delta(now, getattr(previous, attribute or "screen_survival_rate"))


def _delta(now: float, before: float) -> str:
    points = 100 * (now - before)
    if abs(points) < 0.5:
        return " (=)"
    return f" ({'+' if points > 0 else '−'}{abs(points):.0f}pp)"


def _interval(successes: int, total: int) -> str:
    low, high = wilson(successes, total)
    return f"{_pct(low)}–{_pct(high)}" if total else "—"


def _runs(count: int) -> str:
    return "run" if count == 1 else "runs"


def _ticks(count: int) -> str:
    return "tick" if count == 1 else "ticks"


def _pct(value: float) -> str:
    return f"{100 * value:.0f}%"


def _usd(value: float, denominator: float) -> str:
    return f"${value:.2f}" if denominator else "—"


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
