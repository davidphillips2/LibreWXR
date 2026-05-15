# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
import io
from datetime import datetime, timezone

import numpy as np
import pytest
from PIL import Image

pytestmark = pytest.mark.sources

from librewxr.data.regions import REGIONS, RegionDef, resolve_regions
from librewxr.data.sources import (
    MSSSource,
    _decode_mss_png,
    _MSS_PALETTE,
)
from librewxr.tiles.coordinates import tile_overlaps_region


class TestSeacompRegion:
    def test_seacomp_in_regions(self):
        assert "SEACOMP" in REGIONS

    def test_seacomp_group_and_proj(self):
        r = REGIONS["SEACOMP"]
        assert r.proj == "latlon"
        assert r.group == "SOUTHEAST_ASIA"

    def test_seacomp_bounds_around_changi(self):
        # Bounds are derived from MSS Changi radar (1.3521°N, 103.8198°E)
        # ± 4.32° (~480 km).  These must straddle the radar; if the
        # values drift the renderer will mis-register coastlines.
        r = REGIONS["SEACOMP"]
        assert r.west < 103.8198 < r.east
        assert r.south < 1.3521 < r.north
        # ~8.64° span on each axis (480 km × 2).
        assert abs((r.east - r.west) - 8.64) < 0.1
        assert abs((r.north - r.south) - 8.64) < 0.1

    def test_seacomp_dimensions(self):
        r = REGIONS["SEACOMP"]
        # Native 480 km product is 480×480 — fixed grid dimensions avoid
        # pixel-size fencepost rounding ambiguity.
        assert r.width == 480
        assert r.height == 480

    def test_southeast_asia_group_resolution(self):
        assert resolve_regions("SOUTHEAST_ASIA") == ["SEACOMP"]

    def test_all_includes_seacomp(self):
        assert "SEACOMP" in resolve_regions("ALL")


class TestUrlForTimestamp:
    def _src(self) -> MSSSource:
        return MSSSource("https://example.test/files/rainarea/480km")

    def test_rounds_down_to_30_min_boundary(self):
        # 2026-05-15 10:47:32 UTC → 10:30 slot
        src = self._src()
        ts = int(datetime(2026, 5, 15, 10, 47, 32, tzinfo=timezone.utc).timestamp())
        url = src._url_for_timestamp(ts)
        assert url.endswith("dpsri_480km_2026051510300000dBR.dpsri.png"), url

    def test_exact_boundary_kept(self):
        src = self._src()
        ts = int(datetime(2026, 5, 15, 10, 30, 0, tzinfo=timezone.utc).timestamp())
        url = src._url_for_timestamp(ts)
        assert url.endswith("dpsri_480km_2026051510300000dBR.dpsri.png")

    def test_top_of_hour_kept(self):
        src = self._src()
        ts = int(datetime(2026, 5, 15, 11, 0, 0, tzinfo=timezone.utc).timestamp())
        url = src._url_for_timestamp(ts)
        assert url.endswith("dpsri_480km_2026051511000000dBR.dpsri.png")

    def test_base_url_is_preserved(self):
        src = self._src()
        ts = int(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        assert src._url_for_timestamp(ts).startswith(
            "https://example.test/files/rainarea/480km/"
        )

    def test_trailing_slash_stripped(self):
        src = MSSSource("https://example.test/dir/")
        ts = int(datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
        # Should not produce a double-slash in the path.
        assert "//" not in src._url_for_timestamp(ts).split("://", 1)[1]


class TestPaletteDecode:
    """The 480 km MSS PNG uses a discrete 31-stop palette; the decoder
    snaps each opaque pixel to its nearest anchor in RGB space and maps
    the rank to dBZ via the ``_MSS_PALETTE`` table."""

    def _fake_region(self, w: int) -> RegionDef:
        # SEACOMP's full shape isn't needed for decode-correctness tests,
        # but the decoder logs a shape-mismatch warning.  Build a tiny
        # stand-in region matching the test PNG.
        return RegionDef(
            name="SEACOMP", west=0.0, east=1.0, south=0.0, north=1.0,
            pixel_size=1.0, group="SOUTHEAST_ASIA",
            grid_width=w, grid_height=1,
        )

    def _make_png(self, pixels: list[tuple[int, int, int, int]]) -> bytes:
        arr = np.array([pixels], dtype=np.uint8)
        img = Image.fromarray(arr, mode="RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _expected_uint8(self, dbz: float) -> int:
        # Match _dbz_float_to_uint8: clip then astype(uint8), which
        # truncates rather than rounding.
        return int(np.clip((dbz + 32.0) * 2.0, 0, 255).astype(np.uint8))

    def test_transparent_is_no_data(self):
        png = self._make_png([(0, 0, 0, 0)])
        out = _decode_mss_png(png, self._fake_region(1))
        assert out is not None
        assert out.shape == (1, 1)
        assert out[0, 0] == 0

    def test_each_palette_stop_decodes_to_expected_dbz(self):
        pixels = [(r, g, b, 255) for r, g, b, _ in _MSS_PALETTE]
        png = self._make_png(pixels)
        out = _decode_mss_png(png, self._fake_region(len(pixels)))
        assert out is not None
        for i, (_, _, _, dbz) in enumerate(_MSS_PALETTE):
            assert out[0, i] == self._expected_uint8(dbz), (
                f"stop {i} dBZ={dbz} decoded wrong"
            )

    def test_intensity_monotonic_across_palette(self):
        # The palette is ordered by intensity; uint8 dBZ output should
        # rise monotonically through the table.
        pixels = [(r, g, b, 255) for r, g, b, _ in _MSS_PALETTE]
        png = self._make_png(pixels)
        out = _decode_mss_png(png, self._fake_region(len(pixels)))
        diffs = np.diff(out[0].astype(int))
        assert np.all(diffs > 0), f"non-monotonic palette decode: {out[0]}"

    def test_near_anchor_within_tolerance_snaps(self):
        # A pixel within the tolerance should snap to the nearest anchor.
        # First palette stop is (0, 239, 239, dBZ=5).  Perturb by ±1.
        r, g, b, dbz = _MSS_PALETTE[0]
        png = self._make_png([(r + 1, g - 1, b + 1, 255)])
        out = _decode_mss_png(png, self._fake_region(1))
        assert out[0, 0] == self._expected_uint8(dbz)

    def test_off_palette_color_is_no_data(self):
        # Pure black (0,0,0) sits far from every cyan/green/yellow/red/
        # magenta anchor (closest is (0,128,69) ≈ 21 RGB units, dist²
        # ≈ 21000 — well past the 64 tolerance).
        png = self._make_png([(0, 0, 0, 255)])
        out = _decode_mss_png(png, self._fake_region(1))
        assert out[0, 0] == 0

    def test_bad_png_returns_none(self):
        assert _decode_mss_png(b"not a png", self._fake_region(1)) is None


class TestSeacompTileOverlap:
    def test_tile_over_strait_of_malacca_overlaps(self):
        region = REGIONS["SEACOMP"]
        # z=6, x=50, y=31 covers roughly Singapore / Sumatra.
        assert tile_overlaps_region(region, z=6, x=50, y=31)

    def test_tile_over_europe_does_not_overlap(self):
        region = REGIONS["SEACOMP"]
        # z=4, x=8, y=5 is over central Europe — no overlap.
        assert not tile_overlaps_region(region, z=4, x=8, y=5)
