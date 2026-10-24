# Stage 41-E — Live-input benchmark

- Records expected: 1722
- Source workbook SHA-256: `919e7d535da19faf2ae11e51d50b81b424e5a5b09b5f2ad42b7d90310edb4fde`
- Test-frame IDs SHA-256: `c90dee1be1342cd200e8dfc902ccf64c78f684fb733aa9adc92366eab82189c0`
- Result rows: 1722
- Unique record IDs: 1722
- Status counts: `{'COMPUTED': 1700, 'BLOCKED': 21, 'FAILED': 1}`
- Weather-source counts: `{'open_meteo_era5': 1701, 'unknown': 21}`
- Input-quality counts: `{'complete': 1700, 'unavailable': 22}`
- Captured resolved-input records: 1700
- Missing results: 0
- Computed rows missing input capture: 0
- Parameters: ε=2.63, HI=0.45; baseline ε=2.2
- Current pipeline identity hash: `['dd3527db92c073a03ceb6d73fee375990f655f982cdab3321e252cb34401f3c9']`
- Stage 40 frozen model code hash: `1ae6ddbd5a8c17ca2eafcf6909956dda7e0744633f70744e19a65069c2c1e3f6`
- Runner/driver source hashes: `{'engine/hydroma/eval/resumable_benchmark_runner.py': 'ad403596c6829702cd748be869307d2cb109b3d3b9cca1ba080a9c43b444ddb7', 'engine/hydroma/eval/seasonal_predictor.py': '322374c4b3afa10f79c487d1dac2428d74b06b69bd8925cef386772576f2dc80', 'engine/hydroma/eval/identifiability_calibration.py': '6b2e76e31cc301243f0d3b5c0e4a11bb65c82527cbd722040f94e9fa6ff2d580', 'engine/hydroma/simulation/weather_source.py': '7454e2b14b34b73b6fa0d163bb9afe6e70bdcd21277f43bf17e0ca7318aa71c2', 'engine/hydroma/simulation/par_pipeline.py': '61a1fd00166528b1f99927d268f8729ccf4bcbe624629d81188b3bd6b199956e', 'engine/hydroma/models/hyrue.py': 'cc437a5026edf41cbb4ea3ef19de53ae0fbfcca0df6800692441713f2e6dbf3d', 'tools/diagnostics/stage41_run_test_benchmark.py': '89208ba898943b8c2d0b9b5c3b1e349e0d9c8cd00a09d4d954e8a2ceade45868', 'tools/diagnostics/stage41_run_parallel_benchmark.py': '583252f8adbd885768ae582aee35ac3f27f2c0172d46f14ee43770179c9f4314'}`
- Stage 40 file-hash comparison: `{'engine/hydroma/eval/seasonal_predictor.py': {'stage40_sha256': '68c7da0e490b0da724a4cd308614259b1a9919592dacbca60100e3c8d70966ef', 'current_sha256': '322374c4b3afa10f79c487d1dac2428d74b06b69bd8925cef386772576f2dc80', 'matches': False}, 'engine/hydroma/eval/identifiability_calibration.py': {'stage40_sha256': '999465b119477c2397351f6bde48dab4143f709d7d7f1c5d1f86fbf12668817b', 'current_sha256': '6b2e76e31cc301243f0d3b5c0e4a11bb65c82527cbd722040f94e9fa6ff2d580', 'matches': False}, 'engine/hydroma/simulation/weather_source.py': {'stage40_sha256': '7454e2b14b34b73b6fa0d163bb9afe6e70bdcd21277f43bf17e0ca7318aa71c2', 'current_sha256': '7454e2b14b34b73b6fa0d163bb9afe6e70bdcd21277f43bf17e0ca7318aa71c2', 'matches': True}, 'engine/hydroma/simulation/par_pipeline.py': {'stage40_sha256': '61a1fd00166528b1f99927d268f8729ccf4bcbe624629d81188b3bd6b199956e', 'current_sha256': '61a1fd00166528b1f99927d268f8729ccf4bcbe624629d81188b3bd6b199956e', 'matches': True}, 'engine/hydroma/models/hyrue.py': {'stage40_sha256': 'cc437a5026edf41cbb4ea3ef19de53ae0fbfcca0df6800692441713f2e6dbf3d', 'current_sha256': 'cc437a5026edf41cbb4ea3ef19de53ae0fbfcca0df6800692441713f2e6dbf3d', 'matches': True}}`
- This is a fresh live-input run using current code; it is not proof of Stage 40 code equivalence or direct comparability with Stage 40.
- Current and Stage 40 aggregate model-code hashes differ; both `seasonal_predictor.py` and `identifiability_calibration.py` have different file hashes. Numerical scientific equivalence is unproven.
- Weather-source attribution is not verified: fetch results do not set the `source` attribute consumed by the runner, which defaults successful rows to `open_meteo_era5`; the logs also record HTTP 429 and NASA POWER fallback messages.

| Metric | Baseline ε=2.2 | Calibrated ε=2.63 | Mean predictor |
|---|---:|---:|---:|
| n | 1700 | 1700 | 1700 |
| RMSE | 2.886178181 | 2.837688753 | 1.096671034 |
| MAE | 2.39244059 | 2.30859337 | 0.898455672 |
| Bias | -2.203416248 | -1.83826853 | -1.92264505e-16 |
| R² | -5.926176148 | -5.695403759 | 0 |
| MAPE (%) | 53.65714375 | 52.7911869 | 23.66544804 |

## Non-computed records

| Status | Failure reason | Count | Record IDs |
|---|---|---:|---|
| BLOCKED | Weather fetch failed: float() argument must be a string or a real number, not 'NoneType' | 21 | 1002, 1003, 1151, 1343, 1541, 1558, 1590, 1744, 1759, 1839, 1869, 206, 207, 235, 409, 4323, 4340, 4369, 4384, 5968, 735 |
| FAILED | HYRUE computation failed: float() argument must be a string or a real number, not 'NoneType' | 1 | 4238 |

- Calibrated minus baseline ΔRMSE: -0.04848942814 t/ha.
- Calibrated minus mean ΔRMSE: 1.741017718 t/ha.
- Complete 1,722-row accounting: `True`.
- Complete input capture for computed records: `True`.
- Stage 40 equivalence remains unproven; this run alone does not upgrade the Stage 41 closure verdict.
