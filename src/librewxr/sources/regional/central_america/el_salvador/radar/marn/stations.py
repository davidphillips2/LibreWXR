# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""SNET (El Salvador) radar station inventory.

Single S-band radar at San Andrés volcano.  Coordinates from the
viewer's ``center = [13.687, -88.883]`` JS variable
(snet.gob.sv/googlemaps/radares/radaresSV8.php).  120 km product, so
the SVCOMP coverage mask uses the 120 km range override defined in
``librewxr.data.radar_stations``.

Note (2026-05-17): Coverage-mask generation still reads from
``librewxr.data.radar_stations`` for now.  Phase 2 of the sources
refactor migrates that consumer over to per-source ``stations.py``
files like this one.
"""
from __future__ import annotations


STATIONS: list[tuple[float, float]] = [
    (13.687, -88.883),   # San Andrés
]
