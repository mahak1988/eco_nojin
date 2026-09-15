/**
 * HyDroMa Model Registry — the single source of truth for every scientific
 * model in the engine (engine/hydroma). Zero-orphan policy: every model in
 * this registry is rendered on /dashboard; every engine module is listed here.
 * Implementation tags: 'calculator' = live dashboard calculator, 'engine' =
 * implemented in the Python/C++ engine, 'engine+api' = exposed via gateway.
 */

export type ModelImplementation = 'calculator' | 'engine' | 'engine+api' | 'engine+calculator';

export interface RegistryEntry {
  id: string;
  nameFa: string;
  nameEn: string;
  category: string;
  enginePath: string;
  ref: string;
  impl: ModelImplementation;
  descFa: string;
  descEn: string;
}

export interface RegistryCategory {
  key: string;
  nameFa: string;
  nameEn: string;
}

export const categories: RegistryCategory[] = [
  { key: 'indices', nameFa: 'شاخص‌های ترکیبی هیدروما', nameEn: 'HyDroMa composite indices' },
  { key: 'formulas', nameFa: 'فرمول‌های پایه (محاسبه‌گر داشبورد)', nameEn: 'Core formulas (dashboard calculators)' },
  { key: 'soil', nameFa: 'خاک‌شناسی', nameEn: 'Soil science' },
  { key: 'hydro', nameFa: 'هیدرولوژی و آب زیرزمینی', nameEn: 'Hydrology & groundwater' },
  { key: 'simulation', nameFa: 'شبیه‌سازی زنجیره‌ای', nameEn: 'Simulation chain' },
  { key: 'carbon', nameFa: 'کربن و MRV', nameEn: 'Carbon & MRV' },
  { key: 'climate', nameFa: 'اقلیم و آبیاری', nameEn: 'Climate & irrigation' },
  { key: 'economics', nameFa: 'اقتصاد و تصمیم', nameEn: 'Economics & decision' },
];

const E = (entry: RegistryEntry): RegistryEntry => entry;

export const registry: RegistryEntry[] = [
  /* ---------- indices ---------- */
  E({ id: 'ecsi', nameFa: 'ECSI — شاخص ترسیب کربن', nameEn: 'ECSI — Carbon Sequestration Index', category: 'indices', enginePath: 'engine/hydroma/models/ecsi.py', ref: 'Coleman & Jenkinson 1996 (RothC-26.3)', impl: 'engine', descFa: 'دینامیک کربن خاک بر پایهٔ روت‌سی: dC/dt = I − k·C·f(T)·f(M)·f(P).', descEn: 'Soil carbon dynamics on RothC: dC/dt = I − k·C·f(T)·f(M)·f(P).' }),
  E({ id: 'epia', nameFa: 'EPIA — مشاور آبیاری دقیق', nameEn: 'EPIA — Precision Irrigation Advisor', category: 'indices', enginePath: 'engine/hydroma/models/epia.py', ref: 'FAO-56 (Allen 1998)', impl: 'engine', descFa: 'برنامه‌ریزی آبیاری دقیق: ETc = ET0 × Kc × Ks با Kc از سنتینل-۲.', descEn: 'Precision scheduling: ETc = ET0 × Kc × Ks with Sentinel-2 Kc.' }),
  E({ id: 'esri', nameFa: 'ESRI — شاخص ریسک شوری', nameEn: 'ESRI — Salinity Risk Index', category: 'indices', enginePath: 'engine/hydroma/models/esri.py', ref: 'FAO-29, Richards 1954', impl: 'engine', descFa: 'ترکیب شاخص طیفی شوری + EC خاک + مدیریت آبیاری.', descEn: 'Spectral salinity index + soil EC + irrigation management.' }),
  E({ id: 'ewsi', nameFa: 'EWSI — شاخص تنش آبی', nameEn: 'EWSI — Water Stress Index', category: 'indices', enginePath: 'engine/hydroma/models/ewsi.py', ref: 'Gao 1996, Monteith 1993', impl: 'engine', descFa: 'همجوشی چندمنبعی: NDMI سنتینل + VPD جو + رطوبت ریشه.', descEn: 'Fusion of Sentinel-2 NDMI, atmospheric VPD and root-zone moisture.' }),
  E({ id: 'hdvi', nameFa: 'HDVI — شاخص آسیب‌پذیری خشکسالی', nameEn: 'HDVI — Drought Vulnerability Index', category: 'indices', enginePath: 'engine/hydroma/models/hdvi.py', ref: 'McKee 1993, Vicente-Serrano 2010, Kogan 1995', impl: 'engine', descFa: 'ترکیب SPI + SPEI + VHI + SMI در چند مقیاس.', descEn: 'Multi-scale fusion of SPI, SPEI, VHI and SMI.' }),
  E({ id: 'hlhs', nameFa: 'HLHS — امتیاز سلامت منظر', nameEn: 'HLHS — Landscape Health Score', category: 'indices', enginePath: 'engine/hydroma/models/hlhs.py', ref: 'Shannon 1948, Nagendra 2002', impl: 'engine', descFa: 'شاخص ترکیبی مدیریت صندوق منظر: Σ(wi·norm(Xi)).', descEn: 'Composite landscape-fund score: Σ(wi·norm(Xi)).' }),
  E({ id: 'hpheno', nameFa: 'H-Pheno — فنولوژی گیاه', nameEn: 'H-Pheno — Phenology Detection', category: 'indices', enginePath: 'engine/hydroma/models/hpheno.py', ref: 'Zhang 2003, White 2009', impl: 'engine', descFa: 'هموارسازی ساویتسکی-گلی و مشتق‌گیری سری زمانی NDVI.', descEn: 'Savitzky-Golay smoothing + derivatives on NDVI time series.' }),
  E({ id: 'hyrue', nameFa: 'HY-RUE — مدل بهره‌وری تابش', nameEn: 'HY-RUE — Radiation Use Efficiency', category: 'indices', enginePath: 'engine/hydroma/models/hyrue.py', ref: 'Monteith 1977, Steduto 2009', impl: 'engine', descFa: 'B = Σ(PAR·fIPAR·ε·f_stress) و Y = B×HI با LAI سنتینل-۲.', descEn: 'B = Σ(PAR·fIPAR·ε·f_stress), Y = B×HI with Sentinel-2 LAI.' }),
  E({ id: 'runoff-model', nameFa: 'مدل رواناب سطحی', nameEn: 'Surface runoff model', category: 'indices', enginePath: 'engine/hydroma/models/runoff_model.py', ref: 'SCS-CN', impl: 'engine', descFa: 'محاسبهٔ رواناب سطحی حوضه.', descEn: 'Surface runoff computation for the catchment.' }),

  /* ---------- formulas (dashboard calculators) ---------- */
  E({ id: 'horton-infiltration', nameFa: 'نفوذ هورتون', nameEn: 'Horton infiltration', category: 'formulas', enginePath: 'HP-01/03 · F-01', ref: 'Horton 1940', impl: 'calculator', descFa: 'f(t)=fc+(f0−fc)e^(−kt) و نفوذ تجمعی — محاسبه‌گر زنده در داشبورد.', descEn: 'f(t)=fc+(f0−fc)e^(−kt) + cumulative — live dashboard calculator.' }),
  E({ id: 'scs-cn-runoff', nameFa: 'رواناب SCS-CN', nameEn: 'SCS-CN runoff', category: 'formulas', enginePath: 'HP-01/03 · F-02/03', ref: 'USDA-NRCS TR-55', impl: 'calculator', descFa: 'S=25400/CN−254 و Q=(P−0.2S)²/(P+0.8S) — محاسبه‌گر زنده.', descEn: 'S=25400/CN−254 and Q=(P−0.2S)²/(P+0.8S) — live calculator.' }),
  E({ id: 'van-genuchten', nameFa: 'منحنی رطوبت Van Genuchten', nameEn: 'Van Genuchten retention', category: 'formulas', enginePath: 'HP-01/06 · F-04 + soil/water_retention.py', ref: 'van Genuchten 1980, Mualem 1976', impl: 'engine+calculator', descFa: 'θ(h) و هدایت هیدرولیکی اشباع‌نشده — محاسبه‌گر + موتور.', descEn: 'θ(h) and unsaturated K — calculator + engine implementation.' }),
  E({ id: 'darcy-law', nameFa: 'قانون دارسی', nameEn: 'Darcy law', category: 'formulas', enginePath: 'HP-01 · F-06 + groundwater/service.py', ref: 'Freeze & Cherry 1979', impl: 'engine+calculator', descFa: 'q = K·i·A — محاسبه‌گر زنده + سرویس آب زیرزمینی.', descEn: 'q = K·i·A — live calculator + groundwater service.' }),
  E({ id: 'manning-channel', nameFa: 'هیدرولیک کانال مانینگ', nameEn: 'Manning channel hydraulics', category: 'formulas', enginePath: 'HP-02 · F-02/03', ref: 'Manning 1889', impl: 'calculator', descFa: 'Q=(1/n)·A·R^⅔·S^½ و R=A/P — محاسبه‌گر زنده.', descEn: 'Q=(1/n)·A·R^⅔·S^½ and R=A/P — live calculator.' }),
  E({ id: 'reynolds-number', nameFa: 'عدد رینولدز', nameEn: 'Reynolds number', category: 'formulas', enginePath: 'HP-02 · F-04', ref: 'Reynolds 1883', impl: 'calculator', descFa: 'Re = ρ·v·D/μ — تشخیص رژیم جریان.', descEn: 'Re = ρ·v·D/μ — flow regime detection.' }),
  E({ id: 'froude-number', nameFa: 'عدد فرود', nameEn: 'Froude number', category: 'formulas', enginePath: 'HP-02 · F-05', ref: 'Froude 1873', impl: 'calculator', descFa: 'Fr = v/√(g·D) — زیربحرانی/فوقبحرانی.', descEn: 'Fr = v/√(g·D) — sub/super-critical.' }),
  E({ id: 'francis-weir', nameFa: 'سرریز فرانسیس', nameEn: 'Francis weir', category: 'formulas', enginePath: 'HP-01/02 · F-08/F-12', ref: 'Francis 1883', impl: 'calculator', descFa: 'Q = 1.84·L·H^1.5 — محاسبه‌گر زنده.', descEn: 'Q = 1.84·L·H^1.5 — live calculator.' }),
  E({ id: 'ring-storage', nameFa: 'ذخیرهٔ حلقهٔ سنگی', nameEn: 'Stone-ring storage', category: 'formulas', enginePath: 'HP-03 · F-01/02', ref: 'HyDroMa HP-03', impl: 'calculator', descFa: 'V = π·r²·h·n_eff و تخلخل مؤثر لایه‌ای — محاسبه‌گر زنده.', descEn: 'V = π·r²·h·n_eff + layered effective porosity — live calculator.' }),

  /* ---------- soil ---------- */
  E({ id: 'soil-texture', nameFa: 'مثلث بافت خاک USDA', nameEn: 'USDA texture triangle', category: 'soil', enginePath: 'engine/hydroma/soil/texture.py', ref: 'USDA NRCS', impl: 'engine', descFa: 'طبقه‌بندی ۱۲ کلاسهٔ بافت بر اساس ماسه/سیلت/رس.', descEn: '12-class texture classification from sand/silt/clay.' }),
  E({ id: 'soil-taxonomy', nameFa: 'رده‌بندی خاک', nameEn: 'Soil taxonomy', category: 'soil', enginePath: 'engine/hydroma/soil/taxonomy.py', ref: 'Keys to Soil Taxonomy 13th', impl: 'engine', descFa: 'رده‌بندی نظام USDA.', descEn: 'USDA taxonomy classification.' }),
  E({ id: 'soil-water-retention', nameFa: 'مدل نگهداشت آب خاک', nameEn: 'Soil water retention', category: 'soil', enginePath: 'engine/hydroma/soil/water_retention.py', ref: 'van Genuchten 1980; Mualem 1976', impl: 'engine', descFa: 'نگهداشت آب و هدایت هیدرولیکی اشباع‌نشده.', descEn: 'Water retention and unsaturated hydraulic conductivity.' }),
  E({ id: 'pedotransfer', nameFa: 'توابع انتقال خاک', nameEn: 'Pedotransfer functions', category: 'soil', enginePath: 'engine/hydroma/soil/pedotransfer.py', ref: 'Saxton & Rawls 2006', impl: 'engine', descFa: 'برآورد خاکی-آبی از بافت و مادهٔ آلی.', descEn: 'Hydraulic estimates from texture and organic matter.' }),
  E({ id: 'soil-physics', nameFa: 'فیزیک خاک', nameEn: 'Soil physics', category: 'soil', enginePath: 'engine/hydroma/soil/physics.py', ref: 'Brooks-Corey 1964; Campbell 1974', impl: 'engine', descFa: 'مدل‌های فیزیکی نگهداشت و هدایت.', descEn: 'Physical retention/conductivity models.' }),
  E({ id: 'soil-chemistry', nameFa: 'شیمی خاک', nameEn: 'Soil chemistry', category: 'soil', enginePath: 'engine/hydroma/soil/chemistry.py', ref: 'Brady & Weil 2017', impl: 'engine', descFa: 'CEC، ESP، SAR و نیاز آهک.', descEn: 'CEC, ESP, SAR and lime requirement.' }),
  E({ id: 'soil-salinity', nameFa: 'شوری خاک', nameEn: 'Soil salinity', category: 'soil', enginePath: 'engine/hydroma/soil/salinity.py', ref: 'USDA Handbook 60', impl: 'engine', descFa: 'رده‌بندی شوری و مدیریت.', descEn: 'Salinity classification and management.' }),
  E({ id: 'soil-health', nameFa: 'سلامت خاک', nameEn: 'Soil health', category: 'soil', enginePath: 'engine/hydroma/soil/health.py', ref: 'USDA NRCS 2023', impl: 'engine', descFa: 'محاسبهٔ شاخص جامع سلامت خاک.', descEn: 'Comprehensive soil health index.' }),
  E({ id: 'soil-recommendations', nameFa: 'توصیه‌های خاک', nameEn: 'Soil recommendations', category: 'soil', enginePath: 'engine/hydroma/soil/recommendations.py', ref: 'USDA NRCS 2023', impl: 'engine', descFa: 'موتور توصیهٔ مدیریت خاک.', descEn: 'Soil management recommendation engine.' }),

  /* ---------- hydro ---------- */
  E({ id: 'groundwater-model', nameFa: 'مدل آب زیرزمینی', nameEn: 'Groundwater model', category: 'hydro', enginePath: 'engine/hydroma/models/groundwater_model.py', ref: '—', impl: 'engine', descFa: 'مدل‌سازی پایهٔ آب زیرزمینی/اتصال به مدل بیرونی.', descEn: 'Basic groundwater modelling / external model bridge.' }),
  E({ id: 'groundwater-service', nameFa: 'سرویس آب زیرزمینی', nameEn: 'Groundwater service', category: 'hydro', enginePath: 'engine/hydroma/groundwater/service.py', ref: 'Todd & Mays 2005', impl: 'engine', descFa: 'دارسی + شاخص پایداری + بیلان آبخوان.', descEn: 'Darcy + sustainability index + aquifer balance.' }),
  E({ id: 'runoff-surface', nameFa: 'رواناب سطحی', nameEn: 'Surface runoff', category: 'hydro', enginePath: 'engine/hydroma/models/runoff_model.py', ref: 'SCS-CN', impl: 'engine', descFa: 'محاسبهٔ رواناب سطحی (سرویس موتور).', descEn: 'Surface runoff computation (engine service).' }),

  /* ---------- simulation ---------- */
  E({ id: 'sim-orchestrator', nameFa: 'هماهنگ‌کنندهٔ زنجیره', nameEn: 'Chain orchestrator', category: 'simulation', enginePath: 'engine/hydroma/simulation/orchestrator.py', ref: 'doc 28/36', impl: 'engine', descFa: 'اجرای زنجیرهٔ RUSLE → AquaCrop → RothC با برچسب منشأ داده.', descEn: 'Runs the RUSLE → AquaCrop → RothC chain with provenance labels.' }),
  E({ id: 'hecras', nameFa: 'یکپارچه‌سازی HEC-RAS', nameEn: 'HEC-RAS integration', category: 'simulation', enginePath: 'engine/hydroma/simulation/hecras.py', ref: 'HEC-RAS', impl: 'engine', descFa: 'شبیه‌سازی جریان و گسترهٔ سیلاب بر اساس هندسهٔ کانال.', descEn: 'Hydraulic flow and flood-extent simulation from channel geometry.' }),
  E({ id: 'weap', nameFa: 'یکپارچه‌سازی WEAP', nameEn: 'WEAP integration', category: 'simulation', enginePath: 'engine/hydroma/simulation/weap.py', ref: 'WEAP', impl: 'engine', descFa: 'تخصیص آب بر اساس عرضه و تقاضا.', descEn: 'Water allocation from demand and supply data.' }),
  E({ id: 'sim-calibration', nameFa: 'حساسیت‌سنجی و عدم قطعیت', nameEn: 'Sensitivity & uncertainty', category: 'simulation', enginePath: 'engine/hydroma/simulation/calibration.py', ref: 'Saltelli 2010 (Sobol)', impl: 'engine', descFa: 'نمونه‌برداری سالتلی و شاخص‌های سوبول (تأییدشده با تابع ایشیگامی).', descEn: 'Saltelli sampling + Sobol indices (verified on Ishigami).' }),
  E({ id: 'sim-scenarios', nameFa: 'ماتریس سناریوها', nameEn: 'Scenario matrices', category: 'simulation', enginePath: 'engine/hydroma/simulation/scenarios.py', ref: 'doc 28', impl: 'engine', descFa: 'سناریوهای پایه/متوسط/شدید: کاهش CN، ضریب C، P-RUSLE.', descEn: 'Baseline/Medium/Intensive: CN reduction, C-factor, RUSLE P.' }),
  E({ id: 'weather-source', nameFa: 'منبع هواشناسی واقعی', nameEn: 'Real weather source', category: 'simulation', enginePath: 'engine/hydroma/simulation/weather_source.py', ref: 'Open-Meteo + FAO-56 Hargreaves', impl: 'engine', descFa: 'هوای تاریخی روزانه + ET0 هاگریوز — شکست صریح بدون سقوط خاموش.', descEn: 'Daily historical weather + ET0; explicit failure, no silent fallback.' }),

  /* ---------- carbon ---------- */
  E({ id: 'carbon-calculator', nameFa: 'محاسبه‌گر ترسیب کربن', nameEn: 'Carbon sequestration calculator', category: 'carbon', enginePath: 'engine/hydroma/carbon/calculator.py', ref: 'Verra VCS, Gold Standard, IPCC', impl: 'engine', descFa: 'محاسبهٔ ترسیب برای جنگل‌کاری، خاک، بیوچار و آگروفارستری.', descEn: 'Sequestration for afforestation, soil, biochar and agroforestry.' }),
  E({ id: 'mrv-satellite', nameFa: 'MRV ماهواره‌ای (CDSE)', nameEn: 'Satellite MRV (CDSE)', category: 'carbon', enginePath: 'engine/hydroma/mrv/satellite_cdse.py', ref: 'Copernicus CDSE STAC', impl: 'engine+api', descFa: 'NDVI واقعی سنتینل-۲ (B04/B08) با انضباط منشأ داده.', descEn: 'Real Sentinel-2 NDVI (B04/B08) with provenance discipline.' }),
  E({ id: 'mrv-iot', nameFa: 'MRV اینترنت اشیا', nameEn: 'IoT MRV', category: 'carbon', enginePath: 'engine/hydroma/mrv/iot_ingest.py', ref: 'MQTT / TTN v3', impl: 'engine+api', descFa: 'ورودی حسگرها با QA/QC و ردپای حسابرسی.', descEn: 'Sensor ingest with QA/QC screening and audit trail.' }),
  E({ id: 'mrv-citizen', nameFa: 'MRV شهروندی', nameEn: 'Citizen MRV', category: 'carbon', enginePath: 'engine/hydroma/mrv/schemas.py', ref: 'EM-01', impl: 'engine+api', descFa: 'سطح ۳: گزارش‌های میدانی آفلاین-اول کشاورزان.', descEn: 'Level 3: offline-first citizen field reports.' }),
  E({ id: 'mrv-qa', nameFa: 'QA/QC مشاهدات', nameEn: 'Observation QA/QC', category: 'carbon', enginePath: 'engine/hydroma/mrv/qa.py', ref: 'EM-01', impl: 'engine+api', descFa: 'بندهای فیزیکی پذیرش/مشکوک/رد با ردپای حسابرسی.', descEn: 'Plausibility bands (accepted/suspect/rejected) + audit trail.' }),
  E({ id: 'mrv-metrics', nameFa: 'سنجه‌های شفاف MRV', nameEn: 'Transparent MRV metrics', category: 'carbon', enginePath: 'engine/hydroma/mrv/metrics.py', ref: 'EM-01 §3', impl: 'engine+api', descFa: 'هر سنجه نشان منشأ دارد: real / simulated / no_data.', descEn: 'Every metric carries a provenance badge: real / simulated / no_data.' }),

  /* ---------- climate ---------- */
  E({ id: 'et-calculator', nameFa: 'تبخیر-تعرق مرجع FAO-56', nameEn: 'FAO-56 reference ET0', category: 'climate', enginePath: 'engine/hydroma/climate/et_calculator.py', ref: 'Allen et al. 1998', impl: 'engine+api', descFa: 'پنمن-مونتیث کامل + هاگریوز-سمانی (فقط دما).', descEn: 'Full Penman-Monteith + Hargreaves-Samani (temperature-only).' }),
  E({ id: 'irrigation-scheduler', nameFa: 'برنامه‌ریز آبیاری', nameEn: 'Irrigation scheduler', category: 'climate', enginePath: 'engine/hydroma/irrigation/scheduler.py', ref: 'FAO-56; Keller & Bliesner 1990', impl: 'engine', descFa: 'زمان‌بندی آبیاری بر پایهٔ ETc و رطوبت خاک.', descEn: 'Scheduling from ETc and soil moisture.' }),

  /* ---------- economics ---------- */
  E({ id: 'econ-analysis', nameFa: 'تحلیل اقتصادی پروژه', nameEn: 'Project economic analysis', category: 'economics', enginePath: 'engine/hydroma/economics/analysis.py', ref: 'FAO Investment Centre', impl: 'engine', descFa: 'روش‌شناسی مرکز سرمایه‌گذاری فائو.', descEn: 'FAO Investment Centre methodology.' }),
  E({ id: 'econ-costing', nameFa: 'برآورد هزینه', nameEn: 'Costing engine', category: 'economics', enginePath: 'engine/hydroma/economics/costing.py', ref: 'HyDroMa', impl: 'engine', descFa: 'هزینه‌های مدیریت زمین، کشاورزی و زیرساخت.', descEn: 'Land-management, agriculture and infrastructure costs.' }),
  E({ id: 'econ-revenue', nameFa: 'گردآوری درآمد', nameEn: 'Revenue engine', category: 'economics', enginePath: 'engine/hydroma/economics/revenue.py', ref: 'HyDroMa', impl: 'engine', descFa: 'عملکرد، اعتبار کربن و خدمات اکوسیستم.', descEn: 'Yield, carbon credits and ecosystem services.' }),
  E({ id: 'econ-roi', nameFa: 'NPV / IRR / بازگشت', nameEn: 'NPV / IRR / payback', category: 'economics', enginePath: 'engine/hydroma/economics/roi.py', ref: 'HyDroMa', impl: 'engine', descFa: 'شاخص‌های عملکرد مالی پروژه.', descEn: 'Project financial performance indicators.' }),
  E({ id: 'econ-employment', nameFa: 'اشتغال‌زایی', nameEn: 'Employment generation', category: 'economics', enginePath: 'engine/hydroma/economics/employment.py', ref: 'HyDroMa', impl: 'engine', descFa: 'اثرات مستقیم، غیرمستقیم و القایی اشتغال.', descEn: 'Direct, indirect and induced employment effects.' }),
  E({ id: 'econ-risk', nameFa: 'ارزیابی ریسک مالی', nameEn: 'Financial risk assessment', category: 'economics', enginePath: 'engine/hydroma/economics/risk.py', ref: 'HyDroMa', impl: 'engine', descFa: 'ارزیابی ریسک‌های مالی پروژه.', descEn: 'Project financial risk evaluation.' }),
  E({ id: 'econ-integration', nameFa: 'یکپارچه‌سازی اقتصاد', nameEn: 'Economic integration', category: 'economics', enginePath: 'engine/hydroma/economics/integration.py', ref: 'HyDroMa', impl: 'engine', descFa: 'اتصال خروجی کشاورزی/زیرساخت/کربن به موتور اقتصاد.', descEn: 'Feeds agriculture/infrastructure/carbon outputs into economics.' }),

  /* ---------- decision ---------- */
  E({ id: 'multi-objective-optimizer', nameFa: 'بهینه‌سازی چندهدفه', nameEn: 'Multi-objective optimizer', category: 'economics', enginePath: 'engine/hydroma/optimization/optimizer.py', ref: 'NSGA-style', impl: 'engine', descFa: 'بیشینهٔ عملکرد/سود/پایداری و کمینهٔ هزینه/ریسک.', descEn: 'Maximize yield/profit/sustainability; minimize cost/risk.' }),
  E({ id: 'decision-support', nameFa: 'سیستم پشتیبان تصمیم', nameEn: 'Decision Support System', category: 'economics', enginePath: 'engine/hydroma/decision_support/dss.py', ref: 'HyDroMa', impl: 'engine', descFa: 'ترکیب سناریوها، بهینه‌سازی و ریسک به توصیهٔ عملی.', descEn: 'Synthesizes scenarios, optimization and risk into recommendations.' }),
];

export const registryStats = {
  total: registry.length,
  calculators: registry.filter((entry) => entry.impl === 'calculator' || entry.impl === 'engine+calculator').length,
  engine: registry.filter((entry) => entry.impl === 'engine' || entry.impl === 'engine+api').length,
};
