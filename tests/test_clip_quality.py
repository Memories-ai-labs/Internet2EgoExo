"""Fine-grained cleaning of a cut clip, judged on the pixels.

The calibration behind these numbers is in the module docstring and it is the
whole reason the tests look like this: sharpness measured *texture*, not quality
— the softest span in the sample was good egocentric footage of a flat white
wall (96) and the sharpest was a channel's subscribe end card (4144). So the
tests pin that no blur filter exists, and that the one gate is the pair.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from video_searching_agent.pipeline.clip_quality import (
    GRAPHIC_SHARPNESS_MIN,
    IDLE_MOTION_MAX,
    STATIC_MOTION_MAX,
    ClipMeasurement,
    judge_clip,
    measure_clip,
)


def _measured(**kw) -> ClipMeasurement:
    base = {
        "frames": 20,
        "seconds": 10.0,
        "motion_mean": 0.10,
        "motion_p90": 0.15,
        "motion_max": 0.20,
        "sharpness_mean": 1100.0,
        "sharpness_p10": 900.0,
        "clipped_fraction": 0.001,
    }
    return ClipMeasurement(**{**base, **kw})


class TestTheOneGate:
    """Still, and full of hard edges, is type rather than footage."""

    def test_the_end_card_shape_is_rejected(self):
        # The real numbers from the calibration: a GCN outro card.
        verdict = judge_clip(_measured(motion_mean=0.018, sharpness_mean=4144.0))

        assert verdict.usable is False
        assert "static graphic" in verdict.reasons[0]
        assert "title or end card" in verdict.reasons[0]

    def test_still_footage_that_is_not_a_graphic_survives(self):
        """Low motion alone is not a rejection. A hand rests mid-task."""

        verdict = judge_clip(_measured(motion_mean=0.010, sharpness_mean=300.0))

        assert verdict.usable is True
        assert any("idle" in note for note in verdict.notes)

    def test_a_sharp_graphic_that_moves_survives(self):
        """Both halves are required. A moving titled sequence is still footage."""

        verdict = judge_clip(_measured(motion_mean=0.20, sharpness_mean=5000.0))
        assert verdict.usable is True

    @pytest.mark.parametrize(
        ("motion", "sharpness", "usable"),
        [
            (STATIC_MOTION_MAX, GRAPHIC_SHARPNESS_MIN, False),  # the corner itself
            (STATIC_MOTION_MAX + 0.001, GRAPHIC_SHARPNESS_MIN, True),
            (STATIC_MOTION_MAX, GRAPHIC_SHARPNESS_MIN - 1, True),
        ],
    )
    def test_the_boundary_is_where_it_says_it_is(self, motion, sharpness, usable):
        assert judge_clip(_measured(motion_mean=motion, sharpness_mean=sharpness)).usable is usable


class TestNoBlurFilter:
    """The measurement that would have thrown away the good clip."""

    def test_the_softest_real_footage_in_the_sample_is_kept(self):
        # A hand placing a cup into a wall bin: motion 0.047, sharpness 96.
        verdict = judge_clip(_measured(motion_mean=0.047, sharpness_mean=96.0))

        assert verdict.usable is True
        assert verdict.reasons == []

    def test_nothing_rejects_on_sharpness_at_any_value(self):
        for sharpness in (0.0, 1.0, 96.0, 500.0, 5000.0, 50000.0):
            verdict = judge_clip(_measured(motion_mean=0.12, sharpness_mean=sharpness))
            assert verdict.usable is True, sharpness

    def test_the_gated_list_names_only_what_can_reject(self):
        verdict = judge_clip(_measured())
        assert verdict.gated == ("static_graphic",)
        assert "sharpness" not in " ".join(verdict.gated)

    def test_the_measurement_carries_the_warning_about_sharpness(self):
        note = _measured().as_dict()["sharpness_note"]
        assert "texture, not quality" in note
        assert "Never gated on" in note


class TestWhatIsMeasuredButNotEnforced:
    def test_a_shot_cut_guess_is_a_note_and_says_it_is_a_guess(self):
        verdict = judge_clip(_measured(shot_cut_candidates=[3.5, 7.0]))

        assert verdict.usable is True
        joined = " ".join(verdict.notes)
        assert "possible shot cut" in joined
        assert "not shot detection" in joined

    def test_heavy_clipping_is_reported_and_says_it_does_not_reject(self):
        verdict = judge_clip(_measured(clipped_fraction=0.42))

        assert verdict.usable is True
        assert any("does not reject" in note for note in verdict.notes)

    def test_mild_clipping_is_not_even_mentioned(self):
        verdict = judge_clip(_measured(clipped_fraction=0.01))
        assert not any("limit" in note for note in verdict.notes)


class TestAnUnmeasuredClipIsNotJudged:
    def test_a_decode_failure_keeps_the_clip(self):
        verdict = judge_clip(ClipMeasurement(error="decode failed: moov atom not found"))

        assert verdict.usable is True
        assert any("not measured" in note for note in verdict.notes)
        assert any("moov atom" in note for note in verdict.notes)

    def test_one_frame_is_not_enough_to_measure_motion(self):
        verdict = judge_clip(ClipMeasurement(frames=1))
        assert verdict.usable is True
        assert any("not measured" in note for note in verdict.notes)

    def test_a_missing_file_is_an_error_not_an_exception(self):
        measurement = measure_clip("/nonexistent/definitely-not-here.mp4")
        assert measurement.measured is False
        assert measurement.error


def _ffmpeg_available() -> bool:
    if shutil.which("ffmpeg"):
        return True
    try:
        import imageio_ffmpeg

        return bool(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.skipif(not _ffmpeg_available(), reason="needs a decoder")
class TestDecodingRealPixels:
    """Generated clips, so the arithmetic is checked against known content."""

    @staticmethod
    def _render(tmp_path, source: str, name: str) -> str:
        from video_searching_agent.pipeline.clip_quality import _ffmpeg

        path = str(tmp_path / name)
        subprocess.run(  # noqa: S603
            [
                _ffmpeg(),
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                source,
                "-t",
                "3",
                "-pix_fmt",
                "yuv420p",
                path,
            ],
            check=True,
            timeout=120,
        )
        return path

    def test_a_still_colour_field_measures_as_motionless(self, tmp_path):
        path = self._render(tmp_path, "color=c=gray:s=320x180:r=10", "still.mp4")
        measurement = measure_clip(path)

        assert measurement.measured
        assert measurement.frames >= 2
        assert measurement.motion_mean is not None
        assert measurement.motion_mean <= IDLE_MOTION_MAX
        # A flat field has no edges, so it is not a graphic — and must survive.
        assert judge_clip(measurement).usable is True

    def test_noise_measures_as_moving_and_textured(self, tmp_path):
        path = self._render(
            tmp_path, "nullsrc=s=320x180:r=10,geq=random(1)*255:128:128", "noise.mp4"
        )
        measurement = measure_clip(path)

        assert measurement.measured
        assert measurement.motion_mean is not None
        assert measurement.motion_mean > STATIC_MOTION_MAX
        assert measurement.sharpness_mean is not None
        assert measurement.sharpness_mean > 0
        assert judge_clip(measurement).usable is True

    def test_a_still_high_contrast_pattern_is_the_graphic_case(self, tmp_path):
        """Still plus hard edges is what a title card looks like to this pass."""

        path = self._render(tmp_path, "testsrc=s=320x180:r=10", "pattern.mp4")
        measurement = measure_clip(path)

        assert measurement.measured
        assert measurement.sharpness_mean is not None
        assert measurement.sharpness_mean > 0
        # testsrc animates, so this documents the measurement rather than
        # asserting a rejection: the point is that both halves are needed.
        assert measurement.motion_mean is not None
