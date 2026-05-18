# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Region definition for the MARN/SNET El Salvador radar.

Single S-band radar at San Andrés volcano, 120 km product.  PNG with
HSV-style continuous gradient palette; anonymous Google Cloud Storage
bucket (``radar-images-sv``); 5-min cadence.  Pixel grid is slightly
anisotropic (~0.926 km lon × ~1.02 km lat — both pixel sizes set
explicitly).
"""
from __future__ import annotations

from librewxr.data.regions import RegionDef


SVCOMP = RegionDef(
    name="SVCOMP",
    west=-90.833, east=-87.044, south=12.112, north=15.244,
    pixel_size=0.00926, pixel_size_y=0.00916,
    group="CENTRAL_AMERICA",
    grid_width=409, grid_height=342,
)

REGIONS: list[RegionDef] = [SVCOMP]
