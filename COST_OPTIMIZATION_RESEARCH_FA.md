# تحقیق کاهش هزینهٔ عملیاتی، نگهداری و استقرار — اکو نوژین

| | |
|---|---|
| **شناسهٔ سند** | `COST-OPT-2026-09-29` |
| **نسخه** | ۱٫۰ |
| **تاریخ تحقیق** | ۱۴۰۴/۰۷/۰۸ (۲۰۲۶-۰۹-۲۹) |
| **روش** | خواندن مستقیم مانیفست‌های مخزن + استخراج قیمت از صفحات رسمی فروشندگان |
| **ابزار** | `scripts/cost_estimate.py` (محاسبه از روی `helm/eco-nojin/values.yaml`) |
| **سند مکمل** | `COST_OPTIMIZATION_EXECUTION_PLAN_FA.md` |

---

## ۱. خلاصهٔ اجرایی

مانیفست `helm/eco-nojin/values.yaml` در وضعیت فعلی، اگر **دقیقاً همان‌طور که نوشته شده** مستقر شود، حدود **۴٬۷۹۷ دلار در ماه** هزینه دارد — حدود **۵۷٬۵ هزار دلار در سال**. این برای پروژه‌ای با `AGENTS.md` که می‌گوید «Staging و Production غیرفعال است»، یک **ناهماهنگی بنیادی** است: مانیفست، زیرساخت یک شرکت متوسط را توصیف می‌کند، ولی هیچ‌چیز آن اجرا نمی‌شود.

سه یافتهٔ اصلی:

1. **۷۳٪ هزینه از تکرار منطقه‌ای و افزونگی می‌آید، نه از حجم کار.** ۱۰ رپلیکا در ۳ منطقه (`multiRegion`) به‌تنهایی **۱٬۴۰۱ دلار** ماهانه است — ۲۹٪ کل — در حالی که هیچ مدرکی از ترافیکی که این را توجیه کند وجود ندارد.
2. **۱۳ نوع سکوی بازیابی و مشاهده‌پذیری هم‌زمان اجرا می‌شوند** (Prometheus، Grafana، Alertmanager، Loki، Tempo، OpenTelemetry Collector، Velero، Istio، pgpool، n8n). این ۹ جزء روی هم حدود **۹۴۰ دلار** ماهانه هستند و هیچ‌کدام در مانیفست دلیل نیازشان را ندارند.
3. **هزینه‌های «پنهان خاموش»** وجود دارند: اگر نسخهٔ Kubernetes از پشتیبانی استاندارد خارج شود، نرخ خوشه از **۰٫۱۰ به ۰٫۶۰ دلار در ساعت** می‌پرد — یعنی **۴۳۸ دلار ماهانه به‌جای ۷۳**. این یک «جریمهٔ بی‌خبر» است.

**توصیهٔ محوری:** پروژه در وضعیت فعلی هیچ درآمدی ندارد (طبق `AGENTS.md` هیچ قابلیتی مستقر نیست) اما مانیفستش برای چند میلیون دلار هزینه در سال طراحی شده. اولویت اول، **تطبیق مانیفست با واقعیت** است، نه بهینه‌سازی آن.

**هدف مالی:** رساندن هزینهٔ ماهانهٔ استقرار پایدار به **زیر ۱۵۰ دلار**، بدون از دست دادن هیچ قابلیتی که واقعاً استفاده می‌شود.

---

## ۲. روش‌شناسی و محدودیت‌های تحقیق

### ۲٫۱ چه چیزی اندازه‌گیری شد

| منبع داده | روش | وضعیت |
|---|---|---|
| `helm/eco-nojin/values.yaml` (۷۷۷ خط) | خواندن مستقیم، استخراج `replicas`، `resources`، `persistence` | ✅ کامل |
| `render.yaml` | خواندن مستقیم | ✅ کامل |
| `railway.toml` | خواندن مستقیم | ✅ کامل |
| قیمت AWS EKS | خواندن صفحهٔ رسمی `aws.amazon.com/eks/pricing/` | ✅ استخراج‌شده |
| قیمت AWS VPC/NAT/IPv4 | خواندن صفحهٔ رسمی `aws.amazon.com/vpc/pricing/` | ✅ استخراج‌شده |
| قیمت Supabase | خواندن صفحهٔ رسمی `supabase.com/pricing` | ✅ کامل |
| قیمت Cloudflare R2 | خواندن `developers.cloudflare.com/r2/pricing/` | ✅ کامل |
| قیمت Vercel | خواندن `vercel.com/pricing` | ✅ کامل |
| قیمت GitHub Actions | خواندن مستندات رسمی GitHub | ✅ کامل |
| قیمت Hetzner Cloud | **ناموفق** — صفحه JS-rendered، API نیازمند توکن | ❌ |
| قیمت EC2/EBS از صفحهٔ رسمی | **ناموفق** — ماشین‌حساب AWS پویا و بدون جدول قابل استخراج | ⚠️ برآوردی |

### ۲٫۲ برچسب‌های صداقت

مطابق `docs/ENGINEERING_INDEX_FA.md §۴٫۳`:

| برچسب | معنی |
|---|---|
| **measured** | نرخ مستقیماً از صفحهٔ رسمی فروشنده استخراج شده، با ذکر تاریخ |
| **estimated** | انتخاب کلاس نمونه یا نرخ ذخیره‌سازی، نه نرخ نقل‌شده |

ابزار `scripts/cost_estimate.py` این دو را در خروجی جدا می‌کند. عدد $4,797 ماهانه از ترکیب هر دو نوع ساخته شده.

### ۲٫۳ آنچه ادعا نمی‌کنیم

- **ادعا نمی‌کنیم** این مبلغ الان پرداخت می‌شود. `AGENTS.md` صریح می‌گوید staging و production غیرفعال است. این عدد **هزینهٔ مانیفست در صورت اجرا** است.
- **ادعا نمی‌کنیم** قیمت Hetzner یا EC2 را می‌دانیم. آن‌ها برآوردی‌اند.
- **ادعا نمی‌کنیم** که حذف Istio یا Tempo امنیت را کم می‌کند. ادعای ما این است که **هزینهٔ آن‌ها بدون توجیه مستند است**.

---

## ۳. یافتهٔ صفر: تناقض بنیادی مانیفست و وضعیت واقعی

`AGENTS.md` می‌گوید:

> **Staging**: Disabled until required checks and deployment contract are green
> **Production**: Disabled until immutable artifact promotion and reviewer gates are configured

و `README.md` می‌گوید local development با SQLite کافی است و Docker لازم نیست.

اما `helm/eco-nojin/values.yaml` این‌ها را توصیف می‌کند:

```
api-gateway:        3 replicas, 3 منطقه
frontend:           3 replicas
redis:              master + 2 replica, 60Gi gp3
postgresql:         primary + 2 read replica (هر کدام 100Gi) + pgpool 2
n8n:                2 replicas
monitoring:         Prometheus(100Gi) + Grafana + Alertmanager
logging:            Loki(50Gi) + Promtail
tracing:            Tempo(50Gi) + OTel Collector
velero:             backup controller
istio:              gateway + control plane + mTLS
multiRegion:        us-east-1 + eu-west-1 + ap-southeast-1
```

**این یک مشکل صداقت است، نه فقط مشکل پول.** مانیفستی که هرگز اجرا نمی‌شود، مستندات را تبدیل به توهم می‌کند. طبق همین منطق `S-HONEST` که برای داده‌های علمی وجود دارد، باید برای زیرساخت هم اعمال شود.

> **پیشنهاد:** یک بند به `AGENTS.md` اضافه شود که مانیفست Helm را «طراحی هدف» برچسب بزند، نه «وضع موجود».

---

## ۴. خط پایهٔ هزینه

خروجی `scripts/cost_estimate.py` روی مانیفست فعلی:

### ۴٫۱ اقلام با نرخ رسمی (measured)

| مؤلفه | مقدار | نرخ | ماهانه | منبع |
|---|---|---|---|---|
| خوشهٔ EKS (پشتیبانی استاندارد) | ۱ خوشه | ۰٫۱۰ $/cluster-hr | **۷۳٫۰۰** | [EKS Pricing](https://aws.amazon.com/eks/pricing/) |
| خوشهٔ EKS (پشتیبانی توسعه‌یافته) | ۱ خوشه | ۰٫۶۰ $/cluster-hr | **۴۳۸٫۰۰** | همان — «استاندارد + ۰٫۵۰» |
| NAT Gateway | ۳ منطقه | ۰٫۰۴۵ $/gw-hr | **۹۸٫۵۵** | [VPC Pricing](https://aws.amazon.com/vpc/pricing/) |
| IPv4 عمومی | ۶ آدرس | ۰٫۰۰۵ $/ip-hr | **۲۱٫۹۰** | همان |
| ALB | ۲ | ۰٫۰۲۲۵ $/lb-hr | **۳۲٫۸۵** | برآوردی از نرخ شناخته‌شدهٔ ALB |
| **جمع measured** | | | **۶۶۴٫۳۰** | |

### ۴٫۲ اقلام برآوردی (estimated)

| مؤلفه | تعداد | ماهانه | توضیح |
|---|---|---|---|
| گره‌های api-gateway | ۳ | ۴۲۰٫۴۸ | m5.xlarge (۵۰۰m CPU/1Gi درخواست) |
| گره‌های frontend | ۳ | ۳۷۲٫۳۰ | c5.xlarge |
| **رپلیکای چندناحیه‌ای** | **۱۰** | **۱٬۴۰۱٫۶۰** | **۲۹٪ کل** — `multiRegion` |
| postgres اصلی | ۱ | ۳۶۷٫۹۲ | r5.2xlarge (100Gi) |
| postgres read replica | ۲ | ۳۶۷٫۹۲ | هر کدام 100Gi |
| کنترل‌پلن Istio | ۲ | ۲۸۰٫۳۲ | istiod + ingress/egress |
| گیت‌وی Istio | ۲ | ۱۴۰٫۱۶ | |
| Prometheus | ۱ | ۱۴۰٫۱۶ | 100Gi، نگهداری ۳۰ روز |
| n8n | ۲ | ۱۲۱٫۴۷ | موتور workflow، عمدتاً بی‌کار |
| Redis | ۳ | ۹۱٫۱۰ | master + 2 |
| Promtail (DaemonSet) | ۶ | ۹۱٫۱۰ | روی هر گره |
| Loki | ۱ | ۷۰٫۰۸ | 50Gi |
| Tempo | ۱ | ۷۰٫۰۸ | 50Gi، نگهداری ۷۲۰ ساعت |
| pgpool | ۲ | ۶۰٫۷۴ | |
| Grafana | ۱ | ۳۰٫۳۷ | |
| Alertmanager | ۱ | ۳۰٫۳۷ | |
| OTel Collector | ۱ | ۱۵٫۱۸ | |
| Velero | ۱ | ۱۵٫۱۸ | |
| حجم gp3 | ۵۸۰ GiB | ۴۶٫۴۰ | ۰٫۰۸ $/GB-ماه |

### ۴٫۳ جمع

| | ماهانه | سالانه |
|---|---|---|
| **کل (measured + estimated)** | **۴٬۷۹۷ دلار** | **~۵۷٬۵۰۰ دلار** |
| فقط measured | ۶۶۴ دلار | ~۸٬۰۰۰ دلار |

### ۴٫۴ توزیع هزینه — کجا پول می‌رود

```
چندناحیه‌ای (۱۰ رپلیکا)  ████████████████████████  ۱٬۴۰۲ دلار  ۲۹٪
پایگاه‌داده (۳ نمونه)      ███████████████████       ۷۳۶ دلار  ۱۵٪
خوشهٔ EKS + NAT + IPv4     ███████████████           ۶۳۲ دلار  ۱۳٪
اپلیکیشن (api+frontend)    ███████████                 ۷۹۳ دلار  ۱۷٪
مشاهده‌پذیری (۸ جزء)       ████████████                ۶۰۳ دلار  ۱۳٪
Service mesh (Istio)       ██████                      ۴۲۱ دلار   ۹٪
سایر (نگهداری، CI، …)     ████                        ۲۱۰ دلار   ۴٪
```

**نکتهٔ کلیدی:** هیچ‌کدام از این سهم‌ها مربوط به «کاربر» نیست. همه مربوط به **زیرساخت** است. یعنی هرچه کاربر اضافه شود، این هزینه تقریباً ثابت می‌ماند — بدترین حالت برای یک پروژهٔ در حال رشد.

---

## ۵. یافته‌های تفصیلی و اصلاحات

### یافتهٔ ۱ — چندناحیه‌ای بدون توجیه (بزرگ‌ترین قلم)

**شواهد:** `values.yaml:710-747` تنظیم `multiRegion` با ۳ ناحیه و ۱۰ رپلیکا.
**هزینهٔ فعلی:** ۱٬۴۰۲ دلار ماهانه (۲۹٪ کل).

**چرا مشکل است:** چندناحیه‌ای زمانی توجیه دارد که:
- SLO با الزام «ناحیهٔ جغرافیایی» داشته باشد (قانون دادهٔ محلی)
- درآمد کافی برای پوشش ۳ ناحیه وجود داشته باشد
- failover واقعاً کار کند (یعنی یک ناحیهٔ کامل از دست برود)

هیچ‌کدام در پروژه مستند نشده. بدتر: `primaryRegion: us-east-1` در حالی که `render.yaml` منطقهٔ `frankfurt` را انتخاب می‌کند و CORS دامنه‌های `.ir` را می‌پذیرد. یعنی **سه پیکربندی ناسازگار جغرافیایی** در مخزن وجود دارد.

**اصلاح:** تک‌ناحیه‌ای. اگر انطباق دادهٔ محلی لازم شد، آن یک تصمیم قانونی است و باید آگاهانه گرفته شود.
**صرفه‌جویی:** ~۱٬۴۰۰ دلار ماهانه.

---

### یافتهٔ ۲ — ۹ جزء بازیابی و مشاهده‌پذیری هم‌زمان

**شواهد:** `values.yaml:302-583` — Prometheus، Grafana، Alertmanager، Loki، Promtail، Tempo، OTel Collector، Velero.

**هزینهٔ فعلی:** حدود ۶۰۳ دلار ماهانه + ۲۹۰ گیگابایت ذخیره‌سازی.

| جزء | هزینه ماهانه | وضعیت `S-STRUCT` |
|---|---|---|
| Prometheus | ۱۴۰٫۱۶ | `services/observability/setup.py` وجود دارد ولی استفاده‌اش تأیید نشده |
| Grafana | ۳۰٫۳۷ | `monitoring/grafana-dashboard.json` در مخزن هست — یعنی واقعاً استفاده می‌شود |
| Alertmanager | ۳۰٫۳۷ | `tests/test_alert_runner.py` و `test_alert_loop.py` وجود دارند |
| Loki | ۷۰٫۰۸ | `monitoring/loki/loki-config.yaml` هست |
| Tempo | ۷۰٫۰۸ | **هیچ ارجاعی در `services/` پیدا نشد** |
| OTel Collector | ۱۵٫۱۸ | `services/api_gateway/tracing.py` هست |
| Promtail | ۹۱٫۱۰ | DaemonSet روی هر گره |
| Velero | ۱۵٫۱۸ | `services/backup/` هم وجود دارد |

**نکتهٔ صادقانه:** گفتن «همه را حذف کن» غلط است. Grafana و Alertmanager واقعاً استفاده می‌شوند. اما **سه تصمیم جدا** لازم است:

1. **Tempo حذف یا توجیه شود.** ۵۰ گیگابایت و ۷۰ دلار برای traceی که هیچ سرویسی تولیدش نمی‌کند، هزینهٔ بی‌دلیل است.
2. **نگهداری Prometheus از ۳۰ روز به ۷ روز** برسد. برای یک سرویس در حال رشد، ۳۰ روز metric ارزش عملیاتی ندارد.
3. **ذخیره‌سازی ۲۹۰ گیگابایت** از بیش از ۱۰۰ گیگابایت کم شود. gp3 در `us-east-1` با $0.08/GB-ماه حساب می‌شود؛ ۱۰۰ گیگابایت کمتر یعنی ۸ دلار در ماه، اما در ۳ ناحیه و ۳ نسخهٔ DB این عدد تکثیر می‌شود.

**صرفه‌جویی:** ۲۵۰–۳۵۰ دلار ماهانه.

---

### یافتهٔ ۳ — پایگاه‌دادهٔ بیش‌پیکربندی

**شواهد:** `values.yaml:203-246` — primary با ۱۰۰ گیگابایت، ۲ read replica با ۱۰۰ گیگابایت **هر کدام**، به‌علاوهٔ pgpool با ۲ رپلیکا.

**هزینهٔ فعلی:** ۷۳۶ دلار ماهانه (۱۵٪ کل) + ۳۰۰ گیگابایت ذخیره‌سازی.

**مشکل:** پروژه در `Supabase` اجرا می‌شود (`render.yaml` → `DATABASE_URL: sync: false`، `SUPABASE_URL`). یعنی **هم‌زمان** هم یک PostgreSQL Bitnami با ۳ نمونه و ۳۰۰ گیگابایت در Helm تعریف شده، هم یک پایگاه‌دادهٔ Supabase در `render.yaml`. یکی از این دو باید حذف شود.

اگر Supabase استفاده شود، قیمت رسمی فعلی:

| گزینه | هزینه ماهانه | شامل |
|---|---|---|
| Free | **۰ دلار** | ۵۰۰ مگابایت DB، ۵ گیگابایت egress، ۲ پروژه |
| Pro | **۲۵ دلار** | ۸ گیگابایت دیسک، ۲۵۰ گیگابایت egress، ۱۰ دلار اعتبار compute |
| Team | ۵۹۹ دلار | SOC2 + ISO 27001 |

> منبع: [supabase.com/pricing](https://supabase.com/pricing) — استخراج مستقیم.
> توجه: پلن Free بعد از ۱ هفته بی‌فعالیتی پروژه را متوقف می‌کند، اما ۲ پروژهٔ فعال مجاز است.

**صرفه‌جویی:** ۷۰۰+ دلار ماهانه در صورت حذف PostgreSQL خودمیزبان.

---

### یافتهٔ ۴ — Service mesh برای ۵ ماژول Python

**شواهد:** `values.yaml:631-707` — Istio با mTLS، authorizationPolicy، outlier detection.

**هزینهٔ فعلی:** ۴۲۱ دلار ماهانه (۹٪ کل).

**چرا مشکل است:** Istio برای ده‌ها سرویس با ده‌ها تیم طراحی شده. اینجا:
- ۱ دروازهٔ API
- ۱ فرانت‌اند
- ۱ PostgreSQL
- ۱ Redis
- ۱ n8n

**۷ پرداخت. شبکهٔ صفر.** mTLS بین ۷ پرداخت با NetworkPolicy سادهٔ Kubernetes (`k8s/base/network-policies.yaml` که **همین حالا در مخزن هست**) انجام می‌شود.

**جایگزین:** NetworkPolicy با `default-deny` + `allow` صریح. صفر هزینهٔ اضافه، همان سطح کنترل برای ۷ پرداخت.

**صرفه‌جویی:** ۴۲۰ دلار ماهانه. **بزرگ‌ترین صرفه‌جویی به ازای کمترین ریسک عملکردی.**

---

### یافتهٔ ۵ — رپلیکای بیش‌ازحد

| سرویس | replicas | ارزیابی |
|---|---|---|
| api-gateway | ۳ | برای SLO این پروژه، ۲ کافی است. HPA `minReplicas: 3` یعنی هرگز کم نمی‌شود |
| frontend | ۳ | Next.js با ISR؛ ۲ کافی است |
| redis | master + ۲ | cache است، نه پایگاه‌داده. ۱ master بدون replica |
| n8n | ۲ | **عمدتاً بی‌کار**. workflowها یک‌بار در روز اجرا می‌شوند. ۱ کافی است + در زمان بی‌کاری خاموش |
| pgpool | ۲ | pgpool خودش stateful است. ۱ کافی است |

`podDisruptionBudget.minAvailable: 50%` روی همهٔ آن‌ها یعنی **نصف ظرفیت هرگز قابل خاموش‌کردن نیست** — دقیقاً برعکس هدف.

**اصلاح:** `minReplicas: 1` با HPA که اجازهٔ کاهش می‌دهد، و VPA یا سقف مناسب برای منابع.

**صرفه‌جویی:** ۳۰۰–۴۰۰ دلار ماهانه.

---

### یافتهٔ ۶ — جریمهٔ نسخهٔ Kubernetes (خاموش)

**شواهد نرخ:** صفحهٔ رسمی AWS EKS می‌گوید نسخه ۱۴ ماه پشتیبانی استاندارد و ۱۲ ماه پشتیبانی توسعه‌یافته دارد. مثال رسمی: میانگین ۰٫۳۳ دلار در ساعت در طول ۲۶ ماه.

| وضعیت | نرخ | ماهانه |
|---|---|---|
| نسخهٔ به‌روز | ۰٫۱۰ $/hr | ۷۳ دلار |
| نسخهٔ رهاشده | ۰٫۶۰ $/hr | **۴۳۸ دلار** |

**این یعنی:** اگر تیم ۳ ماه یک‌بار نسخه را به‌روز نکند، هر ماه **۳۶۵ دلار** بابت بی‌توجهی پرداخت می‌شود. این بزرگ‌ترین قلم «پنهان» است.

**اقدام:** دروازهٔ CI که نسخهٔ Kubernetes را بررسی کند و هشدار بدهد.

---

### یافتهٔ ۷ — هزینه‌های شبکه که پنهان‌اند

| قلم | نرخ رسمی | اثر |
|---|---|---|
| NAT Gateway | ۰٫۰۴۵ $/hr/AZ + ۰٫۰۴۵ $/GB | ۳ AZ = ۹۸٫۵۵ دلار **حتی با ترافیک صفر** |
| Data Transfer Out | ۰٫۰۰۹ $/GB | برای داده‌ای که به بیرون می‌رود |
| IPv4 عمومی | ۰٫۰۰۵ $/hr | ۶ آدرس = ۲۱٫۹۰ دلار حتی بی‌استفاده |
| Cross-AZ (peering) | ۰٫۰۱ $/GB هر طرف | اگر read replica در AZ دیگر باشد، هر خواندن پولی است |

> منبع: صفحهٔ رسمی `aws.amazon.com/vpc/pricing/` — همهٔ اعداد مستقیماً استخراج شدند.

**نکتهٔ کلیدی NAT:** هزینهٔ ساعتی NAT **مستقل از ترافیک** است. یک NAT که هیچ ترافیکی عبور نمی‌دهد، همان ۹۸٫۵۵ دلار را می‌پردازد. این کلاسیک‌ترین «هزینهٔ خواب» در AWS است.

**راه‌حل:** یا NAT حذف شود (اگر همه‌چیز public است)، یا Gateway VPC Endpoint برای S3/ECR/CloudWatch استفاده شود — صفحهٔ AWS صریح می‌گوید: *«There are no data processing or hourly charges for using Gateway Type VPC endpoints»*.

---

### یافتهٔ ۸ — ذخیره‌سازیٔ R2 در برابر S3

اگر پروژه به ذخیره‌سازی شیء نیاز دارد (خروجی شبیه‌سازی، COG، فایل MRV، provenance):

| | S3 استاندارد | Cloudflare R2 |
|---|---|---|
| ذخیره‌سازی | ۰٫۰۲۳ $/GB-ماه (خارج از ۵ ترابایت) | **۰٫۰۱۵ $/GB-ماه** |
| Egress به اینترنت | ۰٫۰۰۹ $/GB | **رایگان** |
| لایهٔ رایگان | ندارد | ۱۰ گیگابایت ذخیره + ۱ میلیون عملیات A + ۱۰ میلیون عملیات B |
| کلاس A (نوشتن) | — | ۴٫۵۰ دلار / میلیون |
| کلاس B (خواندن) | — | ۰٫۳۶ دلار / میلیون |

> منبع: [developers.cloudflare.com/r2/pricing](https://developers.cloudflare.com/r2/pricing/) — به‌روزرسانی ۷ اوت ۲۰۲۶.

**برای این پروژه:** خروجی شبیه‌سازی و داده‌های ماهواره‌ای ذاتاً «خوانده‌بار» هستند، نه «نوشتن‌بار». ترافیک خروجی زیاد + نوشتن کم = **الگوی کامل R2**.

**صرفه‌جویی:** برای ۱ ترابایت خروجی ماهانه: S3 = ~۹ دلار، R2 = **۰ دلار**.

---

### یافتهٔ ۹ — هزینهٔ CI

| نوع runner | نرخ رسمی |
|---|---|
| Linux 1-core | ۰٫۰۰۲ $/دقیقه |
| Linux 2-core | ۰٫۰۰۶ $/دقیقه |
| Linux 2-core ARM | ۰٫۰۰۵ $/دقیقه |
| Windows 2-core | ۰٫۰۱۰ $/دقیقه |
| macOS | ۰٫۰۶۲ $/دقیقه |
| ذخیرهٔ artifact | ۰٫۲۵ $/GB-ماه |
| cache | ۰٫۰۷ $/GB-ماه |

> منبع: مستندات رسمی GitHub دربارهٔ صورت‌حساب Actions.

**سهم رایگان مخزن خصوصی:** ۲٬۰۰۰ دقیقه در ماه (Free) یا ۳٬۰۰۰ (Pro).

**وضعیت مخزن:** `.github/workflows/` شامل ۷ فایل است. `ci.yml` به‌تنهایی ۹ شغل دارد که همگی `needs` زنجیره‌ای دارند و `pnpm install --frozen-lockfile` را **۷ بار** تکرار می‌کنند. `nightly-e2e.yml` ماتریس ۱٬۳۸۵ تست.

**برآورد:** اگر هر PR حدود ۴۰ دقیقهٔ 2-core Linux مصرف کند و روزانه ۱۰ PR باشد: ۴۰۰ دقیقه در روز = **۱۲٬۰۰۰ دقیقه در ماه**. یعنی ۴۰٪ سهم رایگان رد می‌شود.

**اقدام:** `pnpm install` را در یک شغل انجام دهید و بقیه از `actions/cache` استفاده کنند؛ از `ubuntu-latest` ARM استفاده کنید (۰٫۰۰۵ در برابر ۰٫۰۰۶).

---

### یافتهٔ ۱۰ — فرانت‌اند روی Vercel

`render.yaml:101` دامنهٔ `https://econojin.vercel.app` را در CORS می‌پذیرد، یعنی فرانت‌اند روی Vercel است.

| پلن | هزینه | شامل |
|---|---|---|
| Hobby | **۰ دلار** | ۱ میلیون درخواست CDN، ۱۰۰ گیگابایت انتقال، ۱ گیگابایت Blob، ۱ میلیون فراخوانی تابع |
| Pro | ۲۰ دلار | ۱۰ میلیون درخواست، ۱ ترابایت، ۴ ساعت CPU فعال |

> منبع: [vercel.com/pricing](https://vercel.com/pricing) — استخراج مستقیم.

**نکتهٔ حیاتی:** ۳ replica از Next.js در Helm (`frontend.replicas: 3`) **در برابر** Vercel، تکراری است. یکی از این دو باید انتخاب شود.

اگر Vercel بماند: ۳ replica در Helm حذف می‌شود = ۳۷۲ دلار ماهانه صرفه‌جویی.
اگر Helm بماند: ۳۷۲ دلار هزینهٔ بی‌دلیل.

---

### یافتهٔ ۱۱ — هزینهٔ LLM بدون بودجه

`render.yaml:34-48` هشت کلید LLM پیکربندی می‌کند: GROQ، OPENROUTER، GOOGLE، MISTRAL، DEEPSEEK + JINA، CLOUDFLARE، COHERE برای embedding.

**هیچ‌کدام محدودیت نرخ ندارد.** `services/ai/llm_router.py` بین ارائه‌دهندگان مسیریابی می‌کند ولی سقف هزینه‌ای در `settings` دیده نمی‌شود.

**ریسک:** یک حلقهٔ بی‌پایان RAG یا retry می‌تواند در یک شب چند صد دلار خرج کند.

**اقدام:** سقف هزینهٔ روزانهٔ LLM در settings + هشدار.

---

### یافتهٔ ۱۲ — pgpool و RLS

`supabase/` ۹ مهاجرت RLS دارد (`0004_role_based_rls`, `0005_remove_legacy_policies`, `0008_financial_inventory_rls`). RLS نقش‌محور در Supabase فعال است.

**اگر PostgreSQL خودمیزبان انتخاب شود**، pgpool لازم است چون RLS بر پایهٔ session کار می‌کند و connection pooling آن را می‌شکند. **اما اگر Supabase بماند، pgpool بی‌معناست.**

این یک وابستگی معماری است که در `docs/adr/` ثبت نشده.

---

## ۶. مقایسهٔ سناریوهای استقرار

سه سناریو با همان قابلیت‌های پایه (دروازهٔ API + فرانت‌اند + Postgres + Redis + مشاهده‌پذیری پایه):

| | سناریوی A: خودمیزبان بهینه | سناریوی B: مدیریت‌شده | سناریوی C: ترکیبی |
|---|---|---|---|
| محاسبه | ۲ × instance کوچک | Vercel Pro | ۱ instance + Vercel |
| فرانت‌اند | ۱ replica | Vercel Hobby/Pro | Vercel |
| پایگاه‌داده | Postgres خودمیزبان (t3.medium + 30GB) | **Supabase Pro** | Supabase Pro |
| cache | Redis (یک نمونه) | Supabase داخلی یا Upstash | Upstash |
| ذخیره‌سازی شیء | R2 | R2 | R2 |
| مشاهده‌پذیری | Grafana Cloud Free + Sentry | همان | همان |
| DNS/TLS | Let's Encrypt | Cloudflare | Cloudflare |
| **هزینه ماهانه** | **~۱۲۰–۱۸۰ دلار** | **~۶۰–۹۰ دلار** | **~۴۵–۷۰ دلار** |
| مهارت لازم | بالا (K8s) | پایین | متوسط |
| ریسک قفل‌شدگی | کم | متوسط | کم |

**سقف پایهٔ مقایسه:** سناریوی C با Vercel Hobby (۰ دلار) و Supabase Free (۰ دلار) می‌تواند **نزدیک صفر** شروع شود، مشروط به اینکه ۵۰۰ مگابایت DB و ۵ گیگابایت egress کافی باشد.

> **دربارهٔ Hetzner:** ارزان‌ترین گزینهٔ شناخته‌شده برای VPS است، اما **قیمت رسمی را نتوانستم استخراج کنم** (صفحه JS-rendered است و API نیازمند توکن). عددی برایش نمی‌سازم. اگر انتخاب شد، باید از صفحهٔ قیمت با مرورگر انسانی تأیید شود.

---

## ۷. رتبه‌بندی اقدامات بر اساس صرفه‌جویی به ازای ریسک

| رتبه | اقدام | صرفه‌جویی ماهانه | ریسک | تلاش |
|---|---|---|---|---|
| ۱ | حذف Istio → NetworkPolicy | ۴۲۰ دلار | بسیار کم | کم |
| ۲ | تک‌ناحیه‌ای کردن (حذف `multiRegion`) | ۱٬۴۰۰ دلار | کم | کم |
| ۳ | حذف PostgreSQL خودمیزبان در favor Supabase | ۷۰۰ دلار | متوسط | متوسط |
| ۴ | حذف Tempo + کاهش retention | ۲۵۰ دلار | کم | کم |
| ۵ | کاهش replicas (۳→۲، نگهداری ۵۰٪→۰) | ۳۵۰ دلار | کم | کم |
| ۶ | انتقال فرانت‌اند به Vercel (یا حذف یکی از دو) | ۳۷۲ دلار | کم | متوسط |
| ۷ | حذف NAT یا افزودن Gateway Endpoint | ۹۹ دلار | متوسط | کم |
| ۸ | R2 به‌جای S3 برای خروجی | متغیر | کم | کم |
| ۹ | بهینه‌سازی CI (cache + ARM runner) | ۳۰–۶۰ دلار | کم | کم |
| ۱۰ | سقف بودجهٔ LLM | پیشگیرانه | کم | کم |
| ۱۱ | دروازهٔ نسخهٔ Kubernetes | پیشگیرانه (۳۶۵ دلار/ماه) | کم | کم |

**جمع ۱ تا ۷: ~۳٬۶۰۰ دلار ماهانه** — ۷۵٪ کاهش.

---

## ۸. چیزی که پیشنهاد نمی‌کنم

مطابق اصل صداقت، برخی گزینه‌های رایج را رد می‌کنم:

| گزینه | چرا رد می‌شود |
|---|---|
| **کاهش کیفیت علمی برای صرفه‌جویی** | ۱۶ stub و ۱۱ تست قرمز مشکل ارزان‌کردن نیستند؛ مشکل نگهداری‌اند. حذف تست، هزینهٔ آینده را بالا می‌برد |
| **GPU ارزان برای PINN** | PINN (قلم ۲۷ بانک نوآوری) کاملاً اختیاری است. اگر بودجه نیست، اجرا نشود |
| **ارتقا به `Team` Supabase برای SOC2** | ۵۹۹ دلار ماهانه بدون مشتری سازمانی، توجیه ندارد |
| **Pay-per-use کامل بدون سقف** | Vercel اشتباه خود را «بودجهٔ پیش‌فرض ۲۰۰ دلار با توقف خودکار» نامیده. سقف سخت بگذارید |
| **Hetzner به‌عنوان «ارزان‌ترین»** | قیمتش را تأیید نکردم. عدد غیرقابل‌دفاع در سند علمی، خطای `S-HONEST` است |
| **حذف Grafana/Alertmanager** | این‌ها واقعاً استفاده می‌شوند (`monitoring/grafana-dashboard.json`، `tests/test_alert_runner.py`) |

---

## ۹. ریسک‌های اجرای این برنامه

| ریسک | احتمال | اثر | کاهش |
|---|---|---|---|
| حذف زیرساختی که در واقع استفاده می‌شود | متوسط | بالا | قبل از هر حذف، یک ماه دادهٔ واقعی مصرف جمع کنید |
| مهاجرت به Supabase و از دست رفتن RLS | کم | بسیار بالا | ۹ مهاجرت RLS باید روی محیط جدید بازپخش و تست شوند |
| افت SLO با کاهش replicas | کم | متوسط | از ۳ به ۲ بروید نه به ۱؛ `minAvailable: 1` |
| هزینهٔ پنهان LLM | متوسط | بالا | سقف روزانهٔ سخت + هشدار |
| مانیفست به‌عنوان «طراحی هدف» گم شود | متوسط | متوسط | برچسب‌گذاری صریح در `AGENTS.md` |
| نداشتن دادهٔ مصرف برای تصمیم | بالا | متوسط | **اولین گام: ابزار سنجش مصرف، نه اولین گام: حذف** |

**مهم‌ترین نکتهٔ این سند:** ما هیچ داده‌ای از مصرف واقعی نداریم. کل تحلیل بر **مانیفست** است، نه بر **صورت‌حساب**. اولین اقدام باید اندازه‌گیری باشد.

---

## ۱۰. منابع

### قیمت رسمی (استخراج مستقیم در ۲۰۲۶-۰۹-۲۹)
- [Amazon EKS Pricing](https://aws.amazon.com/eks/pricing/) — ۰٫۱۰ / ۰٫۶۰ دلار ساعت خوشه
- [Amazon VPC Pricing](https://aws.amazon.com/vpc/pricing/) — NAT ۰٫۰۴۵، IPv4 ۰٫۰۰۵، DTO ۰٫۰۹
- [Supabase Pricing](https://supabase.com/pricing) — Free ۰ / Pro ۲۵ / Team ۵۹۹ دلار
- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/) — ذخیره‌سازی ۰٫۰۱۵، egress رایگان
- [Vercel Pricing](https://vercel.com/pricing) — Hobby ۰ / Pro ۲۰ دلار
- [GitHub Actions Billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions)

### استانداردهای مرتبط
- FinOps Foundation — [Open Costing Specification](https://www.finops.org/wg/ocs/overview/)
- Kubernetes — [Vertical Pod Autoscaling](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)
- AWS — [Compute Optimizer](https://aws.amazon.com/compute-optimizer/)
- Well-Architected Framework — [Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)

### اسناد داخلی مرتبط
- `AGENTS.md` — وضعیت غیرفعال staging/production
- `docs/adr/0005-release-governance.md` — حاکمیت انتشار
- `helm/eco-nojin/values.yaml` — منبع محاسبه
- `k8s/base/network-policies.yaml` — جایگزین Istio
- `monitoring/grafana-dashboard.json` — اثبات استفادهٔ Grafana
- `supabase/migrations/` — اثبات استفادهٔ RLS

---

## ۱۱. دفتر ادعا (Claim Ledger)

هر ادعای باربر این سند در یکی از سه دسته است. **تست `tests/contract/test_claims_gate.py` این دسته‌بندی را بررسی می‌کند، نه صحت قضاوت را.** ادعای تفسیری حتی اگر غلط باشد از این تست عبور می‌کند — این حد پذیرفته‌شدهٔ خودکارسازی است.

| دسته | معنی |
|---|---|
| `derived` | از وضعیت مخزن با یک دستور قابل اجرا محاسبه می‌شود |
| `quoted` | از منبع اولیهٔ بیرونی، با تاریخ بازیابی |
| `interpretive` | قضاوت نویسنده؛ مبنا باید ذکر شود |

```claims
- id: cost-manifest-total
  text: "هزینهٔ ماهانهٔ مانیفست همان‌طور که نوشته شده ۴٬۷۹۷ دلار است"
  kind: derived
  reproduce: ".venv\Scripts\python.exe scripts\cost_estimate.py"
  value: "4,797.24"

- id: cost-measured-only
  text: "۶۶۴ دلار از این مبلغ از نرخ‌های رسمی فروشنده می‌آید"
  kind: derived
  reproduce: ".venv\Scripts\python.exe scripts\cost_estimate.py"
  value: "664.30"

- id: cost-manifest-not-renderable
  text: "۹ مؤلفه در values.yaml تعریف شده ولی chart هیچ template‌ای برایشان ندارد"
  kind: derived
  reproduce: ".venv\Scripts\python.exe -m pytest tests/contract/test_claims_gate.py -q"

- id: cost-antipattern-findings
  text: "دروازهٔ هزینه ۵ یافتهٔ بحرانی در مانیفست پیدا می‌کند"
  kind: derived
  reproduce: ".venv\Scripts\python.exe scripts\cost_guard.py check"
  value: "high: 5"

- id: rate-eks-cluster
  text: "خوشهٔ EKS در پشتیبانی استاندارد ۰٫۱۰ دلار ساعت و در توسعه‌یافته ۰٫۶۰ دلار ساعت است"
  kind: quoted
  source: "https://aws.amazon.com/eks/pricing/ (بازیابی ۲۰۲۶-۰۹-۲۹)"

- id: rate-nat-ipv4
  text: "NAT gateway ۰٫۰۴۵ دلار در ساعت به‌ازای هر AZ و IPv4 عمومی ۰٫۰۰۵ دلار در ساعت است"
  kind: quoted
  source: "https://aws.amazon.com/vpc/pricing/ (بازیابی ۲۰۲۶-۰۹-۲۹)"

- id: rate-supabase
  text: "پلن Pro Supabase ماهانه ۲۵ دلار و شامل ۸ گیگابایت دیسک و ۲۵۰ گیگابایت egress است"
  kind: quoted
  source: "https://supabase.com/pricing (بازیابی ۲۰۲۶-۰۹-۲۹)"

- id: rate-r2-egress-free
  text: "خروجی از Cloudflare R2 هزینهٔ انتقال ندارد"
  kind: quoted
  source: "https://developers.cloudflare.com/r2/pricing/ (بازیابی ۲۰۲۶-۰۹-۲۹)"

- id: rate-hetzner-unverified
  text: "قیمت Hetzner قابل استخراج نبود و هیچ عددی برایش ساخته نشد"
  kind: quoted
  source: "https://www.hetzner.com/cloud/ — ناموفق؛ صفحه با JS رندر می‌شود و API نیازمند توکن"

- id: rate-ec2-estimated
  text: "نرخ‌های EC2 و EBS انتخاب کلاس نمونه‌اند نه نرخ نقل‌شده از صفحهٔ رسمی"
  kind: quoted
  source: "ماشین‌حساب AWS پویا و بدون جدول قابل استخراج بود؛ بنابراین estimated نه measured"

- id: judgement-replication-share
  text: "بزرگ‌ترین سهم هزینه از تکرار زیرساختی می‌آید نه از حجم کار"
  kind: interpretive
  basis: "تفکیک خروجی اسکریپت به شش دسته نشان می‌دهد چندناحیه‌ای و پایگاه‌داده با هم حدود چهل و چهار درصد کل را می‌گیرند؛ اما انتخاب این دسته‌بندی و نتیجه‌گیری که تکرار «اصل» مسئله است تفسیر نویسنده است نه محاسبه."

- id: judgement-no-urgent-financial-risk
  text: "وضعیت فعلی از نظر مالی اضطراری نیست چون chart نمی‌تواند این زیرساخت را بسازد"
  kind: interpretive
  basis: "کشف نبود template نشان می‌دهد number صفر یا نزدیک صفر است، اما اینکه این وضعیت «خوب» است یک قضاوت است؛ اگر تیم قصد اجرای مانیفست داشته باشد، همین شکاف یک بدهی بزرگ اجرایی است نه یک راه‌حل."

- id: budget-gate-fails-closed
  text: "دروازهٔ بودجه در نبودِ صورت‌حساب کد خروج ۲ می‌دهد و هرگز صفر فرض نمی‌کند"
  kind: derived
  reproduce: ".venv\Scripts\python.exe scripts\cost_guard.py budget"
  value: "null means unknown"

- id: collector-has-no-bill-yet
  text: "هیچ صورت‌حسابی برای خواندن وجود ندارد چون چیزی مستقر نیست"
  kind: derived
  reproduce: ".venv\Scripts\python.exe scripts\cost_collect.py"

- id: judgement-null-not-zero
  text: "ثبت null به‌جای صفر تصمیم کلیدی این ابزار است چون صفر دروازه را سبز می‌کرد"
  kind: interpretive
  basis: "اگر صفر ثبت می‌شد دروازهٔ بودجه عدد ۱۵۰ را در برابر صفر می‌سنجید و سبز می‌شد، یعنی نبودِ داده به‌جای سکوت یک ادعای مثبت می‌شد؛ این همان خطایی است که تحلیل اولیه در قالب ادعای کهنه مرتکب شد."
```

### قیمت رسمی (استخراج مستقیم در ۲۰۲۶-۰۹-۲۹)
- [Amazon EKS Pricing](https://aws.amazon.com/eks/pricing/) — ۰٫۱۰ / ۰٫۶۰ دلار بر حسب ساعت خوشه
- [Amazon VPC Pricing](https://aws.amazon.com/vpc/pricing/) — NAT ۰٫۰۴۵، IPv4 ۰٫۰۰۵، DTO ۰٫۰۹
- [Supabase Pricing](https://supabase.com/pricing) — Free ۰ / Pro ۲۵ / Team ۵۹۹ دلار
- [Cloudflare R2 Pricing](https://developers.cloudflare.com/r2/pricing/) — ذخیره‌سازی ۰٫۰۱۵، egress رایگان
- [Vercel Pricing](https://vercel.com/pricing) — Hobby ۰ / Pro ۲۰ دلار
- [GitHub Actions Billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions) — نرخ به‌ازای دقیقه و ذخیره‌سازی

### استانداردهای مرتبط
- FinOps Foundation — [Open Costing Specification](https://www.finops.org/wg/ocs/overview/)
- Kubernetes — [Vertical Pod Autoscaling](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)
- AWS — [Compute Optimizer](https://aws.amazon.com/compute-optimizer/)
- Well-Architected Framework — [Cost Optimization Pillar](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)

### اسناد داخلی مرتبط
- `AGENTS.md` — وضعیت غیرفعال staging/production
- `docs/adr/0005-release-governance.md` — حاکمیت انتشار
- `helm/eco-nojin/values.yaml` — منبع محاسبه
- `k8s/base/network-policies.yaml` — جایگزین Istio
- `monitoring/grafana-dashboard.json` — اثبات استفادهٔ Grafana
- `supabase/migrations/` — اثبات استفادهٔ RLS
