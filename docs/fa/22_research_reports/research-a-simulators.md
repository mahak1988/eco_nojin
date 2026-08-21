# گزارش تحقیق علمی-فنی: شبیهسازهای علوم کشاورزی و روشهای ساخت هستههای علمی محاسباتی

**پروژه:** اکو نوژین (Eco Nojin) — پلتفرم بینالمللی کشاورزی/سنجشازدور با موتور علمی HyDroMa
**بکاند:** FastAPI/Python — **هسته عددی:** C++20
**تاریخ:** ۲۰۲۶-۰۸-۱۷
**نوع سند:** گزارش تحقیق وب (خروجی subagent محقق)

---

## فهرست

1. مدلهای محصول (Crop Models)
2. مدلهای هیدرولوژی (Hydrology Models)
3. مدلهای خاک و کربن (Soil & Carbon Models)
4. روشهای عددی و پیادهسازی کدنویسی (Numerical Methods & Implementation)
5. کالیبراسیون و اعتبارسنجی (Calibration & Validation)
6. معماری سرویس-محور (Service-Oriented Architecture)
7. پیادهسازی در HyDroMa
8. فهرست منابع (URLهای یافتشده در جستجو)

---

## ۱) مدلهای محصول (Crop Models)

### ۱.۱ DSSAT / CERES

DSSAT (مخفف Decision Support System for Agrotechnology Transfer) یک بسته نرمافزاری است که شامل مدلهای دینامیک رشد گیاه، پایگاهدادههای آبوهوا/خاک/گیاه و ابزارهای ارزیابی راهبردهای زراعی است (dssat.net). خانواده مدلهای CSM (Cropping System Model) آن بیش از ۴۵ محصول را پوشش میدهد (github.com/DSSAT/dssat-csm-os). مدلهای سری CERES (مانند CERES-Maize، CERES-Rice، CERES-Wheat) زیرمجموعه DSSAT هستند.

**چه چیزی شبیهسازی میکنند؟** فنولوژی (مراحل نمو بر اساس درجه-روز رشد یا GDD)، رشد رویشی و زایشی، توسعه سطح برگ (LAI)، انباشت زیستتوده (biomass)، تخصیص ماده خشک به اندامها، عملکرد نهایی، بیلان آب خاک، چرخه نیتروژن و اثر CO2 اتمسفری. طبق توضیح رسمی دسست (dssat.net/csm-ceres-rice)، انباشت زیستتوده در CERES با رویکرد بازده استفاده از تشعشع (Radiation Use Efficiency) و با احتساب اثر غلظت CO2 انجام میشود.

**ورودیهای اصلی:** ضرایب ژنوتیپی/رقمی (cultivar coefficients)، دادههای هواشناسی روزانه (دمای حداقل و حداکثر، بارش، رطوبت نسبی، تابش)، مشخصات اولیه خاک و مدیریت زراعی (تاریخ کاشت، تراکم، کود و آبیاری) (frontiersin.org — Adnan 2017). خروجیهای اصلی: عملکرد دانه، زیستتوده روی زمین، LAI، مراحل فنولوژی، تبخیر-تعرق و رطوبت خاک؛ طبق quantitative-plant.org مدلهای CERES زیستتوده، شاخص برداشت، تبخیر-تعرق و آب خاک را «معقولانه» شبیهسازی میکنند.

**مفاهیم کلیدی:**
- **شاخص برداشت (Harvest Index):** نسبت عملکرد اقتصادی به کل زیستتوده روی زمین. معادله: **Y = HI × B** (عملکرد = شاخص برداشت × زیستتوده). در مدلهای CERES، HI بهصورت دینامیک در طول دوره پرشدن دانه توسعه مییابد.
- **انباشت زیستتوده:** ΔB = RUE × PAR_intercepted (افزایش زیستتوده = بازده استفاده از تشعشع × تشعشع فعال فتوسنتزی جذبشده توسط تاجپوشش).
- **فنولوژی:** تجمیع درجه-روز رشد: GDD = Σ max(0, (Tmax + Tmin)/2 − Tbase).

### ۱.۲ APSIM

APSIM (Agricultural Production Systems sIMulator) توسط CSIRO استرالیا توسعه یافته و یک «سیستم نرمافزاری» است که مدلهای تولید گیاه و مرتع، تجزیه بقایا و فرآیندهای خاک را یکپارچه میکند (sciencedirect.com — McCown 1996). معماری آن **ماژولار/پلاگینی** است: بیش از ۸۰ ماژول که شبیهسازی برهمکنشهای گیاه، دام، خاک، اقلیم و مدیریت را ممکن میسازد (apsim.info). نکته مهم معماری: مدلهای مختلف گیاهی **ماژولهای مشترک** بیلان آب، نیتروژن و مواد آلی خاک را به اشتراک میگذارند (csiro.au) — این الگو دقیقاً همان چیزی است که در هسته HyDroMa قابل تقلید است.

**ورودیها:** فایلهای پیکربندی XML/JSON شامل اقلیم (متریولوژی روزانه)، خاک (پروفایل لایهای)، مدیریت (تناوب زراعی، آبیاری، کود) و پارامترهای گیاه. **خروجیها:** زیستتوده، عملکرد، نیتروژن گیاه، رطوبت و نیترات خاک، رواناب و آبشویی، تجزیه بقایا. APSIM بهطور خاص برای اراضی دیم و سیستمهای چرخهای (کاشت-داشت متوالی چندساله) قوی است؛ ICARDA نیز دورههای آموزشی APSIM برای محصولات دیم منطقه MENA برگزار میکند (icarda.org).

### ۱.۳ AquaCrop (FAO)

AquaCrop مدل بهرهوری آب محصول فائو است که «پاسخ عملکرد به آب» را با کمترین تعداد پارامتر شبیهسازی میکند (sciencedirect.com — Vanuytrecht 2014). هسته مفهومی مدل، معادله بنیادین زیر است (openknowledge.fao.org — سند رسمی فائو):

**B = WP* × ΣTr**

زیستتوده (B) متناسب با **مجموع تعرق تجمعی** (ΣTr) است؛ WP* پارامتر بهرهوری آب نرمالشده (kg زیستتوده بر مترمربع بر میلیمتر آب تعرقشده) است که برای ETo و CO2 نرمال میشود (openknowledge.fao.org/cb7392en و Reference Manual فائو). سپس عملکرد: **Y = HI × B**.

ویژگی متمایز AquaCrop: بهجای LAI از **درصد پوشش تاج (Canopy Cover, CC)** برای تفکیک تبخیر خاک از تعرق گیاه استفاده میکند (acsess.onlinelibrary.wiley.com — Steduto 2009). مراحل شبیهسازی: (۱) توسعه پوشش سبز تاج، (۲) تعرق گیاه، (۳) انباشت زیستتوده روی زمین، (۴) عملکرد نهایی (Vanuytrecht 2014). AquaCrop تعداد پارامتر نسبتاً کمی دارد و به همین دلیل برای کالیبراسیون سریع در مناطق کمداده محبوب است (researchgate — 265172756).

### ۱.۴ WOFOST

WOFOST (WOrld FOod STudies) مدلی دینامیک و **تبیینی (explanatory)** است که رشد محصول را با گام زمانی روزانه، بر پایه دانش فرآیندها در سطح پایینتر یکپارچگی (فتوسنتز برگ، تنفس، تخصیص) شبیهسازی میکند (wur.nl). این مدل که در دانشگاه واخنینگن توسعه یافته، بیلان آب را با مقایسه ورودی آب به ناحیه ریشه و خروجیها میسنجد (journals.uni-lj.si). نکته بسیار مهم برای پروژه ما: **پیادهسازی رسمی مدرن WOFOST با نام PCSE (Python Crop Simulation Environment) به زبان پایتون خالص نوشته شده** و مدلهای WOFOST، LINGRA و LINTUL3 را شامل میشود (pcse.readthedocs.io؛ github.com/ajwdewit/pcse). مقاله مروری ۲۵ سال WOFOST (de Wit 2019) نیز این پیادهسازی را مستند کرده است (sciencedirect.com — S0308521X17310107). این یعنی الگوی «بازنویسی پایتونی مدلهای علمی کلاسیک» یک مسیر اثباتشده و قابل استناد است.

### ۱.۵ EPIC

EPIC (Erosion-Productivity Impact Calculator) از ۱۹۸۱ برای تعیین رابطه بین فرسایش خاک و بهرهوری گیاه توسعه یافت (jstor.org — Williams 1990). این مدل فرسایش، رشد گیاه و فرآیندهای مرتبط را شبیهسازی و ارزیابی اقتصادی نیز انجام میدهد (ntrl.ntis.gov). اجزای فیزیکی آن شامل فرسایش، رشد گیاه، چرخه عناصر غذایی، بیلان آب و اثرات مدیریت زراعی بر کربن آلی خاک است (sciencedirect.com/topics؛ atlas.co). EPIC پایه مدلهای بعدی خانوادهای مانند APEX و SWAT شد.

**جمعبندی بخش ۱:** مدلهای محصول در یک طیف قرار میگیرند: از ساده/مهندسی (AquaCrop با معادله بهرهوری آب) تا پیچیده/فرآیندگرا (WOFOST، CERES، APSIM). همه حول دو معادله محوری میچرخند: **B = WP* × ΣTr (یا B = RUE × ΣPAR)** و **Y = HI × B**.

---

## ۲) مدلهای هیدرولوژی (Hydrology Models)

### ۲.۱ SWAT

SWAT (Soil & Water Assessment Tool) مدلی در مقیاس حوضه کوچک تا رودخانه است که کمیت و کیفیت آب سطحی و زیرزمینی را شبیهسازی میکند (swat.tamu.edu). این مدل، هیدرولوژی، رسوب، آلایندهها، رشد گیاه و شیوههای مدیریت را در حوضههای بزرگ و پیچیده کمّی میکند (sciencedirect.com — Aloui 2023؛ climatehubs.usda.gov). واحد محاسباتی پایه آن **HRU** (واحد پاسخ هیدرولوژیک = ترکیب کاربری اراضی/خاک/شیب) است. نسخه جدید **SWAT+** قابلیتهای تخصیص آب پیشرفته دارد (swat.tamu.edu/software/plus). برای رواناب از روش SCS-CN و برای روندیابی (routing) رودخانه از روش Muskingum استفاده میکند.

### ۲.۲ HEC-HMS

HEC-HMS محصول سپاه مهندسین ارتش آمریکا است و بهصورت مدولار از اجزای زیر ساخته میشود (اسناد رسمی hec.usace.army.mil):
- **Loss (تلفات/نفوذ):** SCS-CN، Green-Ampt، Deficit-Constant و… که بارش مازاد را محاسبه میکنند. سند رسمی، Green-Ampt را «سادهسازی معادله جامع ریچاردز برای جریان غیرماندگار آب در خاک» معرفی میکند (hec.usace.army.mil/hmsum — Selecting a Loss Method).
- **Transform (تبدیل بارش مازاد به هیدروگراف):** هیدروگراف واحد SCS (با PRF ≈ 484 برای هیدروگراف بدونبعد استاندارد)، Snyder، Clark و… (hec.usace.army.mil — SCS Unit Hydrograph Model).
- **Routing (روندیابی کانال):** Muskingum، موج سینماتیک و معادلات سنت-ونان (hec.usace.army.mil — Channel Flow).

### ۲.۳ MIKE SHE

MIKE SHE (شرکت DHI) یک سیستم شبیهسازی هیدرولوژیک **کاملاً یکپارچه و توزیعشده** است که کل چرخه آب خشکی را مدل میکند (dhigroup.com). مؤلفههای آن: جریان سطحی دوبعدی (موج انتشار/تفرقی)، ناحیه غیراشباع یکبعدی (معادله ریچاردز)، آب زیرزمینی سهبعدی (جریان اشباع)، جریان رودخانه یکبعدی (سنت-ونان) و تعرق گیاه. به همین دلیل MIKE SHE استاندارد طلایی «مدلهای فیزیکی-یکپارچه» است ولی هزینه محاسباتی و داده بالایی دارد (upcommons.upc.edu؛ researchgate — 265539232).

### ۲.۴ HBV

HBV یک مدل **مفهومی (lumped)** بارش-رواناب است که در SMHI سوئد توسعه یافته و از زیرروالهای: انباشت/ذوب برف (درجه-روز)، روال رطوبت خاک (با پارامتر ظرفیت میدانی Fc)، تابع پاسخ (مخازن ناحیه بالایی و پایینی با ضرایب پسروی K) و تبدیل هیدروگراف تشکیل میشود (medium.com/hydroinformatics). به دلیل سادگی و تعداد پارامتر کم، در مطالعات منطقهای و ارزیابی تغییر اقلیم بسیار پرکاربرد است (mdpi.com — El Garnaoui 2024).

### ۲.۵ معادلات کلیدی هیدرولوژی

**معادله ریچاردز (جریان در محیط متخلخل غیراشباع):** حرکت آب در خاک غیراشباع را توصیف میکند (en.wikipedia.org — Richards equation). فرم مخلوط یکبعدی عمودی:

**∂θ/∂t = ∂/∂z [ K(h) ( ∂h/∂z + 1 ) ]**

که θ رطوبت حجمی، h فشار مکش (head)، K(h) هدایت هیدرولیکی غیراشباع و z عمق است. روابط تکمیلی تجربی **van Genuchten-Mualem** منحنی نگهداشت آب θ(h) و K(θ) را با پارامترهای α، n، m = 1 − 1/n، θs (اشباع)، θr (باقیمانده) و Ks (هدایت اشباع) میدهند (researchgate — 382680080؛ ars.usda.gov — Jacques 2002). این معادله غیرخطی است و حل عددی آن به منحنی نگهداشت آب معتبر وابسته است (link.springer.com — Usman 2025).

**معادله Green-Ampt (نفوذ):** سادهسازی مهندسی معادله ریچاردز با فرض جبهه رطوبتی تیز (hec.usace.army.mil). نرخ نفوذ:

**f = Ks × ( 1 + (ψ × Δθ) / F )**

که f نرخ نفوذ، Ks هدایت اشباع، ψ مکش در جبهه خیس، Δθ = θs − θi اختلاف رطوبت و F نفوذ تجمعی است. فرم ضمنی تجمعی: F = Ks×t + ψ×Δθ×ln(1 + F/(ψ×Δθ)). (فرمول استاندارد؛ URL مستقیم برای معادله در جستجو یافت نشد.)

**روش SCS-CN (شماره منحنی):** بارش مازاد را تابعی از بارش تجمعی، نوع خاک، پوشش و کاربری اراضی برآورد میکند (hec.usace.army.mil — SCS Curve Number Loss Model). معادله اصلی (که در چند منبع یافتشده از جمله drainagecalculators.com و hec.usace.army.mil تأیید شده):

**Q = (P − 0.2S)² / (P + 0.8S)** ، برای P > 0.2S و در غیر این صورت Q = 0

که Q رواناب مستقیم، P بارش و S حداکثر نگهداشت بالقوه است؛ S معمولاً با رابطه S = (25400/CN) − 254 (میلیمتر) از شماره منحنی CN (بین ۰ تا ۱۰۰) بهدست میآید. نکته: اصلاح «لاندای ۰.۲S» در برخی مطالعات نقد شده (manula.com — Critical Review of SCS CN).

**معادلات سنت-ونان (جریان کانال باز یکبعدی):** استاندارد مدلسازی جریان با سطح آزاد در یک و دو بعد هستند (en.wikipedia.org — Shallow water equations؛ sciencedirect.com — Hager 2019). دو معادله:
- پیوستگی: **∂A/∂t + ∂Q/∂x = q** (A سطح مقطع، Q دبی، q جریان جانبی)
- مومنتوم: **∂Q/∂t + ∂(Q²/A)/∂x + g×A×∂h/∂x = g×A×(S0 − Sf)** (h عمق، S0 شیب بستر، Sf شیب اصطکاک؛ طبق سند HEC-HMS مجموع نیروی گرانش، فشار و اصطکاک با تغییر تکانه برابر است — hec.usace.army.mil — Channel Flow).

سادهسازیها: موج سینماتیک (S0 = Sf)، موج انتشار (حذف جمله اینرسی).

**هیدروگراف واحد (Unit Hydrograph):** واکنش خطی حوضه به یک واحد بارش مازاد؛ هیدروگراف خروجی از **کانولوشن** بهدست میآید:

**Q(t) = ∫ P(τ) × U(t − τ) dτ**

روش SCS با هیدروگراف واحد بدونبعد و ضریب PRF (نزدیک ۴۸۴ در حالت استاندارد؛ hec.usace.army.mil — SCS Unit Hydrograph Model) پرکاربردترین نسخه است.

**روش Rational (منطقی):** دبی اوج رواناب حوضههای کوچک: **Qp = C × i × A** که Qp دبی اوج، C ضریب رواناب (بین ۰ و ۱)، i شدت بارش و A مساحت حوضه است (در واحدهای SI: Qp [m³/s] = C × i [mm/hr] × A [km²] ÷ 3.6). این روش برای حوضههای کوچک شهری/کشاورزی طراحی شده است. (معادله استاندارد مهندسی؛ URL مستقیم در جستجوهای این تحقیق یافت نشد.)

---

## ۳) مدلهای خاک و کربن (Soil & Carbon Models)

### ۳.۱ HYDRUS-1D

HYDRUS-1D معادله ریچاردز را برای جریان اشباع-غیراشباع آب و معادلات انتقال-پخش (ادوکشن-دیسپرشن فیکینی) را برای گرما و املاح بهصورت عددی حل میکند (pc-progress.com؛ soil-modeling.org). کاربردهای اصلی: نفوذ، بازتوزیع رطوبت، تبخیر-تعرق، آبشویی املاح و کود، و تغذیه آب زیرزمینی. حل عددی آن با روش اجزای محدود (FEM) و تکرار پیکارد/نیوتن برای غیرخطیبودن انجام میشود (link.springer.com — Usman 2025). نکته جالب برای ما: اخیراً HYDRUS-1D با شبکههای عصبی فیزیک-آگاه (PINN) ترکیب شده تا معادله شدیداً غیرخطی ریچاردز را حل کنند (pmc.ncbi.nlm.nih.gov — Li 2025).

### ۳.۲ Century

مدل Century چرخه کربن، نیتروژن، فسفر و گوگرد خاک، تولید اولیه و بیلان آب را شبیهسازی میکند (matteroftrust.org). طبق سند فائو (fao.org/4/y5490e/y5490e08.htm)، Century سه نوع ماده آلی خاک با نرخهای تجزیه متفاوت میشناسد: **سریع (fast)، کند (slow) و مقاوم (resistant/passive)** بهعلاوه دو مخزن بقایا (structural و metabolic litter). تجزیه با سینتیک مرتبه اول و ضرایب تعدیل دما، رطوبت و بافت خاک انجام میشود. خروجی اصلی: پویایی کربن آلی خاک (SOC) در مقیاس دهه تا قرن.

### ۳.۳ RothC

RothC (Rothamsted Carbon model) کربن آلی خاک غیرغرقاب را با **پنج مخزن** مدل میکند: چهار مخزن فعال (DPM بقایای گیاهی تجزیهپذیر، RPM بقایای مقاوم، BIO زیستتوده میکروبی، HUM مواد هومیشده) که با نرخهای تعریفشده تجزیه میشوند، بهعلاوه مخزن بیاثر IOM (egusphere.copernicus.org — Contreras 2026). اثرات خاک، دما، رطوبت و پوشش گیاهی با ضرایب تعدیل اعمال میشود (soil-modeling.org). RothC و Century پرکاربردترین مدلهای SOC هستند (digitalcommons.unl.edu — Geremew 2024) و RothC به زبانهای R و Python پیادهسازی شده است — یعنی برای ادغام در HyDroMa گزینه سبک و اثباتشدهای است.

### ۳.۴ معادله فرسایش RUSLE/USLE

معادله جهانی تلفات خاک (USLE) و نسخه بازبینی RUSLE، میانگین تلفات سالانه خاک را با حاصلضرب پنج عامل برآورد میکنند (stormwateruniv.com؛ storymaps.arcgis.com؛ soilsa.com — Akpa 2024):

**A = R × K × LS × C × P**

- A: میانگین تلفات سالانه خاک (تن بر هکتار در سال)
- R: فرسایندگی باران (rainfall erosivity)
- K: فرسایشپذیری خاک (soil erodibility)
- LS: ترکیب طول شیب و درجه شیب (slope length & steepness)
- C: پوشش گیاهی و مدیریت (cover-management)
- P: عملیات حفاظتی (support practice)

این مدل توسط آژانسهای دولتی جهان برای ارزیابی و فهرستبرداری فرسایش و سیاستگذاری عمومی استفاده میشود (ars.usda.gov — RUSLE). مرور جامع (hess.copernicus.org — Benavidez 2018) روشهای محاسبه LS را بررسی کرده است. محدودیت شناختهشده: USLE/RUSLE برای فرسایش میانگین بلندمدت طراحی شده، نه رویدادهای تکی.

---

## ۴) روشهای عددی و پیادهسازی کدنویسی

### ۴.۱ تفاضل محدود و حجم محدود

- **تفاضل محدود (Finite Difference):** مشتقها با تفاضل روی گرههای شبکه تقریب زده میشوند (صریح: y_{n+1} = y_n + Δt×f؛ ضمنی: y_{n+1} = y_n + Δt×f(y_{n+1})). ساده است ولی پایستگی جرم را تضمین نمیکند مگر با فرمولبندی پایسته.
- **حجم محدود (Finite Volume):** معادلات دیفرانسیل روی سلولها انتگرالگیری میشوند و شار بین سلولها ردوبدل میشود؛ **پایستگی جرم بهصورت ساختاری تضمین میشود** — انتخاب استاندارد برای سنت-ونان، ریچاردز و انتقال املاح.

### ۴.۲ رانگ-کوتای مرتبه ۴ (RK4)

پرکاربردترین حلگر صریح ODE به دلیل تعادل دقت/هزینه (researchgate — Comparison of Runge-Kutta Methods؛ en.wikipedia.org — Runge–Kutta methods). برای dy/dt = f(t, y):

**k1 = f(t_n, y_n)**
**k2 = f(t_n + h/2, y_n + h×k1/2)**
**k3 = f(t_n + h/2, y_n + h×k2/2)**
**k4 = f(t_n + h, y_n + h×k3)**
**y_{n+1} = y_n + (h/6) × (k1 + 2×k2 + 2×k3 + k4)**

### ۴.۳ نیوتن-رافسون

برای ریشهیابی معادلات غیرخطی (که در حلگرهای ضمنی ریچاردز و بیلان آب ضروری است):

**x_{n+1} = x_n − f(x_n) / f'(x_n)**

با مشتق عددی یا تحلیلی. در معادلات خاک معمولاً با تکرار **پیکارد** (جایگزینی متوالی) ترکیب میشود: θ^{k+1} از روی K(θ^k) و h^k محاسبه و تا همگرایی تکرار میشود.

### ۴.۴ پایداری و عدد کورانت (CFL)

شرط کورانت-فردریش-لوی (CFL) شرط **لازم همگرایی** روشهای صریح برای معادلات بادپخشی/موجی است (en.wikipedia.org — CFL؛ simscale.com). عدد کورانت:

**C = u × Δt / Δx**

که u سرعت مشخصه، Δt گام زمانی و Δx گام مکانی است. برای روشهای صریح آپویند، C ≤ 1 لازم است؛ نقض CFL باعث ناپایداری عددی و نتایج غیرقابلاعتماد میشود (neuralconcept.com). در عمل برای معادلات غیرخطی (مانند ریچاردز) گام زمانی تطبیقی با کنترل CFL و خطای محلی لازم است.

### ۴.۵ حلگرهای ODE/PDE

- ODE: خانواده RK (از مرتبه ۱ تا ۵)، روشهای چندگامی (Adams-Bashforth/Moulton)، حلگرهای سخت (stiff) مانند LSODA و BDF که در scipy.integrate.solve_ivp موجودند.
- PDE: روش خطوط (Method of Lines) — گسستهسازی مکانی + حلگر ODE زمانی؛ گسستهسازی مکانی با FDM/FVM/FEM.
- راهبرد «گام زمانی تطبیقی + مشتقگیری خودکار برای ژاکوبین» برای حلگرهای ضمنی توصیه میشود.

### ۴.۶ وکتوریزهسازی با NumPy/Numba

- **NumPy:** عملیات آرایهای را به لایه C منتقل میکند؛ برای محاسبات برداری بلوکی (مثلاً تمام لایههای خاک در یک گام) مناسب است. نکته مهم تجربی: اگر کد کاملاً وکتوریزه NumPy باشد، Numba اغلب سرعت اضافه نمیدهد (github.com/UXARRAY discussion)؛ اما برای حلقههای ترتیبی/شرطی، **Numba با JIT** کد را به ماشین بهینه کامپایل میکند و میتواند شتاب چند دهبرابری بدهد (geeksforgeeks.org؛ python-programming.quantecon.org). الگوی عملی: حلقههای عددی داغ را با @njit، بقیه را NumPy.
- جایگزینهای مدرنتر: JAX (کامپایل JIT + autodiff + موازیسازی) که طبق مقایسه QuantEcon در عملیات وکتوریزه برنده است (python-programming.quantecon.org).

### ۴.۷ هسته C++ و اتصال pybind11

pybind11 یک کتابخانه **header-only سبک** است که تایپهای C++ را در Python و بالعکس در معرض قرار میدهد، عمدتاً برای ساخت binding از کد C++ موجود (github.com/pybind/pybind11). مزایا برای HyDroMa: (۱) هسته عددی C++20 مستقل و قابلتست، (۲) لایه Python بهعنوان چسب منطق کسبوکار، (۳) انتقال آرایهها با بافر پروتکل NumPy بدون کپی سنگین (پشتیبانی از buffer protocol)، (۴) GIL قابل آزادسازی برای اجرای موازی. برای حالت سختگیرتر (محاسبات سنگین)، رویکرد NumPy-سازی اولیه + Cython/Numba برای میانافزار و pybind11 برای ماژولهای C++20 اثباتشده است (medium.com — Python Cython–Numba Playbook).

### ۴.۸ الگوهای معماری ماژولار

- **Interface (واسط انتزاعی):** در پایتون با ABC/Protocol؛ در C++ با کلاسهای انتزاعی. مثال: واسط `SoilWaterModel` با متدهای `step(dt, forcing)` و `state()`.
- **Plugin/Registry:** ثبت پویای مدلها در دیکشنری (الگوی registry) تا افزودن مدل جدید بدون تغییر هسته ممکن شود — دقیقاً الگوی APSIM (بخش ۱.۲) و الگوی `registry.py` موجود در apps/simulation.
- **Service Layer:** لایه سرویس (مثل apps/simulation/service.py) بین API و مدلهای علمی؛ مسئول orchestration، تراکنش، اعتبارسنجی و لاگ.
- **مدیریت حالت و کش (State & Caching):** وضعیت مدل (رطوبت خاک، زیستتوده، مخازن کربن) باید از پارامترها جدا باشد؛ ذخیره checkpoint برای ادامهپذیری (resume) اجراهای طولانی؛ کش نتایج میانی (مثلاً ET0 روزانه) با LRU یا جدولهای محاسباتی؛ حشره رایج: حالت مشترک بین اجراها (stateful singleton) — باید با «یک مدل = یک نمونه state» مدیریت شود.

---

## ۵) کالیبراسیون و اعتبارسنجی مدلها

### ۵.۱ روشهای کالیبراسیون

- **GLUE (Generalized Likelihood Uncertainty Estimation):** روش مونتکارلویی که بسیاری از مجموعهپارامترها را نمونهگیری میکند، با یک تابع درستنمایی (مثل NSE) وزن میدهد و خروجیهایی را که با مشاهدات سازگار نیستند کنار میگذارد؛ بر پایه فرضیه **equifinality** (مجموعههای پارامتر متفاوت میتوانند به همان خوبی عمل کنند) (wires.onlinelibrary.wiley.com — Herrera 2022؛ encyclopedia.pub/entry/6206).
- **PEST (Parameter ESTimation):** نرمافزار اتوماسیون کالیبراسیون **بسیار-پارامتری** و تحلیل عدمقطعیت مقید به کالیبراسیون برای هر مدل عددی؛ مبتنی بر بهینهسازی گاوس-مارکوارت-لونبرگ با پشتیبانی از regularization (pesthomepage.org؛ sspa.com). مقایسه مستقیم GLUE و PEST روی دو مدل در elibrary.asabe.org موجود است.
- **روشهای بیزی:** بر اساس قاعده بیز: **posterior ∝ likelihood × prior**؛ با MCMC (مثلاً Metropolis-Hastings یا DREAM) توزیع پسین پارامترها نمونهگیری میشود. مزیت: عدمقطعیت پارامتر بهصورت توزیع کامل، نه یک تخمین نقطهای.

### ۵.۲ شاخصهای عملکرد (NSE/RMSE/R²/KGE/PBIAS)

- **NSE (Nash-Sutcliffe Efficiency):** NSE = 1 − Σ(O − S)² / Σ(O − Ō)² — مقدار ۱ ایدهآل، ۰ یعنی مدل بهاندازه میانگین مشاهدات خوب است، منفی یعنی بدتر از میانگین (hec.usace.army.mil — Calibration Summary Statistics؛ comptes-rendus.academie-sciences.fr).
- **RMSE:** ریشه میانگین مربعات خطا، هم-واحد با داده.
- **R²:** ضریب تعیین (مجذور همبستگی پیرسون) — فقط همبستگی خطی را نشان میدهد، نه بایاس یا دامنه.
- **KGE (Kling-Gupta Efficiency):** KGE = 1 − sqrt( (r−1)² + (α−1)² + (β−1)² ) که r همبستگی، α = σ_sim/σ_obs نسبت تغییرپذیری و β = μ_sim/μ_obs نسبت میانگین (نسبت بایاس) است (emergentmind.com). KGE بهعنوان اصلاح NSE توسعه یافت تا همبستگی، بایاس و تغییرپذیری را جداگانه بسنجد (ihedelftrepository...؛ sciencedirect.com — Williams 2025).
- **PBIAS (درصد بایاس):** PBIAS = 100 × Σ(S − O) / Σ(O) — مقدار مثبت یعنی بیشبرآورد و منفی یعنی کمبرآورد توسط مدل (hec.usace.army.mil).

### ۵.۳ آنالیز حساسیت

- **Morris (الگوریتم اثرات ابتدایی):** ارزان و مناسب غربالگری پارامترهای پرتعداد؛ اثر ابتدایی EE_i = [y(x + Δe_i) − y(x)]/Δ و شاخصهای میانگین μ و انحراف معیار σ (pmc.ncbi.nlm.nih.gov — PMC12504340).
- **Sobol (آنالیز مبتنی بر واریانس):** تجزیه واریانس خروجی به سهم پارامترهای منفرد (شاخص مرتبه اول S_i) و کل (شاخص کل S_Ti شامل برهمکنشها) (en.wikipedia.org — Variance-based sensitivity analysis؛ arxiv.org/html/2506.11471). دقیق ولی گران (هزاران اجرا).
- راهبرد ترکیبی استاندارد: Morris برای غربالگری → Sobol برای پارامترهای مهم → کالیبراسیون روی زیرمجموعه کاهشیافته.

### ۵.۴ عدمقطعیت (Monte Carlo)

نمونهگیری از توزیع پارامترها/ورودیها (اقلیم، خاک)، اجرای مدل N بار و استخراج کمیتهای (پیشبینینشده (quantiles)، فاصله اطمینان و باند عدمقطعیت. GLUE و PEST-UNCSAM و MCMC همگی در این چارچوب میگنجند.

### ۵.۵ دادهگسیخت (Data Assimilation, EnKF)

فیلتر کالمن تجمعی (Ensemble Kalman Filter) از ترکیب نظریه فیلتر کالمن و تخمین مونتکارلو ساخته شده و در دو گام حرکت میکند: **پیشبینی (forecast)** و **بهروزرسانی (analysis)** (journals.ametsoc.org — Reichle 2002؛ mdpi.com — Zhang 2022). معادله بهروزرسانی:

**x_a = x_f + K × (y − H×x_f)** ، با **K = P_f × Hᵀ × (H×P_f×Hᵀ + R)⁻¹**

که x_f حالت پیشبینیشده، x_a حالت تحلیلشده، y مشاهده، H عملگر مشاهده، P_f کوواریانس خطای پیشبینی (تخمینزدهشده از پراکندگی ensemble) و R کوواریانس خطای مشاهده است. EnKF در هیدرولوژی برای جذب رطوبت خاک و پیشبینی سیلاب بسیار استفاده شده (sciencedirect.com — Clark 2008؛ agupubs.onlinelibrary.wiley.com — Piazzi 2021). نکته پیادهسازی: کد جذب داده با Numba/C++ شتاب میگیرد چون به ازای هر ensemble member یک اجرای مدل لازم است.

---

## ۶) معماری سرویس-محور

### ۶.۱ REST/OpenAPI

بکاند FastAPI بهصورت پیشفرض OpenAPI تولید میکند: تعریف صریح endpoints، schema با Pydantic، مستندات تعاملی Swagger/ReDoc، و اعتبارسنجی ورودی/خروجی. برای موتور شبیهسازی، الگوی پیشنهادی:
- `POST /runs` → ایجاد اجرای شبیهسازی (پارامترها، دوره، سناریو)
- `GET /runs/{id}` → وضعیت و نتایج
- `POST /runs/{id}/resume` → ادامه اجرای ناتمام
- `GET /models` → فهرست مدلهای ثبتشده در registry

### ۶.۲ قراردادهای داده (Data Contracts)

- اسکیمای نسخهدار برای هر مدل (ورودی، پارامتر، خروجی، حالت) با Pydantic/JSON Schema.
- تفکیک «پارامتر مدل» (ثابت کالیبراسیون) از «وضعیت مدل» (متغیرهای دینامیک) از «ورودی رانشی (forcing)» (اقلیم روزانه).
- قرارداد خروجی سری زمانی با واحد صریح (مثلاً mm/day، kg/ha) — واحدها از منابع رایج خطا هستند.

### ۶.۳ اصول FAIR

FAIR چهار اصل بنیادین برای دادههای علمی است: **Findable (یافتپذیر)** با شناساگر پایدار و متادیتای غنی، **Accessible (دسترسپذیر)** با پروتکلهای باز، **Interoperable (همکنشپذیر)** با واژگان/فرمتهای استاندارد، و **Reusable (قابل استفاده مجدد)** با مجوز و provenance شفاف (nature.com — Wilkinson 2016؛ go-fair.org). برای HyDroMa: متادیتای FAIR برای دیتاستهای اقلیمی/خاک، شناسه DOI یا UUID پایدار برای هر run، و مستندسازی provenance (کدام مدل، کدام پارامتر، کدام داده) الزامی است.

### ۶.۴ مقیاسپذیری

- اجرای سنگین شبیهسازی در **worker** جدا (Celery/ARQ یا صف داخلی) با ذخیره نتایج در دیتابیس/object store؛ API فقط شروع و نظارت را انجام دهد.
- **کش (cache)** برای ورودیهای تکراری: ET0 محاسبهشده، منحنیهای نگهداشت آب خاک، DEM-derived metrics.
- **موازیسازی:** اجرای ensembleها (Monte Carlo، EnKF، کالیبراسیون) ذاتاً موازی است — با فرایند/صف، نه ترد.
- پایگاه داده سری زمانی برای خروجیهای مدل (TimescaleDB/ClickHouse) بهجای ذخیره JSON بزرگ.

### ۶.۵ طراحی آفلاین-فیرست برای کاربران روستایی

الگوی آفلاین-فیرست یعنی برنامه طوری طراحی شود که **حالت پیشفرض آن بدون اینترنت کار کند**؛ داده ابتدا محلی ذخیره و هنگام اتصال همگام میشود (brainstacktechnologies.com؛ think-it.io). راهنمای رسمی اندروید این الگو را با لایه داده محلی (Room/SQLite) + همگامسازی (WorkManager) توصیه میکند (developer.android.com — offline-first). پیامدها برای HyDroMa: (۱) نسخه سبک موتور برای اجرای محلی روی گوشی (کاهش شدت محاسبات یا دانلود پیشبینیهای روزانه بهجای محاسبه آنی)، (۲) صف عملیات محلی (ثبت برداشت، عکس زمین) که بعداً sync شود، (۳) پیامک/SMS یا USSD بهعنوان کانال جایگزین برای مناطق بدون دیتا (مفهوم ذکرشده در think-it.io درباره «گوش دادن به وضعیت اتصال کشاورز»)، (۴) پیلود سبک (فشردهسازی، فقط متادیتا در حالت آفلاین).

---

## ۷) پیادهسازی در HyDroMa

بر اساس ساختار فعلی ریپو (apps/simulation با زیرپوشههای agriculture/apsim، agriculture/_dssat_pkg_backup، hydrology، crops، soil، carbon_cycle/co2fix، carbon_cycle/_rothc_pkg_backup و apps/data_assimilation)، پیشنهادهای زیر برای افزودن دانش این گزارش به ماژول موتور علمی ارائه میشود:

### ۷.۱ هسته عددی `engine/hydroma` (C++20 + pybind11)

- ایجاد پوشه `engine/hydroma/` شامل: `core/` (ساختارهای آرایهای، تایپهای واحددار)، `solvers/` (RK4، backward-Euler/Newton-Raphson، روش خطوط)، `models/` (پیادهسازی C++ برای حلقههای داغ: ریچاردز ۱بعدی، سینتیک مخازن RothC، هیدروگراف واحد)، `bindings/` (ماژولهای pybind11 با buffer protocol برای NumPy).
- لایه Python (`apps/simulation/`) فقط orchestration میکند: registry، اعتبارسنجی Pydantic، توزیع کار، ذخیره نتایج. این جداسازی دقیقاً الگوی APSIM (ماژولهای مشترک خاک/آب) و PCSE (بازنویسی پایتونی + هسته محاسباتی) را دنبال میکند.
- برای اجرای موازی ensemble (کالیبراسیون، EnKF): آزادسازی GIL در bindingها (`py::call_guard<py::gil_scoped_release>`).

### ۷.۲ واسطهای مدل (Interfaces) و Registry

- تعریف ABCها در `apps/simulation/base.py` (که وجود دارد) و توسعه: `CropModel`، `HydrologyModel`، `SoilCarbonModel`، `ErosionModel` با متدهای `setup(config)`، `step(forcing, dt)`، `get_state()/set_state()`، `get_outputs()`.
- تقویت `registry.py` برای ثبت پویا: `registry.register("aquacrop", AquaCropModel)` — افزودن مدل جدید بدون تغییر routerها.
- **تطبیق مدلها:** از آنجا که AquaCrop و RothC و SWAT در ریپو وجود دارند، پیشنهاد میشود لایه adapter بنویسیم که خروجی این مدلها را به قرارداد یکسان (dict سری زمانی با واحد صریح) تبدیل کند.

### ۷.۳ ماژولهای جدید پیشنهادی بر اساس این تحقیق

- `apps/simulation/crops/wofost.py`: پیادهسازی/کپسولهسازی WOFOST با مرجع PCSE (منبع: pcse.readthedocs.io) — سبکترین راه، اتصال به PCSE بهجای بازنویسی.
- `apps/simulation/agriculture/apsim/` (موجود): اتصال به APSIM Next Gen از طریق رابط آن؛ استفاده از الگوی ماژولهای مشترک آب/نیتروژن بهعنوان مرجع معماری.
- `apps/simulation/hydrology/` (موجود): افزودن حلگرهای SCS-CN، Green-Ampt، هیدروگراف واحد SCS و موج سینماتیک در `engine/hydroma/solvers`؛ مدل HBV بهعنوان مدل مفهومی مرجع برای مناطق کمداده.
- `apps/simulation/soil/`: حلگر ریچاردز ۱بعدی با روابط van Genuchten-Mualem (پارامترهای θs, θr, α, n, Ks) با روش حجم محدود ضمنی + نیوتن/پیکارد.
- `apps/simulation/carbon_cycle/`: تکمیل RothC (موجود: rothc_model.py) با ماژول C++ برای سینتیک مخازن؛ افزودن Century در صورت نیاز MRV کربن بلندمدت.
- `apps/simulation/erosion.py` (جدید): RUSLE با فرمول A = R × K × LS × C × P و محاسبه LS از DEM (مرجع: hess.copernicus.org — Benavidez 2018).
- `apps/data_assimilation/` (موجود): پیادهسازی EnKF با فرمول x_a = x_f + K(y − Hx_f)؛ نیازمند قابلیت «بازنویسی حالت» در همه مدلها (set_state) و رابط مشاهده H.

### ۷.۴ مدیریت حالت و کش

- یک کلاس `SimulationState` با checkpoint (ذخیره/بازیابی وضعیت mid-run) برای قابلیت resume؛ اتصال به `run_store.py`/`models_runs.py` موجود.
- کش دو سطحی: (۱) کش نتایج میانی پایدار (ET0، NDVI-derived canopy) در Redis/دیتابیس، (۲) کش درون-فرایندی LRU برای منحنیهای خاک.
- **قانون طلایی:** پارامتر، حالت و forcing هرگز در یک ساختار داده قاطی نشوند (منبع خطای کالیبراسیون و resume).

### ۷.۵ کالیبراسیون و اعتبارسنجی

- افزودن پکیج `apps/simulation/calibration/`: پشتیبانی از GLUE (نمونهگیری مونتکارلو + آستانه درستنمایی) و واسط PEST (با ورودی/خروجی فایل تبادل) و MCMC سبک.
- تکمیل `evaluation_metrics.py` موجود با NSE، KGE، RMSE، R²، PBIAS (فرمولهای بخش ۵.۲) و گزارش خودکار.
- آنالیز حساسیت با Morris (غربالگری) سپس Sobol روی پارامترهای کلیدی هر مدل؛ در عمل با اجرای موازی ensemble در worker.
- **اعتبارسنجی دوگانه:** split دوره (کالیبراسیون/اعتبارسنجی زمانی) + split ایستگاهی (اعتبارسنجی مکانی) برای گزارشهای FAIR.

### ۷.۶ سرویس و API

- روتهای جدید: `POST /calibrations` (اجرای کالیبراسیون)، `GET /runs/{id}/state` (بازیابی checkpoint)، `POST /assimilate` (جذب داده EnKF).
- قراردادهای Pydantic نسخهدار (`schemas.py` موجود را توسعه دهید) با واحدهای صریح.
- متادیتای FAIR برای هر run: شناسه پایدار، provenance (مدل، نسخه، پارامترها، دادههای ورودی)، مجوز و قابلیت export به فرمت استاندارد (NetCDF/CSV).

### ۷.۷ آفلاین-فیرست

- تولید باندل «پیشبینی روزانه» قابل دانلود برای مناطق روستایی: خروجی مدلها بهصورت فایل سبک (JSON/Parquet فشرده) + اجرای محلی مدلهای مفهومی سبک (HBV/AquaCrop سادهشده) روی دستگاه کاربر؛ همگامسازی دوطرفه هنگام اتصال (الگوی android offline-first). این باندل میتواند جایگزین کانال پیامکی برای مناطق بدون اینترنت باشد.

### ۷.۸ نقشه راه پیشنهادی

1. **فاز ۱ (زیرساخت):** واسطهای مدل + registry + SimulationState/checkpoint + لایه کش.
2. **فاز ۲ (هسته C++):** solvers پایه (RK4، نیوتن، FVM ریچاردز ۱بعدی، SCS-CN/Green-Ampt، UH) با pybind11 و تست تطبیق عددی با مراجع.
3. **فاز ۳ (مدلها):** اتصال AquaCrop/RothC/SWAT موجود به قرارداد جدید + افزودن WOFOST (از طریق PCSE) و HBV و RUSLE.
4. **فاز ۴ (کالیبراسیون/DA):** GLUE + PEST-interface + Morris/Sobol + EnKF روی وضعیت مدلها.
5. **فاز ۵ (سرویس/آفلاین):** روتهای جدید OpenAPI + متادیتای FAIR + باندل آفلاین.

---

## ۸) فهرست منابع (فقط URLهای یافتشده در web_search)

**مدلهای محصول:**
- https://dssat.net/ | https://dssat.net/about/ | https://dssat.net/csm-ceres-rice/
- https://www.quantitative-plant.org/model/CERES
- https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2017.01118/full
- https://github.com/DSSAT/dssat-csm-os
- https://www.sciencedirect.com/science/article/abs/pii/S1161030102001077
- https://www.apsim.info/ | https://www.apsim.info/apsim-model/
- https://www.csiro.au/en/about/corporate-governance/ensuring-our-impact/impact-case-studies/future-industries/agricultural-productions-systems-simulator
- https://www.sciencedirect.com/science/article/pii/0308521X9400055V
- https://icarda.org/media/events/agricultural-production-systems-simulator-apsim-training-mena-researchers
- https://openknowledge.fao.org/3/cb7392en/cb7392en.pdf
- https://openknowledge.fao.org/server/api/core/bitstreams/23621a46-1512-41a7-ad28-5a3d8141b6dc/content
- https://acsess.onlinelibrary.wiley.com/doi/10.2134/agronj2008.0139s
- https://www.sciencedirect.com/science/article/abs/pii/S136481521400228X
- https://www.sciencedirect.com/science/article/pii/S0378377422000385
- https://www.mdpi.com/2073-4441/14/23/3933
- https://www.wur.nl/en/research/products-services/wofost-world-food-studies
- https://pcse.readthedocs.io/ | https://github.com/ajwdewit/pcse
- https://www.sciencedirect.com/science/article/pii/S0308521X17310107
- https://www.mdpi.com/2071-1050/11/5/1466
- https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/erosion-productivity-impact-calculator
- https://www.jstor.org/stable/76847
- https://atlas.co/gis-use-cases/erosion-productivity-impact-calculator-epic/
- https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/PB91136127.xhtml

**هیدرولوژی:**
- https://swat.tamu.edu/ | https://swat.tamu.edu/software/plus/
- https://www.climatehubs.usda.gov/hubs/international/tools/soil-and-water-assessment-tool
- https://www.sciencedirect.com/science/article/pii/S0301479722023726
- https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/transform/scs-unit-hydrograph-model
- https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/canopy-surface-infiltration-and-runoff-volume/infiltration/scs-curve-number-loss-model
- https://www.hec.usace.army.mil/confluence/hmsdocs/hmsum/4.7/subbasin-elements/selecting-a-loss-method
- https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/channel-flow/channel-flow-basic-concepts-equations-and-solution-techniques
- https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/calibration/calibration-summary-statistics
- https://www.dhigroup.com/technologies/mikepoweredbydhi/mike-she
- https://medium.com/hydroinformatics/hbv-lumped-conceptual-hydrological-model-b0a75b4e61d0
- https://www.mdpi.com/2072-4292/16/20/3756
- https://en.wikipedia.org/wiki/Richards_equation
- https://en.wikipedia.org/wiki/Shallow_water_equations
- https://ascelibrary.org/doi/abs/10.1061/(ASCE)HE.1943-5584.0001838
- https://drainagecalculators.com/reference/curve-numbers/
- https://www.fest.polimi.it/reference/infiltration.html
- https://www.ars.usda.gov/ARSUserFiles/3013/King8.pdf

**خاک و کربن:**
- https://soil-modeling.org/resources-links/model-portal/hydrus-1d
- https://www.pc-progress.com/en/Default.aspx?H1D-description
- https://link.springer.com/article/10.1007/s40808-025-02472-2
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12120032/
- https://www.fao.org/4/y5490e/y5490e08.htm
- https://soil-modeling.org/resources-links/model-portal/rothc
- https://egusphere.copernicus.org/preprints/2026/egusphere-2026-944/egusphere-2026-944.pdf
- https://www.ars.usda.gov/southeast-area/oxford-ms/national-sedimentation-laboratory/watershed-physical-processes-research/docs/revised-universal-soil-loss-equation-rusle-welcome-to-rusle-1-and-rusle-2/
- https://hess.copernicus.org/articles/22/6059/2018/hess-22-6059-2018.pdf
- https://stormwateruniv.com/courses/introduction-to-the-revised-universal-soil-loss-equation/

**روشهای عددی:**
- https://en.wikipedia.org/wiki/Courant–Friedrichs–Lewy_condition
- https://www.simscale.com/blog/cfl-condition/
- https://en.wikipedia.org/wiki/Runge–Kutta_methods
- https://github.com/pybind/pybind11
- https://python-programming.quantecon.org/numpy_vs_numba_vs_jax.html
- https://www.geeksforgeeks.org/data-analysis/unlocking-performance-understanding-numbas-speed-advantages-over-numpy/

**کالیبراسیون/اعتبارسنجی:**
- https://wires.onlinelibrary.wiley.com/doi/10.1002/wat2.1569
- https://pesthomepage.org/ | https://sspa.com/pest/
- https://encyclopedia.pub/entry/6206
- https://elibrary.asabe.org/abstract.asp?aid=35804
- https://comptes-rendus.academie-sciences.fr/geoscience/articles/10.5802/crgeos.189/
- https://www.sciencedirect.com/science/article/abs/pii/S1364815225003494
- https://www.emergentmind.com/topics/kling-gupta-efficiency-kge
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12504340/
- https://en.wikipedia.org/wiki/Variance-based_sensitivity_analysis
- https://arxiv.org/html/2506.11471
- https://journals.ametsoc.org/view/journals/mwre/130/1/1520-0493_2002_130_0103_hdawte_2.0.co_2.xml
- https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2020WR028390
- https://www.sciencedirect.com/science/article/abs/pii/S0309170808001012
- https://www.mdpi.com/2073-4441/14/10/1555

**معماری/FAIR/آفلاین:**
- https://www.go-fair.org/fair-principles/
- https://www.nature.com/articles/sdata201618
- https://developer.android.com/topic/architecture/data-layer/offline-first
- https://think-it.io/insights/offline-apps
- https://www.brainstacktechnologies.com/offline-first-apps

---

*اعداد/مقادیر مشخص (مانند WP* نرمالشده برای محصولات خاص، ضرایب CN دقیق هر خاک، آستانههای عددی NSE/KGE برای قضاوت عملکرد) در این تحقیق یافت نشد و عمداً ذکر نشدهاند؛ برای مقادیر کمی باید به داکیومنت رسمی هر مدل مراجعه شود.*
