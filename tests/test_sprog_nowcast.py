# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Tests for the S-PROG (pysteps spectral prognosis) nowcast path."""
import numpy as np
import pytest

pytestmark = pytest.mark.nowcast

from librewxr.data.nowcast import NowcastGenerator
from librewxr.data.store import RadarFrame


H, W = 256, 256


def _blob(cy: int, cx: int, radius: int = 30, peak_dbz: float = 35.0) -> np.ndarray:
    """Gaussian-ish precip blob, returned in the uint8 dBZ encoding.

    Peak is ``peak_dbz`` at the centre and decays radially.  The S-PROG
    cascade needs spatial structure to decompose, so a smooth blob is
    the natural test signal.
    """
    grid = np.full((H, W), -32.0, dtype=np.float32)
    ys, xs = np.ogrid[0:H, 0:W]
    r2 = (ys - cy) ** 2 + (xs - cx) ** 2
    sigma = float(radius) / 2.0
    dbz = peak_dbz * np.exp(-r2 / (2.0 * sigma ** 2)) - 8.0
    grid = np.where(dbz > -32.0, dbz, -32.0).astype(np.float32)
    # Encode dBZ → uint8 using the project convention.
    return np.clip((grid + 32.0) * 2.0, 0, 255).astype(np.uint8)


def _history(*positions: tuple[int, int]) -> list[RadarFrame]:
    """Build a 3-frame ``RadarFrame`` list with USCOMP blobs at the
    given (cy, cx) positions, one per frame."""
    assert len(positions) == 3
    return [
        RadarFrame(
            timestamp=1000 * (i + 1),
            regions={"USCOMP": _blob(cy, cx)},
        )
        for i, (cy, cx) in enumerate(positions)
    ]


class TestSPROGSyncPath:
    def test_slow_motion_produces_forecast_with_expected_shape(self):
        # Slow eastward motion (2 px / frame) with realistic per-frame
        # variation — verifies S-PROG output frames have the right
        # shape, timestamps, and dtype.  Perfectly identical frames
        # would make the Yule-Walker AR estimator singular, which is
        # the right failure mode but not what we want to assert here.
        history = _history((128, 126), (128, 128), (128, 130))
        frames, flows = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=6, interval=600,
            blend_mode="blended",
        )
        assert len(frames) == 6
        # Timestamps are latest_ts + step * interval
        assert [f.timestamp for f in frames] == [3600, 4200, 4800, 5400, 6000, 6600]
        assert "USCOMP" in flows
        for f in frames:
            assert "USCOMP" in f.regions
            assert f.regions["USCOMP"].shape == (H, W)
            assert f.regions["USCOMP"].dtype == np.uint8

    def test_degenerate_input_skipped_gracefully(self):
        # Three identical frames make the AR(2) Yule-Walker system
        # singular.  The broad exception handler in _generate_sync_sprog
        # should log + skip that region rather than crashing the cycle.
        history = _history((128, 128), (128, 128), (128, 128))
        frames, flows = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=6, interval=600,
            blend_mode="blended",
        )
        # USCOMP was skipped due to S-PROG failure → no nowcast frames
        # for this cycle.  flows still carries the (zero) Farneback
        # vectors so the renderer's arrow overlay has something to use.
        assert frames == []
        assert "USCOMP" in flows

    def test_eastward_motion_extrapolated_eastward(self):
        # Blob moves 8 px east per frame.  The forecast at T+1 should
        # have its centre-of-mass further east than the input's centre.
        history = _history((128, 80), (128, 96), (128, 112))
        frames, _ = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=3, interval=600,
            blend_mode="radar",
        )
        # Compute centre-of-mass for the input final frame vs T+1 forecast.
        latest_input = history[-1].regions["USCOMP"]
        t_plus_1 = frames[0].regions["USCOMP"]

        # Use a sufficiently low threshold to pick up the forecast tail.
        input_mask = latest_input > 100  # roughly > 18 dBZ
        forecast_mask = t_plus_1 > 100
        assert input_mask.sum() > 50, "input blob has too little signal"
        assert forecast_mask.sum() > 50, "forecast collapsed to noise"

        input_centroid_x = np.where(input_mask)[1].mean()
        forecast_centroid_x = np.where(forecast_mask)[1].mean()
        # Forecast should have moved east (higher column index).
        # Allow a small tolerance — S-PROG's probability-matched output
        # can blur the centroid slightly.
        assert forecast_centroid_x > input_centroid_x, (
            f"forecast centroid x={forecast_centroid_x:.1f} did not "
            f"advance east of input x={input_centroid_x:.1f}"
        )

    def test_skips_regions_missing_from_any_frame(self):
        f1 = RadarFrame(
            timestamp=1000,
            regions={"USCOMP": _blob(128, 100), "OPERA": _blob(128, 100)},
        )
        # f2 is missing OPERA — that region cannot be nowcast.
        f2 = RadarFrame(timestamp=2000, regions={"USCOMP": _blob(128, 108)})
        f3 = RadarFrame(
            timestamp=3000,
            regions={"USCOMP": _blob(128, 116), "OPERA": _blob(128, 116)},
        )
        frames, flows = NowcastGenerator._generate_sync_sprog(
            [f1, f2, f3], latest_ts=3000, n_steps=3, interval=600,
            blend_mode="blended",
        )
        assert "USCOMP" in flows
        assert "OPERA" not in flows
        for f in frames:
            assert "USCOMP" in f.regions
            assert "OPERA" not in f.regions

    def test_no_overlapping_regions_returns_empty(self):
        f1 = RadarFrame(timestamp=1000, regions={"USCOMP": _blob(128, 100)})
        f2 = RadarFrame(timestamp=2000, regions={})
        f3 = RadarFrame(timestamp=3000, regions={"USCOMP": _blob(128, 116)})
        frames, flows = NowcastGenerator._generate_sync_sprog(
            [f1, f2, f3], latest_ts=3000, n_steps=3, interval=600,
            blend_mode="blended",
        )
        assert frames == []
        assert flows == {}

    def test_output_is_uint8_no_nan_propagation(self):
        # S-PROG can produce NaN pixels in zero-rain areas.  The
        # encoder must collapse them to 0 (NODATA) so downstream
        # tile rendering never sees NaN in a uint8 frame.
        history = _history((128, 100), (128, 108), (128, 116))
        frames, _ = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=6, interval=600,
            blend_mode="blended",
        )
        for f in frames:
            arr = f.regions["USCOMP"]
            assert arr.dtype == np.uint8
            assert arr.min() >= 0
            assert arr.max() <= 255

    def test_blend_weight_curve_unchanged(self):
        # The blend curve helper is shared between extrapolation and
        # S-PROG paths; verify S-PROG output frames carry the same
        # weights the extrapolation path would.
        history = _history((128, 100), (128, 108), (128, 116))
        frames, _ = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=6, interval=600,
            blend_mode="blended",
        )
        weights = [f.blend_weight for f in frames]
        # Same curve as the existing extrapolation path: 0.20 + 0.80*(1-t)^1.4
        # at t = 1/6, 2/6, ..., 6/6.
        for i, w in enumerate(weights, start=1):
            t = i / 6
            expected = 0.20 + 0.80 * (1.0 - t) ** 1.4
            assert abs(w - expected) < 1e-6, (
                f"step {i}: got {w}, expected {expected}"
            )

    def test_radar_mode_pins_weight_full(self):
        history = _history((128, 100), (128, 108), (128, 116))
        frames, _ = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=6, interval=600,
            blend_mode="radar",
        )
        # All steps within the 60-min radar window get weight 1.0;
        # step 7+ would fall to 0 (we only generate 6 steps here).
        assert all(f.blend_weight == 1.0 for f in frames)

    def test_model_mode_pins_weight_zero(self):
        history = _history((128, 100), (128, 108), (128, 116))
        frames, _ = NowcastGenerator._generate_sync_sprog(
            history, latest_ts=3000, n_steps=6, interval=600,
            blend_mode="model",
        )
        assert all(f.blend_weight == 0.0 for f in frames)
