# Implementation Roadmap - HyDroMa Modules

## Current Status
- [NOT FOUND] برنامه کشت (Crop Planning)
- [IMPLEMENTED] مدیریت آب (Water Management)
- [NOT FOUND] باد و فرسایش (Wind & Erosion)
- [NOT FOUND] دامداری (Livestock)
- [NOT FOUND] کربن و اعتبار (Carbon & Credits)
- [IMPLEMENTED] نقشه و زمین (Map & Land)
- [IMPLEMENTED] بازارچه محلی (Local Marketplace)
- [NOT FOUND] گردشگری بوم‌گردی (Ecotourism)
- [IMPLEMENTED] گزارش‌ها (Reports)
- [NOT FOUND] پایش ماهواره‌ای (Satellite Monitoring)

## Architecture Principles
1. ModuleRegistry = single source of truth
2. Event Bus for decoupled module<->HyDroMa communication
3. Layer Protocol: heatmap/overlay/markers/polygons/arrows/isolines
4. Chart Dock below the map (collapsible)

## Layer types each module should register
- crop-planning: polygons (fields) + heatmap (growth)
- water-management: overlay (runoff) + arrows (flow) + isolines (groundwater)
- wind-erosion: heatmap (erosion) + arrows (wind) + polygons (windbreak)
- livestock: markers (water points) + overlay (grazing capacity)
- carbon-credits: heatmap (SOC) + polygons (eligible zones)
- local-marketplace: markers (sellers) + polygons (delivery)
- ecotourism: markers (POI) + polygons (tour routes)
- satellite-monitoring: overlay (NDVI)
- reports: charts only (Chart Dock)

## Implementation Phases
Phase A (Scientific Core): crop-planning, water-management, wind-erosion, satellite-monitoring
Phase B (Carbon & Econ): carbon-credits, livestock
Phase C (Spatial): local-marketplace, ecotourism
Phase D (Analytics): reports
Phase E (Integration): map-land (ModuleRegistry hub)