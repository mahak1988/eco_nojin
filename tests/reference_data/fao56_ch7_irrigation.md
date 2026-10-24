# FAO-56 Chapter 7 irrigation interval worked example (vendored offline)

Published source: Allen, R.G., Pereira, L.S., Raes, D. and Smith, M. (1998),
FAO Irrigation and Drainage Paper 56, Chapter 7 "Irrigation scheduling",
Section 7.2: the irrigation interval formula

    I = (TAW * p) / ETc

where TAW = total available water in the root zone [mm], p = management-
allowed depletion fraction, and ETc = peak crop evapotranspiration [mm/day].

Published worked example (cited in `engine/strict_tests/test_s08_irrigation.py:139`
as "the FAO-56 worked example"):

    A silt loam wheat field: TAW = 100 mm, p = 0.55 (55 %), peak ETc = 6 mm/day
    → I = (100 * 0.55) / 6 = 9.17 → rounded to 9 days

The engine's `calculate_interval` implements this same formula, rounding to
the nearest whole day and flooring at 1 day, reproducing I = 9.

Constraint: AR-01 — the scientific core is not connected to the internet; this
reference is vendored with a sha256 checksum sidecar (`.meta.json`) and no
gate depends on a live download.
