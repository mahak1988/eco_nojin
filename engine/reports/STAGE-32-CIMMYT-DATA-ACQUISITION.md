# Stage 32: CIMMYT Wheat Dataset Acquisition Verification

## Summary

| Item | Result |
|---|---|
| **HTTP Status (data file)** | 200 OK |
| **HTTP Status (variables file)** | 200 OK |
| **Content-Type** | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| **Data file MD5** | `36e24a6cf5680f1e8fc1640a4ee9567a` — does **not** match published value |
| **Variables file MD5** | `34ac8620ee51108bf71bd8019bab9a4c` — **matches** published value |
| **Data file SHA-256** | `919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde` |
| **Variables file SHA-256** | `9987ac2c91de5e58e14d78bf77ba7d257971d8f8621a1ee50d58b31d3715cfc6` |
| **Download verdict** | Successful — both files are valid XLSX binary files |

---

## A. Download Procedure

### Source URLs

| File | URL |
|---|---|
| Data file | `https://data.cimmyt.org/api/access/datafile/60990` |
| Variable dictionary | `https://data.cimmyt.org/api/access/datafile/60991` |
| Landing page | `https://data.cimmyt.org/dataset.xhtml?persistentId=doi%3A10.71682%2F10549424` |
| DOI | `10.71682/10549424` |

### Method

Both files were downloaded using `curl.exe` with the `-L` (follow redirects) flag.
The download followed one redirect from `data.cimmyt.org` to a StorJ gateway
object storage endpoint (`datarepository.gateway.storjshare.io`).

### HTTP Response Details

#### Data file (`Wheat_Yld_Eastern_IND_Data.xlsx`)

| Field | Value |
|---|---|
| HTTP status code | 200 |
| `Content-Type` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Redirect count | 1 (to StorJ gateway) |
| Final URL | `https://datarepository.gateway.storjshare.io/10.71682/10549424/...` |
| Response body type | Binary Excel (verified via `PK` magic bytes) |
| File size | 1,609,655 bytes |

#### Variable dictionary (`Wheat_Yld_Eastern_IND_Variables.xlsx`)

| Field | Value |
|---|---|
| HTTP status code | 200 |
| `Content-Type` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| Redirect count | 1 (to StorJ gateway) |
| Final URL | `https://datarepository.gateway.storjshare.io/10.71682/10549424/...` |
| Response body type | Binary Excel (verified via `PK` magic bytes) |
| File size | 100,656 bytes |

### File Integrity Verification

The first 8 bytes of each downloaded file were verified as `50 4B 03 04 14 00 06 00`,
confirming the files are valid XLSX/ZIP containers (the `PK` magic signature).
Both responses returned a binary Excel file, not an HTML login/challenge page.

### MD5 Comparison

| File | Published MD5 | Computed MD5 | Match |
|---|---|---|---|
| `Wheat_Yld_Eastern_IND_Data.xlsx` | `36e24a6cf5680f1ee8fc1640a4ee9567a` | `36e24a6cf5680f1e8fc1640a4ee9567a` | **NO** |
| `Wheat_Yld_Eastern_IND_Variables.xlsx` | `34ac8620ee51108bf71bd8019bab9a4c` | `34ac8620ee51108bf71bd8019bab9a4c` | **YES** |

#### MD5 Mismatch Analysis — Data File

The published MD5 for the data file is **33 characters** (`36e24a6cf5680f1ee8fc1640a4ee9567a`),
which is one character longer than a valid 32-character MD5 hex digest. The
computed MD5 is `36e24a6cf5680f1e8fc1640a4ee9567a` (32 characters).

| Position | Computed | Published |
|---|---|---|
| 1–15 | `36e24a6cf5680f1` | `36e24a6cf5680f1` |
| 16 | `e` | `e` |
| 17 | `8` | `e` (extra character in published value) |
| 18–32 | `fc1640a4ee9567a` | `8fc1640a4ee9567a` |

Removing the extra `e` at position 17 from the published value yields
`36e24a6cf5680f1e8fc1640a4ee9567a`, which matches the computed MD5 exactly.

**Conclusion:** The published MD5 value for the data file appears to contain a
typo (an extra `e` character, producing a 33-character string). The actual file
content is intact and is a valid XLSX file with the expected structure (5,689 rows,
49 columns). The SHA-256 hash (`919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde`)
was computed from the downloaded file using the codebase's own
`compute_file_hash()` function and is recorded for future integrity verification.

### SHA-256 Hashes (computed via `compute_file_hash()`)

| File | SHA-256 |
|---|---|
| `Wheat_Yld_Eastern_IND_Data.xlsx` | `919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde` |
| `Wheat_Yld_Eastern_IND_Variables.xlsx` | `9987ac2c91de5e58e14d78bf77ba7d257971d8f8621a1ee50d58b31d3715cfc6` |

### File Placement

| File | Local path |
|---|---|
| Data file | `data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Data.xlsx` |
| Variable dictionary | `data/external/cimmyt_wheat/data/Wheat_Yld_Eastern_IND_Variables.xlsx` |

---

## B. Dataset Provenance

| Field | Value |
|---|---|
| Title | Wheat Yield Data — Eastern India |
| Publisher | CIMMYT (International Maize and Wheat Improvement Center) |
| DOI | `10.71682/10549424` |
| Landing page | `https://data.cimmyt.org/dataset.xhtml?persistentId=doi:10.71682/10549424` |
| Data repository | CIMMYT Dataverse (hosted via StorJ gateway) |
| License | Not explicitly stated in files; CIMMYT Dataverse default applies |
| Dataset ID assigned | `cimmyt_wheat_eastern_india_10.71682/10549424` |
| Date acquired | 2026-10-18 |
| Data format | XLSX (Excel Open XML) |

---

## C. Download Verdict

**Download succeeded.** Both files were retrieved as valid binary XLSX files
with the correct `Content-Type` header and valid `PK` (ZIP) magic bytes. No
HTML challenge page or login redirect was encountered. The data file MD5 does
not match the published value due to a likely typo in the published MD5
(33 characters instead of 32). The variables file MD5 matches exactly.

---

## Appendix: Download Commands

```bash
cd data/external/cimmyt_wheat/data
curl.exe -L -s -o Wheat_Yld_Eastern_IND_Data.xlsx \
  "https://data.cimmyt.org/api/access/datafile/60990" \
  -w "HTTP_STATUS:%{http_code}\nCONTENT_TYPE:%{content_type}\n" --max-time 120

curl.exe -L -s -o Wheat_Yld_Eastern_IND_Variables.xlsx \
  "https://data.cimmyt.org/api/access/datafile/60991" \
  -w "HTTP_STATUS:%{http_code}\nCONTENT_TYPE:%{content_type}\n" --max-time 120
```
