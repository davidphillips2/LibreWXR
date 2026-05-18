# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""USA (NEXRAD-fed) sources.

Both IEM (live + archive N0Q PNGs) and MRMS (NCEP GRIB composites)
serve the same set of US regions, so the canonical region definitions
and NEXRAD station inventory live one level down at
``usa/radar/`` and the per-source packages re-use them.
"""
