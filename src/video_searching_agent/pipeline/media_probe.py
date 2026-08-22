"""Read a video file's real dimensions, out of the file itself.

Orientation is one of the few gate questions with a certain answer: a vertical
phone video is scrapped, full stop, and the pixels say so without any judgement
being involved. It was going unmeasured anyway.

The reason is worth writing down. YouTube's Data API reports `definition` — `hd`
or `sd` — and no dimensions, so the probe could infer a *height* and never knew
a *width*, which leaves `G1-ORIENT` (width >= height) uncomputable. A 9:16 phone
video of somebody using a washing machine was therefore rejected on a hand
density of 43%, an uncertain number read from caption wording, while the certain
and decisive fact — it is portrait — was reported as "not measured".

So this reads the file that was actually downloaded. No new dependency: MP4
stores display dimensions in each track's `tkhd` box, along with a
transformation matrix that phone cameras use to mark rotation. A clip recorded
landscape and rotated 90° for display is *portrait*, and only the matrix says
so, which is exactly the case that would otherwise slip through.
"""

from __future__ import annotations

import logging
import struct
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

# Boxes worth descending into on the way to a track header.
_CONTAINERS = {b"moov", b"trak", b"mdia"}

# How much of a file to walk before giving up. `moov` is normally at the front
# or the back; either way this is generous and bounds a malformed file.
_MAX_BOXES = 4096


def read_mp4_dimensions(path: str | Path) -> tuple[int, int] | None:
    """Display width and height of an MP4's video track, rotation applied.

    Returns None when the file is not an MP4, has no video track, or is
    truncated — an unmeasurable file must stay unmeasured rather than be
    guessed at.
    """
    try:
        with open(path, "rb") as handle:
            found = _walk(handle, end=_size_of(path), depth=0, budget=[_MAX_BOXES])
    except (OSError, struct.error) as exc:
        logger.info("could not read dimensions from %s: %s", path, exc)
        return None
    if not found:
        return None
    # A file can hold several tracks; the video one is the largest by area.
    return max(found, key=lambda pair: pair[0] * pair[1])


def _size_of(path: str | Path) -> int:
    return Path(path).stat().st_size


def _walk(
    handle: BinaryIO, end: int, depth: int, budget: list[int]
) -> list[tuple[int, int]]:
    """Collect the dimensions of every track header found under `end`."""

    found: list[tuple[int, int]] = []
    while handle.tell() + 8 <= end and budget[0] > 0 and depth < 8:
        budget[0] -= 1
        header_start = handle.tell()
        header = handle.read(8)
        if len(header) < 8:
            break
        size, kind = struct.unpack(">I4s", header)
        if size == 1:
            # 64-bit size follows the type.
            extended = handle.read(8)
            if len(extended) < 8:
                break
            size = struct.unpack(">Q", extended)[0]
            body_start = header_start + 16
        elif size == 0:
            # Runs to the end of the file.
            size = end - header_start
            body_start = header_start + 8
        else:
            body_start = header_start + 8

        if size < 8 or header_start + size > end:
            break
        body_end = header_start + size

        if kind == b"tkhd":
            handle.seek(body_start)
            dimensions = _tkhd_dimensions(handle.read(body_end - body_start))
            if dimensions:
                found.append(dimensions)
        elif kind in _CONTAINERS:
            handle.seek(body_start)
            found.extend(_walk(handle, body_end, depth + 1, budget))

        handle.seek(body_end)
    return found


def _tkhd_dimensions(body: bytes) -> tuple[int, int] | None:
    """Width and height from a track header, with its rotation applied.

    Layout after the 4 version/flags bytes: creation and modification times,
    track id, reserved, duration — 8-byte fields in version 0 and 16-byte in
    version 1 — then 8 reserved bytes, layer, alternate group, volume, 2
    reserved, a 36-byte matrix, and finally width and height as 16.16 fixed
    point.
    """
    if len(body) < 4:
        return None
    version = body[0]
    offset = 4 + (32 if version == 1 else 20) + 16
    matrix_at = offset
    if len(body) < matrix_at + 36 + 8:
        return None

    matrix = struct.unpack(">9i", body[matrix_at : matrix_at + 36])
    width_fixed, height_fixed = struct.unpack(">2I", body[matrix_at + 36 : matrix_at + 44])
    width = width_fixed >> 16
    height = height_fixed >> 16
    if width <= 0 or height <= 0:
        return None

    # The matrix is [a b u; c d v; x y w] in 16.16 (the last column is 2.30).
    # A quarter turn has a and d at zero and b and c non-zero, which swaps the
    # displayed axes — the case a phone recording relies on.
    a, b, c, d = matrix[0], matrix[1], matrix[3], matrix[4]
    if a == 0 and d == 0 and (b != 0 or c != 0):
        width, height = height, width
    return width, height
