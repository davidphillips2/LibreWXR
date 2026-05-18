# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""USA NEXRAD-fed radar regions.

Shared between the IEM and MRMS source packages — both fetch composites
for the same 5 US territories.  IEM cares about ``live_dir`` / ``archive_dir``
for URL construction; MRMS ignores those fields (defaults are harmless).
"""
from __future__ import annotations

from librewxr.data.regions import RegionDef


USCOMP = RegionDef(
    name="USCOMP",
    west=-126.0, east=-65.0, south=23.0, north=50.0,
    pixel_size=0.005, group="US",
    live_dir="USCOMP", archive_dir="uscomp",
)

AKCOMP = RegionDef(
    name="AKCOMP",
    west=-170.5, east=-130.5, south=53.2, north=68.7,
    pixel_size=0.01, group="US",
    live_dir="AKCOMP", archive_dir="akcomp",
)

HICOMP = RegionDef(
    name="HICOMP",
    west=-162.4, east=-152.4, south=15.4, north=24.4,
    pixel_size=0.005, group="US",
    live_dir="HICOMP", archive_dir="hicomp",
)

PRCOMP = RegionDef(
    name="PRCOMP",
    west=-71.1, east=-61.1, south=13.1, north=23.1,
    pixel_size=0.01, group="US",
    live_dir="PRCOMP", archive_dir="prcomp",
)

GUCOMP = RegionDef(
    name="GUCOMP",
    west=140.5, east=149.0, south=9.2, north=17.7,
    pixel_size=0.0085, group="US",
    live_dir="GUCOMP", archive_dir="gucomp",
)

REGIONS: list[RegionDef] = [USCOMP, AKCOMP, HICOMP, PRCOMP, GUCOMP]
