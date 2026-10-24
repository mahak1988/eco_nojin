# CITATION-CORRECTIONS — Gap G-H17 (dead DOI repair, 2026-10-10)

Agent: **A-DOIFIX**
Scope: DOI tokens only, inside `reports/hydroma/HYDROMA_REFERENCE_DATA_CATALOG.md`
and `reports/hydroma/HYDROMA_SCIENTIFIC_CRITERIA.md`. No other file was edited.

## Method

Every DOI was resolved against `https://doi.org/` and cross-checked against its owning
registration agency:

* `HEAD https://doi.org/<doi>` (`requests`, the same client and User-Agent
  `eco-nojin-citation-checker/1.0 (mailto:audit@eco-nojin.local)` that
  `tools/check_citations.py` uses), and
* `GET https://doi.org/<doi>` (webfetch), which returns the publisher's citation
  metadata, and
* `https://api.crossref.org/works/<doi>` / `https://api.datacite.org/dois/<doi>`
  for the registration record (title, authors, journal, year, volume, issue, pages).

Every replacement DOI below was confirmed to match the cited work on **author, year,
journal, volume, issue and page range** — not just to "resolve". No DOI was invented
or guessed: each one is a registration-agency record that I fetched.

## Result summary

| outcome | count |
|---|---|
| DOI tokens replaced with a verified DOI | **20** (15 distinct DOIs) |
| DOI tokens replaced with `CITATION-UNVERIFIED` | **6** (6 distinct DOIs) |
| line edits total | 26 |

Dead-DOI count reported by `tools/check_citations.py`:

* before: `SUMMARY total=23 ok=2 dead=21 error=0`
* after: `SUMMARY total=17 ok=7 dead=8 error=2`

### Why 8 DOIs are still reported DEAD after correction

These 8 replacement DOIs are **registered and resolve correctly** (evidence column:
`GET https://doi.org/...` returns the exact publisher citation). `requests.head()`
is answered `403` by the publishers' bot protection (Wiley/ACSess, Atypon, AMS,
T&F, AGU) — a `403`, never a `404`. `tools/check_citations.py` treats any status
`>= 400` on a HEAD as DEAD, so a bot-blocked *valid* DOI is indistinguishable from
a dead one for that tool. The two ASABE DOIs (`10.13031/...`) return
`ConnectionResetError` from this sandbox for `elibrary.asabe.org` on both HEAD and
GET, which the checker reports as `ERROR` ("network — not a citation defect").

This is a limitation of the HEAD-only checker, not a citation defect. The
correctness evidence for each of the 8 is in the table below.

## Corrections table

| # | document | line | dead DOI | cited work | verified DOI (or CITATION-UNVERIFIED) | evidence (URL + resolved title) | action |
|---|---|---|---|---|---|---|---|
| 1 | HYDROMA_REFERENCE_DATA_CATALOG.md | 46 | `10.13030/2151-2137.1982.x` | Hargreaves & Samani, "Estimating Potential Evapotranspiration", *J. Irrigation & Drainage Div.* 108(3), 225–230 (1982) | `10.1061/JRCEA4.0001390` | `https://doi.org/10.1061/jrcea4.0001390` → "Hargreaves, G. H., & Samani, Z. A. (1982). Estimating Potential Evapotranspiration. Journal of the Irrigation and Drainage Division, 108(3), 225–230." (Crossref: HTTP 200, publisher ASCE). Original was a non-existent prefix (`10.13030` → Crossref 404) plus a PII-shaped suffix. | replaced |
| 2 | HYDROMA_REFERENCE_DATA_CATALOG.md | 151 | `10.2136/sssaj2005.0039` | Saxton & Rawls (2006), "Soil Water Characteristic Estimates …", *SSSAJ* 70(5) | `10.2136/sssaj2005.0117` | `https://doi.org/10.2136/sssaj2005.0117` → "Saxton, K. E., & Rawls, W. J. (2006). Soil Water Characteristic Estimates by Texture and Organic Matter for Hydrologic Solutions. Soil Science Society of America Journal, 70(5), 1569–1578." The dead token was a digit-swap of the same paper's DOI. | replaced |
| 3 | HYDROMA_REFERENCE_DATA_CATALOG.md | 234 | `10.1080/00344257_1974_10478314` | Rouse et al. (1974), NDVI, *Canadian Journal of Remote Sensing* 1(1), 7–15 | `CITATION-UNVERIFIED` | No DOI exists. Crossref has **zero** 1974 records for that journal (`api.crossref.org/journals/0703-8992` → `total-results: 0`); DataCite has no work titled "monitoring vegetation systems". NASA NTRS id 19740022614 = "Monitoring vegetation systems in the Great Plains with ERTS", Rouse/Haas/Schell/Deering, conference paper PAPER-A20 in NASA-SP-351-VOL-1-SECT-A — a conference proceeding, no DOI. | replaced with `CITATION-UNVERIFIED` |
| 4 | HYDROMA_REFERENCE_DATA_CATALOG.md | 235 | `10.1109/TGRS.2002.802529` | Huete et al. (2002), MODIS vegetation indices / EVI | `10.1016/S0034-4257(02)00096-2` | `https://doi.org/10.1016/s0034-4257(02)00096-2` → "Huete, A., Didan, K., Miura, T., Rodriguez, E. P., Gao, X., & Ferreira, L. G. (2002). Overview of the radiometric and biophysical performance of the MODIS vegetation indices. Remote Sensing of Environment, 83(1-2), 195–213." (Crossref HTTP 200, Elsevier BV). The EVI paper is in *RSE*, not IEEE *TGRS*; the dead token was a fabricated IEEE suffix. | replaced |
| 5 | HYDROMA_REFERENCE_DATA_CATALOG.md | 236 | `10.1016/S0034-4257(96)00052-7` | McFeeters (1996), NDWI | `10.1080/01431169608948714` | `https://doi.org/10.1080/01431169608948714` → "McFEETERS, S. K. (1996). The use of the Normalized Difference Water Index (NDWI) in the delineation of open water features. International Journal of Remote Sensing, 17(7), 1425–1432." (Crossref HTTP 200, Informa UK Limited). The dead Elsevier token was wrong on venue too: the NDWI paper is in *IJRS*, not *RSE*. | replaced |
| 6 | HYDROMA_REFERENCE_DATA_CATALOG.md | 237 | `10.1109/TGRS.1995.460586` | Key & Benson (1995), NBR | `CITATION-UNVERIFIED` | No DOI exists. The IEEE TGRS token is unregistered (doi.org 404); Crossref returns no 1995 Key/Benson burn-ratio paper and DataCite returns no DataCite record. The NBR originates in Key, C.H. & Benson, N.C., *Landscape Assessment*, in Lutes et al. (2006) **FIREMON: Fire Effects Monitoring and Inventory System**, USDA Forest Service RMRS-GTR-164-CD — a technical report, no DOI, and dated 2006 rather than 1995. | replaced with `CITATION-UNVERIFIED` |
| 7 | HYDROMA_REFERENCE_DATA_CATALOG.md | 238 | `10.1109/IGARSS.1988.137952` | Huete (1988), SAVI | `10.1016/0034-4257(88)90106-X` | `https://doi.org/10.1016/0034-4257(88)90106-X` → "Huete, A. R. (1988). A soil-adjusted vegetation index (SAVI). Remote Sensing of Environment, 25(3), 295–309." (Crossref HTTP 200, Elsevier BV). | replaced |
| 8 | HYDROMA_REFERENCE_DATA_CATALOG.md | 246 | `10.1175/BAMS-D-16-0040.1` | GPM IMERG — GPM mission paper | `10.1175/BAMS-D-13-00164.1` | `https://doi.org/10.1175/bams-d-13-00164.1` → "Hou, A. Y., Kakar, R. K., Neeck, S., Azarbarzin, A. A., Kummerow, C. D., Kojima, M., Oki, R., Nakamura, K., & Iguchi, T. (2014). The Global Precipitation Measurement Mission. Bulletin of the American Meteorological Society, 95(5), 701–722." (Crossref HTTP 200, American Meteorological Society). Dead token was a mis-typed manuscript number; `-13-00164` is the accepted BAMS record. | replaced |
| 9 | HYDROMA_REFERENCE_DATA_CATALOG.md | 247 | `10.1016/j.rfuts.2006.09.007` | MODIS MOD16 global ET algorithm | `10.1016/j.rse.2007.04.015` | `https://doi.org/10.1016/j.rse.2007.04.015` → "Mu, Q., Heinsch, F. A., Zhao, M., & Running, S. W. (2007). Development of a global evapotranspiration algorithm based on MODIS and global meteorology data. Remote Sensing of Environment, 111(4), 519–536." (Crossref HTTP 200, Elsevier BV). The dead token had a fabricated journal code (`j.rfuts`) and year/month digits. | replaced |
| 10 | HYDROMA_REFERENCE_DATA_CATALOG.md | 249 | `10.1080/00344257.2012.721060` | Sentinel-2 L2A mission reference | `10.1016/j.rse.2011.11.026` | `https://doi.org/10.1016/j.rse.2011.11.026` → "Drusch, M., Del Bello, U., Carlier, S., Colin, O., … Bargellini, P. (2012). Sentinel-2: ESA's Optical High-Resolution Mission for GMES Operational Services. Remote Sensing of Environment, 120, 25–36." (Crossref HTTP 200, Elsevier BV). | replaced |
| 11 | HYDROMA_REFERENCE_DATA_CATALOG.md | 257 | `10.1016/0341-8160(94)90066-4` | Renard & Freimund (1994), monthly/annual R-factor indices | `10.1016/0022-1694(94)90110-4` | `https://doi.org/10.1016/0022-1694(94)90110-4` → "Renard, K. G., & Freimund, J. R. (1994). Using monthly precipitation data to estimate the R-factor in the revised USLE. Journal of Hydrology, 157(1-4), 287–306." (Crossref HTTP 200, Elsevier BV). Original carried a one-digit-wrong ISSN for *Catena* (0341-8160 vs 0341-8162) and the wrong journal. | replaced |
| 12 | HYDROMA_REFERENCE_DATA_CATALOG.md | 259 | `10.13030/0275-7040-30-5-1387` | McCool et al. (1987), slope steepness factor | `10.13031/2013.30576` | `https://doi.org/10.13031/2013.30576` → "D. K. McCool, L. C. Brown, G. R. Foster, C. K. Mutchler, & L. D. Meyer. (1987). Revised Slope Steepness Factor for the Universal Soil Loss Equation. Transactions of the ASAE, 30(5), 1387–1396." (Crossref HTTP 200, ASABE). Non-existent prefix `10.13030` (Crossref 404) and a hand-built ISSN-embedded suffix. | replaced |
| 13 | HYDROMA_REFERENCE_DATA_CATALOG.md | 303 | `10.3133/ofr305` | Theis (1935), well function | `10.1029/TR016i002p00519` | `https://doi.org/10.1029/tr016i002p00519` → "The relation between the lowering of the Piezometric surface and the rate and duration of discharge of a well using ground-water storage. Eos, Transactions American Geophysical Union, 16(2), 519–524." (Crossref HTTP 200, AGU). The USGS `ofr` token was unregistered (404); the real Theis 1935 publication is in *Eos Trans. AGU*. | replaced |
| 14 | HYDROMA_SCIENTIFIC_CRITERIA.md | 35 | `10.1016/0341-8160(94)90066-4` | Renard & Freimund (1994) | `10.1016/0022-1694(94)90110-4` | as #11. | replaced |
| 15 | HYDROMA_SCIENTIFIC_CRITERIA.md | 51 | `10.1080/00384347408478153` | Rouse et al. (1974), NDVI | `CITATION-UNVERIFIED` | No DOI exists — see #3 (Crossref journal query returns 0 records for 1974; NASA NTRS id 19740022614 is an unnumbered conference paper, PAPER-A20, NASA SP-351 Vol. 1 Sect. A). The in-document note claiming a "journal DOI" and a *USGS Professional Paper 851* provenance was false; both have been removed. | replaced with `CITATION-UNVERIFIED` |
| 16 | HYDROMA_SCIENTIFIC_CRITERIA.md | 68 | `10.1016/S0034-4257(96)00052-7` | McFeeters (1996), NDWI | `10.1080/01431169608948714` | as #5. | replaced |
| 17 | HYDROMA_SCIENTIFIC_CRITERIA.md | 84 | `10.13030/2151-2137.1982.x` | Hargreaves & Samani (1982), ET0 | `10.1061/JRCEA4.0001390` | as #1. | replaced |
| 18 | HYDROMA_SCIENTIFIC_CRITERIA.md | 103 | `10.13030/0275-7040-24-5-1177` | Foster et al. (1981), erosion/sediment yield | `10.13031/2013.34429` | `https://doi.org/10.13031/2013.34429` → "G. R. Foster, L. J. Lane, J. D. Nowlin, J. M. Laflen, & R. A. Young. (1981). Estimating Erosion and Sediment Yield on Field-Sized Areas. Transactions of the ASAE, 24(5), 1253–1262." (Crossref HTTP 200, ASABE). Non-existent prefix `10.13030`. | replaced |
| 19 | HYDROMA_SCIENTIFIC_CRITERIA.md | 125 | `10.1097/01.for.0000749234.w29554.72` | USDA Salinity Laboratory (1954), exchangeable sodium | `CITATION-UNVERIFIED` | No DOI exists. Crossref has no record for "Exchangeable sodium and its diagram"; the Wolters Kluwer/Ovid-shaped token (prefix `10.1097`) is unrelated to the USDA. The work is the USDA Salinity Laboratory Staff chapter of Richards, L.A. (ed.), *Diagnosis and Improvement of Saline and Alkali Soils*, USDA Agriculture Handbook 60 (1954) — a book/monograph with no DOI. | replaced with `CITATION-UNVERIFIED` |
| 20 | HYDROMA_SCIENTIFIC_CRITERIA.md | 126 | `10.4060/ca9742e` | FAO (1985), *Water Quality for Agriculture*, IDP 29 | `CITATION-UNVERIFIED` | No DOI exists. `https://doi.org/10.4060/ca9742e` → 404; the FAO publication itself is served at `https://www.fao.org/3/t0234e/` carrying "FAO IRRIGATION AND DRAINAGE PAPER 29 Rev. 1 … ISBN 92-5-102263-1" and no DOI (fetched and read, 200 OK). Crossref prefix `10.4060` is not a Crossref member and DataCite has no matching record. | replaced with `CITATION-UNVERIFIED` |
| 21 | HYDROMA_SCIENTIFIC_CRITERIA.md | 175 | `10.2136/sssaj2004.0117` | van Genuchten (1980), closed-form K(ψ) | `10.2136/sssaj1980.03615995004400050002x` | `https://doi.org/10.2136/sssaj1980.03615995004400050002x` → "van Genuchten, M. Th. (1980). A Closed-form Equation for Predicting the Hydraulic Conductivity of Unsaturated Soils. Soil Science Society of America Journal, 44(5), 892–898." (Crossref HTTP 200, Wiley). The dead token was a 2004 SSSAJ record, not the 1980 one. | replaced |
| 22 | HYDROMA_SCIENTIFIC_CRITERIA.md | 176 | `10.1029/WR012p0513` | Mualem (1976) | `10.1029/WR012i003p00513` | `https://doi.org/10.1029/wr012i003p00513` → "Mualem, Y. (1976). A new model for predicting the hydraulic conductivity of unsaturated porous media. Water Resources Research, 12(3), 513–522." (Crossref HTTP 200, AGU). The dead token dropped the `iNNN` issue token from the AGU DOI form. | replaced |
| 23 | HYDROMA_SCIENTIFIC_CRITERIA.md | 200 | `10.5281/zenodo.4725384` | Verra (2021), VCS Program Standard VCS-3000 | `CITATION-UNVERIFIED` | No such record. `https://api.datacite.org/dois/10.5281/zenodo.4725384` → **404** and `https://zenodo.org/api/records/4725384` returns the concept for an unrelated paper ("Electrochemically controlled ion dynamics in porphyrin nanostructures", *J. Phys. Chem. C* 124(33), 18346–18355, 2020). DataCite search for "VCS Program Standard" Verra returns 0 records. Verra publishes VCS-3000 on verra.org without a DOI. | replaced with `CITATION-UNVERIFIED` |
| 24 | HYDROMA_SCIENTIFIC_CRITERIA.md | 249 | `10.3133/ofr305` | Theis (1935) | `10.1029/TR016i002p00519` | as #13. | replaced |
| 25 | HYDROMA_SCIENTIFIC_CRITERIA.md | 274 | `10.2135/stherlin.1994.01.003` | Doran & Parkin (1994), "Defining and Assessing Soil Quality" | `10.2136/sssaspecpub35.c1` | `https://doi.org/10.2136/sssaspecpub35.c1` → "Doran, J. W., & Parkin, T. B. (1994). Defining and Assessing Soil Quality. Defining Soil Quality for a Sustainable Environment, 1–21." (Crossref HTTP 200, Wiley). The dead token used a JSTOR-style prefix (`10.2135`) and a fabricated "stherlin" suffix. | replaced |
| 26 | HYDROMA_SCIENTIFIC_CRITERIA.md | 297 | `10.13030/0275-7040-30-5-1387` | McCool et al. (1987), slope steepness factor | `10.13031/2013.30576` | as #12. | replaced |

## The three most important corrections

1. **NDVI / Rouse et al. 1974** — rows #3 (catalog) and #15 (criteria). The two dead tokens
   `10.1080/00344257_1974_10478314` and `10.1080/00384347408478153` are PII-shaped
   strings, not DOIs: `10.1080` is Taylor & Francis, which registers no such records, and
   Crossref returns **zero** 1974 articles for the Canadian Journal of Remote Sensing.
   Confirmed via NASA NTRS (id 19740022614, "Monitoring vegetation systems in the Great
   Plains with ERTS", Rouse/Haas/Schell/Deering, PAPER-A20) that the NDVI paper is a NASA
   SP-351 conference proceeding with **no DOI at all**, so both tokens became
   `CITATION-UNVERIFIED` and the false "journal DOI / USGS Professional Paper 851" note was
   removed. This matters because NDVI is the most-cited function in the codebase.
2. **EVI / Huete et al. 2002** — row #4. `10.1109/TGRS.2002.802529` was reported as
   "one digit off the real EVI DOI"; it is worse than that — the IEEE TGRS suffix does
   not exist and the paper is not in IEEE TGRS at all. The published record is
   `10.1016/S0034-4257(02)00096-2` (Remote Sensing of Environment 83(1-2), 195–213,
   doi.org resolves to "Overview of the radiometric and biophysical performance of the
   MODIS vegetation indices").
3. **Verra VCS Program Standard (VCS-3000)** — row #23. `10.5281/zenodo.4725384` is not
   merely dead: the Zenodo record at that identifier belongs to an unrelated 2020
   porphyrin/J. Phys. Chem. C paper. DataCite returns 404 for the DOI and 0 results for
   "VCS Program Standard". Marked `CITATION-UNVERIFIED` with the provenance note that
   VCS-3000 is published by Verra on verra.org without a DOI.

## Notes for follow-up (out of A-DOIFIX scope)

* Several row citations carry a wrong venue/author that the DOI evidence contradicts
  (e.g. McFeeters 1996 NDWI is *IJRS* 17(7) 1425–1432, not *RSE* 57(3) 289–298;
  Hargreaves & "Sammugi" is Hargreaves & **Samani**; Foster et al. 1981 is
  *Trans. ASAE* 24(5) 1253–1262, not 1177–1186; Theis 1935 is *Eos Trans. AGU*
  16(2) 519–524, not a USGS Technical Note 69-46). Only DOI tokens were changed here,
  as instructed.
* `tools/check_citations.py` does HEAD-only resolution. Publishers using Atypon
  (Wiley/ACSess), AMS, Informa (T&F), AGU and ASCE answer HEAD with `403` from
  automated clients, so a valid DOI is reported DEAD. Treating `403` as "not resolvable
  elswhere but registered" (e.g. by also accepting a Crossref `GET` hit) would remove
  8 false positives. This is a tool change, not a citation change.
