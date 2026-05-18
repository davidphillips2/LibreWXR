# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Region definition for the OPERA pan-European composite.

LAEA projection: ``+proj=laea +lat_0=55 +lon_0=10 +x_0=1950000
+y_0=-2100000 +ellps=WGS84``.  Native 3800×4400 at 1 km, 5-minute
cadence, ODIM HDF5 with float64 dBZ values.

The bbox is trimmed to the actual European radar network extent
(Iceland–Turkey, southern Mediterranean–northern Scandinavia) rather
than the full LAEA grid — keeps the projected-pixel bookkeeping aligned
with the data we actually have.
"""
from __future__ import annotations

from librewxr.data.regions import RegionDef


OPERA = RegionDef(
    name="OPERA",
    west=-25.0, east=45.0, south=34.0, north=72.0,
    pixel_size=0.01, group="EUROPE",
    proj="laea",
    laea_lat0=55.0, laea_lon0=10.0,
    laea_x0=1950000.0, laea_y0=-2100000.0,
    grid_x_min=0.0, grid_y_max=0.0, grid_scale=1000.0,
    grid_width=3800, grid_height=4400,
)

REGIONS: list[RegionDef] = [OPERA]
