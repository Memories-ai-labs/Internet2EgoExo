"""Dataset manifest models — the deliverable of a collection run.

A run's output is not prose: it is a list of clips with the metadata a
training pipeline needs to fetch and filter them, plus the totals that say
whether the collection goal was met.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from video_searching_agent.curation.cost import CostBreakdown
from video_searching_agent.curation.viewpoint import Viewpoint


class ClipAnnotation(BaseModel):
    """One annotated span inside a clip.

    Mirrors the moment-level schema the curation loop writes back: a span, what
    each hand is doing in it, and the tags that become filters for the next
    query (`hoi/solder-joint/right/operate-iron`).
    """

    span_start: float | None = Field(None, description="Span start in seconds")
    span_end: float | None = Field(None, description="Span end in seconds")
    ref: str | None = Field(None, description="Datalake moment ref, vid_x@start-end")

    segment_id: str | None = Field(None, description="Stable id for this span")
    parent_segment_id: str | None = Field(
        None,
        description="The span this one sits inside; None at the task level",
    )
    hier_level: str | None = Field(
        None,
        description="Where this sits in the tree: 'task', 'action' or 'event'",
    )
    narration: str | None = Field(
        None,
        description="One sentence describing this level in its own words",
    )

    label: str | None = Field(None, description="Short name for what happens here")
    left_hand: str | None = Field(None, description="What the left hand does")
    right_hand: str | None = Field(None, description="What the right hand does")
    objects: list[str] = Field(default_factory=list, description="Objects involved")
    tags: list[str] = Field(default_factory=list, description="Tags written back")

    source: str | None = Field(
        None,
        description="What produced this: 'agent', 'detector', 'human'",
    )
    confidence: float | None = Field(None, ge=0, le=1)
    caveat: str | None = Field(
        None,
        description="Known limitation, e.g. hand assignment read from caption wording",
    )


class DatasetClip(BaseModel):
    """One candidate clip in a collection manifest."""

    url: str
    platform: str
    platform_id: str | None = None
    title: str | None = None
    creator: str | None = None
    duration_seconds: int | None = None
    published_at: str | None = None

    # Curation
    viewpoint: Viewpoint = Viewpoint.UNKNOWN
    viewpoint_confidence: float = 0.0
    viewpoint_evidence: list[str] = Field(default_factory=list)
    license: str | None = None
    usability_score: float = 0.0
    activity_tags: list[str] = Field(default_factory=list)

    # Provenance
    source_tool: str | None = None
    thumbnail_url: str | None = None
    datalake_video_id: str | None = Field(
        None,
        description="Video id if this clip was indexed into the Video Datalake",
    )
    annotations: list[ClipAnnotation] = Field(
        default_factory=list,
        description="Moment-level annotations written by the curation loop",
    )

    # Quality standard (see curation/quality_gates.py)
    commercial_use_ok: bool = Field(
        False,
        description="Gate 0: the licence explicitly permits commercial training use",
    )
    quality_score: int | None = Field(None, ge=0, le=100)
    quality_grade: str | None = Field(None, description="A-D from the scorecard")
    annotation_level: str | None = Field(None, description="L0-L3 annotation depth")
    usable_seconds: int | None = Field(None, description="Duration minus idle")
    idle_seconds: int | None = None
    task_family: str | None = Field(None, description="Gate 3 coverage bucket")
    error_sample: bool = Field(
        False, description="Gate 3: this clip shows an error or a rework"
    )
    dup_group_id: str | None = Field(
        None, description="Near-duplicate group, when deduplication has run"
    )
    blocking_failures: list[str] = Field(
        default_factory=list, description="Gate ids that veto this clip outright"
    )
    notes: str | None = None


class Hours(BaseModel):
    """The four hour measures, kept apart.

    Mixing them is the classic way to overstate a dataset by a third:
    `delivered` is what was downloaded, `accepted` is what cleared the media
    gates with idle time removed, and `accepted_labeled` is the only figure
    that should ever be quoted externally.
    """

    worn_hours: float = 0.0
    delivered_hours: float = 0.0
    accepted_hours: float = 0.0
    accepted_labeled_hours: float = 0.0
    idle_hours: float = 0.0
    media_yield: float = Field(
        0.0, description="accepted / delivered — how much of the download survived"
    )


class DatasetManifest(BaseModel):
    """Everything a collection run gathered, with its totals."""

    query: str
    requested_viewpoint: Viewpoint | None = None
    target_hours: float | None = None

    total_clips: int = 0
    total_hours: float = Field(
        0.0,
        description="Delivered hours — every clip kept, before the media gates. "
        "Use `hours` for the measure you actually want to quote.",
    )
    clips_with_known_duration: int = 0

    hours: Hours = Field(
        default_factory=Hours,
        description="worn / delivered / accepted / accepted_labeled, never mixed",
    )
    accepted_clips: int = 0
    grades: dict[str, int] = Field(
        default_factory=dict, description="Clip count per scorecard grade"
    )
    annotation_levels: dict[str, int] = Field(
        default_factory=dict, description="Clip count per annotation depth"
    )
    dataset_checks: list[dict] = Field(
        default_factory=list, description="Gate 3 diversity/dedup checks"
    )

    by_viewpoint: dict[str, int] = Field(default_factory=dict)
    by_platform: dict[str, int] = Field(default_factory=dict)
    reusable_license_clips: int = 0

    excluded_clips: int = Field(
        0,
        description="Candidates dropped by viewpoint/duration/licence requirements",
    )
    exclusion_reasons: dict[str, int] = Field(default_factory=dict)

    cost: CostBreakdown | None = Field(
        None,
        description="What this collection cost, and the cost per usable hour",
    )

    clips: list[DatasetClip] = Field(default_factory=list)

    @property
    def measured_hours(self) -> float:
        """The hour figure a target should be judged against.

        The deepest measure available: labelled hours if the annotation pass has
        run, otherwise accepted hours, otherwise what was delivered.
        """
        return (
            self.hours.accepted_labeled_hours
            or self.hours.accepted_hours
            or self.total_hours
        )

    @property
    def target_met(self) -> bool:
        """True when a requested hour target has been reached."""
        if not self.target_hours:
            return True
        return self.measured_hours >= self.target_hours

    def recompute_totals(self) -> DatasetManifest:
        """Recalculate every aggregate from the current clip list."""
        self.total_clips = len(self.clips)

        known = [c.duration_seconds for c in self.clips if c.duration_seconds]
        self.clips_with_known_duration = len(known)
        self.total_hours = round(sum(known) / 3600, 3)

        by_viewpoint: dict[str, int] = {}
        by_platform: dict[str, int] = {}
        reusable = 0
        for clip in self.clips:
            key = clip.viewpoint.value if isinstance(clip.viewpoint, Viewpoint) else str(
                clip.viewpoint
            )
            by_viewpoint[key] = by_viewpoint.get(key, 0) + 1
            by_platform[clip.platform] = by_platform.get(clip.platform, 0) + 1
            from video_searching_agent.curation.scoring import is_reusable_license

            if is_reusable_license(clip.license):
                reusable += 1

        self.by_viewpoint = by_viewpoint
        self.by_platform = by_platform
        self.reusable_license_clips = reusable

        grades: dict[str, int] = {}
        levels: dict[str, int] = {}
        accepted_seconds = idle_seconds = labeled_seconds = 0.0
        accepted = 0
        for clip in self.clips:
            if clip.quality_grade:
                grades[clip.quality_grade] = grades.get(clip.quality_grade, 0) + 1
            if clip.annotation_level:
                levels[clip.annotation_level] = levels.get(clip.annotation_level, 0) + 1
            idle_seconds += clip.idle_seconds or 0
            # A clip counts as accepted only once the gates have graded it and
            # nothing blocking failed. Ungraded clips stay in delivered only.
            gated = clip.quality_grade is not None and not clip.blocking_failures
            if gated and clip.quality_grade != "D":
                accepted += 1
                usable = clip.usable_seconds
                if usable is None:
                    usable = (clip.duration_seconds or 0) - (clip.idle_seconds or 0)
                accepted_seconds += max(usable, 0)
                if clip.annotations and clip.annotation_level in ("L2", "L3"):
                    labeled_seconds += max(usable, 0)

        self.grades = grades
        self.annotation_levels = levels
        self.accepted_clips = accepted
        self.hours = Hours(
            delivered_hours=self.total_hours,
            accepted_hours=round(accepted_seconds / 3600, 3),
            accepted_labeled_hours=round(labeled_seconds / 3600, 3),
            idle_hours=round(idle_seconds / 3600, 3),
            media_yield=(
                round((accepted_seconds / 3600) / self.total_hours, 3)
                if self.total_hours
                else 0.0
            ),
        )
        return self
