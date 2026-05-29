# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
import io
from datetime import datetime, timezone

import httpx
import numpy as np
import pytest
import tifffile

pytestmark = pytest.mark.sources

from librewxr.data.regions import REGIONS, RegionDef, resolve_regions
from librewxr.sources.regional.europe.italy.radar.dpc import (
    DPCSource,
    ITCOMP,
    _decode_vmi_dbz,
)
from librewxr.tiles.coordinates import (
    _tmerc_forward,
    overlapping_regions,
    tile_overlaps_region,
)


class TestItcompRegion:
    def test_itcomp_in_regions(self):
        assert "ITCOMP" in REGIONS

    def test_itcomp_proj_and_group(self):
        r = REGIONS["ITCOMP"]
        assert r.proj == "tmerc"
        assert r.group == "EUROPE"

    def test_itcomp_tmerc_params(self):
        # Match the DPC GeoTIFF's GeoKeys (ModelTiepoint / GeoDoubleParams).
        r = REGIONS["ITCOMP"]
        assert r.tmerc_lat0 == 42.0
        assert r.tmerc_lon0 == 12.5
        assert r.tmerc_radius == 6371229.0
        assert r.tmerc_k0 == 1.0

    def test_itcomp_dimensions(self):
        r = REGIONS["ITCOMP"]
        assert r.width == 1200
        assert r.height == 1400
        assert r.grid_scale == 1000.0

    def test_itcomp_grid_origin(self):
        # ModelTiepoint sets the projected coords of pixel (0, 0).
        r = REGIONS["ITCOMP"]
        assert r.grid_x_min == -600000.0
        assert r.grid_y_max == 650000.0

    def test_europe_group_includes_itcomp(self):
        assert "ITCOMP" in resolve_regions("EUROPE")
        # OPERA also stays in the group.
        assert "OPERA" in resolve_regions("EUROPE")

    def test_all_includes_itcomp(self):
        assert "ITCOMP" in resolve_regions("ALL")


class TestTmercProjection:
    """Validate _tmerc_forward against pyproj-confirmed reference values.

    Reference values produced from
    ``+proj=tmerc +lat_0=42 +lon_0=12.5 +R=6371229 +no_defs`` — see
    the smoke-test in the DPC implementation notes.
    """

    def test_center_maps_to_origin(self):
        x, y = _tmerc_forward(np.array(12.5), np.array(42.0), ITCOMP)
        assert abs(float(x)) < 1e-6
        assert abs(float(y)) < 1e-6

    @pytest.mark.parametrize("lon,lat,exp_x,exp_y", [
        # UL corner — DMS 4°31'24"E, 47°34'15"N from the upstream docs
        ( 4.52333, 47.57083, -598258.5,  650303.7),
        # LR corner — DMS 19°04'22"E, 35°03'54"N
        (19.07278, 35.06500,  598675.4, -751385.8),
        ( 8.000, 45.500, -350725.0,  399029.8),   # NW Italy (Piedmont)
        (14.300, 40.800,  151522.3, -131883.2),   # Naples
    ])
    def test_known_lat_lon_pairs(self, lon, lat, exp_x, exp_y):
        x, y = _tmerc_forward(np.array(lon), np.array(lat), ITCOMP)
        # Reference values were generated at one-decimal-of-a-metre precision.
        assert abs(float(x) - exp_x) < 1.0
        assert abs(float(y) - exp_y) < 1.0


class TestItcompPrecedence:
    """ITCOMP's pixel_size (0.009) must sort below OPERA's (0.01) so the
    multi-region compositor lays ITCOMP down first over Italy.  See
    ``tiles/coordinates.overlapping_regions`` — sorts ascending by
    ``pixel_size``."""

    @pytest.mark.parametrize("z,x,y,label", [
        (5, 16, 11, "NW Italy"),
        (6, 33, 22, "Piedmont"),
        (5, 17, 12, "Central Italy"),
    ])
    def test_itcomp_first_over_italy(self, z, x, y, label):
        regs = overlapping_regions(z, x, y, enabled=["OPERA", "ITCOMP"])
        names = [r.name for r in regs]
        assert names[0] == "ITCOMP", f"{label}: expected ITCOMP first, got {names}"
        assert "OPERA" in names, f"{label}: OPERA should still be present"


class TestVmiDecoder:
    """``_decode_vmi_dbz`` reads a tifffile-compatible Float32 GeoTIFF and
    encodes to uint8 via the project's canonical (dBZ + 32) * 2 formula,
    masking the -9999 / -9998 no-data sentinels."""

    @staticmethod
    def _make_tiff(arr: np.ndarray, compression: str | None = None) -> bytes:
        """Encode a 2-D Float32 array as a TIFF and return the bytes."""
        buf = io.BytesIO()
        tifffile.imwrite(buf, arr.astype(np.float32), compression=compression)
        return buf.getvalue()

    def test_basic_float_dbz_roundtrip(self):
        # 10 dBZ → uint8 (10+32)*2 = 84
        # 30 dBZ → uint8 (30+32)*2 = 124
        # 50 dBZ → uint8 (50+32)*2 = 164
        arr = np.array([[10.0, 30.0, 50.0]], dtype=np.float32)
        out = _decode_vmi_dbz(self._make_tiff(arr))
        assert out is not None
        assert out.dtype == np.uint8
        assert out.shape == (1, 3)
        assert out[0, 0] == 84
        assert out[0, 1] == 124
        assert out[0, 2] == 164

    def test_no_data_sentinel_masked(self):
        # -9999 and -9998 both sit below the -100 threshold and should
        # land at pixel value 0 (fully transparent).
        arr = np.array([[-9999.0, -9998.0, 25.0]], dtype=np.float32)
        out = _decode_vmi_dbz(self._make_tiff(arr))
        assert out[0, 0] == 0
        assert out[0, 1] == 0
        # 25 dBZ → (25+32)*2 = 114
        assert out[0, 2] == 114

    def test_lzw_compressed_tiff_decodes(self):
        # The real DPC product uses LZW.  imagecodecs must be available
        # at install time; verify the path works end-to-end.
        arr = np.full((10, 10), 35.0, dtype=np.float32)
        out = _decode_vmi_dbz(self._make_tiff(arr, compression="LZW"))
        assert out is not None
        assert out.shape == (10, 10)
        # 35 dBZ → (35+32)*2 = 134
        assert np.all(out == 134)

    def test_below_threshold_dbz_clamped_to_zero(self):
        # dBZ values at or below -32 encode to 0 (the colorize layer's
        # transparent floor) — same convention as every other source.
        arr = np.array([[-32.0, -50.0]], dtype=np.float32)
        out = _decode_vmi_dbz(self._make_tiff(arr))
        assert out[0, 0] == 0
        assert out[0, 1] == 0

    def test_high_dbz_clamped_to_255(self):
        # Anything ≥ ((255 / 2) - 32) = 95.5 dBZ saturates at pixel 255.
        arr = np.array([[95.0, 200.0]], dtype=np.float32)
        out = _decode_vmi_dbz(self._make_tiff(arr))
        # 95 dBZ → (95+32)*2 = 254
        assert out[0, 0] == 254
        assert out[0, 1] == 255

    def test_bad_tiff_returns_none(self):
        assert _decode_vmi_dbz(b"not a tiff") is None

    def test_rgb_tiff_rejected(self):
        # An RGB TIFF (3-D array) should be rejected — the decoder
        # expects a single-band reflectivity raster.
        arr = np.zeros((4, 4, 3), dtype=np.uint8)
        buf = io.BytesIO()
        tifffile.imwrite(buf, arr, photometric="rgb")
        out = _decode_vmi_dbz(buf.getvalue())
        assert out is None


class TestDpcSource:
    """End-to-end DPCSource exercising the two-step REST protocol via
    ``httpx.MockTransport`` — no live network."""

    @staticmethod
    def _vmi_tiff(arr: np.ndarray) -> bytes:
        buf = io.BytesIO()
        tifffile.imwrite(buf, arr.astype(np.float32), compression="LZW")
        return buf.getvalue()

    def _make_source(self, transport: httpx.MockTransport) -> DPCSource:
        src = DPCSource(api_base="https://radar-api.test")
        src._client = httpx.AsyncClient(transport=transport)
        return src

    async def test_get_latest_timestamp(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/findLastProductByType"
            assert request.url.params["type"] == "VMI"
            return httpx.Response(200, json={
                "total": 1,
                "lastProducts": [
                    {"productType": "VMI", "time": 1780020900000, "period": "PT5M"},
                ],
            })

        src = self._make_source(httpx.MockTransport(handler))
        try:
            assert await src._get_latest_timestamp_ms() == 1780020900000
        finally:
            await src.close()

    async def test_get_latest_handles_empty_response(self):
        def handler(request):
            return httpx.Response(200, json={"total": 0, "lastProducts": []})
        src = self._make_source(httpx.MockTransport(handler))
        try:
            assert await src._get_latest_timestamp_ms() is None
        finally:
            await src.close()

    async def test_resolve_download_url(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert request.url.path == "/downloadProduct"
            return httpx.Response(200, json={
                "bucket": "dpc-radar",
                "key": "VMI/29-05-2026-02-15.tif",
                "url": "https://s3.example.com/signed?token=xyz",
                "expiresSeconds": 900,
            })
        src = self._make_source(httpx.MockTransport(handler))
        try:
            url = await src._resolve_download_url(1780020900000)
            assert url == "https://s3.example.com/signed?token=xyz"
        finally:
            await src.close()

    async def test_resolve_download_url_returns_none_on_error_json(self):
        def handler(request):
            return httpx.Response(200, json={"error": "productType non supportato"})
        src = self._make_source(httpx.MockTransport(handler))
        try:
            assert await src._resolve_download_url(1780020900000) is None
        finally:
            await src.close()

    async def test_fetch_archive_frame_happy_path(self):
        # Synthesize a 1200×1400 raster with a known dBZ patch.
        arr = np.full((ITCOMP.height, ITCOMP.width), -9999.0, dtype=np.float32)
        arr[100:110, 100:110] = 30.0
        tiff_bytes = self._vmi_tiff(arr)

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/downloadProduct":
                return httpx.Response(200, json={"url": "https://s3.test/signed"})
            if request.url.host == "s3.test":
                return httpx.Response(200, content=tiff_bytes)
            return httpx.Response(404)

        src = self._make_source(httpx.MockTransport(handler))
        try:
            out = await src.fetch_archive_frame(
                ITCOMP, datetime(2026, 5, 28, 21, 35, tzinfo=timezone.utc),
            )
        finally:
            await src.close()

        assert out is not None
        assert out.shape == (ITCOMP.height, ITCOMP.width)
        # 30 dBZ → (30+32)*2 = 124 in the patch; -9999 → 0 elsewhere.
        assert out[105, 105] == 124
        assert out[0, 0] == 0

    async def test_fetch_walks_back_when_slot_missing(self):
        attempts: list[int] = []

        # Provide a valid TIFF for the third request, miss the first two.
        arr = np.full((ITCOMP.height, ITCOMP.width), 20.0, dtype=np.float32)
        tiff_bytes = self._vmi_tiff(arr)

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/downloadProduct":
                body = request.read().decode()
                # Crude but sufficient for the test.
                import json as _json
                ts = _json.loads(body)["productDate"]
                attempts.append(ts)
                # Reject first two attempts with the "error" envelope.
                if len(attempts) < 3:
                    return httpx.Response(200, json={"error": "non disponibile"})
                return httpx.Response(200, json={"url": "https://s3.test/signed"})
            if request.url.host == "s3.test":
                return httpx.Response(200, content=tiff_bytes)
            return httpx.Response(404)

        src = self._make_source(httpx.MockTransport(handler))
        try:
            out = await src.fetch_archive_frame(
                ITCOMP, datetime(2026, 5, 28, 21, 35, tzinfo=timezone.utc),
            )
        finally:
            await src.close()

        assert out is not None
        # The three attempts must descend in 5-minute steps.
        assert len(attempts) == 3
        for i in range(1, len(attempts)):
            assert attempts[i] == attempts[i - 1] - 300 * 1000

    async def test_fetch_returns_none_after_all_fallbacks_fail(self):
        def handler(request):
            if request.url.path == "/downloadProduct":
                return httpx.Response(200, json={"error": "non disponibile"})
            return httpx.Response(404)
        src = self._make_source(httpx.MockTransport(handler))
        try:
            out = await src.fetch_archive_frame(
                ITCOMP, datetime(2026, 5, 28, 21, 35, tzinfo=timezone.utc),
            )
            assert out is None
        finally:
            await src.close()


class TestItcompTileOverlap:
    def test_tile_over_italy_overlaps(self):
        # z=5 x=16 y=11 covers roughly north-central Italy.
        assert tile_overlaps_region(REGIONS["ITCOMP"], z=5, x=16, y=11)

    def test_tile_over_us_does_not_overlap(self):
        assert not tile_overlaps_region(REGIONS["ITCOMP"], z=4, x=4, y=6)

    def test_tile_over_arctic_does_not_overlap(self):
        # z=3 x=4 y=1 is high-arctic — well north of Italy.
        assert not tile_overlaps_region(REGIONS["ITCOMP"], z=3, x=4, y=1)
