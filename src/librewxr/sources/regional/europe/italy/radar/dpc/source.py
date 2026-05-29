# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""DPC Italian national radar composite source.

Fetches VMI (Vertical Maximum Intensity) — a national dBZ composite
from 24 radars — via the open Radar-DPC v2 REST API at
``radar-api.protezionecivile.it``.

Two-step fetch protocol:

1. ``GET /findLastProductByType?type=VMI`` returns the most recent
   published timestamp (epoch ms).
2. ``POST /downloadProduct`` with ``{"productType":"VMI","productDate":<ms>}``
   returns a pre-signed S3 URL (300-900 s TTL) for the actual file.

The file is a Cloud-Optimized GeoTIFF (LZW, single-band Float32) at
1200×1400 px / 1 km in spherical Transverse Mercator centred on
(42°N, 12.5°E).  No-data is encoded as -9999.

Anonymous, no API key, CC-BY-SA 4.0 licensed.
"""
from __future__ import annotations

import asyncio
import io
import logging
import time
from datetime import datetime, timezone

import httpx
import numpy as np
import tifffile

from librewxr.data.regions import RegionDef
from librewxr.data.retry import retry_get
from librewxr.sources._helpers import _dbz_float_to_uint8

logger = logging.getLogger(__name__)


class DPCSource:
    """Radar-DPC v2 client for the Italian VMI national composite."""

    _PRODUCT_TYPE = "VMI"
    _CADENCE_SEC = 300         # DPC publishes every 5 min on the clock
    _MAX_FALLBACK_STEPS = 3    # try latest + 3 older slots (15 min lookback)
    _NO_DATA_THRESHOLD = -100.0  # any value < this (e.g. -9999, -9998) is masked

    def __init__(
        self,
        api_base: str = "https://radar-api.protezionecivile.it",
    ):
        self._api_base = api_base.rstrip("/")
        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        # Double-checked locking — the fetcher launches per-region
        # tasks in parallel, all of which may race to open the first
        # client.  Lock keeps us from leaking sockets on cold start.
        if self._client is not None and not self._client.is_closed:
            return self._client
        async with self._client_lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    timeout=httpx.Timeout(60.0, connect=15.0),
                    follow_redirects=True,
                )
            return self._client

    async def _get_latest_timestamp_ms(self) -> int | None:
        """Hit ``/findLastProductByType`` for the most recent published VMI."""
        client = await self._get_client()
        url = f"{self._api_base}/findLastProductByType?type={self._PRODUCT_TYPE}"
        resp = await retry_get(client, url, log_name="DPC findLast")
        if resp is None or resp.status_code != 200:
            return None
        try:
            payload = resp.json()
        except Exception:
            logger.exception("DPC findLastProductByType: bad JSON")
            return None
        products = payload.get("lastProducts") or []
        if not products:
            return None
        try:
            return int(products[0]["time"])
        except (KeyError, TypeError, ValueError):
            logger.warning("DPC findLastProductByType: missing/invalid time field")
            return None

    async def _resolve_download_url(self, timestamp_ms: int) -> str | None:
        """POST ``/downloadProduct`` → pre-signed S3 URL.

        Returns ``None`` if the upstream rejects the timestamp (typically
        because that 5-min slot isn't published yet) or any transport
        error occurs.  The caller's fallback loop walks earlier slots.
        """
        client = await self._get_client()
        url = f"{self._api_base}/downloadProduct"
        try:
            resp = await client.post(
                url,
                json={"productType": self._PRODUCT_TYPE, "productDate": timestamp_ms},
            )
        except httpx.TransportError as e:
            logger.warning("DPC downloadProduct transport error at ts=%d: %s",
                           timestamp_ms, e)
            return None
        if resp.status_code != 200:
            # 4xx/5xx are expected for slots that aren't published.  Don't log
            # every miss at WARNING — the fallback loop handles it.
            return None
        try:
            payload = resp.json()
        except Exception:
            logger.exception("DPC downloadProduct: bad JSON")
            return None
        if "error" in payload:
            return None
        return payload.get("url")

    async def fetch_frame(
        self, region: RegionDef, minutes_ago: int
    ) -> np.ndarray | None:
        """Fetch a recent frame.

        ``minutes_ago=0`` → ask the API for the most recent published
        slot directly (avoids the publish-lag race entirely).  Any
        other value rounds to the matching 5-min clock boundary.
        """
        if minutes_ago == 0:
            target_ms = await self._get_latest_timestamp_ms()
            if target_ms is None:
                return None
        else:
            now_rounded_sec = (
                int(time.time() // self._CADENCE_SEC) * self._CADENCE_SEC
            )
            target_sec = now_rounded_sec - minutes_ago * 60
            target_sec = (target_sec // self._CADENCE_SEC) * self._CADENCE_SEC
            target_ms = target_sec * 1000
        return await self._fetch_with_fallback(region, target_ms)

    async def fetch_archive_frame(
        self, region: RegionDef, dt: datetime
    ) -> np.ndarray | None:
        """Fetch a frame at a specific timestamp (rounded to 5-min boundary)."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        target_sec = int(dt.timestamp())
        target_sec = (target_sec // self._CADENCE_SEC) * self._CADENCE_SEC
        return await self._fetch_with_fallback(region, target_sec * 1000)

    async def _fetch_with_fallback(
        self, region: RegionDef, target_ms: int
    ) -> np.ndarray | None:
        """Try ``target_ms``, walking back 5 min/step on miss."""
        client = await self._get_client()
        for step in range(self._MAX_FALLBACK_STEPS + 1):
            ts_ms = target_ms - step * self._CADENCE_SEC * 1000
            url = await self._resolve_download_url(ts_ms)
            if url is None:
                continue
            resp = await retry_get(client, url, log_name="DPC TIFF")
            if resp is None or resp.status_code != 200:
                continue
            arr = _decode_vmi_dbz(resp.content)
            if arr is None:
                continue
            if arr.shape != (region.height, region.width):
                logger.warning(
                    "DPC TIFF shape %s != region %s (%s × %s)",
                    arr.shape, region.name, region.height, region.width,
                )
                return None
            if step > 0:
                logger.debug("DPC fallback succeeded at step %d (ts %d)", step, ts_ms)
            return arr
        return None

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()


def _decode_vmi_dbz(tiff_bytes: bytes) -> np.ndarray | None:
    """Decode a DPC VMI GeoTIFF into uint8 dBZ.

    Float32 reflectivity with sentinel ``-9999`` (and occasionally
    ``-9998`` — both safely below ``-100``) for pixels outside radar
    coverage or below the receiver noise floor.  Sentinels are mapped
    below ``-32`` so the project encoding ``(dBZ + 32) * 2`` lands them
    at zero (fully transparent across every colour scheme).
    """
    try:
        arr = tifffile.imread(io.BytesIO(tiff_bytes))
    except Exception:
        logger.exception("Failed to decode DPC VMI TIFF")
        return None
    if arr.ndim != 2:
        logger.warning("DPC VMI TIFF has unexpected ndim %d (expected 2)", arr.ndim)
        return None
    if arr.dtype != np.float32:
        arr = arr.astype(np.float32, copy=False)
    sentinel = arr < DPCSource._NO_DATA_THRESHOLD
    if sentinel.any():
        arr = np.where(sentinel, -33.0, arr)
    return _dbz_float_to_uint8(arr)
