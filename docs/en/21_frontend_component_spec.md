# 21 — Component Specification (Front-End Roadmap) — Phase 9

> سند نقشه اجرایی فرانت‌اند اکو نوژین. وضعیت هر گروه: ✅ ساخته شده | 🔨 در فاز ۹ | ⏳ فاز ۱۰+.
> بسته‌ها: radix-ui primitives، recharts، leaflet/react-leaflet، framer-motion، sonner، lucide-react، react-hook-form + zod، tanstack/react-query.
> اصول: `components/ui` کاملاً عمومی (بدون دانش حوزه)؛ لایه تخصصی جدا (charts/gis/simulation/…).

## وضعیت خلاصه

| گروه | وضعیت | مسیر |
|---|---|---|
| 1. Foundation (رنگ/تایپ/فضا/سایه/RTL/a11y) | ✅ | `app/globals.css`, `tailwind` theme tokens, `font-synthesis:none`, `lang=fa dir=rtl` |
| 2. Typography | ✅ | سیستم Tailwind + Vazirmatn (400/500/700/800) |
| 3. Buttons (12 نوع + 8 حالت) | ✅ | `components/ui/button.tsx` (cva variants) |
| 4. Inputs (عمومی + علمی) | ✅/🔨 | `ui/input.tsx`؛ ورودی‌های علمی (SoilDepth/Rainfall/…) در فاز ۹ |
| 5. Forms | 🔨 | react-hook-form + zod موجود؛ `FormField/FormWizard/DynamicForm` در فاز ۹ |
| 6. Selection | ✅/🔨 | select/switch/checkbox/radio-group/slider ساخته شد؛ combobox/color-picker فاز ۱۰ |
| 7. Data Display (Table) | 🔨 | DataTable (sort/filter/export) در فاز ۹؛ virtualized فاز ۱۰ |
| 8. Cards | ✅ | `ui/card.tsx` + KPI/StatCard در داشبوردها |
| 9. Feedback | ✅ | sonner (toast) + Alert/ErrorState (`shared/ApiState.tsx`) |
| 10. Modal/Overlay | ✅/🔨 | dialog/popover/tooltip/dropdown ساخته شد؛ sheet/drawer + command palette فاز ۹ |
| 11. Navigation | ✅ | navbar/sidebar/tabs/breadcrumb در `components/site` |
| 12. Loading & Processing | ✅/🔨 | skeleton/progress ساخته شد؛ skeleton-table + overlay فاز ۹ |
| 13. Charts & Scientific Viz | 🔨 | recharts نصب؛ `components/charts/` (hydrograph/rainfall/chart-card) شروع شد؛ بقیه فاز ۹ |
| 14. GIS / Map | ✅/🔨 | leaflet + react-leaflet؛ MapViewer/لایه‌ها در ماژول‌ها؛ LayerTree/Measure فاز ۹ |
| 15. Simulation Components | 🔨 | فاز ۹ (ScenarioBuilder/Runner/ResultViewer) |
| 16. Hydrology Components | 🔨 | ماژول watershed موجود؛ Hydrograph/WaterBalance فاز ۹ |
| 17. Agriculture Components | 🔨 | FarmDashboard موجود؛ CropPlanner فاز ۹ |
| 18. Monitoring Components | 🔨 | SensorCard/WeatherWidget فاز ۹ |
| 19. Dashboard Components | ✅ | `components/dashboard/*` + KPI grid در صفحات |
| 20. File & Data Management | ⏳ | فاز ۱۰ (FileDropzone/ImportWizard/CSVViewer) |
| 21. User & Authentication | ✅ | login/register/forgot/reset/profile در `app/(auth)` + JWT |
| 22. Reports | ⏳ | فاز ۱۰ (ReportBuilder/PDFExport) |
| 23. Animation System | ✅/🔨 | framer-motion + prefers-reduced-motion؛ WaterFlowAnimation فاز ۹ |
| 24. Icon System | ✅ | lucide-react (SVG) + react-icons؛ راهنما: فقط lucide در کد جدید |
| 25. Accessibility | ✅ | focus-ring/keyboard/ARIA در primitives رادیکس؛ ممیزی در فاز ۹ |
| 26. Responsive | ✅ | breakpoints + use-breakpoint؛ جدول موبایل → کارت در فاز ۹ |

## اولویت فاز ۹ (ساخت + تست)

1. **DataTable** عمومی (sort/filter/pagination/export CSV) — `components/ui/data-table.tsx`
2. **Sheet/Drawer** (روی radix dialog) — `components/ui/sheet.tsx`
3. **CommandPalette** (جستجوی سریع) — `components/ui/command.tsx`
4. **SkeletonTable / LoadingOverlay** — `components/ui/skeleton.tsx` توسعه
5. **FormField/FormWizard** (react-hook-form wrapper) — `components/ui/form.tsx`
6. **کیت نمودار علمی**: WaterBalance, FlowDurationCurve, SoilMoisture, ET0, VegetationIndex — `components/charts/`
7. **Sheet** برای جدول موبایل (تبدیل به کارت)
8. **آزمون‌های کامپوننت** (vitest + testing-library) برای DataTable/Form/Sheet
9. **ممیزی a11y** (focus trap, contrast, reduced-motion)

## قانون معماری

- `components/ui/*` = عمومی، بدون دانش «آبخیزداری».
- `components/charts|gis|simulation|hydrology|agriculture|monitoring` = لایه تخصصی.
- Server Components پیش‌فرض؛ فقط تعاملی‌ها `"use client"`.
- هر کامپوننت جدید باید از entry (main.tsx→App.tsx) قابل ردیابی باشد (zero orphan).
