# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""MET Malaysia radar station inventory.

12-radar national network feeding the combined Peninsular + East
composite GIF.  Coordinates are approximate (taken from each radar's
host airport / city — the operational siting is usually co-located or
within a few km).  Default 240 km Doppler range.

Cross-checked against the station inventory on
rainviewer.com/radars/malaysia.html (12 stations: MY2809–MY2819,
MY2865).

Note (2026-05-17): Coverage-mask generation still reads from
``librewxr.data.radar_stations`` for now.  Phase 2 of the sources
refactor migrates that consumer over to per-source ``stations.py``
files like this one; until then, the provider in ``__init__.py``
forwards these lists via ``RadarSourceContribution.stations`` for
future wiring but the legacy table is the live source.
"""
from __future__ import annotations


PENINSULAR_STATIONS: list[tuple[float, float]] = [
    (6.20, 100.40),    # MY2810 Alor Setar
    (5.47, 100.39),    # MY2819 Butterworth
    (2.04, 103.32),    # MY2818 Kluang
    (6.17, 102.29),    # MY2815 Kota Bharu
    (3.78, 103.21),    # MY2817 Kuantan
    (3.13, 101.55),    # MY2816 Subang
    (2.74, 101.71),    # MY2865 TDR KLIA
]

EAST_STATIONS: list[tuple[float, float]] = [
    (3.16, 113.05),    # MY2812 Bintulu
    (5.94, 116.05),    # MY2809 Kota Kinabalu
    (1.48, 110.34),    # MY2814 Kuching
    (4.32, 113.99),    # MY2813 Miri
    (5.90, 118.06),    # MY2811 Sandakan
]

STATIONS: list[tuple[float, float]] = PENINSULAR_STATIONS + EAST_STATIONS
