# IEM NEXRAD N0Q composite

NEXRAD `N0Q` Level III composites compiled by the **Iowa Environmental
Mesonet (IEM)** and served as palette-indexed PNGs from
`mesonet.agron.iastate.edu`.  Same encoding LibreWXR uses internally
(`(dBZ + 32) * 2`), so decode is a one-step palette-index extract — no
RGB-to-dBZ palette lookup required.

## Coverage

| Region   | Footprint                                        |
| -------- | ------------------------------------------------ |
| `USCOMP` | Continental US                                   |
| `AKCOMP` | Alaska                                           |
| `HICOMP` | Hawaii                                           |
| `PRCOMP` | Puerto Rico + Virgin Islands                     |
| `GUCOMP` | Guam + Northern Marianas                         |

All 5 regions share one `IEMSource` instance — one HTTP client, one
retry policy.  Region definitions and NEXRAD station inventory live at
`sources/regional/north_america/usa/radar/` because MRMS uses the same
set; this package contributes the IEM-specific source + provider.

## Cadence & latency

- Live endpoint: rolling 12 frames at 5-min cadence
  (`n0q_{0..11}.png`) → 0–55 min of recent data.
- Archive endpoint: per-frame PNGs at clock-aligned 5-min slots,
  reachable years back.

## Role in the dispatch

The IEM provider returns a contribution only when
`settings.na_source == "iem"` — the legacy single-source NA profile.
Other NA profiles:

- `mrms` — MRMS owns the slot; IEM is unused.
- `mrms_fallback` (default) — MRMS owns the slot; IEM is reached only
  via `_iem_fallback` in `data/fetcher.py` when MRMS misses.  The
  fallback is wired by direct import, not through the discovery loop.

## License & attribution

IEM N0Q composites are in the public domain (NOAA NEXRAD Level III
`N0Q` products compiled by IEM).  Attribution is a courtesy — see the
top-level `README.md` and `docs/coverage.md`.

## Stations

132 CONUS + 7 Alaska + 4 Hawaii + 1 Puerto Rico + 1 Guam.  Full list
lives in the shared `sources/regional/north_america/usa/radar/stations.py`.
