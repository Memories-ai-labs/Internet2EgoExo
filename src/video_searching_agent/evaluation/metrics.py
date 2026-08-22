"""What a pipeline run yielded, and what each grade of clip cost to get.

The whole-pipeline QA run (`qa/run_pipeline.py`) answers a yes/no question: did
five task queries each produce a set the audit accepts. That is the right
question for a release gate and the wrong one for a business. The numbers this
module produces are the other kind:

* **Yield.** A hundred videos found, twenty downloaded, how many survived, and
  how many narration anchors came out the other end. Every step of that funnel
  loses something, and the interesting number is not the total — it is which
  step is losing it.
* **Yield by grade.** The quality standard's scorecard puts every clip in a band
  (A ≥85, B 70–84, C 55–69, D <55) and gives each band a different disposition:
  A is sellable, B is trainable, C may not be counted as high-quality hours at
  all. "We produced 1,000 clips" therefore means nothing until it is split four
  ways.
* **Cost by grade.** The same split, in dollars. What a run spends is joint —
  one search pays for every clip it finds — so this reports two numbers with
  different meanings and says which is which: an *attributed* cost, where every
  dollar lands on exactly one clip and the bands sum to the total, and a *cost
  to obtain*, which is the whole run divided by the clips of that grade and
  answers "if A-grade footage is all we wanted, what did each one cost?".

Two disciplines are inherited from the standard and are the reason this module
is longer than a few divisions.

**Nothing is reported that was not measured.** The pipeline reports its own
discovery spend, the Datalake bills per video-minute, and the annotation loop's
calls are countable — those are real. The curation model's tokens are not
exposed over the API, and download egress is zero on owned infrastructure.
Those go in `unmeasured`, in the scorecard, in words, instead of being filled
with a plausible guess that would then get quoted.

**Money spent on nothing still counts.** A query that returns nothing has still
paid for its search. That spend cannot be attributed to any clip, so it is held
in `stranded_discovery_usd` and added to the run total. Dropping it would make
a run that failed half its queries look cheaper per clip than one that
succeeded on all of them.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

from video_searching_agent.curation.cost import (
    DERIVED_READ_PER_CALL,
    INDEX_PER_VIDEO_MINUTE,
    MOMENT_PER_CALL,
    SEARCH_PER_CALL,
)
from video_searching_agent.curation.quality_gates import Grade

# The bands, worst last, so every report lists them in the same order.
GRADES: tuple[str, ...] = (Grade.A.value, Grade.B.value, Grade.C.value, Grade.D.value)

# What the standard says each band may be used for. Carried into the scorecard
# so a reader does not have to hold the disposition table in their head.
DISPOSITION: dict[str, str] = {
    Grade.A.value: "score >=85 — main training set, and sellable externally",
    Grade.B.value: "score 70-84 — main training set, not yet external",
    Grade.C.value: "score 55-69 — pretrain / scene-diversity only; not high-quality hours",
    Grade.D.value: "score <55 — not ingested",
}

# A and B are the bands the standard lets a batch count as high-quality hours.
HIGH_QUALITY = frozenset({Grade.A.value, Grade.B.value})


@dataclass
class ClipOutcome:
    """One clip, from what the Datalake billed to what the gates concluded."""

    query_id: str
    video_id: str
    grade: str = Grade.D.value
    score: int = 0
    accepted: bool = False
    annotation_level: str = "L0"
    duration_seconds: int = 0
    usable_seconds: int = 0
    idle_seconds: int = 0
    action_anchors: int = 0
    total_anchors: int = 0
    annotations: int = 0
    blocking_failures: list[str] = field(default_factory=list)

    # --- validity: the one thing the project delivers -------------------
    #
    # A grade is a composite of things a buyer did not ask about; what they
    # asked for is a clip you can train on. That is: the hands are in frame,
    # the manipulation is legible, and there is a tree over it naming atomic
    # actions with what each hand did and to what. These three fields are the
    # per-clip evidence for that, recorded rather than derived from the grade,
    # because the grade also moves with licence and resolution.
    #
    # `hands_gate` is "passed" / "failed" / "unmeasured" — never a bool, since
    # a clip whose captions could not settle it has not failed anything.
    hands_gate: str = "unmeasured"
    # Annotated action spans that name at least one hand, and that name at
    # least one object. An action span with neither is a label, not a
    # demonstration.
    actions_with_hands: int = 0
    actions_with_objects: int = 0

    # --- what it cost, in billable units rather than dollars ------------
    #
    # Units, not dollars, because the rates belong in one place
    # (`curation.cost`) and a run recorded in units can be re-costed when the
    # Datalake's price list changes.
    indexed_minutes: float = 0.0
    moment_search_calls: int = 0
    moment_read_calls: int = 0
    derived_reads: int = 0
    look_usd: float = 0.0

    @property
    def direct_usd(self) -> float:
        """Spend that exists only because of this clip."""
        return (
            self.indexed_minutes * INDEX_PER_VIDEO_MINUTE
            + self.moment_search_calls * SEARCH_PER_CALL
            + self.moment_read_calls * MOMENT_PER_CALL
            + self.derived_reads * DERIVED_READ_PER_CALL
            + self.look_usd
        )

    @property
    def high_quality(self) -> bool:
        return self.accepted and self.grade in HIGH_QUALITY

    @property
    def validity_measured(self) -> bool:
        """Whether this record carries the evidence validity needs.

        Records written before the validity fields existed default to
        `hands_gate="unmeasured"` with zero action detail, which would read as
        *invalid* when it means *not measured* — the repo's own rule broken in a
        new place. The runner never writes "unmeasured" for a clip that has
        annotations (labels present means the gate was read one way or the
        other), so that combination identifies an older record exactly.
        """
        return not (self.hands_gate == "unmeasured" and self.annotations > 0)

    @property
    def valid(self) -> bool:
        """Whether this clip is the thing the project exists to produce.

        Hands in frame, legible footage, and a tree with at least one atomic
        action carrying hand or object detail. Deliberately independent of
        grade: a clip can be a C purely because its licence is not Creative
        Commons (measured: licence is worth 7 points and is the C/B boundary)
        and still be perfectly trainable. Deliberately independent of
        annotation *level* too — L2 versus L3 is depth for its own sake, and
        what matters is whether an action span says what the hands did.

        Legibility is not re-checked here: an illegible candidate is dropped
        before download, so anything that reached grading has passed it.
        """
        return (
            self.hands_gate != "failed"
            and not self.blocking_failures
            and (self.actions_with_hands + self.actions_with_objects) > 0
        )


@dataclass
class QueryOutcome:
    """One eval query, from the search to the graded set."""

    query_id: str
    query: str
    task_family: str = ""
    difficulty: str = ""
    rdt_id: str = ""
    # What the search turned up before the pre-download screen, and what the
    # screen did with it. Without these, a query whose footage all existed but
    # was all tripod-shot is indistinguishable from a query the search could
    # not answer, and the two say opposite things about the pipeline. Measured:
    # "someone assembling the cabinet" finds 18 videos, 14 of which genuinely
    # show cabinet assembly, and every one is exocentric.
    found: int = 0
    screened_out: int = 0
    screen_reasons: dict[str, int] = field(default_factory=dict)
    candidates: int = 0
    attempted: int = 0
    indexed: int = 0
    discovery_usd: float = 0.0
    clips: list[ClipOutcome] = field(default_factory=list)
    seconds: float = 0.0
    error: str = ""
    # A dry run searched and stopped. Recorded, because a dry-run record scored
    # later is otherwise indistinguishable from a run where everything failed.
    dry_run: bool = False

    @property
    def graded(self) -> int:
        return len(self.clips)

    @property
    def accepted(self) -> int:
        return sum(1 for clip in self.clips if clip.accepted)

    @property
    def valid(self) -> int:
        return sum(1 for clip in self.clips if clip.valid)


@dataclass
class YieldChain:
    """The funnel, one number per step, plus the ratios between them."""

    queries: int = 0
    queries_with_candidates: int = 0
    queries_with_an_accepted_clip: int = 0
    queries_errored: int = 0
    queries_dry_run: int = 0
    # A query the search answered and the screen emptied. Its own row, because
    # "the footage does not exist" and "the footage exists and is the wrong
    # viewpoint" are different findings and only one of them is about us.
    queries_screened_to_nothing: int = 0
    found: int = 0
    screened_out: int = 0
    screen_reasons: dict[str, int] = field(default_factory=dict)
    candidates: int = 0
    attempted: int = 0
    indexed: int = 0
    graded: int = 0
    accepted: int = 0
    high_quality: int = 0
    # The headline. Counted alongside `accepted` rather than replacing it, so a
    # divergence between them is visible: a clip that is valid but not accepted
    # is one the gates rejected for something a buyer did not ask about.
    valid: int = 0
    queries_with_a_valid_clip: int = 0
    valid_hours: float = 0.0
    # Clips whose records predate the validity fields. Excluded from the rate's
    # denominator rather than counted against it.
    validity_unmeasured: int = 0
    action_anchors: int = 0
    accepted_action_anchors: int = 0
    total_anchors: int = 0
    annotations: int = 0
    delivered_hours: float = 0.0
    usable_hours: float = 0.0
    idle_hours: float = 0.0

    @property
    def screen_survival_rate(self) -> float:
        """Of what the search found, how much the pre-download screen let through.

        The first ratio in the funnel, and on a robot-derived query set it is
        the smallest one: the footage of a named task usually exists and is
        usually shot on a tripod.
        """
        return _ratio(self.candidates, self.found)

    @property
    def index_rate(self) -> float:
        """Of the candidates we tried to collect, how many reached the Datalake."""
        return _ratio(self.indexed, self.attempted)

    @property
    def acceptance_rate(self) -> float:
        """Of the clips that were graded, how many the gates accepted."""
        return _ratio(self.accepted, self.graded)

    @property
    def validity_rate(self) -> float:
        """Of the clips that were graded, how many are trainable.

        The project's one number: hands in frame, legible, and annotated with
        atomic actions naming hands or objects. Read this before the grade
        bands — a grade mixes in licence and resolution, which are real
        concerns but not what makes a clip usable.
        """
        return _ratio(self.valid, self.graded - self.validity_unmeasured)

    @property
    def valid_query_rate(self) -> float:
        """Of the queries asked, how many produced at least one valid clip."""
        return _ratio(self.queries_with_a_valid_clip, self.queries)

    @property
    def valid_per_query(self) -> float:
        """Valid clips per query asked — the number to compare runs on.

        Per *query asked*, not per query that found something, so a run cannot
        improve by failing to search.
        """
        return _ratio(self.valid, self.queries)

    @property
    def validity_is_measurable(self) -> bool:
        """Whether any clip in this run recorded what validity needs."""
        return self.graded > self.validity_unmeasured

    @property
    def high_quality_rate(self) -> float:
        """Of the clips that were graded, how many an A or a B."""
        return _ratio(self.high_quality, self.graded)

    @property
    def query_success_rate(self) -> float:
        """Of the queries asked, how many produced at least one accepted clip."""
        return _ratio(self.queries_with_an_accepted_clip, self.queries)

    @property
    def usable_time_ratio(self) -> float:
        """Of the footage that reached us, how much of it is usable seconds.

        The standard's `accepted_hours` measure: delivered hours minus idle and
        minus what Gate 1 removed. Reporting delivered hours as output inflates
        the ramp chart by 30-40%, which is why both are carried separately.
        """
        return _ratio(self.usable_hours, self.delivered_hours)

    @property
    def anchors_per_accepted_clip(self) -> float:
        """Anchors on accepted clips, per accepted clip.

        Counted over accepted clips only. Dividing every anchor the run produced
        by the clips that survived would credit the accepted ones with work done
        on footage that was thrown away.
        """
        return _ratio(self.accepted_action_anchors, self.accepted)

    @property
    def anchors_per_usable_hour(self) -> float:
        return _ratio(self.action_anchors, self.usable_hours)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.update(
            {
                "index_rate": round(self.index_rate, 4),
                "acceptance_rate": round(self.acceptance_rate, 4),
                "high_quality_rate": round(self.high_quality_rate, 4),
                "query_success_rate": round(self.query_success_rate, 4),
                "usable_time_ratio": round(self.usable_time_ratio, 4),
                "anchors_per_accepted_clip": round(self.anchors_per_accepted_clip, 2),
                "anchors_per_usable_hour": round(self.anchors_per_usable_hour, 2),
            }
        )
        return data


@dataclass
class CostLedger:
    """Where the money went, and what could not be measured."""

    discovery_usd: float = 0.0
    indexing_usd: float = 0.0
    annotation_usd: float = 0.0
    derived_read_usd: float = 0.0
    look_usd: float = 0.0
    stranded_discovery_usd: float = 0.0
    total_usd: float = 0.0
    unmeasured: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "discovery_usd": round(self.discovery_usd, 4),
            "indexing_usd": round(self.indexing_usd, 4),
            "annotation_usd": round(self.annotation_usd, 4),
            "derived_read_usd": round(self.derived_read_usd, 4),
            "look_usd": round(self.look_usd, 4),
            "stranded_discovery_usd": round(self.stranded_discovery_usd, 4),
            "total_usd": round(self.total_usd, 4),
            "unmeasured": list(self.unmeasured),
        }


@dataclass
class GradeBand:
    """One band of the scorecard: how much of it there is, and what it cost."""

    grade: str
    disposition: str = ""
    clips: int = 0
    share_of_graded: float = 0.0
    accepted: int = 0
    usable_hours: float = 0.0
    action_anchors: int = 0
    annotation_levels: dict[str, int] = field(default_factory=dict)

    # Attributed: every dollar of the run lands on exactly one band, so these
    # sum to the run total.
    attributed_usd: float = 0.0
    usd_per_clip: float = 0.0
    usd_per_usable_hour: float = 0.0
    usd_per_action_anchor: float = 0.0

    # Cost to obtain: the whole run divided by this band's clips. Answers "what
    # did one of these cost us", and deliberately does not sum to the total.
    usd_per_clip_obtained: float = 0.0
    usd_per_usable_hour_obtained: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "share_of_graded",
            "usable_hours",
            "attributed_usd",
            "usd_per_clip",
            "usd_per_usable_hour",
            "usd_per_action_anchor",
            "usd_per_clip_obtained",
            "usd_per_usable_hour_obtained",
        ):
            data[key] = round(data[key], 4)
        return data


@dataclass
class Stratum:
    """One difficulty tier or task family, scored on its own."""

    name: str
    queries: int = 0
    graded: int = 0
    accepted: int = 0
    high_quality: int = 0
    # The headline. Counted alongside `accepted` rather than replacing it, so a
    # divergence between them is visible: a clip that is valid but not accepted
    # is one the gates rejected for something a buyer did not ask about.
    valid: int = 0
    queries_with_a_valid_clip: int = 0
    valid_hours: float = 0.0
    # Clips whose records predate the validity fields. Excluded from the rate's
    # denominator rather than counted against it.
    validity_unmeasured: int = 0
    usable_hours: float = 0.0
    attributed_usd: float = 0.0
    grades: dict[str, int] = field(default_factory=dict)

    @property
    def acceptance_rate(self) -> float:
        return _ratio(self.accepted, self.graded)

    @property
    def high_quality_rate(self) -> float:
        return _ratio(self.high_quality, self.graded)

    @property
    def usd_per_accepted_clip(self) -> float:
        return _ratio(self.attributed_usd, self.accepted)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["usable_hours"] = round(self.usable_hours, 4)
        data["attributed_usd"] = round(self.attributed_usd, 4)
        data["acceptance_rate"] = round(self.acceptance_rate, 4)
        data["high_quality_rate"] = round(self.high_quality_rate, 4)
        data["usd_per_accepted_clip"] = round(self.usd_per_accepted_clip, 4)
        return data


@dataclass
class Scorecard:
    """Everything one eval run concluded."""

    eval_version: str = ""
    queries_run: int = 0
    chain: YieldChain = field(default_factory=YieldChain)
    cost: CostLedger = field(default_factory=CostLedger)
    bands: list[GradeBand] = field(default_factory=list)
    by_difficulty: list[Stratum] = field(default_factory=list)
    by_family: list[Stratum] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def band(self, grade: str) -> GradeBand:
        for band in self.bands:
            if band.grade == grade:
                return band
        return GradeBand(grade=grade, disposition=DISPOSITION.get(grade, ""))

    def as_dict(self) -> dict[str, Any]:
        return {
            "eval_version": self.eval_version,
            "queries_run": self.queries_run,
            "yield": self.chain.as_dict(),
            "cost": self.cost.as_dict(),
            "grades": [band.as_dict() for band in self.bands],
            "by_difficulty": [s.as_dict() for s in self.by_difficulty],
            "by_family": [s.as_dict() for s in self.by_family],
            "contradictions": list(self.contradictions),
            "errors": list(self.errors),
        }


# The terms this harness cannot measure from outside the deployment. Named here
# so the scorecard can say so rather than implying the total is complete.
UNMEASURED_TERMS: tuple[str, ...] = (
    "curation, cleaning and narration model tokens — not reported over the "
    "pipeline API (the frame-examination spend inside them is, and is counted)",
    "download egress and disk — $0 on owned infrastructure, not billed per run",
    "Gate 3 diversity and dedup — scored per dataset, not per clip",
    "human ground truth (IAA, boundary F1, caption 5-scale) — needs annotators",
)


def score_run(
    outcomes: list[QueryOutcome],
    *,
    eval_version: str = "",
    unmeasured: tuple[str, ...] = UNMEASURED_TERMS,
) -> Scorecard:
    """Turn per-query outcomes into the run's scorecard."""
    card = Scorecard(eval_version=eval_version, queries_run=len(outcomes))
    chain = card.chain
    chain.queries = len(outcomes)

    # --- the funnel and the ledger --------------------------------------
    stranded = 0.0
    attributed: dict[str, float] = {}
    for outcome in outcomes:
        if outcome.dry_run:
            chain.queries_dry_run += 1
        if outcome.error:
            chain.queries_errored += 1
            card.errors.append(f"{outcome.query_id}: {outcome.error}")
        if outcome.candidates:
            chain.queries_with_candidates += 1
        if outcome.accepted:
            chain.queries_with_an_accepted_clip += 1
        if outcome.valid:
            chain.queries_with_a_valid_clip += 1
        # Found something, kept nothing. Counted apart from queries_errored,
        # because this is the pipeline working: it says the footage of this task
        # is the wrong viewpoint, not that the search failed.
        if outcome.found and not outcome.candidates:
            chain.queries_screened_to_nothing += 1

        chain.found += outcome.found
        chain.screened_out += outcome.screened_out
        for reason, count in (outcome.screen_reasons or {}).items():
            chain.screen_reasons[reason] = chain.screen_reasons.get(reason, 0) + count
        chain.candidates += outcome.candidates
        chain.attempted += outcome.attempted
        chain.indexed += outcome.indexed
        chain.graded += outcome.graded

        card.cost.discovery_usd += outcome.discovery_usd
        # A search nobody could use is still a search somebody paid for.
        share = outcome.discovery_usd / outcome.graded if outcome.graded else 0.0
        if not outcome.graded:
            stranded += outcome.discovery_usd

        for clip in outcome.clips:
            chain.accepted += 1 if clip.accepted else 0
            chain.high_quality += 1 if clip.high_quality else 0
            if not clip.validity_measured:
                chain.validity_unmeasured += 1
            elif clip.valid:
                chain.valid += 1
                chain.valid_hours += clip.usable_seconds / 3600
            chain.action_anchors += clip.action_anchors
            if clip.accepted:
                chain.accepted_action_anchors += clip.action_anchors
            chain.total_anchors += clip.total_anchors
            chain.annotations += clip.annotations
            chain.delivered_hours += clip.duration_seconds / 3600
            chain.usable_hours += clip.usable_seconds / 3600
            chain.idle_hours += clip.idle_seconds / 3600

            card.cost.indexing_usd += clip.indexed_minutes * INDEX_PER_VIDEO_MINUTE
            card.cost.annotation_usd += (
                clip.moment_search_calls * SEARCH_PER_CALL
                + clip.moment_read_calls * MOMENT_PER_CALL
            )
            card.cost.derived_read_usd += clip.derived_reads * DERIVED_READ_PER_CALL
            card.cost.look_usd += clip.look_usd
            attributed[clip.video_id] = clip.direct_usd + share

    card.cost.stranded_discovery_usd = stranded
    card.cost.total_usd = (
        card.cost.discovery_usd
        + card.cost.indexing_usd
        + card.cost.annotation_usd
        + card.cost.derived_read_usd
        + card.cost.look_usd
    )
    card.cost.unmeasured = list(unmeasured)

    for value in (
        "delivered_hours",
        "usable_hours",
        "idle_hours",
    ):
        setattr(chain, value, round(getattr(chain, value), 4))

    # --- the bands ------------------------------------------------------
    clips = [clip for outcome in outcomes for clip in outcome.clips]
    for grade in GRADES:
        band = GradeBand(grade=grade, disposition=DISPOSITION.get(grade, ""))
        in_band = [clip for clip in clips if clip.grade == grade]
        band.clips = len(in_band)
        band.accepted = sum(1 for clip in in_band if clip.accepted)
        band.share_of_graded = _ratio(band.clips, chain.graded)
        band.usable_hours = sum(clip.usable_seconds for clip in in_band) / 3600
        band.action_anchors = sum(clip.action_anchors for clip in in_band)
        band.annotation_levels = dict(
            sorted(Counter(clip.annotation_level for clip in in_band).items())
        )
        band.attributed_usd = sum(attributed.get(clip.video_id, 0.0) for clip in in_band)
        band.usd_per_clip = _ratio(band.attributed_usd, band.clips)
        band.usd_per_usable_hour = _ratio(band.attributed_usd, band.usable_hours)
        band.usd_per_action_anchor = _ratio(band.attributed_usd, band.action_anchors)
        band.usd_per_clip_obtained = _ratio(card.cost.total_usd, band.clips)
        band.usd_per_usable_hour_obtained = _ratio(card.cost.total_usd, band.usable_hours)
        card.bands.append(band)

    # --- the strata -----------------------------------------------------
    card.by_difficulty = _strata(outcomes, attributed, key=lambda o: o.difficulty)
    card.by_family = _strata(outcomes, attributed, key=lambda o: o.task_family)
    card.contradictions = contradictions(clips)
    return card


def contradictions(clips: list[ClipOutcome]) -> list[str]:
    """Clips the pipeline accepted that the standard would not.

    An eval that only totals up what the pipeline says about itself is a
    self-report. These three are the cases where the pipeline's own two
    verdicts disagree, checked against the standard's text rather than against
    the code that produced them:

    * A D is "not ingested" — accepting one is a contradiction in terms.
    * A blocking Gate 0/1 failure is a veto, not a deduction.
    * L2 is "the minimum grade that is trainable and presentable externally",
      so an accepted clip below it is being counted as something it is not.

    A non-empty list here is a finding about the pipeline, not a bug in this
    module: it is reported and left for somebody to decide about.
    """
    found: list[str] = []
    accepted = [clip for clip in clips if clip.accepted]

    graded_d = [clip.video_id for clip in accepted if clip.grade == Grade.D.value]
    if graded_d:
        found.append(
            f"{len(graded_d)} accepted clip(s) graded D, which the standard says is "
            f"not ingested: {', '.join(graded_d[:5])}"
        )

    vetoed = [clip.video_id for clip in accepted if clip.blocking_failures]
    if vetoed:
        found.append(
            f"{len(vetoed)} accepted clip(s) carry a blocking gate failure: {', '.join(vetoed[:5])}"
        )

    shallow = [clip.video_id for clip in accepted if clip.annotation_level in ("L0", "L1")]
    if shallow:
        found.append(
            f"{len(shallow)} accepted clip(s) below L2, the minimum trainable depth: "
            f"{', '.join(shallow[:5])}"
        )
    return found


def _strata(
    outcomes: list[QueryOutcome],
    attributed: dict[str, float],
    *,
    key: Any,
) -> list[Stratum]:
    """Group query outcomes by one axis and score each group."""
    groups: dict[str, Stratum] = {}
    for outcome in outcomes:
        name = key(outcome) or "unclassified"
        stratum = groups.setdefault(name, Stratum(name=name))
        stratum.queries += 1
        for clip in outcome.clips:
            stratum.graded += 1
            stratum.accepted += 1 if clip.accepted else 0
            stratum.high_quality += 1 if clip.high_quality else 0
            stratum.usable_hours += clip.usable_seconds / 3600
            stratum.attributed_usd += attributed.get(clip.video_id, 0.0)
            stratum.grades[clip.grade] = stratum.grades.get(clip.grade, 0) + 1
    # Worst acceptance first: a stratified report exists to show where it fails.
    return sorted(groups.values(), key=lambda s: (s.acceptance_rate, -s.graded, s.name))


def _ratio(numerator: float, denominator: float) -> float:
    """Divide, or return zero — an undefined ratio is not a zero one, but a
    report full of `None` is unreadable, so the denominator is carried alongside
    every ratio in the output and a zero here always has a zero next to it."""
    return numerator / denominator if denominator else 0.0


# --- persistence ---------------------------------------------------------------
#
# A 200-query run takes hours and costs money, so it is written down one query
# at a time and can be resumed, and a scorecard can be recomputed from the
# record without paying for the run again. Which means the record has to
# round-trip exactly: `outcome_from_dict(outcome_as_dict(x)) == x`.


def clip_as_dict(clip: ClipOutcome) -> dict[str, Any]:
    return asdict(clip)


def outcome_as_dict(outcome: QueryOutcome) -> dict[str, Any]:
    data = asdict(outcome)
    data["clips"] = [clip_as_dict(clip) for clip in outcome.clips]
    return data


def clip_from_dict(data: dict[str, Any]) -> ClipOutcome:
    fields = {f for f in ClipOutcome.__dataclass_fields__}
    return ClipOutcome(**{key: value for key, value in data.items() if key in fields})


def outcome_from_dict(data: dict[str, Any]) -> QueryOutcome:
    fields = {f for f in QueryOutcome.__dataclass_fields__} - {"clips"}
    outcome = QueryOutcome(
        **{key: value for key, value in data.items() if key in fields},
    )
    outcome.clips = [clip_from_dict(clip) for clip in data.get("clips") or []]
    return outcome
