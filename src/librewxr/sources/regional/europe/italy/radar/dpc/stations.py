# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""DPC Italian national radar network — station list.

Sourced from the official DPC document
``LA RETE RADAR METEOROLOGICA NAZIONALE``
(Allegato 1, ANAC publication 2024) — the 11 DPC-direct radars in
Tabella 1 (Gematronik Meteor 600 C and 50 DX) carry exact coordinates
from that document.  The 13 partner radars in Tabella 2 are not given
coordinates there; the values below come from publicly-known site
locations (airport ICAO codes, mountain-top toponyms) and should be
accurate to within a few hundred metres — fine for the 150 km coverage
mask but flagged here for any future application that needs survey
precision.

The DPC platform does not (currently) expose a SITES download endpoint
despite `findLastProductByType?type=SITES` reporting one — the
documentation lists SITES as a product type but `/downloadProduct`
rejects it with `productType non supportato`.  Until that changes, this
list is hand-maintained.

The composite covers all of Italy from a mix of DPC + partner radars;
unlisted partner radars only mean a slightly under-extended coverage
mask (pixels that *are* in radar range get marked as model-fill), not
gaps in the actual composite data.

Range override: a uniform 150 km is applied via ``RANGE_OVERRIDES``.
DPC's C-band radars reach further (~250 km in clear air) and the X-band
radars only ~60 km, but the composite itself decides which radar
contributes each pixel — our mask just needs to know "is there *some*
nearby radar."  150 km is the C-band airport-ASR midpoint and gives a
realistic coverage envelope.
"""
from __future__ import annotations


# Tabella 1 of Allegato 1 — DPC-direct radars (lat/lon authoritative).
_DPC_DIRECT: list[tuple[float, float]] = [
    # 7 C-band Gematronik Meteor 600 C (dual-polarization Doppler)
    (41.939, 14.624),   # Monte II Monte (Tufillo, CH)
    (43.956, 10.607),   # Monte Crocione (Villa Basilica, LU)
    (42.856, 12.791),   # Monte Serano (Campello sul Clitunno, PG)
    (39.373, 16.624),   # Monte Pettinascura (Longobucco, CS)
    (46.556, 12.974),   # Monte Zoufplan (Paluzza, UD)
    (37.123, 14.824),   # Monte Lauro (Buccheri, SI)
    (39.873,  9.491),   # Monte Armidda (Gairo, NU)
    # 4 X-band Gematronik Meteor 50 DX (airport sites)
    (40.880, 14.290),   # Aeroporto Napoli Capodichino
    (38.050, 15.650),   # Aeroporto Reggio Calabria
    (41.139, 16.760),   # Aeroporto Bari Palese
    (37.460, 15.050),   # Aeroporto Catania Fontanarossa
]

# Tabella 2 — Partner sub-network (regional admins + ENAV + Aeronautica
# Militare).  Coordinates derived from public site information; nominal
# precision a few hundred metres at worst.
_DPC_PARTNERS: list[tuple[float, float]] = [
    (45.0367,  7.7325),   # Bric della Croce (Torino — ARPA Piemonte)
    (44.2467,  8.2008),   # Monte Settepani (Piemonte / Liguria border)
    (44.7872, 10.4972),   # Gattatico (Reggio Emilia — ARPASIM)
    (44.6539, 11.6231),   # San Pietro Capofiume (Molinella, BO — ARPASIM)
    (45.3469, 11.6708),   # Monte Grande (Teolo, PD — ARPA Veneto)
    (45.7600, 12.8500),   # Concordia Sagittaria (VE — ARPA Veneto)
    (42.0408, 13.1764),   # Monte Midia (AQ — Regione Abruzzo)
    (46.4683, 11.1839),   # Monte Macaion (TN — PAA di Trento)
    (45.4451,  9.2767),   # Linate (Milano — ENAV)
    (41.8003, 12.2389),   # Fiumicino (Roma — ENAV)
    (45.7256, 13.4581),   # Fossalon di Grado (UD — ARPA FVG)
    (40.5750,  8.1717),   # Capocaccia (SS — Aeronautica Militare)
    (40.4080,  9.0233),   # Monte Rasu (SS — ARPAS Sardegna)
]

STATIONS: list[tuple[float, float]] = _DPC_DIRECT + _DPC_PARTNERS

STATION_MAP: dict[str, list[tuple[float, float]]] = {
    "ITCOMP": STATIONS,
}

# Coverage-mask range per region.  See module docstring on why 150 km.
RANGE_OVERRIDES: dict[str, float] = {
    "ITCOMP": 150.0,
}
