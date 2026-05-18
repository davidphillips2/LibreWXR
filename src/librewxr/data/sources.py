# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Cross-source helper(s) shared by migrated radar sources.

After the 2026-05-17 sources-refactor (Phase 1 steps 3–9), every radar
source class lives in its own package under ``librewxr.sources``:

- IEM:  ``sources/regional/north_america/usa/radar/iem/``
- MRMS: ``sources/regional/north_america/usa/radar/mrms/``
- MSC Canada: ``sources/regional/north_america/canada/radar/msc_canada/``
- MARN El Salvador: ``sources/regional/central_america/el_salvador/radar/marn/``
- OPERA: ``sources/regional/europe/radar/opera/``
- CWA Taiwan: ``sources/regional/east_asia/taiwan/radar/cwa/``
- MMD Malaysia: ``sources/regional/southeast_asia/malaysia/radar/mmd/``

This module is kept (rather than deleted in Phase 4) for two shared
helpers used across packages:

- ``_dbz_float_to_uint8`` — uint8 dBZ encoder imported by every migrated
  radar source so the encoding stays consistent.
- ``_suppress_eccodes_stderr`` — cfgrib stderr muzzle imported by MRMS
  and by every NWP grid that opens GRIB2 (HRRR, HRRR-Alaska, HRDPS,
  ICON-EU, DMI DINI, AROME Antilles).

Phase 3 (NWP grid migrations) and Phase 4 (cleanup) may relocate these
to dedicated modules.  For now they sit here so the NWP grids that
haven't migrated yet don't need import surgery in this phase.
"""
import os
from contextlib import contextmanager

import numpy as np


def _dbz_float_to_uint8(arr: np.ndarray) -> np.ndarray:
    """Convert float32 dBZ values to uint8 using IEM's encoding.

    Formula: pixel = clamp((dBZ + 32) * 2, 0, 255)
    NODATA (anything <= -32) maps to 0 (transparent in all color schemes).
    """
    nodata_mask = arr <= -32.0
    result = np.clip((arr + 32.0) * 2.0, 0, 255).astype(np.uint8)
    result[nodata_mask] = 0
    return result


@contextmanager
def _suppress_eccodes_stderr():
    """Redirect OS-level stderr to /dev/null during the block.

    The eccodes C library (used by cfgrib) writes non-actionable
    ``dataTime`` truncation messages directly to stderr.  This silences
    them without affecting Python logging or other error reporting.
    """
    devnull = os.open(os.devnull, os.O_WRONLY)
    original = os.dup(2)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(original, 2)
        os.close(devnull)
        os.close(original)
