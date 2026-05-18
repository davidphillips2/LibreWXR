# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Taiwan QPESUMS contributing radars.

7 contributing radars operated by the Central Weather Administration.
Approximate coordinates from publicly-documented siting and CWA's radar
inventory.  Two additional Taiwan radars exist (RCMK military, RCWF
civil aviation) but are not part of this composite.

The 240 km default range covers all of Taiwan + a substantial offshore
buffer.  Exact lat/lons to the metre don't matter here because the radar
circles overlap heavily over the island; the resulting union polygon is
insensitive to small per-station shifts.

Note (2026-05-17): Coverage-mask generation still reads from
``librewxr.data.radar_stations`` for now.  Phase 2 of the sources
refactor migrates that consumer over to per-source ``stations.py``
files like this one.
"""
from __future__ import annotations


STATIONS: list[tuple[float, float]] = [
    (25.071, 121.773),   # 五分山 / Wufenshan  (NE Taiwan, original 4)
    (23.991, 121.622),   # 花蓮   / Hualien    (E Taiwan,  original 4)
    (23.146, 120.094),   # 七股   / Qigu/Cigu  (SW Taiwan, original 4)
    (21.902, 120.853),   # 墾丁   / Kenting    (S Taiwan,  original 4)
    (24.998, 121.420),   # 樹林   / Shulin     (N gap-fill)
    (24.140, 120.620),   # 南屯   / Nantun     (central gap-fill)
    (22.510, 120.397),   # 林園   / Linyuan    (S gap-fill, Kaohsiung)
]
