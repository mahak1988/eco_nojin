# 🚀 راهنمای راه‌اندازی بک‌اند (Backend Setup)

Frontend فاز ۲.۵ آماده اتصال به بک‌اند FastAPI است. این راهنما نحوهٔ اجرای همزمان هر دو را نشان می‌دهد.

## پیش‌نیاز

- Python 3.11+
- Node.js 20+
- pnpm 11+
- `D:\eco_nojin\.venv` (venv موجود)

## مرحله ۱: راه‌اندازی بک‌اند

```bash
# در PowerShell
cd D:\eco_nojin
.\.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
```

یا با CMD:

```bash
cd D:\eco_nojin
.venv\Scripts\python.exe -m uvicorn services.api_gateway.main:app --reload --port 8000
```

### بررسی سلامت

```bash
curl http://localhost:8000/health
# باید برگرداند: {"status":"healthy",...}

curl http://localhost:8000/openapi.json | head -c 200
# باید JSON OpenAPI برگرداند

curl http://localhost:8000/api/v1/dashboard/public/full
# باید JSON شامل projects/weather/satellite/soil/carbon/mrv باشد
```

## مرحله ۲: راه‌اندازی Frontend

### Terminal 2 — web app (پورت 5173):

```bash
cd D:\eco_nojin\frontend\apps\web
node ../../node_modules/vite/bin/vite.js
```

### Terminal 3 — dashboard app (پورت 5174):

```bash
cd D:\eco_nojin\frontend\apps\dashboard
node ../../node_modules/vite/bin/vite.js
```

## مرحله ۳: تست اتصال

باز کنید:

- http://localhost:5173 — Eco NojiN public portal
- http://localhost:5174 — HyDroMa dashboard

در dashboard:

| صفحه | URL | اندپوینت |
|---|---|---|
| Overview | `/` | `/api/v1/dashboard/public/full` |
| Carbon | `/carbon` | `/api/v1/carbon/calculate` |
| Water | `/water` | `/api/v1/analyses/runoff` |
| Soil | `/soil` | `/api/v1/soil/analyze` |
| Climate | `/climate` | `/api/v1/climate/drought` |
| Satellite | `/satellite` | `/api/v1/satellite/analyze` |
| MRV | `/mrv` | `/api/v1/mrv/carbon-budget` |
| Models | `/models` | `/api/v1/models` |
| Farms | `/farms` | `/api/v1/farms` |
| Marketplace | `/marketplace` | `/api/v1/marketplace` |
| Wallet | `/wallet` | `/api/v1/carbon/wallet` |
| AI Copilot | `/ai-copilot` | `/api/v1/ai/chat` |
| Chat | `/chat` | `/ws/chat` (WebSocket) |

## رفع مشکلات رایج

### ۱. `CORS` خطا

backend در `services/api_gateway/main.py` CORS را روی چند origin فعال کرده. اگر خطا دیدید، origin را اضافه کنید:

```python
# در main.py
origins=["http://localhost:5173", "http://localhost:5174"]
```

### ۲. WebSocket وصل نمی‌شود

endpoint بک‌اند `/ws/chat` باید route ثبت‌شده داشته باشد. اگر نیست، در `services/api_gateway/main.py`:

```python
app.add_api_websocket_route("/ws/chat", chat_handler)
```

### ۳. `401 Unauthorized`

برخی endpoint ها نیاز به JWT دارند. فعلاً endpoint های `public/*` بدون نیاز به توکن کار می‌کنند.

### ۴. `ECONNREFUSED`

بک‌اند در حال اجرا نیست. مرحلهٔ ۱ را دوباره اجرا کنید.

## اسکریپت راه‌اندازی یک‌باره (PowerShell)

```powershell
# راه‌اندازی همزمان هر دو
$root = "D:\eco_nojin"
$frontend = "$root\frontend"

# Backend
Start-Process -FilePath "$root\.venv\Scripts\python.exe" `
  -ArgumentList "-m", "uvicorn", "services.api_gateway.main:app", "--reload", "--port", "8000" `
  -WorkingDirectory $root

# Web
Start-Process -FilePath "node" `
  -ArgumentList "../../node_modules/vite/bin/vite.js" `
  -WorkingDirectory "$frontend\apps\web"

# Dashboard
Start-Process -FilePath "node" `
  -ArgumentList "../../node_modules/vite/bin/vite.js" `
  -WorkingDirectory "$frontend\apps\dashboard"

Write-Host "✅ Backend :8000 | Web :5173 | Dashboard :5174"
```

## ساختار فعلی Monorepo

```
D:\eco_nojin\frontend\
├── apps\
│   ├── web\          # Public Eco NojiN (:5173)
│   └── dashboard\    # HyDroMa workspace (:5174)
├── packages\
│   ├── api\          # Orval + manual clients + Zod schemas
│   ├── auth\         # Zustand auth store
│   ├── charts\       # ECharts wrappers
│   ├── config\       # Constants + env
│   ├── geo\          # MapLibre helpers
│   ├── i18n\         # i18next (fa/ar/ur/en)
│   ├── models\       # Scientific model registry
│   ├── ui\           # Design system
│   └── utils\        # cn, formatters, units
└── tooling\          # TS/Tailwind/Biome presets
```

## فازهای بعدی

- فاز ۳: MapLibre integration + Supabase auth + WebSocket chat backend
- فاز ۴: Advanced analytics + charts + dashboards
- فاز ۵: Production deployment + monitoring