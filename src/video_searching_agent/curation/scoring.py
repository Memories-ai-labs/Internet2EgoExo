"""Ranking and filtering candidates by training-data usability.

Popularity is not a signal here. A clip earns its place by matching the
requested viewpoint, being long enough to be worth ingesting, and carrying a
licence that allows reuse. View counts are ignored on purpose: a 200-view
head-mounted assembly recording beats a 10M-view meme every time.
"""

from __future__ import annotations

from dataclasses import dataclass

from video_searching_agent.curation.viewpoint import Viewpoint, ViewpointVerdict

# Clips at or beyond this length score full marks for duration. Long,
# uninterrupted footage is what makes a usable training sample.
FULL_CREDIT_DURATION_SECONDS = 600

# Licence values that permit reuse without a case-by-case negotiation.
REUSABLE_LICENSES = frozenset({"creativecommon", "creative_commons", "cc-by", "cc0", "public"})


class LicenseFilter:
    """Accepted values for the licence requirement."""

    ANY = "any"
    REUSABLE = "reusable"


@dataclass
class CandidateScore:
    """Why a candidate was kept or dropped, and how it ranks."""

    total: float
    viewpoint_score: float
    duration_score: float
    license_score: float
    excluded_reason: str | None = None

    @property
    def usable(self) -> bool:
        return self.excluded_reason is None


def is_reusable_license(license_value: str | None) -> bool:
    """True when a licence string clearly permits reuse."""
    if not license_value:
        return False
    return license_value.strip().lower().replace(" ", "") in REUSABLE_LICENSES


def score_candidate(
    verdict: ViewpointVerdict,
    duration_seconds: int | None,
    license_value: str | None = None,
    *,
    wanted_viewpoint: Viewpoint | None = None,
    min_duration_seconds: int | None = None,
    license_filter: str = LicenseFilter.ANY,
) -> CandidateScore:
    """Score one candidate for inclusion in a training set.

    Args:
        verdict: Viewpoint classification for the candidate.
        duration_seconds: Clip length, when known.
        license_value: Platform licence string, when known.
        wanted_viewpoint: Requested viewpoint, or None for any.
        min_duration_seconds: Hard minimum length.
        license_filter: `any`, or `reusable` to require a reuse-permitting licence.

    Returns:
        A CandidateScore; `usable` is False when a hard requirement failed.
    """
    # --- hard requirements -------------------------------------------------
    if wanted_viewpoint and not verdict.matches(wanted_viewpoint):
        return CandidateScore(
            0.0, 0.0, 0.0, 0.0,
            excluded_reason=(
                f"viewpoint is {verdict.viewpoint.value}, "
                f"wanted {wanted_viewpoint.value}"
            ),
        )

    if min_duration_seconds and (duration_seconds or 0) < min_duration_seconds:
        known = "unknown" if duration_seconds is None else f"{duration_seconds}s"
        return CandidateScore(
            0.0, 0.0, 0.0, 0.0,
            excluded_reason=f"duration {known} below the {min_duration_seconds}s minimum",
        )

    if license_filter == LicenseFilter.REUSABLE and not is_reusable_license(license_value):
        return CandidateScore(
            0.0, 0.0, 0.0, 0.0,
            excluded_reason=f"licence {license_value or 'unknown'} is not known to permit reuse",
        )

    # --- ranking -----------------------------------------------------------
    if wanted_viewpoint is None:
        # No viewpoint asked for: any confident classification is a small plus,
        # because a labelled clip is more useful than an unlabelled one.
        viewpoint_score = 0.5 + 0.5 * verdict.confidence
    elif verdict.viewpoint == wanted_viewpoint:
        viewpoint_score = verdict.confidence
    else:
        # Unknown but not excluded — worth keeping, ranked below matches.
        viewpoint_score = 0.2

    if duration_seconds is None:
        duration_score = 0.3  # unknown length is a mild unknown, not a fault
    else:
        duration_score = min(duration_seconds / FULL_CREDIT_DURATION_SECONDS, 1.0)

    license_score = 1.0 if is_reusable_license(license_value) else 0.4

    total = round(
        0.6 * viewpoint_score + 0.3 * duration_score + 0.1 * license_score,
        4,
    )
    return CandidateScore(
        total=total,
        viewpoint_score=round(viewpoint_score, 4),
        duration_score=round(duration_score, 4),
        license_score=license_score,
    )
