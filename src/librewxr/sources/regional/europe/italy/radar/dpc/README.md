# DPC Italy Radar Composite (VMI)

Italian national reflectivity composite from the
**Dipartimento della Protezione Civile** (DPC), accessed via the open
Radar-DPC v2 REST API at `radar-api.protezionecivile.it`.

## Coverage

- **Region:** `ITCOMP` (group `EUROPE`)
- **Native grid:** 1200 × 1400 px, 1 km resolution, spherical
  Transverse Mercator (`lat_0 = 42°N`, `lon_0 = 12.5°E`,
  `R = 6371229 m`, `k_0 = 1`)
- **Geographic extent:** ≈ (35.08°N, 4.50°E) to (47.57°N, 19.09°E) —
  Italy + a buffer into S. France, S. Switzerland, S. Austria,
  W. Slovenia/Croatia, Tunisia coast, Sardinia, Sicily.
- **Cadence:** 5 min (DPC); LibreWXR samples every 10 min on the clock.

## Source network

24 radars total:

- **11 DPC-direct** (Table 1 of Allegato 1 of the *Rete Radar
  Meteorologica Nazionale*): 7 C-band Gematronik Meteor 600 C, 4
  X-band Gematronik Meteor 50 DX. Coordinates verbatim from that
  document.
- **13 partner radars** (Table 2): ARPA regional networks (Piemonte,
  Liguria, Emilia-Romagna, Veneto, FVG, Abruzzo, Sardegna), PAA
  Trento, ENAV (Linate, Fiumicino), Aeronautica Militare (Capocaccia).
  Coordinates from publicly-known site locations; accurate to a few
  hundred metres.

## API protocol

Anonymous, no API key, no session bootstrap.

1. `GET /findLastProductByType?type=VMI` → JSON with the latest
   published `time` (epoch ms).
2. `POST /downloadProduct` with body
   `{"productType":"VMI","productDate":<epoch_ms>}` → JSON with a
   pre-signed S3 URL (300–900 s TTL).
3. `GET <presigned_url>` → Cloud-Optimized GeoTIFF (LZW, single-band
   Float32). No-data sentinel: `-9999`.

Decoded to uint8 dBZ via `(dBZ + 32) × 2`, clamped to `[0, 255]`.

## License

**Creative Commons Attribution-ShareAlike 4.0 (CC-BY-SA 4.0).**

Commercial use, modification, and redistribution are all permitted
provided that:

- The source is credited as **"Radar-DPC"**.
- Derivative works (modified data, including resampled tiles) are
  released under the **same** CC-BY-SA terms.

This is the strictest license in LibreWXR's source stack — every
other radar/satellite/NWP source is permissive (MIT-style, Etalab,
OGDL, or simple attribution-only). Operators serving ITCOMP-derived
tiles must surface the CC-BY-SA inheritance to their downstream
consumers.

## Why this source exists

Italy is **not** in the EUMETNET OPERA station list, so the
pan-European OPERA layer over Italian airspace consists entirely of
edge-of-range data from neighbouring radars (France Côte d'Azur,
Switzerland, Slovenia, southern Germany, Croatia, Malta). At those
ranges the beam is wide, the SNR is poor, and ground-clutter filters
have less to work with — the result reads as residual noise that
visually overestimates precipitation. ITCOMP fills the gap with native
high-quality data, and the multi-region compositor's
`pixel_size`-based precedence (ITCOMP `0.009` < OPERA `0.01`) ensures
ITCOMP wins wherever it has values.

## Configuration

| Env var | Default | Effect |
|---|---|---|
| `LIBREWXR_DPC_ENABLED` | `true` | Set to `false` to disable the DPC fetch and let OPERA cover Italy as before. |
| `LIBREWXR_DPC_BASE_URL` | `https://radar-api.protezionecivile.it` | Override for testing against a mirror or stub. |

## References

- [Radar-DPC v2 documentation](https://dpc-radar.readthedocs.io/it/latest/)
- [REST API specification](https://dpc-radar.readthedocs.io/it/latest/api.html)
- [Public viewer](https://mappe.protezionecivile.gov.it/it/mappe-e-dashboard-rischi/piattaforma-radar/)
- *La Rete Radar Meteorologica Nazionale*, DPC, Allegato 1 (Tabella 1
  and 2) — authoritative site coordinates.
