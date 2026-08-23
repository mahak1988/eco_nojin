# ساختار فایل‌های پروژه

این سند ساختار فایل‌های تولید شده توسط ماژول‌های جدید را توضیح می‌دهد.

## `data/maps/`

- `M-ERS_{id}/metadata.json`: متادیتا خروجی RUSLE.
- `cache/`: کش نتایج پایپلاین‌های نقشه.

## `data/analyses/`

### `topography/{site_id}/`

- `{slope, aspect, curvature, flow_direction, flow_accumulation}.tif`: لایه‌های تحلیل توپوگرافی.
- `metadata.json` در دیتابیس ذخیره می‌شود.

## `data/spatial_runoff/`

- `runoff_cn_{method}_site_{hash}.tif`: نقشه رواناب محاسبه شده.

## `data/designs/`

### `structures/{design_id}/`

- `design.geojson`: طرح سازه.
- `bill_of_materials.json`: لیست مواد.
- `cost_estimate.json`: برآورد هزینه.

### `irrigation/{design_id}/`

- `layout.geojson`: طرح سیستم آبیاری.
- `equipment_list.json`: لیست تجهیزات.
- `schedule.json`: برنامه آبیاری.

## `data/calibration/`

- `calibration_{model}_{site_id}_{timestamp}.json`: نتایج کالیبراسیون.