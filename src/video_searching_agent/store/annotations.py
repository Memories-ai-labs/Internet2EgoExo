"""Where the annotation trees live, so the clean clips can be searched.

The Datalake stores video. It is very good at that and it is not an annotation
database: a tree is currently stuffed into a clip's `metadata.custom.segments`,
which means it round-trips fine and cannot be *queried*. There is no way to ask
"every clip with a fold-shirt action", or "everything egocentric with both hands
named", or "clips from this source video", because those are questions about the
annotation and the annotation is an opaque blob hanging off a video record.

So the tree goes here, keyed on the Datalake `video_id` of the clip in the clean
collection. That id is the join, in both directions:

    Datalake                     this store
    col_…/vid_…  ── video_id ──▶  clips.video_id
      the pixels                    the tree, the grade, the provenance

Nothing here duplicates the footage and nothing here is authoritative about it.
If the two disagree about a clip's existence the Datalake wins, and
:func:`prune_missing` is how that gets reconciled.

**Two tables, because a tree is not a row.** `clips` is one row per clean clip.
`segments` is one row per node, carrying `parent_segment_id` so the hierarchy is
reconstructable and, more importantly, *queryable* — a search for an action
label can return the task it sits under, which is the thing a person browsing
actually wants.

**On the backend.** SQLite by default, which needs a writable file and therefore
works locally and on any host with a disk. It does **not** persist on a
serverless filesystem: Vercel gives a read-only tree and a `/tmp` that vanishes
between invocations. `ANNOTATION_STORE_PATH` points it somewhere else, and
:func:`store_path` falls back to memory when nothing on the host persists —
which is the honest answer, because a store that serves one request and forgets
is visibly different from one that claims to have kept something.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clips (
    video_id          TEXT PRIMARY KEY,
    collection_id     TEXT,
    source_video_id   TEXT,
    source_start      REAL,
    source_end        REAL,
    source_url        TEXT,
    title             TEXT,
    duration_seconds  REAL,
    viewpoint         TEXT,
    grade             TEXT,
    annotation_level  TEXT,
    accepted          INTEGER DEFAULT 0,
    motion_mean       REAL,
    sharpness_mean    REAL,
    query             TEXT,
    created_at        TEXT,
    payload           TEXT
);
CREATE INDEX IF NOT EXISTS clips_viewpoint ON clips(viewpoint);
CREATE INDEX IF NOT EXISTS clips_grade ON clips(grade);
CREATE INDEX IF NOT EXISTS clips_source ON clips(source_video_id);

CREATE TABLE IF NOT EXISTS segments (
    rowid_alias       INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id          TEXT NOT NULL,
    segment_id        TEXT NOT NULL,
    parent_segment_id TEXT,
    hier_level        TEXT,
    span_start        REAL,
    span_end          REAL,
    label             TEXT,
    narration         TEXT,
    hands_visible     INTEGER,
    left_hand         TEXT,
    right_hand        TEXT,
    evidence          TEXT,
    UNIQUE(video_id, segment_id)
);
CREATE INDEX IF NOT EXISTS segments_video ON segments(video_id);
CREATE INDEX IF NOT EXISTS segments_level ON segments(hier_level);
CREATE INDEX IF NOT EXISTS segments_label ON segments(label);

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


@dataclass
class Segment:
    """One node of an annotation tree."""

    segment_id: str
    hier_level: str = ""
    span_start: float = 0.0
    span_end: float = 0.0
    parent_segment_id: str | None = None
    label: str | None = None
    narration: str | None = None
    hands_visible: bool | None = None
    left_hand: str | None = None
    right_hand: str | None = None
    evidence: list[str] = field(default_factory=list)

    @property
    def seconds(self) -> float:
        return max(0.0, self.span_end - self.span_start)

    def as_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "parent_segment_id": self.parent_segment_id,
            "hier_level": self.hier_level,
            "span_start": self.span_start,
            "span_end": self.span_end,
            "seconds": round(self.seconds, 2),
            "label": self.label,
            "narration": self.narration,
            "hands_visible": self.hands_visible,
            "left_hand": self.left_hand,
            "right_hand": self.right_hand,
            "evidence": self.evidence,
        }


@dataclass
class Clip:
    """One clean clip, as this store knows it."""

    video_id: str
    collection_id: str = ""
    source_video_id: str = ""
    source_start: float | None = None
    source_end: float | None = None
    source_url: str = ""
    title: str = ""
    duration_seconds: float | None = None
    viewpoint: str = ""
    grade: str = ""
    annotation_level: str = ""
    accepted: bool = False
    motion_mean: float | None = None
    sharpness_mean: float | None = None
    query: str = ""
    created_at: str = ""
    segments: list[Segment] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def action_segments(self) -> list[Segment]:
        return [s for s in self.segments if s.hier_level == "action"]

    def as_dict(self, *, with_segments: bool = True) -> dict[str, Any]:
        row: dict[str, Any] = {
            "video_id": self.video_id,
            "collection_id": self.collection_id,
            "source_video_id": self.source_video_id,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "source_url": self.source_url,
            "title": self.title,
            "duration_seconds": self.duration_seconds,
            "viewpoint": self.viewpoint,
            "grade": self.grade,
            "annotation_level": self.annotation_level,
            "accepted": self.accepted,
            "motion_mean": self.motion_mean,
            "sharpness_mean": self.sharpness_mean,
            "query": self.query,
            "created_at": self.created_at,
            "segment_count": len(self.segments),
            "action_count": len(self.action_segments),
        }
        if with_segments:
            row["segments"] = [s.as_dict() for s in self.segments]
        return row


class AnnotationStore:
    """The clean clips and their trees, joined on the Datalake video id.

    Writes are idempotent per `video_id`: putting the same clip twice replaces
    its tree rather than doubling it, because a re-annotation is a correction and
    two copies of a tree would double every hour count derived from it.
    """

    def __init__(self, path: str = ":memory:") -> None:
        self.path = path
        # check_same_thread=False plus one lock: a FastAPI worker touches this
        # from whichever thread the event loop hands it, and SQLite objects the
        # moment a connection crosses threads.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._lock = threading.Lock()
        with self._tx() as cur:
            cur.executescript(_SCHEMA)
            cur.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def close(self) -> None:
        self._conn.close()

    # ---- writing --------------------------------------------------------

    def put(self, clip: Clip) -> None:
        """Insert or replace one clip and its whole tree."""
        with self._tx() as cur:
            cur.execute(
                """INSERT INTO clips (video_id, collection_id, source_video_id,
                       source_start, source_end, source_url, title,
                       duration_seconds, viewpoint, grade, annotation_level,
                       accepted, motion_mean, sharpness_mean, query, created_at,
                       payload)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(video_id) DO UPDATE SET
                       collection_id=excluded.collection_id,
                       source_video_id=excluded.source_video_id,
                       source_start=excluded.source_start,
                       source_end=excluded.source_end,
                       source_url=excluded.source_url,
                       title=excluded.title,
                       duration_seconds=excluded.duration_seconds,
                       viewpoint=excluded.viewpoint,
                       grade=excluded.grade,
                       annotation_level=excluded.annotation_level,
                       accepted=excluded.accepted,
                       motion_mean=excluded.motion_mean,
                       sharpness_mean=excluded.sharpness_mean,
                       query=excluded.query,
                       created_at=excluded.created_at,
                       payload=excluded.payload""",
                (
                    clip.video_id,
                    clip.collection_id,
                    clip.source_video_id,
                    clip.source_start,
                    clip.source_end,
                    clip.source_url,
                    clip.title,
                    clip.duration_seconds,
                    clip.viewpoint,
                    clip.grade,
                    clip.annotation_level,
                    1 if clip.accepted else 0,
                    clip.motion_mean,
                    clip.sharpness_mean,
                    clip.query,
                    clip.created_at,
                    json.dumps(clip.payload, ensure_ascii=False),
                ),
            )
            # Replace, never append: a re-annotation is a correction, and two
            # copies of a tree would double every hour derived from it.
            cur.execute("DELETE FROM segments WHERE video_id = ?", (clip.video_id,))
            cur.executemany(
                """INSERT INTO segments (video_id, segment_id, parent_segment_id,
                       hier_level, span_start, span_end, label, narration,
                       hands_visible, left_hand, right_hand, evidence)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        clip.video_id,
                        s.segment_id,
                        s.parent_segment_id,
                        s.hier_level,
                        s.span_start,
                        s.span_end,
                        s.label,
                        s.narration,
                        None if s.hands_visible is None else int(s.hands_visible),
                        s.left_hand,
                        s.right_hand,
                        json.dumps(s.evidence, ensure_ascii=False),
                    )
                    for s in clip.segments
                ],
            )

    def put_many(self, clips: Iterable[Clip]) -> int:
        count = 0
        for clip in clips:
            self.put(clip)
            count += 1
        return count

    def delete(self, video_id: str) -> None:
        with self._tx() as cur:
            cur.execute("DELETE FROM segments WHERE video_id = ?", (video_id,))
            cur.execute("DELETE FROM clips WHERE video_id = ?", (video_id,))

    def prune_missing(self, live_video_ids: Iterable[str]) -> list[str]:
        """Drop clips the Datalake no longer has.

        The Datalake is authoritative about whether a clip exists; this store is
        authoritative about nothing. A row for a deleted video is a search result
        that 404s when clicked.
        """
        live = set(live_video_ids)
        with self._tx() as cur:
            cur.execute("SELECT video_id FROM clips")
            stale = [r["video_id"] for r in cur.fetchall() if r["video_id"] not in live]
        for video_id in stale:
            self.delete(video_id)
        return stale

    # ---- reading --------------------------------------------------------

    def get(self, video_id: str) -> Clip | None:
        with self._tx() as cur:
            cur.execute("SELECT * FROM clips WHERE video_id = ?", (video_id,))
            row = cur.fetchone()
            if row is None:
                return None
            cur.execute(
                "SELECT * FROM segments WHERE video_id = ? ORDER BY span_start, segment_id",
                (video_id,),
            )
            segments = [_segment_from_row(r) for r in cur.fetchall()]
        return _clip_from_row(row, segments)

    def search(
        self,
        *,
        text: str = "",
        viewpoint: str = "",
        grade: str = "",
        hier_level: str = "",
        hands_only: bool = False,
        accepted_only: bool = False,
        source_video_id: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Clip], int]:
        """Find clips. Returns the page and the total that matched.

        `text` matches a clip's title or any of its segments' labels and
        narrations, so searching "fold" finds a clip whose *action* is folding
        even when its title never says so — which is the whole reason the tree
        is in a database instead of a blob.
        """
        where: list[str] = []
        params: list[Any] = []
        if viewpoint:
            where.append("c.viewpoint = ?")
            params.append(viewpoint)
        if grade:
            where.append("c.grade = ?")
            params.append(grade)
        if accepted_only:
            where.append("c.accepted = 1")
        if source_video_id:
            where.append("c.source_video_id = ?")
            params.append(source_video_id)
        if text:
            like = f"%{text.lower()}%"
            clause = (
                "(LOWER(COALESCE(c.title,'')) LIKE ? OR c.video_id IN ("
                "SELECT video_id FROM segments WHERE LOWER(COALESCE(label,'')) LIKE ? "
                "OR LOWER(COALESCE(narration,'')) LIKE ?))"
            )
            where.append(clause)
            params.extend([like, like, like])
        if hier_level:
            where.append("c.video_id IN (SELECT video_id FROM segments WHERE hier_level = ?)")
            params.append(hier_level)
        if hands_only:
            where.append("c.video_id IN (SELECT video_id FROM segments WHERE hands_visible = 1)")

        sql_where = (" WHERE " + " AND ".join(where)) if where else ""
        with self._tx() as cur:
            cur.execute(f"SELECT COUNT(*) AS n FROM clips c{sql_where}", params)
            total = int(cur.fetchone()["n"])
            cur.execute(
                f"SELECT * FROM clips c{sql_where} "
                "ORDER BY COALESCE(c.created_at, '') DESC, c.video_id "
                "LIMIT ? OFFSET ?",
                [*params, max(1, limit), max(0, offset)],
            )
            rows = cur.fetchall()
            clips: list[Clip] = []
            for row in rows:
                cur.execute(
                    "SELECT * FROM segments WHERE video_id = ? ORDER BY span_start, segment_id",
                    (row["video_id"],),
                )
                clips.append(_clip_from_row(row, [_segment_from_row(r) for r in cur.fetchall()]))
        return clips, total

    def labels(self, *, hier_level: str = "action", limit: int = 60) -> list[dict[str, Any]]:
        """The label vocabulary actually in the store, commonest first.

        This is what a browse UI offers as filters. Inventing a facet list would
        offer labels nothing has.
        """
        with self._tx() as cur:
            sql = (
                "SELECT label, COUNT(*) AS n, COUNT(DISTINCT video_id) AS clips "
                "FROM segments WHERE label IS NOT NULL AND label != ''"
            )
            params: list[Any] = []
            if hier_level:
                sql += " AND hier_level = ?"
                params.append(hier_level)
            sql += " GROUP BY label ORDER BY n DESC LIMIT ?"
            params.append(max(1, limit))
            cur.execute(sql, params)
            return [
                {"label": r["label"], "segments": r["n"], "clips": r["clips"]}
                for r in cur.fetchall()
            ]

    def totals(self) -> dict[str, Any]:
        """What is in here, for a header line that is not a guess."""
        with self._tx() as cur:
            cur.execute(
                "SELECT COUNT(*) AS clips, "
                "COALESCE(SUM(duration_seconds), 0) AS seconds, "
                "SUM(accepted) AS accepted FROM clips"
            )
            row = cur.fetchone()
            cur.execute("SELECT COUNT(*) AS n FROM segments WHERE hier_level = 'action'")
            actions = int(cur.fetchone()["n"])
            cur.execute("SELECT viewpoint, COUNT(*) AS n FROM clips GROUP BY viewpoint")
            # Accumulate rather than assign: an empty viewpoint and a literal
            # "unknown" are different rows that display as the same word, and a
            # dict comprehension keeps only the last of them — which reported
            # three clips as one.
            by_viewpoint: dict[str, int] = {}
            for viewpoint_row in cur.fetchall():
                key = viewpoint_row["viewpoint"] or "unknown"
                by_viewpoint[key] = by_viewpoint.get(key, 0) + int(viewpoint_row["n"])
        seconds = float(row["seconds"] or 0.0)
        return {
            "clips": int(row["clips"] or 0),
            "accepted_clips": int(row["accepted"] or 0),
            "hours": round(seconds / 3600, 4),
            "action_segments": actions,
            "by_viewpoint": by_viewpoint,
        }


def _segment_from_row(row: sqlite3.Row) -> Segment:
    try:
        evidence = json.loads(row["evidence"] or "[]")
    except json.JSONDecodeError:
        evidence = []
    hands = row["hands_visible"]
    return Segment(
        segment_id=row["segment_id"],
        parent_segment_id=row["parent_segment_id"],
        hier_level=row["hier_level"] or "",
        span_start=float(row["span_start"] or 0.0),
        span_end=float(row["span_end"] or 0.0),
        label=row["label"],
        narration=row["narration"],
        hands_visible=None if hands is None else bool(hands),
        left_hand=row["left_hand"],
        right_hand=row["right_hand"],
        evidence=evidence if isinstance(evidence, list) else [],
    )


def _clip_from_row(row: sqlite3.Row, segments: list[Segment]) -> Clip:
    try:
        payload = json.loads(row["payload"] or "{}")
    except json.JSONDecodeError:
        payload = {}
    return Clip(
        video_id=row["video_id"],
        collection_id=row["collection_id"] or "",
        source_video_id=row["source_video_id"] or "",
        source_start=row["source_start"],
        source_end=row["source_end"],
        source_url=row["source_url"] or "",
        title=row["title"] or "",
        duration_seconds=row["duration_seconds"],
        viewpoint=row["viewpoint"] or "",
        grade=row["grade"] or "",
        annotation_level=row["annotation_level"] or "",
        accepted=bool(row["accepted"]),
        motion_mean=row["motion_mean"],
        sharpness_mean=row["sharpness_mean"],
        query=row["query"] or "",
        created_at=row["created_at"] or "",
        segments=segments,
        payload=payload if isinstance(payload, dict) else {},
    )


# ---- opening one ---------------------------------------------------------

_OPEN: dict[str, AnnotationStore] = {}
_OPEN_LOCK = threading.Lock()


def store_path() -> str:
    """Where the store lives, and whether it can live there at all.

    Returns ``":memory:"`` when nothing on this host persists, which is the
    honest answer for a serverless function: an in-memory store serves a single
    request correctly and forgets, and that is visibly different from a store
    that claims to have kept something.
    """
    import os
    import tempfile

    from video_searching_agent.config.settings import get_settings

    configured = getattr(get_settings(), "annotation_store_path", "") or ""
    for candidate in (configured, "data/annotations.sqlite3"):
        if not candidate:
            continue
        directory = os.path.dirname(os.path.abspath(candidate)) or "."
        try:
            os.makedirs(directory, exist_ok=True)
            probe = os.path.join(directory, ".store-probe")
            with open(probe, "wb") as handle:
                handle.write(b"x")
            os.unlink(probe)
            return candidate
        except OSError:
            continue
    # A tmp file at least survives the process, which is enough for one run of
    # the pipeline on a host whose project tree is read-only.
    try:
        fallback = os.path.join(tempfile.gettempdir(), "i2e-annotations.sqlite3")
        with open(fallback, "ab"):
            pass
        return fallback
    except OSError:
        logger.warning("no writable location for the annotation store; using memory")
        return ":memory:"


def open_store(path: str | None = None) -> AnnotationStore:
    """The process-wide store for a path, opened once."""
    resolved = path or store_path()
    with _OPEN_LOCK:
        existing = _OPEN.get(resolved)
        if existing is None:
            existing = AnnotationStore(resolved)
            _OPEN[resolved] = existing
        return existing
