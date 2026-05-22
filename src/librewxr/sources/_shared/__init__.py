# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Joshua Kimsey
"""Shared base classes and helpers for source families.

A "source family" is a group of three or more variants that share the
same upstream provider, format, and decoder — e.g. the AROME overseas
models (Antilles, Réunion, French Guiana, …) all published through
data.gouv.fr in the same GRIB2 layout.  When that condition holds,
the shared machinery lives here and each variant package becomes a
thin subclass with just its domain constants and URL token.

Modules in this directory are NOT discovered as sources — the registry
walker in ``librewxr.sources.__init__`` checks ``ispkg`` and yields
packages whose ``__init__.py`` exposes a provider function.  Underscore-
prefixed directories like this one are still walked (Python doesn't
treat them as private at the package level), but contain no providers,
so they're silently ignored at collection time.

Rule of thumb: only add a family base here when ≥3 variants will share
it.  Below that threshold, plain copy-paste between variant packages
is cheaper than the abstraction.
"""
