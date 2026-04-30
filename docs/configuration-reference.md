# LibreWXR Configuration Reference

All settings are configured via environment variables prefixed with `LIBREWXR_` or through a `.env` file. Copy `.env.example` to `.env` and adjust as needed. Every setting has a sensible default — you only need to set what you want to change.

LibreWXR uses [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) for configuration. Environment variables take precedence over `.env` file values.

## Table of Contents

- [Server](#server)
- [Radar Data](#radar-data)
- [Regions](#regions)
- [Tile Rendering](#tile-rendering)
- [ECMWF Global Fallback](#ecmwf-global-fallback)
- [Nowcasting](#nowcasting)
- [Performance and Memory](#performance-and-memory)
- [RAM Sizing Guide](#ram-sizing-guide)
- [Scaling](#scaling)
- [Example Configurations](#example-configurations)

---

## Server

### `LIBREWXR_HOST`

The address the server binds to.

| | |
|---|---|
| **Default** | `0.0.0.0` |
| **Type** | string |

### `LIBREWXR_PORT`

The port the server listens on.

| | |
|---|---|
| **Default** | `8080` |
| **Type** | integer |

### `LIBREWXR_PUBLIC_URL`

The public-facing URL of your LibreWXR instance. This value is returned in the `host` field of `/public/weather-maps.json` responses. Clients use it to construct full tile URLs.

Set this to whatever URL users will use to reach your instance (e.g., your domain name, Cloudflare Tunnel URL, or reverse proxy address).

| | |
|---|---|
| **Default** | `http://localhost:8080` |
| **Type** | string |

**Example:**
```bash
LIBREWXR_PUBLIC_URL=https://radar.example.com
```

### `LIBREWXR_WORKERS`

Number of uvicorn worker processes. Each worker is a fully independent copy of LibreWXR with its own frame store, caches, and fetcher.

More workers improve concurrency for simultaneous users, but each uses significant RAM (frames + coordinate caches + tile cache). A caching reverse proxy in front of LibreWXR will do more for scalability than adding workers — tiles are already served with `Cache-Control: public, max-age=300`.

| | |
|---|---|
| **Default** | `1` |
| **Type** | integer |

**Guideline:** 1 worker per 2 CPU cores. See [Scaling](#scaling) for detailed recommendations.

### `LIBREWXR_CORS_ORIGINS`

Allowed CORS origins for cross-origin requests from web browsers.

| | |
|---|---|
| **Default** | `["*"]` (all origins) |
| **Type** | list of strings |

If you restrict this, make sure your web app's origin is included or tile requests from browsers will fail silently.

---

## Radar Data

### `LIBREWXR_FETCH_INTERVAL`

Seconds between radar data fetches. Frame timestamps are always aligned to clock boundaries (e.g., :00, :10, :20) regardless of when the server starts.

The default of 600 seconds (10 minutes) matches Rain Viewer's cadence. IEM publishes US composites every 5 minutes; MRMS publishes every 2 minutes. Setting the interval below 300 seconds is not recommended as most sources don't update faster than that.

| | |
|---|---|
| **Default** | `600` |
| **Type** | integer |
| **Unit** | seconds |

### `LIBREWXR_MAX_FRAMES`

Number of past radar frames to keep in memory. Each frame stores radar data for all enabled regions.

At the default 10-minute cadence:
- 12 frames = 2 hours of history
- 18 frames = 3 hours
- 24 frames = 4 hours

More frames = longer animation history = more RAM usage.

| | |
|---|---|
| **Default** | `12` |
| **Type** | integer |

### `LIBREWXR_NA_SOURCE`

Data source for North American radar composites (USCOMP, AKCOMP, HICOMP, PRCOMP, GUCOMP, and CACOMP). Three modes:

- **`mrms_fallback`** (default) — NCEP MRMS quality-controlled mosaics as the primary source, with IEM NEXRAD fallback for US regions and MSC blending for Canadian gaps. Best coverage: MRMS includes Canadian radar ingest and quality control. IEM is only fetched when MRMS fails for a specific frame.
- **`mrms`** — NCEP MRMS only, no fallback or blending. Pure MRMS where available; gaps show as empty (ECMWF IFS global fallback still fills in outside radar coverage). Least bandwidth.
- **`iem`** — Legacy mode. IEM NEXRAD N0Q for US regions, MSC GeoMet standalone for Canada. NEXRAD-only without Canadian radar ingest. Simplest and most battle-tested, but fewer radars and no QC.

| | |
|---|---|
| **Default** | `mrms_fallback` |
| **Type** | string |
| **Values** | `mrms_fallback`, `mrms`, `iem` |

**Note:** This setting does not affect the OPERA (Europe) source, which always uses EUMETNET OPERA via MeteoGate S3.

### `LIBREWXR_MRMS_BASE_URL`

Base URL for NCEP MRMS data products. Each region (CONUS, Alaska, Hawaii, Caribbean, Guam) has its own subdirectory under this path.

| | |
|---|---|
| **Default** | `https://mrms.ncep.noaa.gov/2D` |
| **Type** | string |

Only change this if you're mirroring MRMS data to a custom endpoint.

### `LIBREWXR_IEM_BASE_URL`

Base URL for the Iowa Environmental Mesonet NEXRAD composites (US regions). Only used when `LIBREWXR_NA_SOURCE` is `iem` or `mrms_fallback`.

| | |
|---|---|
| **Default** | `https://mesonet.agron.iastate.edu` |
| **Type** | string |

### `LIBREWXR_MSC_CANADA_BASE_URL`

Base URL for the Environment and Climate Change Canada MSC GeoMet WMS service (Canadian radar). Only used when `LIBREWXR_NA_SOURCE` is `iem` or `mrms_fallback`.

| | |
|---|---|
| **Default** | `https://geo.weather.gc.ca` |
| **Type** | string |

### `LIBREWXR_ENABLED_REGIONS`

Which radar regions to fetch and serve. Accepts group aliases, individual region codes, or comma-separated combinations.

| | |
|---|---|
| **Default** | `ALL` |
| **Type** | string |

**Group aliases:**

| Group | Expands to | Description |
|-------|-----------|-------------|
| `CONUS` | `USCOMP` | Continental US only (lightest option) |
| `US` | `USCOMP`, `AKCOMP`, `HICOMP`, `PRCOMP`, `GUCOMP` | All US regions |
| `CANADA` | `CACOMP` | Canada |
| `EUROPE` | `OPERA` | Pan-European composite (~155 radars, 24 countries) |
| `ALL` | All of the above | Every available region |

**Individual regions:**

| Region | Area | Source | Grid Size | Resolution | RAM / Frame |
|--------|------|--------|-----------|------------|-------------|
| `USCOMP` | Continental US | NCEP MRMS (IEM fallback) | 12200 x 5400 | 0.005° (~500m) | ~63 MB |
| `AKCOMP` | Alaska | NCEP MRMS (IEM fallback) | 4000 x 1550 | 0.01° (~1km) | ~6 MB |
| `HICOMP` | Hawaii | NCEP MRMS (IEM fallback) | 2000 x 1800 | 0.005° (~500m) | ~3.4 MB |
| `PRCOMP` | Puerto Rico | NCEP MRMS (IEM fallback) | 1000 x 1000 | 0.01° (~1km) | ~1 MB |
| `GUCOMP` | Guam | NCEP MRMS (IEM fallback) | 1000 x 1000 | 0.0085° (~850m) | ~1 MB |
| `CACOMP` | Canada | MSC GeoMet (MRMS blending) | 3560 x 1720 | 0.025° (~2.5km) | ~6 MB |
| `OPERA` | Europe | EUMETNET OPERA (MeteoGate S3) | 3800 x 4400 | 1km (LAEA) | ~16 MB |

**Examples:**
```bash
LIBREWXR_ENABLED_REGIONS=CONUS            # Continental US only
LIBREWXR_ENABLED_REGIONS=US               # All US regions
LIBREWXR_ENABLED_REGIONS=EUROPE           # Europe only
LIBREWXR_ENABLED_REGIONS=CANADA           # Canada only
LIBREWXR_ENABLED_REGIONS=CONUS,EUROPE     # Continental US + Europe
LIBREWXR_ENABLED_REGIONS=US,CANADA        # US + Canada
LIBREWXR_ENABLED_REGIONS=ALL              # Everything
```

### `LIBREWXR_OPERA_BASE_URL`

Base URL for the OPERA CIRRUS composite S3 bucket (European radar via MeteoGate).

| | |
|---|---|
| **Default** | `https://s3.waw3-1.cloudferro.com` |
| **Type** | string |

---

## Tile Rendering

### `LIBREWXR_MAX_ZOOM`

Maximum tile zoom level. Higher values allow more detail when zoomed in but use more memory for cached tiles. 12 is the maximum supported by the source data resolution.

| | |
|---|---|
| **Default** | `12` |
| **Type** | integer |
| **Range** | 0 - 12 |

### `LIBREWXR_SMOOTH_RADIUS`

Gaussian blur radius applied when smoothing is enabled in the tile URL (`smooth=1`). Higher values produce a softer appearance. Set to 0 to disable smoothing entirely, even when clients request it.

| | |
|---|---|
| **Default** | `2.0` |
| **Type** | float |

**Recommended range:** 2.0 - 4.0. Rain Viewer used approximately 3.0.

### `LIBREWXR_NOISE_FLOOR_DBZ`

Minimum dBZ value to display. Pixels below this threshold are made transparent. Filters out ground clutter, anomalous propagation, and weak noise.

For reference on the dBZ scale:
- 5 dBZ = barely detectable
- 10 dBZ = very light precipitation
- 20 dBZ = light rain

| | |
|---|---|
| **Default** | `10.0` |
| **Type** | float |

Set to `-32` to disable and show everything.

### `LIBREWXR_DESPECKLE_MIN_NEIGHBORS`

Speckle filter strength. A pixel is removed if it has fewer than this many non-zero neighbors (out of 8 surrounding pixels). Removes isolated radar artifacts and ground clutter.

| | |
|---|---|
| **Default** | `3` |
| **Type** | integer |
| **Range** | 0 - 8 |

- `0` = disabled
- `2` = light filtering
- `3` = moderate (recommended)
- `4+` = aggressive (may remove edges of real precipitation)

### `LIBREWXR_WEBP_QUALITY`

WebP encoding quality for tiles requested in `.webp` format. Does not affect PNG tiles.

| | |
|---|---|
| **Default** | `80` |
| **Type** | integer |
| **Range** | 1 - 100 |

- `100` = lossless (best quality, larger files)
- `80` = lossy (visually identical for radar imagery, ~3-4x smaller than PNG)
- `1-79` = increasingly lossy

---

## ECMWF Global Fallback

LibreWXR uses ECMWF IFS 9km global precipitation data from [Open-Meteo](https://open-meteo.com/) S3 to fill in worldwide coverage where no radar composite exists. This provides global precipitation display (at lower resolution than radar) and per-pixel snow/rain classification.

### `LIBREWXR_ECMWF_S3_BUCKET`

S3 bucket name for Open-Meteo ECMWF data.

| | |
|---|---|
| **Default** | `openmeteo` |
| **Type** | string |

### `LIBREWXR_ECMWF_S3_REGION`

AWS region of the Open-Meteo S3 bucket.

| | |
|---|---|
| **Default** | `us-west-2` |
| **Type** | string |

### `LIBREWXR_ECMWF_S3_PREFIX`

S3 key prefix for ECMWF IFS data.

| | |
|---|---|
| **Default** | `data_spatial/ecmwf_ifs` |
| **Type** | string |

### `LIBREWXR_ECMWF_SNOW_RATIO_THRESHOLD`

Snowfall fraction threshold for per-pixel snow/rain classification. When the snow-to-total precipitation ratio exceeds this value, the pixel is classified as snow and rendered with the snow color palette (when `snow=1` in the tile URL).

| | |
|---|---|
| **Default** | `0.5` |
| **Type** | float |
| **Range** | 0.0 - 1.0 |

### `LIBREWXR_ECMWF_MAX_TIMESTEPS`

Number of ECMWF IFS hourly timesteps to fetch for global fallback animation.

| | |
|---|---|
| **Default** | `0` (auto) |
| **Type** | integer |

When set to `0` (recommended), the count is derived automatically from `LIBREWXR_MAX_FRAMES` so ECMWF animation covers the same time window as radar. The formula is `ceil(max_frames / 6) + 1`, plus extra hours when nowcast is enabled to cover the forecast window.

At the default 10-min cadence:
- 12 frames (2h) = 3 timesteps
- 18 frames (3h) = 4 timesteps
- 24 frames (4h) = 5 timesteps

Each timestep adds ~13 MB RAM and ~1-2 seconds to fetch time. Set to `1` for a static single snapshot.

### `LIBREWXR_ECMWF_INTERPOLATION`

Enable optical flow interpolation of ECMWF IFS hourly data to 10-minute frames. Uses dense motion vectors (OpenCV Farneback) to animate precipitation movement between IFS hours, so the global fallback animates smoothly like real radar data instead of jumping hour-to-hour.

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |

Adds ~130 MB RAM for synthetic frames and ~5-10 seconds of compute per IFS fetch cycle. Disable to have IFS data snap to the nearest hour (visually jumpier but lighter on resources).

---

## Nowcasting

Precipitation nowcasting is an experimental feature that extrapolates recent radar data forward using optical flow to generate short-range forecast frames. These can optionally be blended with ECMWF IFS forecast data.

### `LIBREWXR_NOWCAST_ENABLED`

Enable or disable nowcast frame generation.

| | |
|---|---|
| **Default** | `true` |
| **Type** | boolean |

When enabled, nowcast frames appear in the `radar.nowcast` array of the `/public/weather-maps.json` response.

### `LIBREWXR_NOWCAST_FRAMES`

Number of nowcast frames to generate. Each frame covers one fetch interval (default 10 minutes).

| | |
|---|---|
| **Default** | `6` |
| **Type** | integer |

At the default 10-minute cadence, 6 frames = 60 minutes of forecast. More frames extend the forecast range but accuracy decreases at the far end. Rain Viewer offered ~30 minutes free / 60 minutes paid.

### `LIBREWXR_NOWCAST_BLEND_MODE`

Controls how radar extrapolation and ECMWF IFS forecast data are combined during the nowcast window. Beyond 60 minutes, pure IFS is always used regardless of this setting.

| | |
|---|---|
| **Default** | `radar` |
| **Type** | string |
| **Values** | `radar`, `blended`, `ifs` |

- **`radar`** — Pure radar extrapolation for the first 60 minutes. Closest to Rain Viewer behavior. Best for short-range forecasts of existing precipitation, but less reliable for cell initiation or dissipation.
- **`blended`** — Smooth transition from radar-heavy to IFS-heavy (~87% radar at T+10 min, fading to ~30% at T+60 min). Balances radar detail with IFS large-scale consistency. Uses spatial feathering at radar coverage boundaries to prevent hard seams.
- **`ifs`** — Pure IFS forecast for all nowcast frames. Most spatially consistent but misses fine detail from recent radar observations.

---

## Performance and Memory

### `LIBREWXR_TILE_CACHE_MB`

Maximum tile cache size in megabytes. The cache stores rendered tile images (PNG/WebP bytes) and evicts the oldest entries when this byte limit is reached.

Higher values mean faster tile serving for repeat requests. Lower values save RAM.

| | |
|---|---|
| **Default** | `200` |
| **Type** | integer |
| **Unit** | megabytes |

### `LIBREWXR_COORD_CACHE_SIZE`

Maximum entries per coordinate LRU cache. Controls how many tile-coordinate mappings are kept in memory. There are 6 internal coordinate caches, and each entry is 0.5-2 MB depending on tile size.

These caches are the largest RAM consumer after frame data. Reducing this saves significant RAM at the cost of occasional recomputation (~5-20ms per cache miss).

| | |
|---|---|
| **Default** | `2048` |
| **Type** | integer |

**Worst-case RAM usage:** `coord_cache_size x 6 x ~1 MB`

### `LIBREWXR_MEMORY_LIMIT_MB`

Memory limit in MB for the memory pressure monitor. When RSS usage exceeds 85% of this limit, the tile cache and coordinate caches are automatically trimmed.

| | |
|---|---|
| **Default** | `0` (auto-detect) |
| **Type** | integer |
| **Unit** | megabytes |

When set to `0`, the limit is auto-detected from Docker/cgroup limits or falls back to system RAM. Set this explicitly if auto-detection doesn't work in your environment.

### `LIBREWXR_MEMORY_PRESSURE_CHECK_INTERVAL`

Seconds between memory pressure checks.

| | |
|---|---|
| **Default** | `30` |
| **Type** | integer |
| **Unit** | seconds |

Lower values make the monitor more responsive to memory spikes. Higher values reduce overhead.

### `LIBREWXR_WARMER_THREADS`

Thread pool size for background tile cache warming. When a tile is requested, the warmer pre-renders that same tile position for all other timestamps in the background, so animation playback is smooth without waiting for each frame to render on demand.

| | |
|---|---|
| **Default** | `4` |
| **Type** | integer |

4 is a good default. 6-8 on machines with many cores. This is a "nice to have" optimization — scale workers before increasing this.

---

## RAM Sizing Guide

RAM usage depends primarily on which regions are enabled, how many frames are kept in memory, and how many workers are running. Caches (coordinate + tile) fill up under real traffic and account for a large portion of steady-state usage.

| Configuration | Estimated RAM |
|---|---|
| CONUS, 1 worker, 12 frames | ~3 GB |
| CONUS, 1 worker, 20 frames | ~4 GB |
| ALL regions, 1 worker, 12 frames | ~7 GB |
| ALL regions, 1 worker, 20 frames | ~8 GB |
| ALL regions, 2 workers, 12 frames | ~12 GB |
| ALL regions, 2 workers, 20 frames | ~14 GB |

Set the Docker memory limit in `docker-compose.yml` accordingly:

```yaml
deploy:
  resources:
    limits:
      memory: 7G  # Adjust for your configuration
```

---

## Scaling

| Users | Workers | RAM (ALL regions) | RAM (CONUS only) |
|-------|---------|-------------------|------------------|
| 1-5 (personal) | 1 | ~7 GB | ~3 GB |
| 5-50 (small community) | 2 | ~12 GB | ~5 GB |
| 50-200 (medium) | 4 + CDN | ~22 GB | ~9 GB |
| 200+ (large) | 8+ + CDN | 40+ GB | 16+ GB |

Tiles are served with `Cache-Control: public, max-age=300`, so any caching reverse proxy (nginx, Cloudflare, etc.) absorbs repeat tile requests automatically. A CDN like Cloudflare (free tier works) can dramatically reduce the number of requests hitting your server. Using a Cloudflare Tunnel also provides free HTTPS with no certificate management.

For most self-hosting scenarios, **1 worker behind Cloudflare is sufficient**.

---

## Example Configurations

### Minimal (personal use, US only)

```bash
LIBREWXR_PUBLIC_URL=http://localhost:8080
LIBREWXR_ENABLED_REGIONS=CONUS
```

Docker memory limit: 3 GB

### Full coverage, single user

```bash
LIBREWXR_PUBLIC_URL=https://radar.example.com
LIBREWXR_ENABLED_REGIONS=ALL
```

Docker memory limit: 7 GB

### Community server with CDN

```bash
LIBREWXR_PUBLIC_URL=https://radar.example.com
LIBREWXR_ENABLED_REGIONS=ALL
LIBREWXR_WORKERS=2
LIBREWXR_WEBP_QUALITY=80
LIBREWXR_TILE_CACHE_MB=400
```

Docker memory limit: 14 GB. Put Cloudflare or nginx in front.

### Lightweight / low-RAM

```bash
LIBREWXR_ENABLED_REGIONS=CONUS
LIBREWXR_MAX_FRAMES=6
LIBREWXR_COORD_CACHE_SIZE=512
LIBREWXR_TILE_CACHE_MB=50
LIBREWXR_ECMWF_INTERPOLATION=false
LIBREWXR_NOWCAST_ENABLED=false
```

Minimizes RAM at the cost of shorter history (1 hour), slower cache hits, and no interpolation or nowcasting. Docker memory limit: ~1.5 GB.
