"""Step five: put the dataset on disk, where somebody can actually look at it.

The four steps before this one leave the deliverable spread across two systems
that neither of them owns end to end. The footage is in the Datalake, reachable
only through a signed URL that expires in a day. The tree is in a local SQLite
store. The provenance — which source video a clip was cut from, and between
which two seconds — is in a third place again, on the clip's Datalake record.
Every one of those is a live service call, and none of them is a dataset.

A dataset is a directory. Someone hands it to a colleague, mounts it in a
training job, or opens it in a file browser and watches a clip, and none of
that should require an API key or a running server. So this module writes one:

```
<out>/
  manifest.json          every clip, one array, with the run's totals
  manifest.jsonl         the same rows, one per line, for an ingest pipeline
  clips/<video_id>.mp4   the footage, named by the id that identifies it
  thumbnails/<video_id>.jpg     one still, so the directory is browsable
  annotations/<video_id>.json   the tree, the provenance, the grade
```

**The filename is the join key.** `clips/vid_x.mp4` and
`annotations/vid_x.json` are the same clip, and the id in the name is the same
id the Datalake and the store know it by. No index file has to be consulted to
pair them up, and a clip whose media failed to download still gets its JSON —
with `clip_file: null`, which says so, rather than being dropped from the
manifest and silently reducing the count.

**Signed URLs are fetched, not recorded.** A clip's `source_url` from the
Datalake is valid for about a day. Writing it into the manifest would produce a
file that looks complete and is broken by tomorrow, which is worse than one that
is obviously missing. So the URL is used here and thrown away; what lands on
disk is the bytes.

**Re-running is safe and cheap.** The export reads state that other steps
already paid to produce; it calls no model and indexes nothing. Media already
present is skipped unless `--refresh-media`, because the expensive part of a
re-export is downloading footage that has not changed.

**The one thing it does decide is viewpoint.** The deliverable is first-person
footage, so a clip whose own frames were not confirmed egocentric is held back —
and counted in the manifest by *what the frames said*, split between `exocentric`
(looked at, and wrong) and `unchecked` (step four has not looked yet). Those are
different problems with different fixes and a single "12 excluded" would hide
both. `--include-non-egocentric` ships everything, for the case where somebody
is deliberately assembling an exocentric set.

**Nothing else is filtered.** A clip with no tree is exported with no tree, and
the manifest counts it in `clips_without_tree` rather than hiding it. If that
number is high the answer is to run step four, not to filter here: an exporter
that quietly drops the unannotated is how a corpus comes to look better on disk
than it was in the pipeline.

**Not to be confused with `curation/export.py`.** That module exports *anchors*
— it asks the Datalake to cut a span out of a whole source video on demand and
hands back a signed URL, at $0.005 a clip, and the corpus stays a set of movable
time anchors (`G2-TREE-5`). This module exports the clean collection, whose
clips `refine` has already cut into files of their own; there is nothing left to
cut and nothing further to bill. One is a view over anchors, the other is the
directory those cut clips live in.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Written into the manifest so a consumer can tell two exports apart when the
# shape changes. Bump it when a field is renamed or removed, not when one is
# added — adding is backwards compatible and renaming is not.
MANIFEST_VERSION = 1

# Matches the served thumbnail, so the directory and the UI show the same frame.
THUMBNAIL_WIDTH = 320
THUMBNAIL_AT = 0.33


@dataclass
class ExportReport:
    """What one export pass wrote."""

    out_dir: str = ""
    clips: int = 0
    media_written: int = 0
    media_skipped: int = 0
    media_failed: int = 0
    with_tree: int = 0
    without_tree: int = 0
    total_seconds: float = 0.0
    # Held back by the egocentric requirement, counted by what the frames said.
    # Never a bare total: "12 excluded" invites the reader to assume they were
    # all junk, and `unverified` is a different problem from `exocentric`.
    withheld: dict[str, int] = field(default_factory=dict)
    thumbnails: int = 0
    # Files an earlier export wrote for a clip that has since been withheld.
    removed_stale: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def withheld_total(self) -> int:
        return sum(self.withheld.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "out_dir": self.out_dir,
            "clips": self.clips,
            "media_written": self.media_written,
            "media_skipped": self.media_skipped,
            "media_failed": self.media_failed,
            "clips_with_tree": self.with_tree,
            "clips_without_tree": self.without_tree,
            "total_seconds": round(self.total_seconds, 1),
            "thumbnails": self.thumbnails,
            "withheld_not_egocentric": self.withheld_total,
            "withheld_by_viewpoint": dict(sorted(self.withheld.items())),
            "removed_stale_files": self.removed_stale,
            "errors": self.errors,
        }


async def _signed_url(lake: Any, video_id: str) -> str:
    """The clip's own footage, as a link that works for about a day.

    `list_videos` deliberately returns null here — the URL has to be signed per
    video — so this asks for the one record. Getting that wrong is how an
    export concludes there is no footage when every byte of it is present.
    """
    record = await lake.get_video(video_id)
    video = record.get("video") if isinstance(record.get("video"), dict) else record
    return str(video.get("source_url") or "")


async def _download(url: str, dest: Path) -> int:
    """Stream one clip to disk. Returns the bytes written."""
    import httpx

    tmp = dest.with_suffix(dest.suffix + ".part")
    written = 0
    async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with tmp.open("wb") as handle:
                async for chunk in response.aiter_bytes(1 << 16):
                    handle.write(chunk)
                    written += len(chunk)
    # Rename only once the whole body arrived, so an interrupted export leaves a
    # `.part` rather than a truncated mp4 that the next run believes is done.
    tmp.replace(dest)
    return written


def _still_from(video: Path, dest: Path, duration: float | None) -> bool:
    """Cut one frame out of a local file. False when this host has no ffmpeg.

    A third of the way in rather than the first frame: a cut often opens on a
    wipe or on a hand still entering, and the middle is where the manipulation
    is. Failure is not an error — a directory without stills is still a
    dataset — so this reports rather than raises.
    """
    import subprocess

    from video_searching_agent.agent.eyes import Eyes

    ffmpeg = Eyes().ffmpeg
    if not ffmpeg:
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)
    at = max(0.0, (duration or 0.0) * THUMBNAIL_AT)
    try:
        done = subprocess.run(
            [ffmpeg, "-nostdin", "-y", "-ss", f"{at:.3f}", "-i", str(video),
             "-frames:v", "1", "-q:v", "4", "-vf", f"scale={THUMBNAIL_WIDTH}:-2", str(dest)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # noqa: BLE001 - one still
        logger.info("could not still %s: %s", video.name, exc)
        return False
    return done.returncode == 0 and dest.exists() and dest.stat().st_size > 0


async def export_dataset(
    out_dir: str | Path,
    *,
    collection_id: str = "",
    limit: int = 500,
    media: bool = True,
    refresh_media: bool = False,
    egocentric_only: bool = True,
    store: Any = None,
    lake: Any = None,
) -> ExportReport:
    """Write the clean clips, their trees and a manifest into `out_dir`.

    Args:
        out_dir: Directory to write. Created if missing; existing files with the
            same names are replaced.
        collection_id: Restrict to one collection, or empty for every clip the
            store knows.
        limit: Most clips to export in one pass.
        media: Download the footage. `False` writes the JSON only, which is fast
            and needs no network beyond the store.
        refresh_media: Re-download clips whose file is already on disk.
        egocentric_only: Ship only clips whose own frames were confirmed
            first-person. On by default. What is held back is counted in the
            manifest by the viewpoint that held it back, never as a bare total.
        store: An annotation store, or the default one.
        lake: A Datalake client, or one built from settings.
    """
    from video_searching_agent.store.annotations import open_store

    out = Path(out_dir)
    (out / "clips").mkdir(parents=True, exist_ok=True)
    (out / "annotations").mkdir(parents=True, exist_ok=True)
    (out / "thumbnails").mkdir(parents=True, exist_ok=True)

    target = store or open_store()
    rows, _total = target.search(limit=limit)
    if collection_id:
        rows = [clip for clip in rows if clip.collection_id == collection_id]

    report = ExportReport(out_dir=str(out))

    if egocentric_only:
        # A blank viewpoint is a clip step four has not looked at yet, which is
        # not the same as one it looked at and could not call — the manifest
        # keeps them apart so "run step four" and "this footage is wrong" do
        # not arrive as the same number.
        kept = []
        withheld_ids: list[str] = []
        for clip in rows:
            seen = (clip.viewpoint or "").strip().lower()
            if seen == "egocentric":
                kept.append(clip)
            else:
                key = seen or "unchecked"
                report.withheld[key] = report.withheld.get(key, 0) + 1
                withheld_ids.append(clip.video_id)
        rows = kept

        # A clip can be withheld *after* an earlier export already wrote it —
        # step four re-checked it and the frames said presenter, not wearer. A
        # manifest saying 10 beside a directory holding 15 files hands the
        # footage over anyway to anyone who reads the directory rather than the
        # manifest, which is most consumers. So the files go with the verdict.
        # Only ids this pass actually considered and refused are touched;
        # nothing else in the directory is the exporter's to delete.
        for video_id in withheld_ids:
            for path in (
                out / "clips" / f"{video_id}.mp4",
                out / "annotations" / f"{video_id}.json",
                out / "thumbnails" / f"{video_id}.jpg",
            ):
                if path.exists():
                    path.unlink()
                    report.removed_stale += 1

    if media and lake is None:
        from video_searching_agent.api.memories_datalake_client import (
            MemoriesDatalakeClient,
        )
        from video_searching_agent.config.settings import get_settings

        lake = MemoriesDatalakeClient(api_key=get_settings().memories_api_key)

    items: list[dict[str, Any]] = []

    for clip in rows:
        record = clip.as_dict(with_segments=True)
        video_id = record["video_id"]
        destination = out / "clips" / f"{video_id}.mp4"

        if media:
            if destination.exists() and not refresh_media:
                report.media_skipped += 1
            else:
                try:
                    url = await _signed_url(lake, video_id)
                    if not url:
                        raise ValueError("the Datalake returned no source_url")
                    await _download(url, destination)
                    report.media_written += 1
                except Exception as exc:  # noqa: BLE001 - one clip, not the run
                    report.media_failed += 1
                    report.errors.append(f"{video_id}: {str(exc)[:160]}")
                    logger.warning("could not fetch %s: %s", video_id, exc)

        # A still, cut from the file that is already on disk — no network and no
        # seek against a signed URL. It makes the directory browsable in a file
        # manager without opening fifteen videos to find one.
        still = out / "thumbnails" / f"{video_id}.jpg"
        if destination.exists() and (refresh_media or not still.exists()):
            if _still_from(destination, still, record.get("duration_seconds")):
                report.thumbnails += 1

        # The paths are relative on purpose: the directory has to survive being
        # moved or mounted somewhere else, which an absolute path does not.
        record["clip_file"] = f"clips/{video_id}.mp4" if destination.exists() else None
        record["thumbnail_file"] = f"thumbnails/{video_id}.jpg" if still.exists() else None
        record["annotation_file"] = f"annotations/{video_id}.json"
        (out / "annotations" / f"{video_id}.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        if record["segment_count"]:
            report.with_tree += 1
        else:
            report.without_tree += 1
        report.total_seconds += record.get("duration_seconds") or 0.0
        report.clips += 1

        items.append(
            {
                key: record.get(key)
                for key in (
                    "video_id",
                    "clip_file",
                    "annotation_file",
                    "title",
                    "duration_seconds",
                    "source_video_id",
                    "source_start",
                    "source_end",
                    "viewpoint",
                    "grade",
                    "annotation_level",
                    "accepted",
                    "segment_count",
                    "action_count",
                )
            }
        )

    # Longest first: the clips worth looking at are at the top of the file, and
    # a six-second fragment is not what anyone opens a manifest to find.
    items.sort(key=lambda row: -(row.get("duration_seconds") or 0))

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "collection_id": collection_id,
        **report.as_dict(),
        "items": items,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with (out / "manifest.jsonl").open("w", encoding="utf-8") as handle:
        for row in items:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    return report


def _print(report: ExportReport) -> None:
    print(
        f"{report.clips} clip(s) -> {report.out_dir}  "
        f"({report.with_tree} with a tree, {report.without_tree} without, "
        f"{report.total_seconds / 60:.1f} min)"
    )
    print(
        f"  media: {report.media_written} written, "
        f"{report.media_skipped} already there, {report.media_failed} failed"
    )
    if report.thumbnails:
        print(f"  stills: {report.thumbnails} rendered")
    if report.withheld:
        breakdown = ", ".join(f"{n} {label}" for label, n in sorted(report.withheld.items()))
        print(f"  held back {report.withheld_total} clip(s), not first-person: {breakdown}")
        if report.removed_stale:
            print(f"  removed {report.removed_stale} file(s) an earlier export had written")
    for err in report.errors[:10]:
        print(f"  ! {err}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="dataset", help="directory to write")
    parser.add_argument("--collection", default="", help="restrict to one collection")
    parser.add_argument("--limit", type=int, default=500, help="most clips to export")
    parser.add_argument(
        "--no-media",
        action="store_true",
        help="write the JSON only, downloading no footage",
    )
    parser.add_argument(
        "--refresh-media",
        action="store_true",
        help="re-download clips whose file is already on disk",
    )
    parser.add_argument(
        "--include-non-egocentric",
        action="store_true",
        help="ship clips the frames did not confirm are first-person "
        "(off by default: the deliverable is egocentric)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    report = asyncio.run(
        export_dataset(
            args.out,
            collection_id=args.collection,
            limit=args.limit,
            media=not args.no_media,
            refresh_media=args.refresh_media,
            egocentric_only=not args.include_non_egocentric,
        )
    )
    _print(report)
    return 0 if report.clips else 1


if __name__ == "__main__":
    raise SystemExit(main())
