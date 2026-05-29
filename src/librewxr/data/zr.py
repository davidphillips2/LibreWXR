# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Z-R reflectivity ↔ rainfall-rate conversion.

The S-PROG nowcast (and any future pysteps-based method) operates on
rainfall rate in mm/h, but the frame store keeps radar data in the
project's uint8 dBZ encoding.  These helpers bridge the two
representations.

The Marshall-Palmer relationship ``Z = 200 · R^1.6`` is the climatology
used by every radar source in the stack (MARN, MMD, OPERA, MRMS all
either decode from or to this convention).  Type-aware Z-R (convective
vs stratiform) is a separate, larger change.

Encoding boundary, for reference:

    uint8 pixel = clamp((dBZ + 32) * 2, 0, 255)   # NODATA → 0
    dBZ         = (uint8 / 2) - 32                # 0 → -32 dBZ (≈ no rain)
"""
from __future__ import annotations

import numpy as np

# Marshall-Palmer: Z [mm^6/m^3] = A · R^b, R [mm/h]
_MP_A = 200.0
_MP_B = 1.6

# dBZ value the encoder treats as "no rain / NODATA".  Anything at or
# below this maps to uint8 0; the inverse decode lands here.
_DBZ_NODATA = -32.0

# Below this rainfall rate (mm/h), forecast values are clamped to 0 to
# avoid floating-point dust forecasting as faint rain.  Matches the
# rate at dBZ = -32 to a few significant figures.
_R_FLOOR = 1.0e-3


def dbz_to_mmh(dbz: np.ndarray) -> np.ndarray:
    """Marshall-Palmer inverse: dBZ → mm/h.

    NaN inputs are preserved as NaN.  Values at or below ``-32`` dBZ
    (the NODATA sentinel) map to ``0`` mm/h — this is the convention
    that "no detectable signal" is the same as "no rain" for nowcast
    input purposes.  Coverage masking is the renderer's job, not ours.
    """
    arr = np.asarray(dbz, dtype=np.float32)
    out = np.zeros_like(arr)
    valid = np.isfinite(arr) & (arr > _DBZ_NODATA)
    # R = (10^(dBZ/10) / A) ^ (1/b)
    z_linear = np.power(10.0, arr[valid] / 10.0)
    out[valid] = np.power(z_linear / _MP_A, 1.0 / _MP_B).astype(np.float32)
    # Preserve NaN so callers can distinguish "no rain" (0) from
    # "missing data" (NaN) if they want.
    out[~np.isfinite(arr)] = np.nan
    return out


def mmh_to_dbz(mmh: np.ndarray) -> np.ndarray:
    """Marshall-Palmer forward: mm/h → dBZ.

    Rainfall rates below ``_R_FLOOR`` (the M-P equivalent of -32 dBZ)
    map to the NODATA dBZ sentinel.  NaN inputs propagate as NaN so
    callers can mask them explicitly.
    """
    arr = np.asarray(mmh, dtype=np.float32)
    out = np.full_like(arr, _DBZ_NODATA)
    valid = np.isfinite(arr) & (arr > _R_FLOOR)
    # dBZ = 10 · log10(A · R^b)
    out[valid] = (10.0 * np.log10(_MP_A * np.power(arr[valid], _MP_B))).astype(np.float32)
    out[~np.isfinite(arr)] = np.nan
    return out


def uint8_to_mmh(arr: np.ndarray) -> np.ndarray:
    """uint8 dBZ encoding → mm/h float32.

    The project encoding maps uint8 0 to dBZ = -32 (NODATA), which this
    helper converts to 0 mm/h — the same convention the S-PROG cascade
    treats as "no rain" via the ``precip_thr`` parameter.
    """
    dbz = (np.asarray(arr, dtype=np.float32) / 2.0) - 32.0
    return dbz_to_mmh(dbz)


def mmh_to_uint8(arr: np.ndarray) -> np.ndarray:
    """mm/h float32 → uint8 dBZ encoding.

    NaN values (from masked S-PROG forecast pixels) and sub-floor
    rates collapse to uint8 0, so the output is safe to drop into
    ``NowcastFrame.regions`` without extra masking by the caller.
    """
    dbz = mmh_to_dbz(arr)
    # NaN in mm/h propagates to NaN in dBZ; treat as NODATA on encode.
    dbz = np.where(np.isfinite(dbz), dbz, _DBZ_NODATA)
    encoded = np.clip((dbz + 32.0) * 2.0, 0, 255).astype(np.uint8)
    return encoded
