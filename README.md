# Eco Nojin / HyDroMa

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
| `engine/hydroma/` | Scientific engine (soil, climate, hydrology, erosion, carbon, satellite, scenarios) |
| `engine/cpp_core/` | C++20 numerical core (Richards, Saint-Venant, FAO-56, RUSLE, sampling) with pybind11 bindings |
| `services/` | Microservices (api_gateway, auth, ledger, notification, reporting, workflow) |
| `frontend/` | Next.js PWA with 14-language i18n (fa/ar/ur RTL) |
| `docs/en` `docs/fa` | Bilingual documentation (00–12) |
| `tests/` | Unit + integration tests |

### Honesty note on satellite data

The `earth_search` provider returns **simulated** tiles (labeled
`data_source="simulated"`). Real Sentinel-2 ingestion requires an S3 download
path that is not yet implemented. Never present simulated data as real
observations.

### Documentation

- `docs/en/00_master_plan.md`, `docs/fa/00_master_plan.md` — master plan
- `docs/10_quality_standards.md` — internal quality standards STD-001…015
- `docs/11_weaknesses_and_fixes.md` — known weaknesses W-001…021 with evidence
- `docs/12_30_year_strategy.md` — 30-year maintenance strategy (until 2055)

---

## فارسی

اکو نوژین پلتفرمی بین‌المللی و مبتنی بر استاندارد برای احیای اکوسیستم،
کشاورزی هوشمند، مدیریت آب و خاک، رونق روستایی، حمایت از عشایر، مشوق‌های
کربن، بازارچه و بوم‌گردی است.

«هیدروما» (HyDroMa) موتور علمی و محاسباتی اکو نُجین است.

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
npm install
npm run dev

# تست‌ها
pytest
```

### ساختار

| مسیر | کاربرد |
|---|---|
| `engine/hydroma/` | موتور علمی (خاک، اقلیم، هیدرولوژی، فرسایش، کربن، ماهواره، سناریو) |
| `engine/cpp_core/` | هسته عددی C++20 (ریچاردز، سنت-ونانت، FAO-56، RUSLE، نمونه‌برداری) با اتصال pybind11 |
| `services/` | میکروسرویس‌ها (api_gateway، auth، ledger، notification، reporting، workflow) |
| `frontend/` | PWA مبتنی بر Next.js با i18n چهارده‌زبانه (RTL برای فارسی/عربی/اردو) |
| `docs/en` `docs/fa` | مستندات دوزبانه (۰۰ تا ۱۲) |
| `tests/` | تست‌های واحد و یکپارچه |

### نکته صداقت درباره داده ماهواره‌ای

تأمین‌کننده `earth_search` فعلاً داده **شبیه‌سازی‌شده** برمی‌گرداند (با برچسب
`data_source="simulated"`). دریافت تصاویر واقعی Sentinel-2 نیازمند مسیر
دانلود S3 است که هنوز پیاده‌سازی نشده. داده شبیه‌سازی‌شده هرگز نباید به‌عنوان
مشاهده واقعی ارائه شود.

### مستندات

- `docs/fa/00_master_plan.md` — نقشه راه کلان
- `docs/fa/10_quality_standards.md` — استانداردهای کیفی داخلی STD-001…015
- `docs/fa/11_weaknesses_and_fixes.md` — نقاط ضعف شناخته‌شده W-001…021 همراه شواهد
- `docs/fa/12_30_year_strategy.md` — راهبرد نگهداری ۳۰ ساله (تا ۲۰۵۵)
