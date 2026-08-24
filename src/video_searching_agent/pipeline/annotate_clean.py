"""Step four: annotate the clips in the clean collection, so the output is usable.

Refine cuts the accepted spans and uploads them to `egoexo-clean-clips`, and
`record_refined` lands a row for each one with its provenance and its pixel
measurements and *no tree* — deliberately, because "cut but not yet annotated"
is a real state the Library should be able to show. The tree was meant to arrive
afterwards, keyed on the same `video_id`.

Nothing ever brought it. That is what this module is: the pass that walks the
clean collection and gives each clip a tree of its own, in the clip's own time
base rather than the source video's.

**Why re-annotate at all**, when the source video was already annotated to get
the anchors. Because those annotations describe spans of somebody else's video —
`vid_source@41.5-63.5` — and the deliverable is `vid_clean`, a 22-second file
whose first frame is second zero. A tree in the wrong time base is not a
correction away from being right; it is measuring a different object. And the
grade the clip carries was earned by the *source*: a clip cut from an A-graded
video can still be a title card (three of the first ten were).

**It reconciles first.** The Datalake is authoritative about whether a clip
exists; this store is authoritative about nothing. Three rows in the real store
pointed at videos deleted along with a duplicate collection — search results
that 404 when clicked. So a successful listing prunes them, and a *failed*
listing prunes nothing: "the lookup broke" and "the collection is empty" are
indistinguishable from the return value, and acting on the second when it was
the first is how six duplicate collections got made in ten minutes.

**The gate enforces the request, not a preference.** A set built out of
egocentric footage must be egocentric; a set built out of exocentric footage is
*meant* to be a fixed camera, and refusing a tripod shot there would be refusing
the thing that was asked for. So `--viewpoint` says which, and the clip's own
frames have to agree with it.

**Off unless asked for**, like every step that spends money: the CLI needs
`--yes`, and `--limit` caps how many clips one pass will pay to annotate.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# The clean collection: cut, cleaned, accepted footage and nothing else.
CLEAN_COLLECTION_ID = "col_pelhcnsu2avutdnyamgnshohxu"

# The endpoint caps a listing at 100 and 400s above it. Paging is not optional.
PAGE = 100


@dataclass
class ClipResult:
    """What one clip's annotation pass did, including when it did nothing."""

    video_id: str
    nodes: int = 0
    annotation_level: str = ""
    accepted: bool | None = None
    grade: str = ""
    hands_named: int = 0
    objects_named: int = 0
    viewpoint: str = ""
    viewpoint_why: str = ""
    skipped: str = ""
    error: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "nodes": self.nodes,
            "annotation_level": self.annotation_level,
            "accepted": self.accepted,
            "grade": self.grade,
            "hands_named": self.hands_named,
            "objects_named": self.objects_named,
            "viewpoint": self.viewpoint,
            "viewpoint_why": self.viewpoint_why,
            "skipped": self.skipped,
            "error": self.error,
        }


@dataclass
class AnnotateReport:
    """The pass as a whole. `looked` says whether the listing actually worked."""

    collection_id: str = ""
    looked: bool = False
    live_clips: int = 0
    pruned: list[str] = field(default_factory=list)
    results: list[ClipResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def annotated(self) -> list[ClipResult]:
        return [r for r in self.results if r.nodes > 0]

    @property
    def with_hands(self) -> list[ClipResult]:
        return [r for r in self.annotated if r.hands_named > 0]

    @property
    def refused(self) -> list[ClipResult]:
        """Clips whose frames did not show the viewpoint the run asked for."""
        return [r for r in self.results if r.skipped.startswith(REFUSED)]

    def as_dict(self) -> dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "looked": self.looked,
            "live_clips": self.live_clips,
            "pruned": self.pruned,
            "annotated": len(self.annotated),
            "with_hands": len(self.with_hands),
            "refused_wrong_viewpoint": len(self.refused),
            "results": [r.as_dict() for r in self.results],
            "errors": self.errors,
        }


# The prefix every viewpoint refusal carries, so the report can count them
# without re-deriving the rule from the wording of a message.
REFUSED = "wrong viewpoint: "

# What a run can ask the delivered footage to be. `any` turns the gate off,
# which is not the same as asking for `unknown`: one is "do not check", the
# other is a verdict no set should be built out of.
VIEWPOINTS = ("egocentric", "exocentric", "any")


AGENT_NAME = "viewpoint"

# Two or three looks. A clip whose viewpoint is still unsettled after that is
# one the agent should say it cannot call, not one it should keep paying to
# stare at.
LOOK_BUDGET_USD = 0.02

VIEWPOINT_PROMPT = """You judge whether one short clip is the kind of footage a \
dataset was asked for. The set being built is {wanted} footage.

egocentric: the camera is worn or held by the person doing the task. Their own \
hands enter from the bottom of the frame; the view moves when they move.
exocentric: the camera is somewhere else — a tripod, a phone on a shelf, another \
person filming. The subject is in front of it, often facing it.

Two things this is not. It is not a judgement about quality: a shaky, dim, \
first-person clip is still first-person. And it is not settled by the subject \
matter: a person demonstrating a product to a worn camera is egocentric footage \
of a demonstration, and a beautifully shot manipulation on a tripod is not \
egocentric at all.

Look before you answer. One span can mislead — a clip can open on a title card, \
or on the wearer setting the camera down. If two spans disagree, judge what the \
clip is mostly.

Answer with ONLY:
{{"matches": true|false, "viewpoint": "egocentric"|"exocentric"|"unknown", \
"why": "<what in the frames decided it, one sentence>"}}

`matches` is whether this clip is {wanted} footage. If you looked and still \
cannot tell, answer with viewpoint "unknown" and matches false — an unjudged \
clip must not ship."""


async def see_viewpoint(
    video_id: str,
    *,
    wanted: str,
    duration_seconds: float | None,
    task: str = "",
    eyes: Any = None,
    llm: Any = None,
    max_steps: int = 4,
) -> dict[str, Any]:
    """Let an agent look at the delivered clip and say what viewpoint it is.

    `PRE-SIGHT` asks this of the *candidate*, from YouTube's storyboard stills,
    before anything is downloaded. This asks it of the thing being shipped, and
    the two are not the same object: the candidate is a whole video and the
    deliverable is a span cut out of it, so a source that is egocentric for four
    of its twelve minutes passes the first check and can still yield a clip that
    is entirely a presenter talking to camera.

    It is a loop rather than one look because one look is a guess about where to
    look. A clip that opens on a title card and then shows the work reads as
    neither from its first frames; an agent that can sample the middle and the
    end settles it, and one that cannot has to guess. The agent decides how many
    spans it needs, inside a step and money bound.

    Returns ``{"viewpoint", "matches", "why", "looked", "cost_usd", "error"}``.
    `looked` false means nothing was seen and the caller must not treat the
    verdict as a judgement — see the note on strictness in
    :func:`annotate_clean_collection`.
    """
    from video_searching_agent.agent.eyes import Eyes
    from video_searching_agent.agent.react_loop import Tool, ToolResult, run_loop
    from video_searching_agent.api.llm import get_llm_client

    blank: dict[str, Any] = {
        "viewpoint": "unknown",
        "matches": False,
        "why": "",
        "looked": False,
        "cost_usd": 0.0,
        "error": "",
    }

    eyes = eyes or Eyes()
    if not eyes.available:
        blank["error"] = "no ffmpeg, so the clip's frames cannot be read"
        return blank

    end = float(duration_seconds or 0.0)
    if end <= 0:
        blank["error"] = "the clip has no known duration to sample across"
        return blank

    seen_any = False

    async def look(arguments: dict[str, Any]) -> ToolResult:
        nonlocal seen_any
        # Clamped to the clip: an agent asking for 0-600s of a 25s clip is
        # asking about footage that does not exist, and ffmpeg would hand back
        # whatever it found rather than saying so.
        start = max(0.0, min(float(arguments.get("start", 0.0) or 0.0), end))
        stop = max(start, min(float(arguments.get("end", end) or end), end))
        if stop <= start:
            stop = end
        frames = await eyes.look(video_id, start, stop, int(arguments.get("frames", 4) or 4))
        if not frames.looked:
            return ToolResult(observation=frames.describe())
        seen_any = True
        return ToolResult(
            observation=frames.describe(), images=frames.images, cost_usd=frames.cost_usd
        )

    tools = [
        Tool(
            name="look",
            description=(
                "sample frames from a span of this clip and see them. The clip is "
                f"{end:.0f} seconds long and its first frame is second zero"
            ),
            arguments='{"start": <seconds>, "end": <seconds>, "frames": 2-6}',
            run=look,
        )
    ]

    opening = (
        f"Clip {video_id}, {end:.0f} seconds long."
        + (f" It was collected for: {task}." if task else "")
        + f" Decide whether it is {wanted} footage."
    )

    outcome = await run_loop(
        llm or get_llm_client(),
        VIEWPOINT_PROMPT.format(wanted=wanted),
        opening,
        tools,
        agent=AGENT_NAME,
        max_steps=max_steps,
        budget_usd=LOOK_BUDGET_USD,
        answer_keys=("matches",),
    )

    if outcome.answer is None:
        blank["cost_usd"] = outcome.cost_usd
        blank["error"] = outcome.stopped_because or "the agent did not reach a verdict"
        blank["looked"] = False
        return blank

    verdict = str(outcome.answer.get("viewpoint") or "unknown").strip().lower()
    return {
        "viewpoint": verdict if verdict in ("egocentric", "exocentric") else "unknown",
        "matches": bool(outcome.answer.get("matches")),
        "why": str(outcome.answer.get("why") or "").strip(),
        # A verdict reached without ever seeing a frame is a guess from the
        # prompt, and this gate exists precisely because captions and titles
        # were not enough.
        "looked": seen_any,
        "cost_usd": outcome.cost_usd,
        "error": "" if seen_any else "the agent answered without looking at any frames",
    }


async def live_video_ids(lake: Any, collection_id: str) -> list[str] | None:
    """Every video the collection actually holds, or None if the lookup broke.

    None is not an empty list, and the distinction is the whole reason this
    returns an optional: a caller that treats a failed listing as "nothing is
    there" will prune a store it could not read.
    """
    ids: list[str] = []
    cursor: str | None = None
    for _ in range(20):  # a hard stop, so a broken cursor cannot loop forever
        kwargs: dict[str, Any] = {"collection_id": collection_id, "limit": PAGE}
        if cursor:
            # `cursor`, which is what the client's signature calls it. `after`
            # would have been a TypeError swallowed by the except below and
            # reported as "could not list the collection".
            kwargs["cursor"] = cursor
        try:
            page = await lake.list_videos(**kwargs)
        except Exception as exc:
            logger.warning("could not list %s: %s", collection_id, exc)
            return None
        rows = page.get("videos") or page.get("data") or []
        if isinstance(rows, dict):
            rows = rows.get("list") or []
        found = [str(r.get("video_id") or r.get("videoNo") or "") for r in rows]
        ids.extend(v for v in found if v)
        cursor = page.get("next") or page.get("next_cursor") or None
        if not cursor or len(found) < PAGE:
            break
    return ids


def _count_detail(clip: Any) -> tuple[int, int]:
    """How many action nodes name a hand, and how many name an object."""
    hands = objects = 0
    for segment in clip.segments:
        if segment.hier_level != "action":
            continue
        if segment.left_hand or segment.right_hand:
            hands += 1
        if segment.objects:
            objects += 1
    return hands, objects


async def annotate_clean_collection(
    *,
    collection_id: str = CLEAN_COLLECTION_ID,
    limit: int = 5,
    only_missing: bool = True,
    write_back: bool = False,
    wanted_viewpoint: str = "egocentric",
    lake: Any = None,
    agent: Any = None,
    store: Any = None,
    eyes: Any = None,
    llm: Any = None,
) -> AnnotateReport:
    """Give the clips in the clean collection trees of their own.

    **The viewpoint gate.** Before a clip is paid to be annotated, its own
    frames are looked at, and a clip that is not confirmed first-person does not
    get a tree. This is stricter than the screen before the download, on
    purpose, and the asymmetry is the point:

    `SightVerdict.contradicts` only rules a *candidate* out on a confident,
    opposite reading — unknown never does — because a candidate that is kept by
    mistake is corrected later by the caption pass, and one dropped by mistake
    is gone. At delivery there is no later pass. Nothing downstream of here
    re-examines a clip, so "not established" and "wrong" have the same
    consequence and must be treated the same way: **confirmed egocentric, or it
    does not ship.** A clip whose frames could not be read is refused too, and
    the reason says which of the two it was.

    Refusals cost one look (about $0.002) and stop before the annotation spend.
    They are recorded on the clip as its viewpoint, so a second pass does not
    pay to look again at footage already judged, and `--no-require-egocentric`
    exists for the case where somebody is deliberately building an exocentric
    set.

    Args:
        collection_id: Which collection to walk.
        limit: The most clips this pass will pay to annotate.
        only_missing: Skip clips that already have a tree. Off re-annotates,
            which replaces the tree rather than adding a second copy.
        write_back: Also write the tree onto the Datalake video's metadata.
        wanted_viewpoint: The viewpoint this set is being built out of —
            `egocentric`, `exocentric`, or `any` to turn the gate off. A clip
            the frames do not confirm as the one asked for is refused. Asking
            for exocentric footage and getting a fixed camera is a hit, not a
            miss; the gate enforces the request, not a preference.
        lake: Datalake client. Created when omitted.
        agent: Curation agent. Created when omitted.
        store: Annotation store. Opened when omitted.
        eyes: Frame extractor for the viewpoint gate. Created when omitted.
        llm: Model client for the viewpoint gate. Resolved when omitted.

    Returns:
        An AnnotateReport. `looked` false means the collection could not be
        listed and nothing was pruned or annotated.
    """
    from video_searching_agent.agent.curation_agent import CurationAgent
    from video_searching_agent.api.memories_datalake_client import MemoriesDatalakeClient
    from video_searching_agent.store.annotations import open_store

    lake = lake or MemoriesDatalakeClient()
    agent = agent or CurationAgent(client=lake)
    store = store or open_store()

    wanted = (wanted_viewpoint or "egocentric").strip().lower()
    if wanted not in VIEWPOINTS:
        raise ValueError(f"wanted_viewpoint must be one of {VIEWPOINTS}, not {wanted_viewpoint!r}")

    report = AnnotateReport(collection_id=collection_id)

    ids = await live_video_ids(lake, collection_id)
    if ids is None:
        report.errors.append("could not list the collection, so nothing was pruned or annotated")
        return report
    report.looked = True
    report.live_clips = len(ids)

    report.pruned = store.prune_missing(ids)
    if report.pruned:
        logger.info("pruned %d row(s) whose video the Datalake no longer has", len(report.pruned))

    todo: list[str] = []
    for video_id in ids:
        clip = store.get(video_id)
        if clip is None:
            # In the collection but not in the store: refine records a row for
            # every clip it uploads, so this means the row was lost, not that
            # the clip is new. Annotating it would have nothing to hang on.
            report.results.append(ClipResult(video_id=video_id, skipped="no clip row in the store"))
            continue
        if only_missing and clip.segments:
            report.results.append(
                ClipResult(
                    video_id=video_id,
                    skipped=f"already has {len(clip.segments)} node(s)",
                    annotation_level=clip.annotation_level,
                    grade=clip.grade,
                )
            )
            continue
        todo.append(video_id)

    for video_id in todo[:limit]:
        result = ClipResult(video_id=video_id)
        clip_row = store.get(video_id)

        if wanted != "any":
            verdict = await see_viewpoint(
                video_id,
                wanted=wanted,
                duration_seconds=getattr(clip_row, "duration_seconds", None),
                task=getattr(clip_row, "query", "") or getattr(clip_row, "title", ""),
                eyes=eyes,
                llm=llm,
            )
            looked = bool(verdict.get("looked"))
            result.viewpoint = str(verdict.get("viewpoint") or "") if looked else ""
            result.viewpoint_why = str(verdict.get("why") or verdict.get("error") or "")
            if result.viewpoint:
                store.set_viewpoint(video_id, result.viewpoint)
            # The agent's own verdict on whether this is the footage asked for,
            # rather than a string comparison here. It has the frames and the
            # request; re-deciding from its label would throw away what it saw
            # and put the judgement back in a place that cannot see anything.
            if not looked or not verdict.get("matches"):
                result.skipped = REFUSED + (
                    f"asked for {wanted} — {result.viewpoint_why}"
                    if looked
                    else f"asked for {wanted}, and nothing was seen — {verdict.get('error')}"
                )
                report.results.append(result)
                continue

        try:
            curation = await agent.curate(
                video_ids=[video_id],
                query=(store.get(video_id).query if store.get(video_id) else ""),
                annotate=True,
                write_back=write_back,
                limit=1,
            )
        except Exception as exc:
            result.error = f"curate failed: {str(exc)[:200]}"
            report.results.append(result)
            continue

        report.errors.extend(curation.errors)
        curated = curation.clips[0] if curation.clips else None
        if curated is None:
            result.error = "curation returned no clip"
            report.results.append(result)
            continue

        result.accepted = curated.accepted
        result.grade = curated.grade or ""
        result.annotation_level = curated.annotation_level or ""
        run = curated.annotation
        nodes = list(getattr(run, "annotations", None) or [])
        if not nodes:
            result.skipped = curated.rejection_reason or "the annotation run produced no nodes"
            report.results.append(result)
            continue

        result.nodes = store.put_tree(
            video_id,
            nodes,
            annotation_level=result.annotation_level,
            grade=result.grade,
            accepted=curated.accepted,
        )
        stored = store.get(video_id)
        if stored is not None:
            result.hands_named, result.objects_named = _count_detail(stored)
        report.results.append(result)

    return report


def _print(report: AnnotateReport) -> None:
    print(f"collection {report.collection_id}: {report.live_clips} live clip(s)")
    if report.pruned:
        print(f"pruned {len(report.pruned)} dead row(s): {', '.join(report.pruned)}")
    for r in report.results:
        if r.nodes:
            print(
                f"  {r.video_id}  {r.nodes} node(s)  {r.annotation_level or '-'}  "
                f"hands {r.hands_named}  objects {r.objects_named}"
            )
        else:
            print(f"  {r.video_id}  — {r.error or r.skipped or 'nothing written'}")
    print(
        f"annotated {len(report.annotated)} clip(s), {len(report.with_hands)} of them naming a hand"
    )
    if report.refused:
        print(
            f"refused {len(report.refused)} clip(s) for the wrong viewpoint, "
            "before paying to annotate them"
        )
    for err in report.errors[:10]:
        print(f"  ! {err}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--collection", default=CLEAN_COLLECTION_ID)
    parser.add_argument("--limit", type=int, default=3, help="clips to annotate this pass")
    parser.add_argument(
        "--all",
        action="store_true",
        help="re-annotate clips that already have a tree (replaces it)",
    )
    parser.add_argument("--write-back", action="store_true", help="also write onto the Datalake")
    parser.add_argument(
        "--viewpoint",
        default="egocentric",
        choices=list(VIEWPOINTS),
        help="the viewpoint this set is built out of; a clip the frames do not "
        "confirm as this is refused. `any` turns the gate off (default: egocentric)",
    )
    parser.add_argument("--yes", action="store_true", help="required: this pass spends money")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.yes:
        print("this pass calls paid endpoints; re-run with --yes")
        return 2

    report = asyncio.run(
        annotate_clean_collection(
            collection_id=args.collection,
            limit=args.limit,
            only_missing=not args.all,
            write_back=args.write_back,
            wanted_viewpoint=args.viewpoint,
        )
    )
    _print(report)
    return 0 if report.looked else 1


if __name__ == "__main__":
    raise SystemExit(main())
