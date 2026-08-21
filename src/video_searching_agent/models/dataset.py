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
    notes: str | None = None


class DatasetManifest(BaseModel):
    """Everything a collection run gathered, with its totals."""

    query: str
    requested_viewpoint: Viewpoint | None = None
    target_hours: float | None = None

    total_clips: int = 0
    total_hours: float = 0.0
    clips_with_known_duration: int = 0

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
    def target_met(self) -> bool:
        """True when a requested hour target has been reached."""
        if not self.target_hours:
            return True
        return self.total_hours >= self.target_hours

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
        return self
