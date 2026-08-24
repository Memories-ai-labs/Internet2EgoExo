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
        """Clips the viewpoint gate turned away before anything was spent."""
        return [r for r in self.results if r.skipped.startswith(REFUSED)]

    def as_dict(self) -> dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "looked": self.looked,
            "live_clips": self.live_clips,
            "pruned": self.pruned,
            "annotated": len(self.annotated),
            "with_hands": len(self.with_hands),
            "refused_not_egocentric": len(self.refused),
            "results": [r.as_dict() for r in self.results],
            "errors": self.errors,
        }


# The prefix every viewpoint refusal carries, so the report can count them
# without re-deriving the rule from the wording of a message.
REFUSED = "not first-person: "


async def see_viewpoint(
    video_id: str,
    *,
    duration_seconds: float | None,
    task: str = "",
    eyes: Any = None,
    llm: Any = None,
) -> Any:
    """Look at the delivered clip's own frames and say what viewpoint they show.

    `PRE-SIGHT` already asks this question, of the *candidate*, from YouTube's
    storyboard stills, before anything is downloaded. This asks it again of the
    thing being shipped, and the two are not the same object: the candidate is a
    whole video and the deliverable is a span cut out of it, so a source that is
    egocentric for four of its twelve minutes passes the first check and can
    still yield a clip that is entirely a presenter talking to camera.

    Returns a `SightVerdict`. A look that could not run comes back with
    `looked` false and an error, which the gate treats as *not established* —
    see the note on strictness in :func:`annotate_clean_collection`.
    """
    from video_searching_agent.agent.eyes import Eyes
    from video_searching_agent.api.llm import get_llm_client
    from video_searching_agent.curation.frame_viewpoint import SightVerdict, look_at_frames

    eyes = eyes or Eyes()
    if not eyes.available:
        return SightVerdict(error="no ffmpeg, so the clip's frames cannot be read")

    end = float(duration_seconds or 0.0)
    if end <= 0:
        return SightVerdict(error="the clip has no known duration to sample across")

    frames = await eyes.look(video_id, 0.0, end)
    if not frames.looked:
        return SightVerdict(error=frames.error or "no frames came back")

    return await look_at_frames(llm or get_llm_client(), frames.images, task=task or None)


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
    require_egocentric: bool = True,
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
        require_egocentric: Refuse to annotate a clip the frames do not confirm
            is first-person. On by default; the deliverable is egocentric.
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

        if require_egocentric:
            verdict = await see_viewpoint(
                video_id,
                duration_seconds=getattr(clip_row, "duration_seconds", None),
                task=getattr(clip_row, "query", "") or getattr(clip_row, "title", ""),
                eyes=eyes,
                llm=llm,
            )
            seen = str(getattr(verdict.viewpoint, "value", verdict.viewpoint) or "")
            result.viewpoint = seen if verdict.looked else ""
            result.viewpoint_why = verdict.why or verdict.error or ""
            if result.viewpoint:
                store.set_viewpoint(video_id, result.viewpoint)
            if seen != "egocentric" or not verdict.looked:
                result.skipped = REFUSED + (
                    f"the frames show {seen} footage — {verdict.why}"
                    if verdict.looked
                    else f"the viewpoint could not be established — {verdict.error}"
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
            f"refused {len(report.refused)} clip(s) that are not first-person, "
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
        "--no-require-egocentric",
        action="store_true",
        help="annotate clips the frames do not confirm are first-person "
        "(off by default: the deliverable is egocentric)",
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
            require_egocentric=not args.no_require_egocentric,
        )
    )
    _print(report)
    return 0 if report.looked else 1


if __name__ == "__main__":
    raise SystemExit(main())
