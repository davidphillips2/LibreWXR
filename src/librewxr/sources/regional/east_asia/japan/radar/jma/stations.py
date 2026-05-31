# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""JMA C-band Doppler radar station locations.

20 operational sites covering Japan.  Kept for documentation /
coverage-map purposes only — JPCOMP is intentionally NOT registered
in ``STATION_MAP`` (see below).

Station coordinates from the JMA Observations page
(``www.jma.go.jp/jma/en/Activities/observations.html``).  XRAIN X-band
sites are not listed here — they're fused into HRPN upstream and don't
need separate mask handling.

Why JPCOMP has no station mask:
HRPN is JMA's gauge-corrected QPE composite — it fuses the 20 C-band
Doppler radars with XRAIN X-band radars and the AMeDAS rain-gauge
network into one product whose published extent extends well past
individual Doppler reach.  A 240 km station-circle union dramatically
under-represents the real product footprint, so anywhere offshore
where HRPN genuinely has data falls outside the union mask and the
renderer's NWP-fill path paints model precipitation on top of the
radar pixels.  The clean fix is to skip the station-circle mask
entirely (same convention used by MRMS-style fused composites) and
let ``data/coverage.py`` fall back to "full region bbox = covered"
inside the JPCOMP rectangle.  See ``sample_coverage`` for the
fallback semantics.
"""
from __future__ import annotations


# (latitude, longitude) — 20 JMA C-band Doppler radars.  Documentation
# only; consumed by the coverage-map script (``scripts/generate_coverage_map.py``)
# but NOT by the runtime coverage mask builder.
STATIONS: list[tuple[float, float]] = [
    (43.063, 141.349),   # Sapporo (Ishikari)
    (43.910, 144.069),   # Kitami (Mombetsu area)
    (42.998, 144.494),   # Kushiro
    (41.775, 140.739),   # Hakodate
    (40.190, 140.797),   # Akita
    (38.262, 140.902),   # Sendai
    (37.392, 138.616),   # Niigata
    (36.069, 139.769),   # Tokyo (Kashiwa)
    (35.243, 138.973),   # Mt. Fuji (Shizuoka)
    (35.180, 136.906),   # Nagoya (Komaki)
    (34.694, 135.502),   # Osaka (Tanigawa)
    (35.452, 133.066),   # Matsue
    (34.013, 131.067),   # Hiroshima (Sera)
    (33.595, 130.451),   # Fukuoka
    (32.745, 129.866),   # Nagasaki (Seburi)
    (32.749, 132.949),   # Muroto Cape (Kochi)
    (31.790, 130.393),   # Kagoshima (Tanegashima)
    (28.380, 129.547),   # Naze (Amami Oshima)
    (26.205, 127.687),   # Naha (Okinawa main)
    (24.453, 122.951),   # Yonaguni (westernmost Ryukyu)
]


# Empty intentionally — see module docstring above.  The empty dict
# leaves JPCOMP out of ``_COVERAGE_MASKS`` so ``sample_coverage``
# returns the full-region-bbox fallback.
STATION_MAP: dict[str, list[tuple[float, float]]] = {}

# Empty intentionally — no per-station range overrides apply when no
# station mask is registered in the first place.
RANGE_OVERRIDES: dict[str, dict[tuple[float, float], float]] = {}
