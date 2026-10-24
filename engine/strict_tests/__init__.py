"""Rigorous / adversarial verification suite for the HyDroMa scientific engine.

Scope
-----
This package is deliberately separate from the pre-existing smoke tests. It exists
to hold the engine to the standards it cites in its own docstrings:

* FAO-56 (Allen et al., 1998) — reference evapotranspiration, equations 8/11/13/17/21/39/52
* NRCS TR-55 — SCS-CN, Rational method
* Saxton & Rawls (2006) — pedotransfer AWC cross-check
* Carsel & Parrish (1988) — van Genuchten parameter table
* van Genuchten (1980) / Mualem (1976) — retention and conductivity
* Theis (1935) — confined-aquifer drawdown
* Brune (1953) — reservoir trap efficiency
* Horton (1932) / Strahler (1957) — network statistics
* Kirpich (1948) — time of concentration
* Muskingum (1935) — flood routing
* FAO-29 / Ayers & Westcot (1985) — leaching requirement

Design rules
------------
1. Every numeric assertion is anchored to an external reference value, never to a
   value previously observed from this codebase.
2. Known engine defects are pinned with ``pytest.mark.xfail(strict=True)``. Strict
   xfail means a *fix* turns the test into an XPASS failure, so the tripwire can
   never silently rot. Each reason records the file:line, the governing standard
   and the measured magnitude.
3. Property-based tests (hypothesis) assert invariants and monotonicity, not
   recorded outputs.
4. No test asserts against a value that was copied out of the engine's own output.
"""
