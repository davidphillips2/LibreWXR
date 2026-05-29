# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Tests for Marshall-Palmer Z-R conversion + uint8 boundary helpers."""
import numpy as np
import pytest

pytestmark = pytest.mark.nowcast

from librewxr.data.zr import (
    dbz_to_mmh,
    mmh_to_dbz,
    mmh_to_uint8,
    uint8_to_mmh,
)


# Reference points computed analytically from the M-P relationship
# (Z = 200 · R^1.6) so the test verifies the helper against the exact
# formula, not against rounded table values that don't exact-round-trip.
def _mp_dbz_from_mmh(r: float) -> float:
    return 10.0 * np.log10(200.0 * r ** 1.6)


def _mp_mmh_from_dbz(dbz: float) -> float:
    return (10.0 ** (dbz / 10.0) / 200.0) ** (1.0 / 1.6)


class TestMarshallPalmer:
    def test_dbz_to_mmh_matches_analytical(self):
        dbz_values = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0], dtype=np.float32)
        expected = np.array(
            [_mp_mmh_from_dbz(float(d)) for d in dbz_values], dtype=np.float32,
        )
        result = dbz_to_mmh(dbz_values)
        # float32 precision floor — we're within 0.1% of the analytical
        # formula across 7 orders of magnitude in rainfall rate.
        rel_err = np.abs(result - expected) / np.maximum(expected, 1e-6)
        assert rel_err.max() < 1e-3, f"max rel_err={rel_err.max():.4e}"

    def test_mmh_to_dbz_matches_analytical(self):
        mmh_values = np.array([0.1, 1.0, 5.0, 10.0, 25.0, 100.0], dtype=np.float32)
        expected = np.array(
            [_mp_dbz_from_mmh(float(r)) for r in mmh_values], dtype=np.float32,
        )
        result = mmh_to_dbz(mmh_values)
        assert np.allclose(result, expected, atol=0.01), (
            f"result={result.tolist()} expected={expected.tolist()}"
        )

    def test_round_trip_mmh(self):
        mmh = np.linspace(0.5, 100.0, 50, dtype=np.float32)
        round_tripped = dbz_to_mmh(mmh_to_dbz(mmh))
        # Round-trip preserves to better than 0.5% — the only loss is
        # float32 precision in the log/exp pair.
        rel_err = np.abs(round_tripped - mmh) / mmh
        assert rel_err.max() < 5e-3, f"max rel_err={rel_err.max():.4e}"

    def test_round_trip_dbz(self):
        dbz = np.linspace(0.0, 70.0, 50, dtype=np.float32)
        round_tripped = mmh_to_dbz(dbz_to_mmh(dbz))
        assert np.allclose(round_tripped, dbz, atol=0.05)


class TestUint8Boundary:
    def test_uint8_zero_to_mmh_zero(self):
        arr = np.zeros((5, 5), dtype=np.uint8)
        out = uint8_to_mmh(arr)
        assert out.dtype == np.float32
        assert (out == 0.0).all()

    def test_mmh_zero_to_uint8_zero(self):
        arr = np.zeros((5, 5), dtype=np.float32)
        out = mmh_to_uint8(arr)
        assert out.dtype == np.uint8
        assert (out == 0).all()

    def test_uint8_round_trip_preserves_meaningful_values(self):
        # uint8 encoding step is 0.5 dBZ.  Values above the M-P floor
        # (~dBZ -23, ~uint8 18) round-trip via mm/h within one step.
        # Sub-floor values intentionally collapse to 0 — that's the
        # design, since they're well below any usable noise floor and
        # represent rain rates under 0.001 mm/h.
        original = np.arange(20, 256, dtype=np.uint8)
        round_tripped = mmh_to_uint8(uint8_to_mmh(original))
        diff = np.abs(round_tripped.astype(np.int16) - original.astype(np.int16))
        assert diff.max() <= 1, f"max diff={diff.max()} values={diff[diff > 1]}"

    def test_uint8_subfloor_values_collapse_to_zero(self):
        # uint8 1..14 corresponds to dBZ -31.5 to -25 → R < 0.001 mm/h
        # → below the floor → encodes back to 0.  This is intentional
        # design, not a precision bug.
        original = np.arange(1, 15, dtype=np.uint8)
        round_tripped = mmh_to_uint8(uint8_to_mmh(original))
        assert (round_tripped == 0).all(), f"expected all zero, got {round_tripped}"

    def test_uint8_84_is_roughly_10_dbz(self):
        # The default noise floor is 10 dBZ which encodes to pixel 84.
        # M-P at 10 dBZ: R = (10/200)^(1/1.6) = 0.153 mm/h
        arr = np.array([[84]], dtype=np.uint8)
        out = uint8_to_mmh(arr)
        assert abs(out[0, 0] - 0.153) < 0.01, f"got {out[0, 0]}"


class TestEdgeCases:
    def test_dbz_below_nodata_threshold_to_zero(self):
        dbz = np.array([-50.0, -40.0, -32.0, -32.1], dtype=np.float32)
        out = dbz_to_mmh(dbz)
        assert (out == 0.0).all()

    def test_dbz_just_above_threshold_nonzero(self):
        dbz = np.array([-31.5, -30.0, -20.0], dtype=np.float32)
        out = dbz_to_mmh(dbz)
        assert (out > 0.0).all()
        assert (out < 0.01).all()  # all very low rates, well under 0.01 mm/h

    def test_nan_dbz_preserves_nan(self):
        dbz = np.array([np.nan, 30.0, np.nan], dtype=np.float32)
        out = dbz_to_mmh(dbz)
        assert np.isnan(out[0])
        assert not np.isnan(out[1])
        assert np.isnan(out[2])

    def test_nan_mmh_preserves_nan_in_dbz(self):
        mmh = np.array([np.nan, 5.0, np.nan], dtype=np.float32)
        out = mmh_to_dbz(mmh)
        assert np.isnan(out[0])
        assert not np.isnan(out[1])
        assert np.isnan(out[2])

    def test_nan_mmh_encodes_to_zero_uint8(self):
        # Forecast pixels can come out NaN from S-PROG masking; encoder
        # must collapse them to NODATA rather than propagating NaN.
        mmh = np.array([[np.nan, 5.0], [np.nan, 0.0]], dtype=np.float32)
        out = mmh_to_uint8(mmh)
        assert out[0, 0] == 0
        assert out[0, 1] > 0
        assert out[1, 0] == 0
        assert out[1, 1] == 0

    def test_negative_mmh_encodes_to_zero(self):
        # S-PROG output should be non-negative but defensive code path.
        mmh = np.array([-0.5, 0.0, 1.0], dtype=np.float32)
        out = mmh_to_uint8(mmh)
        assert out[0] == 0
        assert out[1] == 0
        assert out[2] > 0

    def test_2d_array_shapes_preserved(self):
        arr = np.zeros((7, 13), dtype=np.uint8)
        arr[3, 5] = 100
        out = uint8_to_mmh(arr)
        assert out.shape == (7, 13)
        assert out[3, 5] > 0
        assert out[0, 0] == 0.0

    def test_very_high_dbz_no_overflow(self):
        # 70 dBZ is at the top of what hardware sees in extreme hail;
        # M-P gives ~370 mm/h.  Round-trip should not overflow.
        dbz = np.array([70.0], dtype=np.float32)
        mmh = dbz_to_mmh(dbz)
        assert np.isfinite(mmh).all()
        back = mmh_to_dbz(mmh)
        assert abs(back[0] - 70.0) < 0.1
