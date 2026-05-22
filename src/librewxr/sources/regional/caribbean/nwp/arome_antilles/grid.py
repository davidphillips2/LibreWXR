# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Météo-France AROME Antilles regional precipitation source.

Thin subclass of ``AROMEOverseasGrid`` that fixes the Caribbean grid
extent, URL token, feather distance, and config prefix.  Domain
covers Guadeloupe, Martinique, Saint Martin, Saint-Barthélemy, and
surrounding eastern Caribbean waters at 0.025° (~2.5 km) regular
lat/lon resolution.  All fetch / decode / cache machinery lives in
``librewxr.sources._shared.arome``.

Data attribution: Météo-France, Etalab Open Licence v2.0.
"""
from __future__ import annotations

from typing import ClassVar

from librewxr.sources._shared.arome import (
    AROMEOverseasGrid,
    BRACKET_INTERVAL_SECONDS,
    CYCLE_INTERVAL_SECONDS,
    bracket_lead_seconds,
    floor_cycle,
    latest_published_run,
    precip_rate_to_dbz_encoded,
)


class AROMEAntillesGrid(AROMEOverseasGrid):
    """AROME Antilles grid — eastern Caribbean.

    Grid corners back-decoded from GRIB Section 3 of a representative
    ``arome-om-ANTIL__0025__SP1__006H`` file on 2026-05-08; all four
    corners match cfgrib's reported lat/lon arrays within float
    precision.  The domain is small (~2600 km E-W, ~1500 km N-S), so
    the feather tightens to ~50 km (20 cells × 0.025° × 110 km/°)
    instead of the ~75 km used by HRRR/DMI.
    """

    name: ClassVar[str] = "arome_antilles"
    friendly_name: ClassVar[str] = "AROME Antilles"
    settings_prefix: ClassVar[str] = "arome_antilles"
    memmap_subdir: ClassVar[str] = "arome_antilles"

    url_token: ClassVar[str] = "ANTIL"

    LAT_NORTH: ClassVar[float] = 22.9
    LAT_SOUTH: ClassVar[float] = 9.7
    LON_WEST_DEG_E: ClassVar[float] = 284.7
    LON_EAST_DEG_E: ClassVar[float] = 308.3
    GRID_DLAT: ClassVar[float] = 0.025
    GRID_DLON: ClassVar[float] = 0.025
    GRID_WIDTH: ClassVar[int] = 945
    GRID_HEIGHT: ClassVar[int] = 529
    FEATHER_DISTANCE_CELLS: ClassVar[int] = 20


# ── Backward-compat module-level aliases ──
#
# Tests (and any out-of-tree code that imported the pre-refactor API)
# pull these names from this module.  New variants don't need such
# aliases — class-attribute access on the subclass is the going-forward
# pattern.

AROME_ANT_LAT_NORTH = AROMEAntillesGrid.LAT_NORTH
AROME_ANT_LAT_SOUTH = AROMEAntillesGrid.LAT_SOUTH
AROME_ANT_LON_WEST_DEG_E = AROMEAntillesGrid.LON_WEST_DEG_E
AROME_ANT_LON_EAST_DEG_E = AROMEAntillesGrid.LON_EAST_DEG_E
AROME_ANT_GRID_DLAT = AROMEAntillesGrid.GRID_DLAT
AROME_ANT_GRID_DLON = AROMEAntillesGrid.GRID_DLON
AROME_ANT_GRID_WIDTH = AROMEAntillesGrid.GRID_WIDTH
AROME_ANT_GRID_HEIGHT = AROMEAntillesGrid.GRID_HEIGHT
AROME_ANT_FEATHER_DISTANCE_CELLS = AROMEAntillesGrid.FEATHER_DISTANCE_CELLS

grid_indices = AROMEAntillesGrid.grid_indices
domain_mask = AROMEAntillesGrid.domain_mask
feather_mask = AROMEAntillesGrid.feather_mask
file_url = AROMEAntillesGrid.file_url
decode_tp_message = AROMEAntillesGrid.decode_tp_message


__all__ = [
    "AROMEAntillesGrid",
    "AROME_ANT_LAT_NORTH",
    "AROME_ANT_LAT_SOUTH",
    "AROME_ANT_LON_WEST_DEG_E",
    "AROME_ANT_LON_EAST_DEG_E",
    "AROME_ANT_GRID_DLAT",
    "AROME_ANT_GRID_DLON",
    "AROME_ANT_GRID_WIDTH",
    "AROME_ANT_GRID_HEIGHT",
    "AROME_ANT_FEATHER_DISTANCE_CELLS",
    "BRACKET_INTERVAL_SECONDS",
    "CYCLE_INTERVAL_SECONDS",
    "bracket_lead_seconds",
    "decode_tp_message",
    "domain_mask",
    "feather_mask",
    "file_url",
    "floor_cycle",
    "grid_indices",
    "latest_published_run",
    "precip_rate_to_dbz_encoded",
]
