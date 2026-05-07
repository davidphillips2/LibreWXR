# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey

import threading
import time
from dataclasses import dataclass
from typing import Optional

from shapely.geometry import Polygon


@dataclass
class AlertEntry:
    """Parsed CAP alert with optional polygon geometry."""
    source_id: str
    event: str
    description: str
    severity: str
    effective: str
    expires: str
    area_desc: str
    url: str
    polygon: Optional[Polygon] = None


class AlertsStore:
    """Thread-safe in-memory store of active weather alerts."""

    def __init__(self):
        self._lock = threading.RLock()
        self._alerts: list[AlertEntry] = []
        self.last_updated: float = 0.0
        self._fetch_success: bool = False

    @property
    def alerts(self) -> list[AlertEntry]:
        with self._lock:
            return list(self._alerts)

    def replace_all(self, alerts: list[AlertEntry]) -> None:
        with self._lock:
            self._alerts = alerts
            self.last_updated = time.time()
            self._fetch_success = True

    def mark_failed(self) -> None:
        with self._lock:
            self._fetch_success = False

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._alerts)

    @property
    def fetch_success(self) -> bool:
        with self._lock:
            return self._fetch_success
