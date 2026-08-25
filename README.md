# Eco Nojin (اکو نوژین) / HyDroMa (هیدروما)

## English

Eco Nojin is an international, standards-based platform for ecosystem restoration,
smart agriculture, water and soil management, rural prosperity, pastoralist support,
carbon incentives, marketplace, and ecotourism.

HyDroMa is the scientific and computational engine of Eco Nojin.

### Quick start

```bash
# Python 3.11+ virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# API gateway
uvicorn services.api_gateway.main:app --reload --port 8000

# Frontend (Next.js)
cd frontend
pnpm install
pnpm run dev

# Tests
pytest
```

### Layout

| Path | Purpose |
|---|---|
| `engine/hydroma/` | Scientific engine (soil, climate, hydrology, erosion, carbon, satellite, scenarios, biofertilizer, economics, finance, risk, irrigation, groundwater, materials, ecotourism, land, infrastructure, decision support, simulation, calibration, mrv, standards) |
| `engine/cpp_core/` | C++20 numerical core (Richards, Saint-Venant, FAO-56, RUSLE, sampling) with pybind11 bindings |
| `services/` | Microservices (api_gateway, admin, auth, ledger, notification, reporting, workflow, analytics, bots, carbon, content, data_sources, ecowallet, field_monitoring, land, map_engine, mobile_monitoring, science, scientific_motors, supabase, telegram_bot) |
| `frontend/` | Next.js PWA with 14-language i18n (fa/ar/ur RTL) |
| `docs/en` `docs/fa` | Bilingual documentation (00–12) |
| `tests/` | Unit + integration tests |

### Honesty note on satellite data

The `earth_search` provider returns **simulated** tiles (labeled
`data_source="simulated"`). Real Sentinel-2 ingestion requires an S3 download
path that is not yet implemented. Never present simulated data as real
observations.

### Documentation

- `docs/en/00_master_plan.md`, `docs/fa/00_master_plan.md` – master plan
- `docs/10_quality_standards.md` – internal quality standards STD-001–015
- `docs/11_weaknesses_and_fixes.md` – known weaknesses W-001–021 with evidence
- `docs/12_30_year_strategy.md` – 30-year maintenance strategy (until 2055)

---

## فارسی

اکو نوژین یک پلتفرم بین‌المللی و مبتنی بر استاندارد برای ترمیم اکوسیستم،
کشاورزی هوشمند، مدیریت آب و خاک، رفاه روستایی، حمایت از دامداران و عشایر،
انگیزه‌های کربن، بازارگاه و اکوتوریسم است.

هایدروما (HyDroMa) موتور علمی و محاسباتی اکو نوژین است.

### شروع سریع

```bash
# محیط مجازی پایتون 3.11+
python -m venv .venv
.venv\Scripts\activate          # ویندوز
pip install -r requirements.txt

# دروازه API
uvicorn services.api_gateway.main:app --reload --port 8000

# فرانت‌اند (Next.js)
cd frontend
pnpm install
pnpm run dev

# تست‌ها
pytest
```

### ساختار

| مسیر | کاربرد |
|---|---|
| `engine/hydroma/` | موتور علمی (خاک، اقلیم، هیدرولوژی، فرسایش، کربن، ماهواره، سناریو، بیوفرتیلایزر، اقتصاد، مالی، ریسک، آبیاری، آب زیرزمینی، مواد، اکوتوریسم، زمین، زیرساخت، تصمیم‌گیری، شبیه‌سازی، کالیبراسیون، MRV، استانداردها) |
| `engine/cpp_core/` | هسته عددی C++20 (ریچاردز، سن‌ونان، FAO-56، RUSLE، نمونه‌برداری) با اتصال pybind11 |
| `services/` | میکروسرویس‌ها (api_gateway، admin، auth، ledger، notification، reporting، workflow، analytics، bots، carbon، content، data_sources، ecowallet، field_monitoring، land، map_engine، mobile_monitoring، science، scientific_motors، supabase، telegram_bot) |
| `frontend/` | PWA مبتنی بر Next.js با بومی‌سازی ۱۴ زبانه (فارسی/عربی/اردو RTL) |
| `docs/en` `docs/fa` | مستندات دوزبانه (۰۰–۱۲) |
| `tests/` | تست‌های واحد و یکپارچه |

### نکته صداقت درباره داده ماهواره

ارائه‌دهنده `earth_search` تایل‌های **شبیه‌سازی‌شده** برمی‌گرداند (برچسب
`data_source="simulated"`). دریافت واقعی Sentinel-2 نیازمند مسیر دانلود S3 است
که هنوز پیاده‌سازی نشده. داده شبیه‌سازی‌شده را هرگز به عنوان مشاهدات واقعی ارائه نکنید.

### مستندات

- `docs/en/00_master_plan.md`، `docs/fa/00_master_plan.md` – نقشه جامع
- `docs/10_quality_standards.md` – استانداردهای کیفیت داخلی STD-001–015
- `docs/11_weaknesses_and_fixes.md` – نقاط ضعف شناخته‌شده W-001–021 همراه با شواهد
- `docs/12_30_year_strategy.md` – استراتژی نگهداری ۳۰ ساله (تا ۲۰۵۵)

## Installation

```bash
git clone https://github.com/mahak1988/eco_nojin.git
cd eco_nojin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn services.api_gateway.main:app --reload
```

## Usage

```bash
curl -X POST http://127.0.0.1:8000/api/v1/platform/analyze \
  -H "Content-Type: application/json" \
  -d '{"name": "Farm", "latitude": 35.6892, "longitude": 51.3890, "area_ha": 50.0}'
```

## API Documentation

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## License

MIT License
