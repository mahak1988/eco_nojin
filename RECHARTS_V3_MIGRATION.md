# Recharts v3 Migration Plan

**تاریخ:** ۱۳ شهریور ۱۴۰۵
**وضعیت:** ✅ تکمیل شده (۱۴ سپتامبر ۲۰۲۶)

---

 وضعیت فعلی
- نسخه نصب‌شده: `recharts@2.12.7` (منقضی شده)
- نسخه پیشنهادی: `recharts@^3.0`
- فایل‌های نیاز‌منند: `RechartsChart.tsx`, `NDVIChart.tsx`

---

## تغییرات شناسایی‌شده برای کد فعلی

### 1. S compatibility
| Component | v2 → v3 | اقدام |
|---|---|---|
| `AreaChart`, `Area` | ✅ سازگار | بدون تغییر |
| `XAxis`, `YAxis` | ✅ سازگار | بدون تغییر |
| `CartesianGrid` | ✅ سازگار | بدون تغییر |
| `Tooltip` | ⚠️ partials | `contentStyle` سازگار — بررسی `itemStyle` |
| `ResponsiveContainer` | ⚠️ partials | نیاز به `height` مشخص در parent ✅ (داریم) |
| `Legend` | ✅ سازگار | بدون تغییر |

### 2. Props که باید بررسی شوند
- **`tick={{ fill: '...', fontSize: 10 }}`** — در v2 اشتباه style object قبول می‌شد. در v3 همچنان به عنوان shortcut پشتیبانی می‌شود ولی ممکن است warning بدهد.
- **`strokeLinecap` و `strokeLinejoin`** در `<Area>` — در v3 ممکن است به `<Line>` منتقل شوند. باید تست شوند.
- **`strokeDasharray="6 4"`** — سازگار ✅

### 3. TypeScript Changes
- v3 دارای انواع stricter است
- `margin` prop ممکن است types مختلفی داشته باشد
- `height` در `ResponsiveContainer` ممکن است string | number باشد

---

## مراحل مهاجرت

### گام ۱: آپدیت نسخه
```bash
cd frontend
pnpm add recharts@^3.0
```

### گام ۲: Build و تست
```bash
pnpm build:prod
pnpm type-check
```
بررسی خطاهای TypeScript و deprecation warnings.

### گام ۳: رفع خطاها
بر اساس خطاهایی که ساخت بدهد:
1. `tick` prop → تبدیل به تابع سفارشی
2. `strokeLinecap` → بررسی سازگاری
3. انواع TypeScript → اصلاح interface props

### گام ۴: تست بصری
- مقایسه نمودارهای قبل و بعد
- بررسی رنگ‌ها، اندازه‌ها، animation ها
- بررسی رفتار در سایزهای مختلف صفحه

---

## تخمین منابع
| مورد | زمان |
|---|---|
| آپدیت نسخه | ۵ دقیقه |
| رفع خطاهای build/type | ۱-۲ ساعت |
| تست بصری | ۳۰ دقیقه |
| **مجموع** | **۲-۳ ساعت** |

---

## Risk
- ریز: اندکی تغییر در ظاهر نمودار (color opacity، gradient behavior)
- کاملاً: dependency conflict با React 19 (باید بررسی شود — v3 از React 19 پشتیبانی می‌کند)
