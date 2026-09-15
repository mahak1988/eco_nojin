# بازارگاه چندفروشنده‌ای — نقشه راه فنی و پیاده‌سازی

## ۱. نمای کلی معماری

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React/TS)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │CatalogPage│ │ProductPage│ │VendorPage│ │CheckoutPage│  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │
│       │             │            │              │        │
│  ┌────┴─────────────┴────────────┴──────────────┴────┐    │
│  │           MarketplaceContext + useBilingual        │    │
│  └──────────────────────┬────────────────────────────┘    │
│                         │                                 │
│  ┌──────────────────────┴────────────────────────────┐    │
│  │          MarketplaceLayout (nav + filter bar)      │    │
│  └───────────────────────────────────────────────────┘    │
└────────────────────────┬──────────────────────────────────┘
                         │ GET/POST /api/v1/marketplace/*
┌────────────────────────┴──────────────────────────────────┐
│              API Gateway (FastAPI)                         │
│  routers/marketplace.py — 20+ endpoints                   │
└────────────────────────┬──────────────────────────────────┘
                         │
┌────────────────────────┴──────────────────────────────────┐
│         Services Layer                                     │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ ┌──────────┐  │
│  │Catalog   │  │Orders    │  │Vendors    │ │Cart      │  │
│  │Service   │  │Service   │  │Service    │ │Service   │  │
│  └──────────┘  └──────────┘  └───────────┘ └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ ┌──────────┐  │
│  │Payments  │  │Reviews   │  │Admin      │ │Notifications│
│  │Service   │  │Service   │  │Service    │ │Service   │  │
│  └──────────┘  └──────────┘  └───────────┘ └──────────┘  │
└───────────────────────────────────────────────────────────┘
```

## ۲. نقشه راه فازی

### فاز A — زیرساخت (هفته ۱–۲)
- [x] اندپوینت‌های پایه کاتالوگ (GET /products, /search, /{id})
- [x] اندپوینت‌های تولیدکننده (GET /producers)
- [x] اندپوینت سفارش (POST /orders, GET /orders)
- [x] اندپوینت آمار (GET /stats)
- [ ] **اندپوینت‌های سبد خرید** (POST/GET/DELETE /cart)
- [ ] **اندپوینت‌های مدیریت فروشنده** (POST/PUT/DELETE /vendors)
- [ ] **اندپوینت‌های ادمین** (PATCH /admin/*)
- [ ] **اندپوینت‌های پرداخت** (POST /payments)

### فاز B — صفحات فرانت‌اند (هفته ۲–۳)
- [x] MarketplacePage (پیش‌نمایش)
- [ ] **CatalogPage** — صفحه کاتالوگ با فیلتر و جستجو
- [ ] **ProductPage** — صفحه جزئیات محصول
- [ ] **VendorPage** — صفحه فروشگاه فروشنده
- [ ] **CartPage** — سبد خرید
- [ ] **CheckoutPage** — جریان پرداخت
- [ ] **BuyerDashboard** — داشبورد خریدار
- [ ] **VendorDashboard** — داشبورد فروشنده
- [ ] **VendorApplication** — ثبت‌نام فروشنده
- [ ] **AdminPanel** — پنل ادمین

### فاز C — یکپارچه‌سازی (هفته ۳–۴)
- [ ] Context و Hookهای بازارگاه
- [ ] Layout مشترک بازارگاه
- [ ] Routing کامل
- [ ] Type checking و build
- [ ] تست‌های یکپارچه

## ۳. مدل داده

### کاربر (از AuthContext ارث‌بری)
```typescript
interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'buyer' | 'seller' | 'admin';
  is_admin: boolean;
  country: string | null;
}
```

### محصول
```typescript
interface Product {
  id: string;
  name: string;
  slug: string;
  category: 'grains' | 'fruits' | 'vegetables' | 'dairy' | 'meat' | 'spices' | 'other';
  description: string;
  price: number; // per kg
  quantity_available: number; // kg
  minimum_order: number;
  organic_certified: boolean;
  carbon_footprint_kg_co2: number;
  water_footprint_liters: number;
  producer_name: string;
  producer_id: string;
  origin_location: string;
  harvest_date: string;
  batch_number: string;
  traceability_code: string;
  pgs_certified: boolean;
  status: 'pending' | 'approved' | 'rejected' | 'out_of_stock';
  images: string[];
  tags: string[];
  rating: number;
  review_count: number;
}
```

### فروشنده
```typescript
interface Vendor {
  id: string;
  user_id: string;
  shop_name: string;
  slug: string;
  description: string;
  location: string;
  village_id: string;
  logo: string | null;
  banner: string | null;
  rating: number;
  total_sales: number;
  certifications: string[];
  is_verified: boolean;
  status: 'pending' | 'active' | 'suspended';
  created_at: string;
}
```

### سبد خرید
```typescript
interface CartItem {
  product_id: string;
  quantity: number;
  unit: 'kg';
}
```

### سفارش
```typescript
interface Order {
  id: string;
  order_number: string;
  buyer_id: string;
  seller_id: string;
  items: OrderItem[];
  subtotal: number;
  platform_fee: number;
  landscape_fee: number;
  total: number;
  shipping_address: Address;
  status: 'pending' | 'paid' | 'shipped' | 'delivered' | 'cancelled';
  payment_status: 'pending' | 'paid' | 'refunded';
  tracking_code: string | null;
  created_at: string;
}
```

### ردیابی
```typescript
interface TraceEvent {
  timestamp: string;
  event: string;
  location: string;
  actor: string;
  notes: string;
}
```

## ۴. نقشه مسیر فرانت‌اند

```
/marketplace              → CatalogPage (صفحه اصلی کاتالوگ)
/marketplace/category/:cat → CatalogPage (فیلتر دسته)
/marketplace/product/:id   → ProductPage (جزئیات محصول)
/marketplace/vendor/:id    → VendorPage (فروشگاه فروشنده)
/marketplace/cart          → CartPage (سبد خرید)
/marketplace/checkout      → CheckoutPage (پرداخت)
/marketplace/orders        → BuyerDashboard (سفارشات خریدار)
/marketplace/sell          → VendorDashboard (داشبورد فروشنده)
/marketplace/apply         → VendorApplication (ثبت‌نام فروشنده)
/marketplace/admin         → AdminPanel (پنل ادمین)
```

## ۵. اندپوینت‌های مورد نیاز بک‌اند

### کاتالوگ
- `GET /api/v1/marketplace/products` — لیست با pagination، فیلتر، sort
- `GET /api/v1/marketplace/products/search` — جستجو
- `GET /api/v1/marketplace/products/{id}` — جزئیات
- `GET /api/v1/marketplace/products/{id}/trace` — ردیابی
- `GET /api/v1/marketplace/products/{id}/reviews` — بررسی‌ها
- `GET /api/v1/marketplace/categories` — دسته‌ها
- `GET /api/v1/marketplace/producers` — تولیدکنندگان

### فروشنده
- `POST /api/v1/marketplace/vendors` — ثبت‌نام فروشنده
- `GET /api/v1/marketplace/vendors` — لیست فروشندگان
- `GET /api/v1/marketplace/vendors/{id}` — جزئیات فروشنده
- `PUT /api/v1/marketplace/vendors/{id}` — ویرایش
- `GET /api/v1/marketplace/vendors/{id}/products` — محصولات فروشنده
- `GET /api/v1/marketplace/vendors/{id}/ratings` — امتیاز

### سبد و سفارش
- `POST /api/v1/marketplace/cart` — افزودن به سبد
- `GET /api/v1/marketplace/cart` — دریافت سبد
- `DELETE /api/v1/marketplace/cart/{product_id}` — حذف از سبد
- `POST /api/v1/marketplace/orders` — ایجاد سفارش (از سبد)
- `GET /api/v1/marketplace/orders` — لیست سفارشات
- `GET /api/v1/marketplace/orders/{id}` — جزئیات سفارش
- `POST /api/v1/marketplace/orders/{id}/cancel` — لغو سفارش
- `POST /api/v1/marketplace/orders/{id}/confirm` — تأیید سفارش

### ادمین
- `GET /api/v1/marketplace/admin/stats` — آمار کل
- `PATCH /api/v1/marketplace/admin/products/{id}/approve` — تأیید محصول
- `PATCH /api/v1/marketplace/admin/vendors/{id}/approve` — تأیید فروشنده
- `GET /api/v1/marketplace/admin/orders` — لیست همه سفارشات
- `PATCH /api/v1/marketplace/admin/orders/{id}/status` — تغییر وضعیت

### پرداخت
- `POST /api/v1/marketplace/payments` — ایجاد پرداخت
- `POST /api/v1/marketplace/payments/{id}/confirm` — تأیید پرداخت

## ۶. فناوری و الگوها

| لایه | تکنولوژی | الگو |
|------|----------|------|
| State | React Context + useState | MarketplaceContext |
| Server State | TanStack Query | useQuery, useMutation |
| Routing | React Router v6 | Nested routes |
| Styling | Tailwind CSS + CSS vars | glass, glass-hover |
| Forms | Controlled inputs + validation | Zod-like checks |
| i18n | useBilingual | fa/en/ur/ps |
| Auth | AuthContext + localStorage | useAuth |
| API | fetch + getApiBase | rest client pattern |

## ۷. طراحی کامپوننت‌ها

### MarketLayout
- نوار ناوبری بازارگاه (حروف اول، کاتالوگ، سبد، داشبورد)
- نوار جستجوی محصولات
- بنر پروموشنال

### ProductCard
- تصویر محصول
- نام، قیمت/kg، تولیدکننده
- پرچم ارگانیک
- دکمه «افزودن به سبد»

### FilterBar
- فیلتر دسته (چندانتخابی)
- فیلتر قیمت (بازه)
- فیلتر ارگانیک (تا/فقط)
- فیلتر مبدأ
- مرتب‌سازی (قیمت، امتیاز، جدید)

### CartDrawer / CartPage
- لیست اقلام سبد
- ویرایش مقدار
- جمع‌بندی قیمت و کارمزد
- دکمه «پرداخت»

### CheckoutForm
- آدرس ارسال
- روش پرداخت
- تأیید سفارش

## ۸. استراتژی اجرا

### هفته ۱: زیرساخت بک‌اند
1. اندپوینت‌های سبد خرید
2. اندپوینت‌های فروشنده
3. اندپوینت‌های ادمین
4. دیتاسیت فیکت (seed data)

### هفته ۲: فرانت‌اند — کاتالوگ و محصول
1. CatalogPage با فیلتر و جستجو
2. ProductPage با جزئیات و ردیابی
3. ProductCard و FilterBar components
4. MarketplaceLayout

### هفته ۳: فرانت‌اند — تراکنش و داشبورد
1. CartPage و CheckoutPage
2. VendorPage (فروشگاه فروشنده)
3. BuyerDashboard و VendorDashboard

### هفته ۴: پنل‌ها و نهایی‌سازی
1. VendorApplication
2. AdminPanel
3. Routing کامل و type checking
4. تست و بیلد
