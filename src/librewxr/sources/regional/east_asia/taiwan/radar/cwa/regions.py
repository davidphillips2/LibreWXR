# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Region definition for the Taiwan CWA QPESUMS composite.

Single region (TWCOMP) — 921×881 grid at 0.0125° (~1.4 km), 10-min
cadence.  Decoded from CWA's ``O-A0059-001`` XML feed on anonymous AWS
S3 (``cwaopendata`` in ``ap-northeast-1``).  Datum is TWD67; the sub-
pixel offset vs WGS84 is below the rendering resolution.
"""
from __future__ import annotations

from librewxr.data.regions import RegionDef


TWCOMP = RegionDef(
    name="TWCOMP",
    west=115.0, east=126.5125, south=18.0, north=29.0125,
    pixel_size=0.0125, group="TAIWAN",
    grid_width=921, grid_height=881,
)

REGIONS: list[RegionDef] = [TWCOMP]
