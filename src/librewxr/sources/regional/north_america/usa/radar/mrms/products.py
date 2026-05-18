# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""MRMS MergedReflectivityQCComposite product paths and grid extents.

Each US territory has its own MRMS regional product on the NCEP server.
USCOMP and CACOMP share the bare CONUS path (MRMS's CONUS product
covers both — Canada gets ingested via a separate processing step on
NCEP's side, and the same GRIB2 carries both extents).
"""
from __future__ import annotations


MRMS_PRODUCTS: dict[str, str] = {
    "USCOMP": "MergedReflectivityQCComposite",
    "CACOMP": "MergedReflectivityQCComposite",
    "AKCOMP": "ALASKA/MergedReflectivityQCComposite",
    "HICOMP": "HAWAII/MergedReflectivityQCComposite",
    "PRCOMP": "CARIB/MergedReflectivityQCComposite",
    "GUCOMP": "GUAM/MergedReflectivityQCComposite",
}

# MRMS grid extents per region (south, north, west, east) in degrees.
# These match the actual GRIB2 grid bounds from NCEP.  Cross-source
# blending (CACOMP MRMS+MSC in ``data/fetcher.py::_blend_cacomp``)
# imports the USCOMP entry directly to mask the MRMS extent inside the
# blended CACOMP frame.
MRMS_EXTENTS: dict[str, tuple[float, float, float, float]] = {
    "USCOMP": (20.005, 54.995, -129.995, -60.005),
    "CACOMP": (20.005, 54.995, -129.995, -60.005),
    "AKCOMP": (50.005, 71.995, -175.995, -126.005),
    "HICOMP": (15.002, 25.997, -163.998, -151.002),
    "PRCOMP": (10.005, 24.995, -89.995, -60.005),
    "GUCOMP": (9.002, 17.997, 140.002, 149.998),
}
