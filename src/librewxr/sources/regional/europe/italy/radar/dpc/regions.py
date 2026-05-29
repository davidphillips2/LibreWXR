# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Region definition for the DPC Italian national radar composite.

Projection (per upstream ``ModelTiepoint`` + ``GeoKeyDirectory``):
spherical Transverse Mercator, ``lat_0 = 42°N``, ``lon_0 = 12.5°E``,
``R = 6371229`` m, ``k_0 = 1``, no false easting/northing.  Grid is
1200 × 1400 px at 1 km, top-left projected at (-600000, 650000) m.

Geographic extent (inverse-projected corners): UL ≈ (47.57°N, 4.50°E),
LR ≈ (35.08°N, 19.09°E) — covers all of Italy plus a buffer into
S. France, S. Switzerland, S. Austria, W. Slovenia/Croatia, the
N. African coast, Sardinia, and Sicily.

``pixel_size`` is set just below OPERA's (0.01) so the multi-region
compositor in ``tiles/coordinates.overlapping_regions`` sorts ITCOMP
first — ITCOMP fills any pixel where it has data, OPERA covers the
rest of the European group.  See research notes for why this matters:
Italy isn't in the EUMETNET OPERA station list, so what OPERA shows
over Italian airspace is edge-of-range data from neighbouring countries
that the native Italian network can replace cleanly.
"""
from __future__ import annotations

from librewxr.data.regions import RegionDef


ITCOMP = RegionDef(
    name="ITCOMP",
    # Geographic bounding box (used for tile-overlap checks); slightly
    # generous vs the actual inverse-projected corners so tile selection
    # doesn't drop edge tiles to numerical rounding.
    west=4.5, east=19.1, south=35.0, north=47.6,
    pixel_size=0.009,
    group="EUROPE",
    proj="tmerc",
    # Grid origin matches the upstream GeoTIFF ModelTiepoint.
    grid_x_min=-600000.0, grid_y_max=650000.0, grid_scale=1000.0,
    grid_width=1200, grid_height=1400,
    tmerc_lat0=42.0, tmerc_lon0=12.5,
    tmerc_radius=6371229.0, tmerc_k0=1.0,
)

REGIONS: list[RegionDef] = [ITCOMP]
