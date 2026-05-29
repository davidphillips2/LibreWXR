# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Tests for FrameStore accessors used by the nowcast pipeline."""
import numpy as np
import pytest

pytestmark = pytest.mark.store

from librewxr.data.store import FrameStore, RadarFrame


def _frame(ts: int, region: str = "USCOMP", h: int = 8, w: int = 8) -> RadarFrame:
    return RadarFrame(timestamp=ts, regions={region: np.zeros((h, w), dtype=np.uint8)})


class TestGetLastNFrames:
    async def test_empty_store_returns_empty(self):
        store = FrameStore(max_frames=12)
        assert await store.get_last_n_frames(3) == []

    async def test_zero_or_negative_n_returns_empty(self):
        store = FrameStore(max_frames=12)
        await store.add_frame(_frame(1000))
        assert await store.get_last_n_frames(0) == []
        assert await store.get_last_n_frames(-1) == []

    async def test_returns_all_when_fewer_than_n(self):
        store = FrameStore(max_frames=12)
        await store.add_frame(_frame(1000))
        await store.add_frame(_frame(2000))
        result = await store.get_last_n_frames(5)
        assert [f.timestamp for f in result] == [1000, 2000]

    async def test_returns_exactly_n_when_more_available(self):
        store = FrameStore(max_frames=12)
        for ts in (1000, 2000, 3000, 4000, 5000):
            await store.add_frame(_frame(ts))
        result = await store.get_last_n_frames(3)
        assert [f.timestamp for f in result] == [3000, 4000, 5000]

    async def test_chronological_order(self):
        # Insert out of order — store should still return ascending.
        store = FrameStore(max_frames=12)
        for ts in (3000, 1000, 5000, 2000, 4000):
            await store.add_frame(_frame(ts))
        result = await store.get_last_n_frames(3)
        assert [f.timestamp for f in result] == [3000, 4000, 5000]

    async def test_result_is_snapshot_not_view(self):
        # Mutating the returned list must not affect the store.
        store = FrameStore(max_frames=12)
        for ts in (1000, 2000, 3000):
            await store.add_frame(_frame(ts))
        result = await store.get_last_n_frames(3)
        result.clear()
        assert await store.frame_count() == 3
