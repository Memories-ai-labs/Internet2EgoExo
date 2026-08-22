"""Render an eval run as something a person will actually read.

The JSON the metrics module produces is the record; this is the page somebody
looks at. Two rules shape it:

* **Every ratio is printed next to its denominator.** "44% accepted" out of nine
  clips and out of nine hundred are different claims, and a percentage on its
  own hides which one it is.
* **What was not measured is printed too**, at the bottom, in words. A cost
  table with a missing term looks exactly like a complete one.
"""

from __future__ import annotations

from video_searching_agent.evaluation.metrics import GRADES, Scorecard, Stratum


def render(card: Scorecard, *, title: str = "Eval scorecard") -> str:
    """Render the scorecard as Markdown."""
    chain = card.chain
    cost = card.cost
    lines: list[str] = [
        f"# {title}",
        "",
        f"Eval set `{card.eval_version or 'unversioned'}` · "
        f"{card.queries_run} quer{'y' if card.queries_run == 1 else 'ies'} run",
        "",
    ]
    if chain.queries_dry_run:
        lines += [
            f"> ⚠️ {chain.queries_dry_run} of these were **dry runs**: they searched "
            "and stopped. Nothing was downloaded, indexed, graded or annotated, so "
            "everything below the candidate count is empty by construction.",
            "",
        ]
    lines += [
        "## 1. Yield — where the funnel loses things",
        "",
        "| step | count | of the step before |",
        "| --- | --- | --- |",
        f"| queries asked | {chain.queries} | — |",
        f"| queries that found candidates | {chain.queries_with_candidates} | "
        f"{_pct(chain.queries_with_candidates, chain.queries)} |",
        f"| candidates found | {chain.candidates} | — |",
        f"| candidates we tried to collect | {chain.attempted} | "
        f"{_pct(chain.attempted, chain.candidates)} |",
        f"| reached the Datalake | {chain.indexed} | {_pct(chain.indexed, chain.attempted)} |",
        f"| graded by the gates | {chain.graded} | {_pct(chain.graded, chain.indexed)} |",
        f"| **accepted** | **{chain.accepted}** | "
        f"**{_pct(chain.accepted, chain.graded)}** |",
        f"| of those, an A or a B | {chain.high_quality} | "
        f"{_pct(chain.high_quality, chain.graded)} |",
        f"| queries with at least one accepted clip | "
        f"{chain.queries_with_an_accepted_clip} | "
        f"{_pct(chain.queries_with_an_accepted_clip, chain.queries)} |",
        "",
        "| time and anchors | value |",
        "| --- | --- |",
        f"| delivered hours (what reached us) | {chain.delivered_hours:.2f} |",
        f"| usable hours (Gate 0+1, idle removed) | {chain.usable_hours:.2f} |",
        f"| usable time ratio | {_pct(chain.usable_hours, chain.delivered_hours)} |",
        f"| idle hours, explicitly marked | {chain.idle_hours:.2f} |",
        f"| action anchors produced | {chain.action_anchors} |",
        f"| anchors per accepted clip | {chain.anchors_per_accepted_clip:.1f} |",
        f"| anchors per usable hour | {chain.anchors_per_usable_hour:.1f} |",
        "",
        "## 2. Grade bands — the same output, split four ways",
        "",
        "| grade | clips | share | usable h | anchors | $ attributed | $/clip | "
        "$/usable h | $ to obtain one |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for grade in GRADES:
        band = card.band(grade)
        lines.append(
            f"| **{band.grade}** | {band.clips} | "
            f"{_pct(band.clips, chain.graded)} | {band.usable_hours:.2f} | "
            f"{band.action_anchors} | ${band.attributed_usd:.2f} | "
            f"{_usd(band.usd_per_clip, band.clips)} | "
            f"{_usd(band.usd_per_usable_hour, band.usable_hours)} | "
            f"{_usd(band.usd_per_clip_obtained, band.clips)} |"
        )

    lines += [
        "",
        "`$ attributed` splits the run so every dollar lands on one clip; the "
        "column sums to the run total less stranded discovery spend. "
        "`$ to obtain one` is the whole run divided by that band's clips — it "
        "answers \"if this grade is all we wanted, what did each one cost\", and "
        "deliberately does not sum.",
        "",
        "| grade | what the standard allows |",
        "| --- | --- |",
    ]
    for grade in GRADES:
        lines.append(f"| {grade} | {card.band(grade).disposition} |")

    lines += [
        "",
        "## 3. Cost",
        "",
        "| term | USD |",
        "| --- | --- |",
        f"| discovery (measured: model + search tools) | ${cost.discovery_usd:.2f} |",
        f"| indexing (Datalake, per video-minute) | ${cost.indexing_usd:.2f} |",
        f"| annotation (moment search + read per anchor) | ${cost.annotation_usd:.2f} |",
        f"| derived reads (caption / transcription / summary) | "
        f"${cost.derived_read_usd:.4f} |",
        f"| looking at frames (measured by the agents) | ${cost.look_usd:.4f} |",
        f"| **total** | **${cost.total_usd:.2f}** |",
        f"| of which paid for queries that yielded nothing | "
        f"${cost.stranded_discovery_usd:.2f} |",
        "",
        f"Cost per usable hour delivered: "
        f"**{_usd(_div(cost.total_usd, chain.usable_hours), chain.usable_hours)}/h**. "
        f"Cost per accepted clip: "
        f"**{_usd(_div(cost.total_usd, chain.accepted), chain.accepted)}**. "
        f"Cost per A-or-B clip: "
        f"**{_usd(_div(cost.total_usd, chain.high_quality), chain.high_quality)}**.",
        "",
        "## 4. By difficulty",
        "",
        *_stratum_table(card.by_difficulty),
        "",
        "## 5. By task family — worst acceptance first",
        "",
        *_stratum_table(card.by_family),
        "",
        "## 6. Where the pipeline contradicts the standard",
        "",
    ]
    if card.contradictions:
        lines += [f"* {item}" for item in card.contradictions]
    else:
        lines.append("Nothing — every accepted clip is one the standard would accept.")

    lines += ["", "## 7. What this run did not measure", ""]
    lines += [f"* {term}" for term in cost.unmeasured]

    if card.errors:
        lines += ["", f"## 8. Queries that errored ({len(card.errors)})", ""]
        lines += [f"* {error}" for error in card.errors]

    return "\n".join(lines) + "\n"


def _stratum_table(strata: list[Stratum]) -> list[str]:
    rows = [
        "| stratum | queries | graded | accepted | A+B | usable h | $/accepted clip |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for stratum in strata:
        rows.append(
            f"| {stratum.name} | {stratum.queries} | {stratum.graded} | "
            f"{stratum.accepted} ({_pct(stratum.accepted, stratum.graded)}) | "
            f"{stratum.high_quality} ({_pct(stratum.high_quality, stratum.graded)}) | "
            f"{stratum.usable_hours:.2f} | "
            f"{_usd(stratum.usd_per_accepted_clip, stratum.accepted)} |"
        )
    return rows


def _pct(numerator: float, denominator: float) -> str:
    """A percentage, or an em dash when there is nothing to divide by."""
    if not denominator:
        return "—"
    return f"{100 * numerator / denominator:.0f}%"


def _usd(value: float, denominator: float) -> str:
    """A dollar figure, or an em dash when there was nothing to divide by.

    `$0.00` and "there were none of these" are different claims, and the second
    one is the more common.
    """
    return f"${value:.2f}" if denominator else "—"


def _div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
