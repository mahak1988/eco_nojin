# برنامه پیاده‌سازی: درآمد اسپانسرشیپ و اسلات حامی
## اکو نوژین — سند مهندسی و اجرایی

- **تاریخ:** ۱۴۰۵/۰۶/۰۴ (2026-09-26)
- **سند مادر:** `reports/REVENUE_GROWTH_BRAND_PLAN_FA_2026-09-26.md` §۲.۶
- **هدف:** تبدیل اسلات حامی طراحی‌شده به درآمد واقعی، بدون به‌خطر انداختن دارایی اعتماد
- **اصل حاکم:** کاربر هرگز نمی‌پردازد · اسلات هرگز روی سطح توصیه کشاورزی نیست · شبکه تبلیغاتی هرگز نصب نمی‌شود

---

# ۱. دامنه

## ۱.۱ داخل دامنه (در این سند)
| # | کار |
|---|---|
| ۱ | مدل داده اسپانسرشیپ + مهاجرت Alembic |
| ۲ | API عمومی خواندن + API مدیریت |
| ۳ | کامپوننت `<SponsorSlot>` + گارد صفحات ممنوع |
| ۴ | ۱۴ کلید i18n + صفحه سیاست حامیان + فهرست عمومی حامیان |
| ۵ | دروازه‌های کیفیت: تست، a11y، snapshot، سیاست |
| ۶ | خط پایه سنجه اعتماد + قاعده ۳۰ روزه + کلید قطع |
| ۷ | کیت فروش و فرایند مذاکره |
| ۸ | WBS زمان‌بندی و برآورد |

## ۱.۲ خارج از دامنه (عمداً)
- شبکه تبلیغاتی، AdMob/AdSense، روش‌های کسب درآمد از بازدید
- تارگتینگ رفتاری، پروفایل‌سازی، پیکسل، کوکی تبلیغاتی
- SDK بیگانه هر نوع (حتی analytics) — وابستگی خارجی = ریسک اعتماد و ممیزی گرنت
- اسلات در `/hydroma`، `/virtual-lab`، `/simulator`، `/models/*`، `checkout/*`، `wallet`، `escrow/*`
- اسلات در هر مسیر USSD / IVR / پیامک / خروجی توصیه زراعی
- فروش مستقیم توکن یا کالای سرمایه‌گذاری (بخش ۳)

---

# ۲. مدل داده

## ۲.۱ فایل جدید: `services/sponsors/models/__init__.py`

سبک دقیقاً مطابق `services/marketplace/models/__init__.py` (‏`StrEnum`، کلید `String(36)`، `DateTime(timezone=True)`، `Numeric(15,2)`، `Index` در `__table_args__`).

```python
import uuid

"""
مدل‌های داده اسپانسرشیپ
"""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)

from database.base import Base


class SponsorTier(StrEnum):
    PAGE = "page"
    SECTION = "section"
    TOOL = "tool"
    DISTRICT = "district"
    FOUNDING = "founding"


class SponsorshipStatus(StrEnum):
    PROSPECT = "prospect"
    CONTRACTED = "contracted"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ENDED = "ended"
    TERMINATED = "terminated"


class SlotPlacement(StrEnum):
    PUBLIC_SERVICES = "public_services"
    PUBLIC_AUDIENCES = "public_audiences"
    TOOL_FOOTER = "tool_footer"


class Sponsorship(Base):
    __tablename__ = "sponsorships"
    __table_args__ = (
        Index("idx_sponsorship_status", "status"),
        Index("idx_sponsorship_placement", "placement"),
        Index("idx_sponsorship_sponsor", "sponsor_name"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sponsor_name = Column(String(200), nullable=False, index=True)
    sponsor_name_fa = Column(String(200), nullable=True)
    sponsor_url = Column(String(500), nullable=False)
    logo_url = Column(String(500), nullable=True)
    tagline = Column(String(200), nullable=True)
    tagline_fa = Column(String(200), nullable=True)

    tier = Column(SQLEnum(SponsorTier), nullable=False, default=SponsorTier.PAGE)
    status = Column(SQLEnum(SponsorshipStatus), default=SponsorshipStatus.PROSPECT, index=True)
    placement = Column(SQLEnum(SlotPlacement), nullable=False)

    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    starts_on = Column(Date, nullable=False)
    ends_on = Column(Date, nullable=False)

    is_project_funder = Column(Boolean, default=False, index=True)
    is_revenue_source_funder = Column(Boolean, default=False)
    disclosure_required = Column(Boolean, default=True, index=True)
    green_claims_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    green_claims_attested_by = Column(String(120), nullable=True)

    internal_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
```

## ۲.۲ قیدهای دامنه که در دیتابیس اعمال می‌شوند

| قید | دلیل |
|---|---|
| `CHECK (ends_on > starts_on)` | جلوگیری از قرارداد پایان‌یافته در روز اول |
| `CHECK (placement IN (...))` | فهرست بسته — افزودن placement جدید نیازمند بازبینی است |
| `CHECK (amount > 0)` | مبلغ صفر یعنی تبلیغ رایگان، که ممنوع است |
| **ایندکس ترکیبی** `(status, placement, ends_on)` | کوئری عمومی همیشه همین سه فیلتر را دارد |
| `sponsor_name` یکتا نیست، اما `CHECK` روی `(sponsor_name, placement, starts_on)` | جلوگیری از تکرار تصادفی |

## ۲.۳ مهاجرت Alembic

`alembic/versions/xxxx_sponsorships.py`:

```python
def upgrade() -> None:
    op.create_table(
        "sponsorships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sponsor_name", sa.String(200), nullable=False),
        sa.Column("sponsor_name_fa", sa.String(200)),
        sa.Column("sponsor_url", sa.String(500), nullable=False),
        sa.Column("logo_url", sa.String(500)),
        sa.Column("tagline", sa.String(200)),
        sa.Column("tagline_fa", sa.String(200)),
        sa.Column("tier", sa.Enum(*[t.value for t in SponsorTier]), nullable=False),
        sa.Column("status", sa.Enum(*[s.value for s in SponsorshipStatus]), nullable=False),
        sa.Column("placement", sa.Enum(*[p.value for p in SlotPlacement]), nullable=False),
        sa.Column("amount", sa.Numeric(15, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("starts_on", sa.Date, nullable=False),
        sa.Column("ends_on", sa.Date, nullable=False),
        sa.Column("is_project_funder", sa.Boolean(), server_default=sa.false()),
        sa.Column("is_revenue_source_funder", sa.Boolean(), server_default=sa.false()),
        sa.Column("disclosure_required", sa.Boolean(), server_default=sa.true()),
        sa.Column("green_claims_reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("green_claims_attested_by", sa.String(120)),
        sa.Column("internal_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("ends_on > starts_on", name="ck_sponsorship_window"),
        sa.CheckConstraint("amount > 0", name="ck_sponsorship_amount_positive"),
    )
    op.create_index("ix_sponsorship_status", "sponsorships", ["status"])
    op.create_index("ix_sponsorship_placement", "sponsorships", ["placement"])
    op.create_index("ix_sponsorship_sponsor", "sponsorships", ["sponsor_name"])
    op.create_index(
        "ix_sponsorship_active_lookup",
        "sponsorships",
        ["status", "placement", "ends_on"],
    )
```

> ⚠️ **نکته پروژه:** `alembic.ini` و `database/models.py` الگوی مشخصی دارند و طبق `AGENTS.md` پوشش تست مهاجرت اجباری است. پس از افزودن مهاجرت، `tests/integration/test_sqlite_migrations.py` باید از سر تا ته سبز بماند.

## ۲.۴ فهرست سیاه (در کد، نه فقط در سیاست)

یک ماژول کوچک `services/sponsors/policy.py` که هم در مسیر نوشتن API و هم در مسیر رندر فرانت‌اند صدا زده می‌شود:

```python
FORBIDDEN_CATEGORIES = (
    "fossil_fuel",
    "petrochemical",
    "synthetic_fertilizer",
    "pesticide",
    "gambling",
    "adult",
    "data_extraction",
    "surveillance_sales",
)

FORBIDDEN_PLACEMENTS = (
    "/hydroma",
    "/virtual-lab",
    "/simulator",
    "/simulators",
    "/models",
    "/checkout",
    "/wallet",
    "/escrow",
    "/monitoring",
    "/settings",
    "/profile",
    "/telecom",  # مسیر USSD/کانال
)

MAX_VISUAL_WEIGHT_PCT = 12
MAX_SPONSORS_PER_PLACEMENT = 1
```

---

# ۳. API

## ۳.۱ API عمومی (بدون احراز هویت)

```
GET  /api/v1/sponsors                 # فهرست عمومی حامیان فعلی
GET  /api/v1/sponsors/slot?placement=public_services&locale=fa
```

**قرارداد `GET /api/v1/sponsors/slot`:**

```json
{
  "status": "success",
  "data": {
    "present": true,
    "disclosure": {
      "required": true,
      "template_key": "sponsors.slot.disclosure"
    },
    "sponsor": {
      "name": "Acme Agronomy",
      "name_fa": "آکمی آگرونومی",
      "url": "https://example.org",
      "logo_url": "https://cdn.example.org/logo.svg",
      "tagline": "Funded the rainfed-wheat FAO-56 module",
      "tagline_fa": "ماژول گندم دیم FAO-56 را تأمین کرد",
      "tier": "section",
      "is_project_funder": true
    },
    "expires_on": "2027-03-31"
  }
}
```

**قواعد قطعی API:**
- `present: false` وقتی حامی فعالی وجود ندارد → **کامپوننت هیچ چیز رندر نمی‌کند، نه حتی قاب خالی**
- انتخاب فقط از `status = ACTIVE` و `starts_on <= today <= ends_on` و `placement` مطابق
- **بدون کوکی، بدون `Set-Cookie`، بدون هدر قابل‌ردیابی‌شدن به کاربر** (جز CORS معمول)
- پاسخ `Cache-Control: public, max-age=900` + `ETag` — چون داده عمومی و کم‌تغییر
- **هیچ پارامتر کاربری در کوئری** (نه `user_id`، نه `visitor_id`) — ساختاراً تارگتینگ را ناممکن می‌کند

## ۳.۲ API مدیریت

```
POST   /api/v1/admin/sponsors            # ایجاد  → status=PROSPECT
PATCH  /api/v1/admin/sponsors/{id}       # ویرایش
POST   /api/v1/admin/sponsors/{id}/activate
POST   /api/v1/admin/sponsors/{id}/suspend     # تعلیق فوری
POST   /api/v1/admin/sponsors/{id}/terminate   # خاتمه با دلیل
POST   /api/v1/admin/sponsors/{id}/green-review  # ثبت بازبینی ادعاهای سبز
GET    /api/v1/admin/sponsors/expired
```

**قواعد ایمنی نوشتن:**
- `activate` بدون `green_claims_reviewed_at` رد می‌شود (۴۰۳) ← اجرای خودکار تعهد CMA ۲۰۲۶
- `activate` با `sponsor_name` در فهرست سیاه رد می‌شود
- `activate` با `placement` در `FORBIDDEN_PLACEMENTS` رد می‌شود
- `activate` وقتی حامی فعال دیگری روی همان `placement` هست رد می‌شود (`MAX_SPONSORS_PER_PLACEMENT`)
- همه این مسیرها `AuditEvent` می‌نویسند (`database/models.py:401` — الگوی موجود)

## ۳.۳ فایل‌های لازم
```
services/sponsors/__init__.py
services/sponsors/models/__init__.py     # ۲.۱
services/sponsors/policy.py             # ۲.۴
services/sponsors/schemas.py            # Pydantic
services/sponsors/service.py            # SponsorshipService
services/sponsors/routers/sponsors.py   # عمومی
services/sponsors/routers/admin.py      # مدیریت
services/sponsors/tests/test_sponsors.py
```
ثبت در `services/api_gateway/main.py` (الگو: `main.py:457-479`).

## ۳.۴ کارهای تکمیلی
- `scripts/generate_openapi_schema.py` را اجرا کنید (الزام `AGENTS.md`)
- تست قرارداد در `tests/test_contract.py` برای هر دو مسیر عمومی

---

# ۴. کامپوننت فرانت‌اند

## ۴.۱ فایل: `apps/web/src/components/SponsorSlot.tsx`

```tsx
import Image from 'next/image';
import { useTranslations } from 'next-intl';
import { useQuery } from '@tanstack/react-query';

type Placement = 'public_services' | 'public_audiences' | 'tool_footer';

type Props = {
  placement: Placement;
  className?: string;
};

type SlotPayload = {
  present: boolean;
  disclosure: { required: boolean; template_key: string };
  sponsor: {
    name: string;
    name_fa?: string | null;
    url: string;
    logo_url?: string | null;
    tagline?: string | null;
    tagline_fa?: string | null;
    tier: string;
    is_project_funder: boolean;
  };
  expires_on: string;
};

export function SponsorSlot({ placement, className }: Props) {
  const t = useTranslations('sponsors.slot');

  const { data } = useQuery<SlotPayload>({
    queryKey: ['sponsor-slot', placement],
    queryFn: async () => {
      const res = await fetch(`/api/v1/sponsors/slot?placement=${placement}`);
      if (!res.ok) return { present: false } as SlotPayload;
      return (await res.json()).data;
    },
    staleTime: 900_000,
    retry: 1,
  });

  if (!data?.present) return null;

  return (
    <aside
      aria-label={t('region_label')}
      data-testid="sponsor-slot"
      data-placement={placement}
      data-tier={data.sponsor.tier}
      className={[
        'eco-sponsor-slot',
        'flex items-center gap-3 rounded-lg border p-3',
        'max-w-[240px]',            // سقف عرض دسکتاپ
        'sm:max-w-full',
        className ?? '',
      ].join(' ')}
      style={{ maxWidth: 'min(240px, 100%)' }}
    >
      {data.sponsor.logo_url && (
        <Image
          src={data.sponsor.logo_url}
          alt=""
          width={56}
          height={32}
          className="shrink-0 object-contain"
        />
      )}

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">
          <a
            href={data.sponsor.url}
            rel="sponsored noopener noreferrer"
            target="_blank"
          >
            {data.sponsor.name}
          </a>
        </p>
        {data.sponsor.tagline && (
          <p className="truncate text-xs opacity-70">{data.sponsor.tagline}</p>
        )}
      </div>

      {data.disclosure.required && (
        <p
          data-testid="sponsor-disclosure"
          className="mt-1 basis-full text-[10px] leading-tight opacity-60"
        >
          {t('disclosure', { sponsor: data.sponsor.name })}
        </p>
      )}
    </aside>
  );
}
```

**نکات کلیدی که در کد بالا رعایت شده:**
- `rel="sponsored"` ← نشانه استاندارد HTML5 برای محتوای پولی. مرورگر و ابزارهای دسترس‌پذیری آن را می‌فهمند
- برچسب افشا **پایین‌ترین عنصر** است، نه حذف‌شدنی، نه `aria-hidden`
- `alt=""` روی لوگو — چون نام حامی در متن مجاور هست (screen reader تکرار نخواند)
- `if (!data?.present) return null` — **بدون قاب خالی، بدون ارتفاع رزرو‌شده**
- `truncate` روی متن‌ها → اسلات هرگز ارتفاع صفحه را جابه‌جا نمی‌کند (CLS = صفر)
- `basis-full` برای برچسب تا در موبایل به خط بعدی برود
- **بدون `useEffect`، بدون IntersectionObserver، بدون اسکریپت ردیابی** — واکنش‌گرایی با CSS

## ۴.۲ گارد صفحات ممنوع — مهم‌ترین بخش

این فایل تضمین می‌کند که حتی یک توسعه‌دهنده در آینده نتواند اسلات را جای اشتباه بگذارد:

```tsx
// apps/web/src/components/SponsorSlot.tsx — انتهای فایل
const FORBIDDEN_PREFIXES = [
  '/hydroma', '/virtual-lab', '/simulator', '/simulators', '/models',
  '/checkout', '/wallet', '/escrow', '/monitoring', '/settings',
  '/profile', '/telecom', '/ussd', '/voice', '/simple',
];

export function assertPlacementAllowed(pathname: string): void {
  if (FORBIDDEN_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    throw new Error(`<SponsorSlot /> is forbidden on ${pathname}`);
  }
}
```

و یک تست که **کل صفحات را می‌گردد** (نه فقط صفحات امروز):

```ts
// apps/web/tests/sponsor-placement.test.ts
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { describe, it, expect } from 'vitest';

const FORBIDDEN = ['hydroma', 'virtual-lab', 'simulator', 'simulators', 'models',
  'checkout', 'wallet', 'escrow', 'monitoring', 'settings', 'profile', 'telecom'];

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? walk(p) : p.endsWith('.tsx') ? [p] : [];
  });
}

describe('SponsorSlot placement policy', () => {
  const files = walk('apps/web/src/app');

  it('no forbidden route mounts <SponsorSlot />', () => {
    const violations: string[] = [];
    for (const f of files) {
      if (!readFileSync(f, 'utf8').includes('SponsorSlot')) continue;
      const rel = f.replace('apps/web/src/app/[locale]', '');
      if (FORBIDDEN.some((p) => rel === `/${p}` || rel.startsWith(`/${p}/`))) {
        violations.push(rel);
      }
    }
    expect(violations).toEqual([]);
  });

  it('every mount site passes a placement prop', () => {
    for (const f of files) {
      const src = readFileSync(f, 'utf8');
      if (!src.includes('<SponsorSlot')) continue;
      expect(src).toMatch(/placement=\{?\s*['"](public_services|public_audiences|tool_footer)['"]/);
    }
  });

  it('the slot never renders inside a farmer-advisory surface', () => {
    for (const f of [...walk('services')]) {
      if (readFileSync(f, 'utf8').includes('SponsorSlot')) {
        throw new Error(`SponsorSlot must not be imported in backend: ${f}`);
      }
    }
  });
});
```

> **نکته کلیدی:** `walk('services')` عمداً در تست آمده. اگر کسی فردا منطق رندر را به بک‌اند ببرد (مثلاً برای ایمیل یا پیامک)، تست fail می‌شود. **این دقیقاً همان چیزی است که «ممنوعیت روی سطح توصیه کشاورزی» را از یک نیت به یک قابلیت‌سنجی تبدیل می‌کند.**

## ۴.۳ نقاط نصب (نقشه صفحه‌به‌صفحه)

| مسیر | placement | فایل |
|---|---|---|
| `app/[locale]/public/services/marketplace-access/page.tsx` | `public_services` | ✅ |
| `app/[locale]/public/services/carbon-registry/page.tsx` | `public_services` | ✅ |
| `app/[locale]/public/services/mrv-verification/page.tsx` | `public_services` | ✅ |
| `app/[locale]/public/services/api-access/page.tsx` | `public_services` | ✅ |
| `app/[locale]/public/services/satellite-intelligence/page.tsx` | `public_services` | ✅ |
| `app/[locale]/public/audiences/government/page.tsx` | `public_audiences` | ✅ |
| `app/[locale]/public/audiences/ngos/page.tsx` | `public_audiences` | ✅ |
| `app/[locale]/public/audiences/investors/page.tsx` | `public_audiences` | ✅ |
| `app/[locale]/public/audiences/researchers/page.tsx` | `public_audiences` | ✅ |
| فوترنوت ابزارهای `hydroma-economics` و `economy` | `tool_footer` | ✅ |
| همه مسیرهای دیگر | — | ❌ بدون نصب |

> **قاعده:** اسلات فقط جایی می‌رود که کاربر در حال **ارزیابی یک تصمیم اداری یا اقتصادی** است، نه جایی که در حال **گرفتن توصیه کشاورزی** است.

---

# ۵. i18n — ۱۴ زبان

## ۵.۱ کلیدها (افزوده به `apps/web/messages/en.json` و ۱۳ فایل دیگر)

```json
{
  "sponsors": {
    "slot": {
      "region_label": "Sponsorship disclosure",
      "disclosure": "This section is funded by {sponsor}.",
      "current": "Current sponsors",
      "become": "Become a sponsor"
    },
    "policy": {
      "title": "Sponsorship policy",
      "no_targeting": "We do not use behavioural targeting, tracking pixels, or third-party advertising SDKs.",
      "no_advisory": "Sponsorships never appear in agronomic advice, USSD replies, voice calls, or SMS.",
      "transparency": "The full list of current sponsors is published on this page.",
      "review": "Each sponsor attests quarterly that its environmental claims remain substantiated."
    }
  }
}
```

## ۵.۲ ترجمه به‌عنوان `good-first-issue`

هر ۱۳ زبان باقی‌مانده یک issue جداگانه با عنوان الگو:

> `feat(i18n): translate sponsors.slot disclosure string into <locale>`

این هم‌زمان سه چیز است: (الف) جذب مشارکت‌کننده OSS، (ب) یک نتیجه فراگیری واقعی، (ج) عددی که برای تأمین‌کننده قابل‌استناد است.

**ترجمه `en` و `fa` را خودتان بنویسید**؛ ۱۲ زبان دیگر را بازبینی بومی لازم دارد. **ترجمه ماشینی بدون بازبینی، برای یک برچسب حقوقی-افشاگر خطرناک است** — همان منطقی که در سند مادر برای زراعت گفته شد، اینجا هم صادق است.

## ۵.۳ برچسب فارسی (نمونه)

```
fa: "این بخش با حمایت مالی {sponsor} تأمین شده است."
```

بدون «تبلیغ»، بدون «اسپانسر»، بدون «حمایت تبلیغاتی». واژه فارسی درست، خودش یک سیگنال اعتماد است.

---

# ۶. صفحات شفافیت

## ۶.۱ `app/[locale]/public/policy/sponsors/page.tsx`

سه بخش اجباری:
1. **فهرست کامل و عمومی حامیان فعلی** — نام، سطح، بازه، مبلغ یا «مبلغ افشانشده»، تاریخ بازبینی ادعاهای سبز
2. **سیاست** — متن `sponsors.policy.*` بالا
3. **سیاست لغو** — «ما هر حامی را که پس از انتشار اسلات، نرخ ریزش را بیش از دو برابر پایه ببرد، فوراً حذف می‌کنیم، حتی اگر قرارداد باقی مانده باشد.»

> **بند ۳ یک ریسک قراردادی عمدی است:** به حامی از قبل اعلام می‌کنید که می‌توانید او را حذف کنید. این بند در مذاکره، اعتبار شما را بالا می‌برد چون نشان می‌دهد اسلات را جدی نمی‌گیرید. و در آینده اگر لازم شد، کنترل قانونی دست شماست.

## ۶.۲ مسیر دوم: `app/[locale]/trust/sponsors/page.tsx`

هم‌نشینی با صفحات `trust/*` موجود (`trust/carbon-registry` از قبل هست). این کار اسلات را از «محتوای تبلیغاتی» به «حوزه اعتماد» منتقل می‌کند — **جایگاه‌دهی، نه فقط ظاهر.**

---

# ۷. دروازه‌های کیفیت

| دروازه | ابزار | معیار قبولی |
|---|---|---|
| تست واحد بک‌اند | `pytest services/sponsors/tests/` | انتخاب حامی، رد حامی منقضی، رد placement ممنوع، رد فهرست سیاه |
| تست قرارداد | `tests/test_contract.py` | هر دو مسیر عمومی، بدون خطای 4xx/5xx |
| تست جای‌گذاری | `apps/web/tests/sponsor-placement.test.ts` | هر سه تست سبز |
| تست رندر | vitest + Testing Library | `present: false` → هیچ DOM؛ `present: true` → برچسب افشا در DOM |
| تست a11y | Playwright + axe | **صفر نقض بحرانی**؛ برچسب افشا `aria-live="polite"` نباشد (مزاحم صفحه‌خوان) |
| تست CLS | Playwright | **CLS = 0** (به همین دلیل `truncate` و `max-width` ثابت) |
| مهاجرت | `tests/integration/test_sqlite_migrations.py` | سبز |
| اسکیمای OpenAPI | `scripts/generate_openapi_schema.py` | commit شود |
| Lint/Type | `ruff check .` · `pnpm -C apps/web type-check` · `pnpm quality` | سبز |
| **حافظ نهادی** | تست دستی فصلی | هیچ حامی فعالی بدون `green_claims_reviewed_at` |

## ۷.۱ تست منفی حیاتی

```python
def test_activate_without_green_review_is_rejected(client, admin_token):
    """ECGT/CMA 2026: no sponsor goes live without a substantiation review."""
    r = client.post("/api/v1/admin/sponsors", json={...}, headers=admin_token)
    sp = client.post(f"/api/v1/admin/sponsors/{r.json()['id']}/activate", headers=admin_token)
    assert sp.status_code == 403


def test_slot_is_absent_when_no_active_sponsor(client):
    r = client.get("/api/v1/sponsors/slot?placement=public_services")
    assert r.json()["data"]["present"] is False
```

---

# ۸. خط پایه اعتماد و قاعده ۳۰ روزه

## ۸.۱ پیش از فعال‌سازی: خط پایه را بگیرید

بدون خط پایه، قاعده ۳۰ روزه بی‌معناست. **حداقل ۳۰ روز داده جمع کنید** (حتی با اسلات خالی، چون خودِ کامپوننت و رندر آن باید بی‌اثر باشد).

| سنجه | تعریف | منبع در کد |
|---|---|---|
| نرخ ریزش ماهانه | کاربر فعال ماه قبل که در این ماه بازنشسته شده / کل فعال ماه قبل | `AnalyticsSnapshot` (`services/analytics/models.py:11`) |
| نرخ بازگشت | کاربر فعال ماه قبل که در این ماه فعال بوده | همان |
| شکایت | تیکت‌های برچسب‌دار `trust` | دفتر حسابرسی/پشتیبانی |
| تکمیل گام ترویج | نرخ پذیرش توصیه بین کاربرانی که صفحات اسلات‌دار دیده‌اند و کسانی که ندیده‌اند | `AuditEvent` + رویداد صفحه |

> **سنجه چهارم، مهم‌ترین است:** اگر کسانی که اسلات را دیده‌اند کمتر توصیه‌ها را اجرا کنند، اسلات کار خود را کرده — حتی اگر شکایتی ثبت نشده باشد. **این سنجه را از روز اول بسازید.**

## ۸.۲ قاعده ۳۰ روزه

```
روز 0:   فعال‌سازی حامی  →  ثبت در سیستم
روز 1-30: پایش روزانه چهار سنجه بالا
روز 30:  بازبینی
         ├─ همه سنجه‌ها در محدوده  →  ادامه تا پایان قرارداد
         ├─ ریزش > ۲× پایه  →  حذف فوری، حتی با قرارداد فعال
         └─ تکمیل گام < ۹۵٪ خط پایه  →  حذف + ریشه‌یابی
```

## ۸.۳ کلید قطع اضطراری

```python
# settings.py
ENABLE_SPONSOR_SLOT = False  # پیش‌فرض خاموش
```

**اسلات در حالت پیش‌فرض خاموش است.** فعال‌سازی یک عملیات عمدی است. اگر روزی همه‌چیز خراب شد، یک تغییر پرچم کل سیستم را خاموش می‌کند — بدون استقرار.

```ts
// SponsorSlot.tsx
if (process.env.NEXT_PUBLIC_SPONSOR_SLOT === 'off') return null;
```

---

# ۹. کیت فروش

## ۹.۱ مشتری هدف (ICP) — به ترتیب اولویت
| اولویت | دسته | چرا می‌خرد | بودجه |
|---|---|---|---|
| ۱ | **نهادهای تأمین‌کننده موجود** (Gates، GIZ/BMZ، UN، بنیادها) | بودجه CSR/تأمین مالی آماده دارد؛ رابطه از قبل هست | بالا |
| ۲ | بیمه‌های کشاورزی و شاخص | می‌خواهند MRV را ببینند | متوسط |
| ۳ | توزیع‌کنندگان نهاده و لجستیک | می‌خواهند به کشاورز برسند | متوسط |
| ۴ | آزمایشگاه خاک/آب | صداقت علمی شما برایشان ارزش دارد | کم |
| ۵ | بانک‌های توسعه و سازمان‌های مالی | ریسک اعتبار + اعتبار برند | متوسط |
| ۶ | اپراتورهای مخابراتی و پلتفرم داده | دسترسی به کاربر + اعتبار | متوسط |

> **توجه:** هدف اصلی شما هیچ‌کدام از این‌ها نیست. آن‌ها فقط «تماس فروش» هستند. هدف اصلی، گرنت‌ها و قراردادهای B2G است. **اسلات نباید وقت فروش را از آن‌ها بگیرد.**

## ۹.۲ متریال (همه آماده، همه رایگان، همه CC-BY)
1. **یک صفحه** `eco-nojin.org/sponsor` — توضیح، سطوح قیمت، فرم تماس
2. **یک برگه یک‌صفحه‌ای** PDF — ۶ خط: چه می‌کنیم، چه می‌بینند، چه نمی‌بینند، چقدر، چگونه لغو می‌کنیم
3. **نمونه گزارش تأمین‌کننده** — یک صفحه، همان قالبی که حامی دریافت می‌کند
4. **نامه افشای حقوقی** (نمونه قرارداد) — شامل: بدون تارگتینگ · بدون SDK · بدون اسلات در توصیه زراعی · تعهد بازبینی فصلی ادعاهای سبز · **حق حذف ما در صورت آسیب به اعتماد**
5. **کیت رسانه** — بر پایه `VillageBrand.media_kit_url` / `brand_guidelines_url` (موجود در کد)

## ۹.۳ قیمت‌گذاری ارائه‌ای
| سطح | بازه سالانه | چه چیزی |
|---|---|---|
| صفحه سایت | ۵٬۰۰۰ تا ۲۰٬۰۰۰$ | یک اسلات، یک صفحه |
| بخش | ۲۵٬۰۰۰ تا ۶۰٬۰۰۰$ | یک اسلات + سرصفحه بخش + گزارش سالانه |
| ابزار | ۱۰٬۰۰۰ تا ۴۰٬۰۰۰$ | فوترنوت ابزار + صفحات ابزار |
| ناحیه | ۱۰٬۰۰۰ تا ۳۰٬۰۰۰$ به ازای هر ناحیه | تابلوی ناحیه + گزارش بازیابی |
| بنیادی | ۵۰٬۰۰۰ تا ۱۵۰٬۰۰۰$ | همه + گزارش سالانه + کانال گفت‌وگو |

**اهرم‌های غیرپولی که باید در مذاکره استفاده کنید:**
- **معافیت مالیاتی** (هسته فروش در هند، مالزی، آفریقای جنوبی، برزیل — FRIM و WeForest هر دو از آن استفاده می‌کنند)
- **گزارش تأمین‌کننده** با داده‌ی خودِ پروژه — چیزی که هیچ‌کدام از تبلیغات برنامه‌ای نمی‌دهند
- **دسترسی به `public/sponsors` صفحه** به‌عنوان آیتم اعتبار برند (بعضی برندها فقط برای این حاضرند پول بدهند)
- **پیوند با `CLAIMS.md` شما** — حامی‌هایی که ادعای سبز جدی دارند، دوست دارند به رجیستری شواهد شما لینک شوند

## ۹.۴ قیف فروش
```
سرد:  ۴۰ نهاد هدف × ۳۰ دقیقه معرفی یک‌صفحه‌ای
↓
گرم:  ۱۵ گفت‌وگوی ۴۵ دقیقه‌ای  (نرخ تبدیل هدف ۳۰-۴۰٪)
↓
تصمیم: ۵ ارسال پیشنهاد قیمتی
↓
امضا:  ۲ تا ۳ قرارداد
```
**زمان تخمینی: ۴ تا ۶ هفته برای اولین قرارداد، ۳ تا ۶ ماه برای سطح بخش.**

---

# ۱۰. WBS زمان‌بندی

> فرض: یک توسعه‌دهنده تمام‌وقت + بنیان‌گذار برای فروش

| هفته | کار | خروجی | ساعت |
|---:|---|---|---:|
| **۱** | مدل + Alembic + `policy.py` + تست مهاجرت | جدول `sponsorships` روی SQLite و PostgreSQL | ۱۲ |
| **۲** | `service.py` + `schemas.py` + API عمومی | `GET /api/v1/sponsors*` کار می‌کند | ۱۰ |
| **۳** | API مدیریت + `AuditEvent` + قواعد فعال‌سازی | رد بدون بازبینی سبز تست‌شده | ۱۰ |
| **۴** | `<SponsorSlot>` + گارد + تست جای‌گذاری | ۳ تست سیاست سبز | ۱۲ |
| **۵** | نصب روی ۱۰ صفحه + تست رندر + a11y + CLS | CLS صفر · axe بدون نقض بحرانی | ۱۲ |
| **۶** | ۱۴ کلید i18n (en + fa) + صفحه سیاست + صفحه `trust/sponsors` | صفحات منتشرشده | ۱۰ |
| **۷** | ابزار سنجه اعتماد (۴ سنجه) + داشبورد | **خط پایه شروع به ثبت** | ۱۲ |
| **۸** | تست قرارداد + OpenAPI + lint/type | CI سبز | ۶ |
| — | **نقطه ورود فروش** (پس از گذشت ۳۰ روز خط پایه) | | |
| **۹-۱۲** | آماده‌سازی کیت فروش + سرد ۴۰ نهاد + ۱۵ گفت‌وگو | ۱۵ گفت‌وگو | ۲۰ |
| **۱۳-۱۴** | ۵ پیشنهاد قیمتی + مذاکره | ۲-۳ قرارداد | ۱۵ |

**جمع مهندسی: ~۸۴ ساعت (~۳ هفته).** این کوچک‌ترین کار با بیشترین بازده مالی فوری در کل برنامه است.

## ۱۰.۱ وابستگی به سند مادر
این WBS **در روز ۵۵ نقشه راه ۱۸۰ روزه** می‌نشیند، یعنی **بعد از** رفع B1 تا B3. اگر بازارگاه هنوز کار نمی‌کند، حامی روی صفحه‌ای می‌نشیند که خراب است. **ترتیب: کد → اعتماد → اسلات → فروش.**

---

# ۱۱. برآورد مالی

## ۱۱.۱ هزینه
| قلم | هزینه |
|---|---:|
| توسعه | ~۸۴ ساعت (هزینه لبه صفر اگر تیم موجود) |
| زیرساخت | صفر (اسلات استاتیک + CDN؛ بدون SDK) |
| هزینه لبه تبلیغ | ۰ درصد روی هر اسپانسر |
| تولید محتوای گزارش سالانه | ۱٬۰۰۰ تا ۳٬۰۰۰$ به ازای هر حامی |
| **جمع سال اول (۳ حامی)** | **~۹٬۰۰۰$** |

## ۱۱.۲ درآمد
| سناریو | حامی | میانگین | سال ۱ | سال ۲ | سال ۳ |
|---|---:|---:|---:|---:|---:|
| بدبینانه | ۲ | ۱۰٬۰۰۰$ | ۲۰٬۰۰۰$ | ۳۵٬۰۰۰$ | ۵۰٬۰۰۰$ |
| پایه | ۳ | ۲۵٬۰۰۰$ | ۷۵٬۰۰۰$ | ۱۴۰٬۰۰۰$ | ۲۱۰٬۰۰۰$ |
| خوش‌بینانه | ۵ | ۴۰٬۰۰۰$ | ۲۰۰٬۰۰۰$ | ۳۵۰٬۰۰۰$ | ۵۰۰٬۰۰۰$ |

**حاشیه ناخالص ~۹۰٪** (تنها هزینه، تولید گزارش سالانه است).

## ۱۱.۳ مقایسه با گزینه رد‌شده
| گزینه | درآمد سال ۱ | هزینه | ریسک اعتماد |
|---|---:|---:|---|
| شبکه تبلیغات برنامه‌ای | ۳٬۶۰۰ تا ۴۳٬۲۰۰$ | SDK + نگهداری + حریم خصوصی | **بالا** |
| **اسپانسرشیپ** | **۲۰٬۰۰۰ تا ۲۰۰٬۰۰۰$** | ~۹٬۰۰۰$ | **کنترل‌شده** |

**نتیجه:** اسپانسرشیپ هم پول بیشتری می‌آورد، هم ارزان‌تر است، هم ریسک اعتمادش کمتر. تفاوت فقط در ماهیت مدل است، نه در نتیجه.

---

# ۱۲. ریسک و برنامه بازگشت

| ریسک | آشکارساز | بازگشت |
|---|---|---|
| حامی بی‌برچسب یا خارج از محدوده | تست `sponsor-placement.test.ts` | CI قرمز، merge ممنوع |
| اسلات روی سطح توصیه | همان تست + ایمپورت در بک‌اند | CI قرمز |
| تارگتینگ رفتاری در آینده | بازبینی دوره‌ای: هیچ پارامتر کاربری در کوئری API | `Cache-Control` عمومی، endpoint عمومی |
| SDK بیگانه اضافه شود | بازبینی `package.json` هر فصل | حذف |
| حامی با ریسک اعتباری | فهرست سیاه + بازبینی فصلی ادعاهای سبز | `POST /terminate` |
| آسیب به اعتماد | ۴ سنجه §۸.۱ | کلید قطع §۸.۳ |
| تبدیل به شبکه تبلیغاتی | بازبینی فصلی + سقف سخت ۱۲٪ و ۱ حامی در هر صفحه | بازگشت به سیاست §۲.۶.۲ |

**بازگشت کامل کل سیستم: یک پرچم.** `ENABLE_SPONSOR_SLOT = False` بدون استقرار، همه ۱۰ صفحه را پاک می‌کند.

---

# پیوست — چک‌لیست راه‌اندازی

**پیش از نوشتن اولین خط کد**
- [ ] خط پایه چهار سنجه اعتماد ثبت شده (حداقل ۳۰ روز)
- [ ] B1 تا B3 رفع شده (بازارگاه کار می‌کند، داده دمو حذف شده)
- [ ] `CLAIMS.md` ساخته شده
- [ ] `ENABLE_SPONSOR_SLOT = False` در `settings.py`
- [ ] یک حامی بالقوه شناسایی شده که حاضر است ۲۰٬۰۰۰ دلار بدهد ← **بدون تقاضای واقعی، این کار اولویت نیست**

**پیش از فعال‌سازی**
- [ ] هر ۱۴ زبان ترجمه شده
- [ ] صفحه `public/policy/sponsors` منتشر
- [ ] فهرست عمومی حامیان منتشر (حتی اگر خالی باشد — **خالی بودن خودش یک پیام اعتماد است**)
- [ ] axe صفر نقض بحرانی · CLS صفر
- [ ] تست قرارداد سبز · OpenAPI به‌روز · lint/type سبز

**پیش از اولین قرارداد**
- [ ] نامه افشای حقوقی بازبینی و امضا
- [ ] فهرست سیاه توافق و امضا شده
- [ ] تعهد بازبینی فصلی در قرارداد
- [ ] **حق حذف ما در قرارداد**

**فصلی**
- [ ] بازبینی ادعاهای سبز همه حامیان فعال
- [ ] بازبینی `package.json` برای SDK بیگانه
- [ ] بازبینی ۴ سنجه اعتماد
- [ ] بازبینی سقف ۱۲٪ و ۱ حامی در هر صفحه
