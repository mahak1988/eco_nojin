# 01. Architecture: Hybrid Scientific-Computational Platform

**Status:** Approved | **Pattern:** Modular Monolith evolving to Microservices

## 1. High-Level Architecture
The system follows a decoupled, API-first architecture separating the heavy computational engine from the user-facing applications.

1. **User Interfaces (Frontend & USSD):** Next.js (Web/PWA) with 14-language i18n support, SMS/USSD gateways for offline rural access, and Voice AI (IVR) for low-literacy users.
2. **API Gateway & Services:** FastAPI-based services handling Auth, Workflow orchestration, Ledger, and Notifications.
3. **HyDroMa Engine (Python + C++):**
   - **Python Layer:** Orchestration, Data Ingestion (Satellite/IoT), ML pipelines, RAG-based Knowledge Assistant, and API endpoints.
   - **C++ Core:** High-performance numerical solvers for Richards equation (groundwater), Saint-Venant (hydrology), and RUSLE (erosion). Bound to Python via `pybind11`.
4. **Data Layer (Research Mode):** 
   - **DuckDB:** For fast analytical queries on time-series climate and sensor data.
   - **SQLite / GeoPackage:** For spatial geometries, soil profiles, and farm boundaries.
   - **Local File System:** For raw satellite imagery (GeoTIFF/NetCDF).
5. **Trust & Ledger Layer:** Cryptographic hashing of MRV data, preparing for post-quantum signatures and consortium blockchain integration.

## 2. Data Flow (Example: Irrigation Recommendation)
1. **Ingestion:** Python fetches local weather API and soil moisture sensor data.
2. **Processing:** HyDroMa triggers the C++ FAO-56 Penman-Monteith kernel to calculate ET0.
3. **AI Enhancement:** ML model corrects the physical output based on historical local yield data.
4. **Standardization:** Output is formatted according to OGC API Features and WaterML 2.0.
5. **Delivery:** Translated to the user's local language and pushed via SMS or Dashboard.

## 3. Security & Privacy
- **Data Sovereignty:** Farmers own their data. Aggregated data is anonymized before external use.
- **Post-Quantum Readiness:** Architecture reserves interfaces for NIST-approved PQC algorithms (ML-KEM, ML-DSA) for future ledger and API security.
