"""Reading a video's real dimensions out of the file.

Orientation is one of very few gate questions with a certain answer, and it was
going unmeasured. YouTube's Data API reports `hd`/`sd` and no dimensions, so the
probe inferred a height and never knew a width, which leaves `G1-ORIENT`
(width >= height) uncomputable — and a 9:16 phone video of somebody using a
washing machine was rejected on a hand density of 43% read from caption wording
while "it is portrait" was reported as not measured.
"""

from __future__ import annotations

import struct

import pytest

from video_searching_agent.pipeline.media_probe import read_mp4_dimensions


def _box(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I4s", len(body) + 8, kind) + body


def _tkhd(width: int, height: int, rotated: bool = False, version: int = 0) -> bytes:
    body = bytes([version, 0, 0, 0])
    body += b"\x00" * (32 if version == 1 else 20)  # times, id, reserved, duration
    body += b"\x00" * 16  # reserved, layer, alternate group, volume, reserved
    unity = 0x00010000
    if rotated:
        # A quarter turn: a and d zero, b and c set. This is how a phone marks a
        # clip recorded landscape and displayed portrait.
        matrix = (0, unity, 0, -unity, 0, 0, 0, 0, 0x40000000)
    else:
        matrix = (unity, 0, 0, 0, unity, 0, 0, 0, 0x40000000)
    body += struct.pack(">9i", *matrix)
    body += struct.pack(">2I", width << 16, height << 16)
    return _box(b"tkhd", body)


def _mp4(*tracks: bytes) -> bytes:
    traks = b"".join(_box(b"trak", track) for track in tracks)
    return _box(b"ftyp", b"isom" + b"\x00" * 8) + _box(b"moov", traks)


def test_a_landscape_track_reads_landscape(tmp_path):
    path = tmp_path / "landscape.mp4"
    path.write_bytes(_mp4(_tkhd(854, 480)))
    assert read_mp4_dimensions(path) == (854, 480)


def test_a_portrait_track_reads_portrait(tmp_path):
    path = tmp_path / "portrait.mp4"
    path.write_bytes(_mp4(_tkhd(240, 360)))
    assert read_mp4_dimensions(path) == (240, 360)


def test_a_rotated_track_is_portrait_however_it_was_recorded(tmp_path):
    """The case that would otherwise slip through: recorded 1920x1080, marked
    for a quarter turn, displayed 1080x1920. Only the matrix says so."""

    path = tmp_path / "rotated.mp4"
    path.write_bytes(_mp4(_tkhd(1920, 1080, rotated=True)))
    assert read_mp4_dimensions(path) == (1080, 1920)


def test_the_video_track_wins_over_an_audio_track(tmp_path):
    """Audio tracks carry zero dimensions; a subtitle track can carry small ones."""

    path = tmp_path / "multi.mp4"
    path.write_bytes(_mp4(_tkhd(0, 0), _tkhd(1280, 720), _tkhd(320, 60)))
    assert read_mp4_dimensions(path) == (1280, 720)


def test_a_version_one_track_header_is_read(tmp_path):
    path = tmp_path / "v1.mp4"
    path.write_bytes(_mp4(_tkhd(640, 360, version=1)))
    assert read_mp4_dimensions(path) == (640, 360)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not a video at all",
        struct.pack(">I4s", 8, b"ftyp"),
        # A box claiming to be longer than the file.
        struct.pack(">I4s", 1 << 20, b"moov") + b"\x00" * 16,
    ],
)
def test_an_unreadable_file_stays_unmeasured(tmp_path, content):
    """Guessing is worse than an honest "not measured"."""

    path = tmp_path / "broken.mp4"
    path.write_bytes(content)
    assert read_mp4_dimensions(path) is None


def test_a_missing_file_stays_unmeasured(tmp_path):
    assert read_mp4_dimensions(tmp_path / "nope.mp4") is None
