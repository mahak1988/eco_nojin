# 03. Eco Nojin Platform

**Status:** Approved | **Version:** 1.0.0 | **Language:** English

## 1. What Eco Nojin Is

Eco Nojin is an international, standards-based platform for ecosystem
restoration, smart agriculture, water and soil management, rural prosperity,
pastoralist support, carbon incentives, marketplace, and ecotourism. It is
built around the HyDroMa scientific engine (see `02_hydroma_engine.md`).

## 2. Target Users

- Smallholder farmers — yield optimization, water efficiency, climate resilience
- Pastoralists and nomads — migration routing, forage monitoring, livestock insurance
- Rural youth and women — gig economy, ecotourism, local processing
- Cooperatives — group sales and input procurement
- Governments and NGOs — MRV tools for national climate commitments
- Buyers and impact investors — verified organic/carbon products

## 3. User Interfaces

1. **Web/PWA** (`frontend/`): Next.js, 14-language i18n, installable PWA with
   offline-first storage hooks (IndexedDB), service worker, Capacitor-ready
   for Android/iOS packaging. Panels: soil, satellite, crop planner, scenarios,
   carbon, watershed, marketplace, benchmarks, mobile features, AI chat.
2. **USSD/SMS gateway** (`engine/hydroma/ussd/` + `services/api_gateway/routers/ussd.py`):
   feature-phone access with telco webhook formats (Africa's Talking, Twilio,
   Kavehnegar, generic). USSD menu `*384*73#`, SMS commands (SOIL, CROP,
   PRICE, WEATHER, ASK).
3. **Voice AI (IVR):** planned for low-literacy users.

## 4. API Gateway

FastAPI gateway (`services/api_gateway/`) exposing `/api/v1/*`:

| Area | Endpoints |
|---|---|
| Soil & materials | profile CRUD, compost C/N formulation |
| Satellite | point analysis (NDVI/EVI/SAVI/NDWI/NBR), health |
| Scenarios | SSP projections, crop simulation, what-if, Monte Carlo |
| Carbon | project types, calculation, registration, verification |
| Marketplace | products, producers, orders, traceability |
| Watershed | check dams, contour trenches, half-moons |
| AI assistant | chat (RAG), health |
| Sync | offline batch sync for mobile clients |
| USSD/SMS | webhook handlers |
| Benchmark | performance comparisons |
| System | `/api/v1/health` |

## 5. Services Status (honest)

| Service | Status |
|---|---|
| api_gateway | Implemented (FastAPI) |
| auth, ledger, workflow, notification, reporting | **Placeholders** (print-only stubs) |
| blockchain, ml, data, deploy | Empty scaffolding (`.gitkeep`) |

## 6. Mobile / Offline Strategy

- Service worker for app-shell caching; offline storage hooks for camera,
  geolocation, and queued actions; `/api/v1/sync/batch` accepts queued writes.
- Current sync endpoint logs items and returns success (research mode) — real
  replay/conflict resolution is planned.

## 7. Current Limitations

- Frontend panels call the API at hardcoded `http://127.0.0.1:8000`; a
  configurable base URL is needed for deployment.
- No authentication layer yet (auth service is a placeholder).
- Satellite-derived indices are simulated data until real downloads are wired.

## 8. Success Path (Example)

Weather + soil moisture → HyDroMa FAO-56 kernel computes ET0 → ML correction
(planned) → OGC/WaterML formatting (planned) → localized delivery via SMS or
dashboard.
