# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Region definition for the MSC Canada (ECCC GeoMet) composite.

Latlon grid; MSC serves pre-colored PNG only, decoded via palette
reverse-engineering.  Resolution chosen for a ~3560×1720 single-request
WMS tile (under typical server size caps).
"""
from __future__ import annotations

from librewxr.data.regions import RegionDef


CACOMP = RegionDef(
    name="CACOMP",
    west=-141.0, east=-52.0, south=41.0, north=84.0,
    pixel_size=0.025, group="CANADA",
)

REGIONS: list[RegionDef] = [CACOMP]
