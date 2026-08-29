# 📦 گزارش v2 — ممیزی وابستگی‌ها

## کاندید حذف (28) — همه با build+test راستی‌آزمایی می‌شوند

- `@ant-design/icons`
- `@deck.gl/geo-layers`
- `@deck.gl/mesh-layers`
- `@dimforge/rapier3d-compat`
- `@emotion/react`
- `@emotion/styled`
- `@hookform/resolvers`
- `@mui/material`
- `@react-three/postprocessing`
- `@tanstack/react-query`
- `@turf/turf`
- `@types/d3`
- `@types/mapbox-gl`
- `@types/maplibre-gl`
- `@web3modal/wagmi`
- `d3`
- `deck.gl`
- `ethers`
- `georaster-layer-for-leaflet`
- `geotiff`
- `gsap`
- `immer`
- `qrcode.react`
- `react-hook-form`
- `terraformer`
- `viem`
- `wagmi`
- `zod`

## نکات هوشمند

- ℹ️ import از `geojson` فقط type-only است → `@types/geojson` کافی است؛ پکیج runtime لازم نیست
- ℹ️ `node:url` builtin نود است — نیازی به نصب ندارد (باگ v1 رفع شد)


## نگهداری

- 🔁 منسوخ → Reown AppKit (مهاجرت بعدی)
- ⚠️ به leaflet نیاز دارد که نصب نیست
- 🪦 منسوخ (Esri آرشیو کرده)