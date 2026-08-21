# گزارش تحقیق: موضوعات فنی گامهای طرح «هیدروما نوژین»

**پروژه:** هیدروما نوژین / اکو نوژین — کشت و صنعت دشت امید نارون (مرکز رشد پارک علم و فناوری کهگیلویه و بویراحمد)
**مبنای تحقیق:** سند طرح توجیهی فنی-کسبوکار (۲۰۵ صفحه، ۲۱ بخش)
**دامنه:** تحقیق وب روی موضوعات علمی-فنی گامهای کلیدی سند و اعتبارسنجی آنها با منابع معتبر
**تاریخ:** مرداد ۱۴۰۵ (آگوست ۲۰۲۶)

---

## مقدمه و روش

سند هیدروما نوژین، یک طرح احیای منظر در مقیاس ملی با ۲۱ بسته فنی-مهندسی (HP) و زنجیره شبیهسازی ششمدلی است. در این گزارش، گامهای فنی سند به شش گروه موضوعی دستهبندی شده و هر موضوع با منابع علمی جستجوشده در وب اعتبارسنجی و تکمیل میشود:

1. **گام ۱:** بستههای فنی HP (آب، خاک، میکروبیوم، پوشش گیاهی، پایش) — بخش ۳ و ۶ سند
2. **گام ۲:** زنجیره شبیهسازی یکپارچه (SWAT+, RUSLE, RothC, AquaCrop, WEAP, HEC-RAS) — بخش ۱۴
3. **گام ۳:** سیستم تریگر خشکسالی و اقدام پیشدستانه (SPI-3, VHI, CHIRPS) — بخش ۱۲
4. **گام ۴:** تحقیق و توسعه و اختراعات (پوسته زیستی، کانال مارپیچ، کنسرسیوم میکروبی) — بخش ۱۱
5. **گام ۵:** پلتفرم اکو نوژین (MRV، مدارس مزرعهای، KoboToolbox) — بخش ۱۵ و ۲۰
6. **گام ۶:** بازار و اعتبارسنجی اقتصادی (رقبا GGW/JILMI/LDN، بازار کربن، کتیرا، بیمه شاخصمحور) — بخش ۵، ۱۸، ۱۹

---

## گام ۱: بستههای فنی-مهندسی (HP) و اعتبارسنجی علمی

### ۱-۱. حلقههای سنگی نیمههلالی و هلالیهای آبگیر برفی (HP-WH-01 و HP-WH-05)

این سازهها نوعی **میکروکچمنت (Microcatchment)** هستند که در سند قبلی پژوهش این پروژه (research-c) نیز از دیدگاه مهندسی آبخیز بررسی شدند: حوضچههای هلالی/لوزی کوچک که رواناب سطح کوچک (۱۰ تا ۱۰۰ مترمربع) را به نقطه کاشت متمرکز میکنند. UNCCD این سازهها را «سازههایی برای به دام انداختن رواناب محلی» تعریف میکند (UNCCD Toolbox). نسخه «برفی» (هلالی آبگیر برفی) برای مناطق سرد با هدف مدیریت ذوب برف و تقویت جریان پایه، نوآوری بومی سند است؛ در منابع بینالمللی، آبگیری برف (snow harvesting) با بانکتهای کمعمق در دامنههای بادگیر انجام میشود و نیاز به تحقیق میدانی بیشتر در اقلیم زاگرس شمالی دارد — این موضوع در ادبیات جستجوشده بهطور مستقیم پوشش داده نشد و نقطه ضعف مستندسازی سند است.

### ۱-۲. کانالهای مارپیچ ارشمیدس (HP-WH-02)

سند این سازه را «کانال غیرخطی با هندسه مارپیچ (r=a+bθ) و لایهبندی بیوچار برای استهلاک انرژی سیلاب و تغذیه آبخوان» معرفی میکند (بخش ۱۱-۲). این ایده با ادبیات علمی **Vortex Drop Shaft (شفت ریزش گردابی)** همخوانی دارد:
- شفتهای ریزش گردابی برای استهلاک انرژی جریان در انتقال آب از ارتفاع بالا به پایین بهکار میروند و نسبت به شفتهای قائم ساده، انرژی بیشتری مستهلک و الگوی جریان پایدارتری حفظ میکنند (Mahmoudi-Rad et al., 2023, PMC).
- چهار نوع ورودی شناختهشده دارد: دایرهای، اسکرول، مارپیچ و مماسی (ResearchGate).
- بهطور خاص، **ورودی مارپیچ ارشمیدسی (Archimedean spiral inlet)** بهعنوان طرح جدید ورودی شفت گردابی آزمایش شده است (Scilit) و در سرریزهای شفت گردابی (VDS Spillway) انتقال سیلاب و استهلاک انرژی به داخل تونل منتقل میشود و از مهپاشی خروجی جلوگیری میکند (Yang et al., MDPI Water 2021).
- نکته مهم برای سند: ادبیات موجود بر شفتهای قائم (رابط آب بالا و پایین) متمرکز است، در حالی که «کانال مارپیچ افقی/کمعمق» در دامنه با لایه بیوچار، ترکیب نوینی است که شبیهسازی HEC-RAS (که سند ادعا کرده TRL 4) باید با مدل فیزیکی و آزمایشگاه هیدرولیک اعتبارسنجی شود.

### ۱-۳. چاله نفوذی و چاهک تزریق عمیق (HP-WH-03)

چالههای نفوذ (قطر ۲ متر، عمق ۱٫۵ متر در پیچ کانالها) و چاهک تزریق (قطر ۱٫۵ متر، عمق ۲–۴ متر با لوله سوراخدار و پرکننده قلوهسنگ و بیوچار) با ادبیات تغذیه مصنوعی آبخوان (Artificial Recharge) هماهنگ است: روشهای تغذیه شامل حوضچه نفوذ، کانال نفوذ و تزریق چاهی است و چالش اصلی، گرفتگی (Clogging) است که NGWA بر آن تأکید دارد (NGWA). لایهبندی با بیوچار بهعنوان فیلتر و زیستگاه میکروبی، افزوده نوآورانه سند است که با یافتههای بیوچار (بند ۱-۴) سازگار است. توصیه فنی: برای چاهکهای عمیقتر، پیشتصفیه و کنترل کیفیت آب تزریقی (رسوب، شوری) الزامی است تا از گرفتگی سریع جلوگیری شود.

### ۱-۴. بیوچار فعالشده (HP-SL-01) — پایه علمی قوی

ادبیات جستجوشده بهشدت از ادعای سند حمایت میکند:
- بیوچار بهخاطر کربن آروماتیک بالا در برابر تجزیه میکروبی مقاوم است و **۶۰ تا ۸۰ درصد کربن زیستتوده اولیه** را تثبیت میکند (Waheed et al., Springer Biochar 2026).
- در مرورها، بیوچار **نگهداشت آب خاک را ۱۵ تا ۳۵ درصد** بهبود میدهد و **زیستتوده میکروبی را تا ۵۰ درصد** افزایش میدهد (EurekAlert/مرور Biochar 2026)؛ در برخی سامانهها افزایش نگهداشت آب تا ۴۰ درصد و زیستتوده چمن تا ۵۰ درصد و کاهش فرسایش بادی تا ۳۰ درصد گزارش شده (Biochar Today).
- در خاک شنی، بیوچار با افزایش نگهداشت رطوبت، آبشویی کود را کاهش و بهرهوری محصول را بالا میبرد (Li et al., USDA FS 2021) و در سیستم دیم، رطوبت نگهداشتی را افزایش و تبخیر تجمعی را کاهش میدهد (Thao et al., Vadose Zone J. 2023).
- **توصیه برای سند:** افزودن دو مخزن مجزا برای بیوچار (ناپایدار و پایدار) در RothC — که سند در بخش ۱۴ اعلام کرده — دقیقاً مطابق رویکرد علمی است و باید با مقادیر میدانی واسنجی شود.

### ۱-۵. پوسته زیستی سیانوباکتری (HP-SL-03) — نوآوری با پشتوانه علمی

ادبیات بهطور مستقل از سند، پتانسیل این فناوری را تأیید میکند:
- تلقیح سیانوباکتر روشی «از پایین به بالا» (bottom-up) برای احیای بومشناختی خاکهای بیابانی و توسعه پوسته زیستی مصنوعی (ABSC) است (Xie et al., 2024, ScienceDirect).
- تلقیح سیانوباکتر در مقیاس میدانی در چین، توالی جوامع گیاهی را تسریع کرده و روند بیابانزایی را معکوس کرده است (Lan et al., 2014, ACS — 219 استناد؛ Ayuso et al., 2017, PMC).
- تلقیح همزمان قارچ و سیانوباکتر بیابانی، تشکیل پوسته زیستی و حاصلخیزی خاک را بهبود میدهد (Zhou et al., Frontiers in Microbiology 2024).
- پوستههای زیستی (Biocrusts) در ۱ تا ۲ سانتیمتر بالایی خاک، ذرات را میبندند و فرسایش بادی و انتشار گردوغبار (PM10) را مهار میکنند (Fick et al., USDA ARS 2020).
- **ملاحظه برای سند:** تولید انبوه تلقیح در «مهدکودک میکروبی» (Microbial Nursery) امکانپذیر و استاندارد است (Ayuso et al., PMC 2017)؛ اما بقای بلندمدت در اقلیمهای مختلف (شوری، چرا، آتش) نیازمند آزمون پایلوت ۱۰۰ هکتاری است که سند نیز به TRL 5 و نیاز به تست میدانی اشاره کرده — این ارزیابی سند دقیق است.

### ۱-۶. کنسرسیوم میکروبی AMF + PGPR + سیانوباکتر (HP-BT-01)

سند ادعای «افزایش بهرهوری آب (WUE) تا ۳۰٪ و حذف کود شیمیایی» دارد. شواهد:
- تلقیح دوگانه PGPR–AMF در ذرت تحت تنش شدید آبی، **رطوبت نسبی برگ را ۱۰٫۷٪ و عملکرد را ۱۹٫۵٪** نسبت به شاهد افزایش داد (Chenche-López et al., Frontiers 2026).
- تلقیح دوگانه در مقایسه با AMF تنها، در خشکی شدید کارآمدتر است (Silva et al., 2023, ScienceDirect).
- PGPR با افزایش تولید ABA در تنش خشکی، کاهش اتلاف آب را القا میکند (Savastano et al., MDPI 2024) و ریزوباکترها کارایی مصرف عناصر و کاهش اثر تنش آبی را بهبود میدهند (Pereira et al., PMC 2020).
- **توصیه:** ادعای «۳۰٪ WUE و حذف کامل کود شیمیایی» خوشبینانه است؛ در ادبیات، حذف کامل کود در شرایط مزرعهای واقعبینانه نیست و بهتر است به «کاهش ۳۰–۵۰٪ کود» تعدیل شود. ادعاهای کمی باید با کرتهای شاهد در پایلوت اثبات شوند (خود سند نیز آزمون کرت کوچک TRL 6 را ذکر کرده).

### ۱-۷. آگروفارستری چندلایه و بادشکن زنده (HP-VG-01/02)

این بستهها با اصول کشاورزی حفاظتی و آگروفارستری (که در گزارش research-c بررسی شد: کاهش تلفات خاک تا ۸۶٪ در کشت مستقیم، Cornell/EESI/Jacobs 2022) همسو هستند. بادشکن زنده برای کنترل فرسایش بادی در اقلیم خشک جنوب (پکیج AR-1) ضروری است و با کاهش تبخیر سطحی، ریزاقلیم را بهبود میدهد.

---

## گام ۲: زنجیره شبیهسازی یکپارچه (بخش ۱۴) — اعتبارسنجی مدلها

### ۲-۱. SWAT+ و کالیبراسیون در حوضههای بدون ایستگاه

رویکرد سند — کالیبراسیون SWAT+ با الگوریتم SUFI-2 در SWAT-CUP و استفاده از تبخیر-تعرق ماهوارهای (MOD16A2) و رطوبت خاک (ESA CCI) بهجای دبی اندازهگیریشده — دقیقاً مطابق روند روز دنیاست:
- کالیبراسیون چندمتغیره SWAT با تبخیر-تعرق سنجشازدوری، قابلیت پیشبینی مدل را در حوضههای فاقد ایستگاه بهبود میدهد (Dangol et al., MDPI Remote Sensing 2023).
- کالیبراسیون SWAT با ۱۲ ماه داده ETa ماهوارهای در حوضههای بدون ایستگاه موفق بوده (Bennour et al., TU Delft 2022) و استفاده از ET سنجشازدوری برای واسنجی و اعتبارسنجی در حوضههای کممنبع اثبات شده (Odusanya et al., HESS 2019).
- استفاده از SUFI-2 برای کالیبراسیون چندمتغیره (دبی + ET) رایج و توصیهشده است (Koltsida et al., FAO AGRIS 2022؛ Parajuli et al., USDA FS 2018).
- **شاخص NSE هدف ۰٫۷۵** که سند تعیین کرده، مطابق معیارهای پذیرش کیفیت مدلهای هیدرولوژیک است (NSE>0.7 خوب ارزیابی میشود).
- دادههای پایه (ERA5-Land 9×9km، ALOS PALSAR/SRTM 12.5/30m، SoilGrids 250m، Sentinel-2 10m) انتخابهای درستی هستند و با روشهای استاندارد (Random Forest برای طبقهبندی کاربری) هماهغنگاند.

### ۲-۲. RUSLE و فاکتور C از NDVI

سند فاکتور C را ماهانه و با رگرسیون از NDVI محاسبه میکند — این رویکرد استاندارد است:
- دو روش شناختهشده (CrA و CVK) برای برآورد C-factor از NDVI مقایسه و اعتبارسنجی شدهاند (Almagro et al., 2019, ScienceDirect — 210 استناد).
- مقادیر C مبتنی بر NDVI به فرسایشپذیری خاک و شکل شیب حساساند (Ayalew et al., MDPI 2020) — یعنی همان ترکیب با دادههای SoilGrids که سند انجام میدهد درست است.
- RUSLE پرکاربردترین مدل تجربی برآورد فرسایش سالانه است (IWA Publishing 2024؛ Pal et al., 2025).

### ۲-۳. RothC و مخازن بیوچار

سند با «افزودن دو مخزن مجزا برای بیوچار (ناپایدار و پایدار)» مدل RothC را بومیسازی میکند. این اقدام علمی است: بیوچار به دلیل پایداری بالا (۶۰–۸۰٪ تثبیت کربن) در مدلهای کربن خاک بهعنوان پول مجزا مدلسازی میشود (Waheed et al., 2026). در گزارشهای بینالمللی، بیوچار «مسیر اقلیم-هوشمند احیای خاکهای خشک» نامیده شده است (Springer Biochar 2026). پیشنهاد: خروجی RothC (مثلاً ۲۰ ساله) باید با اندازهگیری میدانی SOC (نمونهبرداری ۰–۳۰ سانتیمتر) در سالهای ۱، ۳ و ۵ اعتبارسنجی شود.

### ۲-۴. AquaCrop، WEAP و HEC-RAS

- **AquaCrop** مدل استاندارد FAO برای شبیهسازی عملکرد محصول و بهرهوری آب بر پایه پاسخ به تنش آبی است؛ واسنجی با ارقام بومی (که سند اعلام کرده) روش صحیح است. خروجی بقایای گیاهی به RothC — اتصالی که سند طراحی کرده — یکپارچگی زنجیره را تقویت میکند.
- **WEAP** مدل مرجع تخصیص منابع آب با رویکرد تقاضامحور است؛ دریافت رواناب و تغذیه آبخوان از SWAT+ معماری استاندارد «مدل هیدرولوژیک → مدل تخصیص» است.
- **HEC-RAS** مدل مرجع هیدرولیک کانال باز است؛ محاسبه پروفیل سطح آب و تنش برشی برای «اثبات پایداری کانال مارپیچ» که سند ادعا کرده، دقیقاً کاربرد درست HEC-RAS است. اما باید تأکید شود: HEC-RAS یکبعدی برای جریان مارپیچی/چرخشی محدودیت دارد و بهتر است با مدل دوبعدی (HEC-RAS 2D) یا مدل فیزیکی تکمیل شود.
- **نکته کلی:** ادعای سند مبنی بر کاهش خطای پیشبینی به «کمتر از ۱۰٪» پس از کالیبراسیون میدانی، برای مدلهای هیدرولوژیک جاهطلبانه است؛ در ادبیات، NSE>0.7 (نه خطای ۱۰٪) معیار پذیرش است. توصیه میشود سند شاخصهای کمی خطا (NSE، PBIAS، R²) را جایگزین «درصد خطا» کند تا با معیارهای داوری بینالمللی قابل مقایسه باشد.

---

## گام ۳: سیستم تریگر خشکسالی و اقدام پیشدستانه (بخش ۱۲)

### ۳-۱. اعتبارسنجی شاخصها
- **SPI-3 (شاخص بارش استانداردشده ۳ ماهه):** شاخص استاندارد جهانی پایش خشکسالی هواشناسی است و در سامانههای هشدار اولیه (UN-SPIDER) و پروتکلهای اقدام پیشدستانه FAO استفاده میشود. آستانههای سند (SPI-3 < −0.8/−2/−1.6) با طبقهبندی استاندارد (خشکسالی ملایم/شدید/بسیار شدید) هماهنگ است.
- **VHI (شاخص سلامت پوشش گیاهی):** ترکیب VCI و TCI از MODIS؛ در UN-SPIDER بهعنوان داده استاندارد پایش خشکسالی کشاورزی معرفی شده و آستانههای <40 (هشدار) و <35 (اقدام) با معیارهای رایج سازگار است.
- **CHIRPS:** داده بارش ادغامی ماهواره-ایستگاه با تفکیک ۰٫۰۵ درجه که برای SPI در مناطق خشک دقت قابل قبولی دارد (Faisol et al., JWLD 2022 — دقت ۵۳٪ در اندونزی)؛ برای ایران نیز مناسب است.
- **رطوبت خاک IoT و پیزومتر:** مکمل درست شاخصهای ماهوارهای است.

### ۳-۲. اقدام پیشدستانه (Anticipatory Action)
سند این سیستم را «بر اساس پروتکلهای FAO و GCF» معرفی میکند — درست است:
- FAO دستورالعمل رسمی «راهاندازی سازوکار تریگر برای اقدام پیشدستانه خشکسالی» را منتشر کرده که «پنجرههای فرصت اقدام در طول شوک قابل پیشبینی» را تعریف میکند (FAO Open Knowledge, cd1403en).
- پروتکل نمونه «خشکسالی کشاورزی پاکستان» (FAO/PMD) نمونه عملیاتی همین ساختار است (Anticipation Hub).
- در سال ۲۰۲۳، FAO به بیش از ۲ میلیون نفر در ۲۴ کشور کمک پیشدستانه ارائه کرد (ReliefWeb/FAO Annual Report 2023) — این رویکرد از حالت آزمایشی خارج شده است.
- روششناسی «تریگر خشکسالی کشاورزی با SPI1 و پیشبینی تبدیل خشکسالی هواشناسی به کشاورزی» (Isaev et al., MDPI Water 2024) دقیقاً مکمل طراحی سند است.

### ۳-۳. بیمه شاخصمحور
سند در سطح ۳ به «بیمه محصولات مبتنی بر شاخص» اشاره میکند. الگوی موفق جهانی **IBLI (بیمه دام شاخصمحور)** در شاخ آفریقا است که با داده ماهوارهای خشکسالی، پرداخت خودکار به دامداران را انجام میدهد (ILRI؛ Jensen et al., 2025) و اثرات مثبت اقتصادی در دورههای خشکسالی نشان داده (UC Davis BASIS؛ UNFCCC). پیشنهاد: طراحی محصول بیمه شاخصمحور برای دیمکاران ایران با تریگرهای SPI-3/VHI دقیقاً با زیرساخت اکو نوژین قابل اجراست و باید در برنامه ریسک سند پررنگتر شود.

---

## گام ۴: تحقیق و توسعه و اختراعات (بخش ۱۱)

### ۴-۱. ارزیابی قابلیت ثبت اختراع
- **پوسته زیستی سیانوباکتری بومی زاگرس (تلقیح در بستر کود گاوی، آب دریا، خاکستر):** ایده «مهدکودک میکروبی» علمی است (Ayuso et al., PMC 2017)؛ اما «آب دریا» برای مناطق غیرساحلی (زاگرس) عجیب است و احتمالاً به معنی آب شور/اشباع نمک است — باید در اظهارنامه پتنت شفاف شود. قابلیت ثبت: متوسط تا بالا (وابسته به ادعای ترکیب اختصاصی سویه).
- **کانال مارپیچ (r=a+bθ):** هندسه مارپیچ ارشمیدسی در ورودی شفتهای گردابی پیشینه دارد (Scilit)؛ ادعای نوآوری سند «کانال کمعمق دامنهای + لایه بیوچار + استهلاک انرژی سیلاب» است که ترکیبی نوین است و قابلیت ثبت (Utility Model) دارد، مشروط به اثبات مزیت با مدل فیزیکی و مقایسه با کانال مستقیم همابعاد.
- **کنسرسیوم میکروبی (AMF+PGPR+Cyanobacteria):** ترکیب سهگانه اختصاصی با ادعای کمی (WUE +۳۰٪) — قابلیت ثبت دارد اما ادعاهای کمی باید با دادههای کرتی مستند شوند.
- **نکته راهبردی:** طبق گزارش سند، ثبت PCT تا ۹۰٪ توسط صندوق نوآوری حمایت میشود — این عدد با قوانین معاونت علمی (حمایت از هزینههای بینالمللی) سازگار است و باید در قرارداد با صندوق راستیآزمایی شود.

### ۴-۲. پکیجهای اقلیمی
ایده «ورود مختصات → تولید خودکار پکیج (گونه، ابعاد سازه، دستورالعمل اجرایی)» و کاهش زمان طراحی از ۶ ماه به ۲ هفته، با منطق سیستمهای توصیهگر اقلیم-خاک (که در گزارش research-c بهعنوان ماژول B پیشنهاد شد) همخوانی دارد. جدول ۵ اقلیم (FR-1 زاگرس، AR-1 جنوب شور، HU-1 خزری، SN-1 سرد کوهستانی) منطقی است؛ اما برای ادعای «کاهش طراحی به ۲ هفته»، سند باید کتابخانه SOP و بانک ابعاد سازهها را کامل کند.

---

## گام ۵: پلتفرم اکو نوژین و پایش (بخش ۱۵ و ۲۰)

- **MRV سهسطحی:** معماری پایش «مزرعه → محلی → ملی» با اتصال به بازار کربن (Verra/GHG Protocol) با الزامات روش VM0042 (بند ۶-۲) سازگار است؛ روش VM0042 سختگیرانهترین متدولوژی کربن خاک شناخته میشود (Eagronom) و تازه توسط ICVCM تأیید شده (ClearBlue Markets؛ Senken) — یعنی پنجره فرصت برای ثبت زودهنگام پروژههای کربن خاک باز است.
- **KoboToolbox:** ابزار متنباز و استاندارد جمعآوری داده آفلاین میدانی است؛ در پروژههای کشاورزی (مثلاً موزامبیک) برای تابآوری مزارع کوچک استفاده شده (KoboToolbox Blog) و قابلیت همگامسازی آفلاین→آنلاین را دارد (KoboToolbox Community). FAO نیز پایش FFS را با Kobo انجام میدهد (FAO Survey). انتخاب درستی است.
- **مدارس مزرعهای (FFS):** مدل آموزشی مشارکتی FAO است (FAO Open Knowledge — Introduction to FFS). **هشدار:** مرور سیستماتیک Cochrane نشان میدهد که FFS در مقیاس بزرگشده، شواهد کافی برای بهبود پیامدهای کشاورزی ندارد (ResearchGate/Waddington et al. 2014)؛ بنابراین سند باید شاخصهای اثربخشی (تغییر عملکرد، نرخ پذیرش) را در KPIهای FFS بگنجاند تا از این نقد شناختهشده عبور کند.

---

## گام ۶: بازار، رقبا و اقتصاد (بخش ۵، ۱۸، ۱۹)

### ۶-۱. رقبای بینالمللی
- **دیوار بزرگ سبز آفریقا (GGW):** هدف رسمی UNCCD: احیای ۱۰۰ میلیون هکتار زمین تخریبشده، ترسیب ۲۵۰ میلیون تن کربن و ایجاد ۱۰ میلیون شغل سبز تا ۲۰۳۰ (UNCCD؛ IFAD؛ GCF). این اعداد دقیقاً چارچوبی است که سند باید خود را در آن مقایسه کند؛ پیشرفت واقعی GGW کمتر از اهداف اولیه بوده و درس «مشارکت محلی و پایش» را برجسته میکند (World Bank IEG).
- **JILMI اردن:** پروژه مدیریت یکپارچه منظر اردن با حمایت GCF (که سند بهعنوان رقیب/مرجع معرفی کرده) — در جستجوهای این دور بهطور مستقیم نیامد؛ برای تکمیل تحلیل رقابتی باید در گام بعدی جستجوی اختصاصی انجام شود.
- **LDN (خنثیبودن تخریب سرزمین):** چارچوب هدف ۱۵.۳ SDG که سند به آن ارجاع میدهد؛ رویکرد «همارزی» (برابری تخریب و احیا) مبنای طراحی MRV سند است.
- **مزیت نسبی سند:** هزینه مداخله پایین در مقایسه با سازههای بتنی صنعتی — که در گزارش research-c با اعداد (گابیون ۳۵–۷۰ دلار/m³ و یکچهارم هزینه بند بنایی) پشتیبانی شد.

### ۶-۲. بازار کربن خاک
- متدولوژی **VM0042 (Verra)** برای «بهبود مدیریت اراضی کشاورزی» توسط ICVCM تحت Core Carbon Principles تأیید شده (Verra؛ ClearBlue؛ Senken) — یعنی اعتبار کربن خاک اکنون «قابل قبول در بازار معتبر» است.
- روند ثبت پروژه VM0042 پیچیدهترین روند بازار داوطلبانه است (Eagronom) — سند باید تیم MRV تخصصی و بودجه ثبت را جدی بگیرد.
- قیمت اعتبار کربن خاک متغیر است؛ تحلیل حساسیت سند (تأثیر ۲٪ قیمت کربن بر IRR) واقعبینانه است و درست که سبد درآمدی به کربن وابسته نمیکند.

### ۶-۳. کتیرا و گیاهان دارویی
- بازار جهانی کتیرا حدود **۱۸۵٫۴ میلیون دلار (۲۰۲۵)** با رشد پایدار ارزیابی شده (DataIntelo) و ایران صادرکننده عمده صمغ کتیرا از گون وحشی است (IRNA؛ FAO NWFP). در دهه ۱۹۵۰ صادرات ایران به بیش از ۴۰۰۰ تن در سال میرسید (FAO Pl@ntUse).
- مطالعه اخیر Frontiers (Shariatzadeh et al., 2025) توسعه پایدار صادرات گیاهان دارویی ایران (از جمله کتیرا و باریجه) را تحلیل کرده — این منبع مستقیماً برای بخش ۱۸ سند (سبد درآمدی) قابل استناد است.

### ۶-۴. ارزش خدمات اکوسیستمی (بخش ۱۹)
ارزشگذاری سالانه ۵ دلار/هکتار (ترسیب کربن، تغذیه آبخوان، کنترل سیلاب، حاصلخیزی، گردهافشانی، اکوتوریسم) با رویکردهای ارزشگذاری خدمات اکوسیستمی همسو است اما ارقام آن باید به روشهای استاندارد (هزینه جایگزینی، ارزش بازار، انتقال منفعت) مستند شود؛ در گزارش research-c، ارزش ۸ دلار/تن خاک (روش هزینه جایگزینی) بهعنوان مبنا ذکر شد که میتواند عدد سند را پشتیبانی کند. نسبت B/C اجتماعی >۴ با نرخ تنزیل ۳٪ (که سند ذکر کرده) مطابق رهنمودهای ارزشگذاری پروژههای اقلیمی است.

---

## جمعبندی و پیشنهادهای اصلاحی برای سند

**نقاط قوت تأییدشده:** معماری زنجیره ششمدلی، کالیبراسیون با سنجشازدوری در حوضههای بدون ایستگاه، بیوچار (۶۰–۸۰٪ تثبیت کربن)، تلقیح سیانوباکتر، کنسرسیوم PGPR–AMF، تریگرهای SPI/VHI/CHIRPS و پروتکل FAO اقدام پیشدستانه، انتخاب KoboToolbox، و همزمانی با تأیید ICVCM برای VM0042.

**نقاط نیازمند اصلاح:**
1. جایگزینی «خطای کمتر از ۱۰٪» با شاخصهای کمی (NSE, PBIAS, R²) مطابق معیارهای داوری.
2. تعدیل ادعای «حذف کامل کود شیمیایی» و «WUE +۳۰٪» به مقادیر قابل دفاع با داده کرتی.
3. شفافسازی «آب دریا» در اظهارنامه پوسته زیستی و آزمون بقای بلندمدت.
4. تکمیل اعتبارسنجی کانال مارپیچ با مدل فیزیکی/دوبعدی HEC-RAS (محدودیت مدل یکبعدی برای جریان گردابی).
5. گنجاندن KPI اثربخشی برای FFS (پاسخ به نقد مرورهای سیستماتیک).
6. جستجوی اختصاصی JILMI و اسناد GCF برای تکمیل جدول رقبا.

---

## فهرست منابع (فقط منابع جستجوشده در این دور)

**پوسته زیستی سیانوباکتری:**
- Xie et al. — Mechanisms of artificial biological soil crusts development (2024): https://www.sciencedirect.com/science/article/pii/S235218642400018X
- Zhou et al. — Co-inoculation of fungi and desert cyanobacteria (Frontiers, 2024): https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2024.1377732/full
- Ayuso et al. — Microbial Nursery Production of High-Quality BSCs (PMC, 2017): https://pmc.ncbi.nlm.nih.gov/articles/PMC5244311/
- Lan et al. — Artificially Accelerating Reversal of Desertification (ACS, 2014): https://pubs.acs.org/doi/abs/10.1021/es403785j
- Fick et al. — Induced BSC controls on wind erodibility and PM10 (USDA ARS, 2020): https://www.ars.usda.gov/ARSUserFiles/24758/13.%20Induced%20biological%20soil%20crust%20controls%20on%20winderodibility%20and%20dust%20(PM10)%20emissions.pdf

**کانال مارپیچ / شفت گردابی:**
- Mahmoudi-Rad et al. — Energy dissipation efficiency of vortex drop shafts (PMC, 2023): https://pmc.ncbi.nlm.nih.gov/articles/PMC9886980/
- ResearchGate — Types of vortex drop shafts (circular/scroll/spiral/tangential): https://www.researchgate.net/figure/Types-of-vortex-drop-shafts-a-circular-b-scroll-c-spiral-and-d-tangential_fig1_335133543
- Yang et al. — 3D Flow of a Vortex Drop Shaft Spillway (MDPI Water, 2021): https://www.mdpi.com/2073-4441/13/4/504
- Scilit — Archimedean spiral inlet vortex drop shaft: https://www.scilit.com/publications/8872507fc09aab94528d77e96a8b4e57

**کنسرسیوم میکروبی:**
- Chenche-López et al. — PGPR–AMF consortia drought tolerance maize (Frontiers, 2026): https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2026.1802481/full
- Silva et al. — AMF and rhizobacteria under drought (ScienceDirect, 2023): https://www.sciencedirect.com/science/article/pii/S0944501323000526
- Savastano et al. — AMF and PGPR (MDPI, 2024): https://www.mdpi.com/2037-0164/15/4/67
- Pereira et al. — PGPR improve nutrient use efficiency (PMC, 2020): https://pmc.ncbi.nlm.nih.gov/articles/PMC7550905/

**بیوچار:**
- Waheed et al. — Biochar climate-smart strategy dryland soils (Springer Biochar, 2026): https://link.springer.com/article/10.1007/s42773-025-00537-0
- EurekAlert — Biochar restores dryland soils (15–35% water retention): https://www.eurekalert.org/news-releases/1121790
- Biochar Today — 40% water retention, 50% grass biomass: https://biochartoday.com/news/biochar-systems-can-restore-dryland-soils-by-increasing-water-retention-forty-percent-and-boosting-grass-biomass-by-fifty-percent/
- Li et al. — Biochar in sandy soil water retention (USDA FS, 2021): https://research.fs.usda.gov/treesearch/64867
- Thao et al. — Biochar amendments soil water uptake (Vadose Zone J., 2023): https://acsess.onlinelibrary.wiley.com/doi/full/10.1002/vzj2.20266

**زنجیره شبیهسازی:**
- Dangol et al. — Multivariate Calibration of SWAT with RS (MDPI, 2023): https://www.mdpi.com/2072-4292/15/9/2417
- Odusanya et al. — Multi-site calibration SWAT with satellite ET (HESS, 2019): https://hess.copernicus.org/articles/23/1113/2019/hess-23-1113-2019.pdf
- Bennour et al. — SWAT calibrated with 12 months ETa (TU Delft, 2022): https://repository.tudelft.nl/file/File_9d042048-f4f3-4996-bfe1-aaf8a902c704
- Koltsida et al. — Multi-variable SWAT calibration SUFI-2 (FAO AGRIS, 2022): https://agris.fao.org/search/en/providers/122535/records/65df88f290674e46e653f33e
- Parajuli et al. — RS ET data in SWAT-CUP SUFI-2 (USDA FS, 2018): https://research.fs.usda.gov/download/treesearch/56648.pdf
- Almagro et al. — C-factor from NDVI (ScienceDirect, 2019): https://www.sciencedirect.com/science/article/pii/S2095633919301832
- Ayalew et al. — Sensitivity of NDVI-based C factor (MDPI, 2020): https://www.mdpi.com/2072-4292/12/7/1136
- IWA — Assessing soil erosion with RUSLE (2024): https://iwaponline.com/ws/article/24/7/2487/103147/Assessing-soil-erosion-through-the-implementation

**تریگر خشکسالی و اقدام پیشدستانه:**
- FAO — Setting up a drought Anticipatory Action trigger mechanism: https://openknowledge.fao.org/handle/20.500.14283/cd1403en
- FAO — Anticipatory Action Protocol: Agricultural drought Pakistan (Anticipation Hub): https://www.anticipation-hub.org/Documents/Framework_documents/fao-pakistan-drought-cc7046en.pdf
- UN-SPIDER — Data Application of the Month: Drought Monitoring (SPI/VHI): https://un-spider.org/links-and-resources/data-sources/daotm-drought
- Isaev et al. — Agricultural Drought-Triggering for Anticipatory Action (MDPI Water, 2024): https://www.mdpi.com/2073-4441/16/14/2009
- ReliefWeb — FAO Anticipatory Action Annual Report 2023: https://reliefweb.int/report/world/anticipatory-action-annual-report-2023
- Faisol et al. — Agricultural drought CHIRPS SPI (JWLD, 2022): https://www.jwld.pl/files/2022-01-JWLD-06-Faisol.pdf

**بیمه شاخصمحور:**
- ILRI — Index-based livestock insurance after 10 years: https://www.ilri.org/news/after-10-years-kenya-and-ethiopia-are-we-ready-scale-livestock-insurance-horn-africa
- Jensen et al. — IBLI to support pastoralists (ScienceDirect, 2025): https://www.sciencedirect.com/science/article/pii/S0306919225001149
- UC Davis BASIS — Favorable Impacts of IBLI (Ethiopia): https://basis.ucdavis.edu/publication/update-favorable-impacts-index-based-livestock-insurance-evaluation-results-ethiopia
- UNFCCC — IBLI document: https://unfccc.int/documents/637324

**رقبا و بازار کربن:**
- UNCCD — Great Green Wall Initiative (100M ha, 250 Mt C, 10M jobs): https://www.unccd.int/our-work/ggwi
- IFAD — Great Green Wall: https://www.ifad.org/en/climate/great-green-wall
- GCF — Great Green Wall portfolio: https://www.greenclimate.fund/portfolio/areas-of-work/great-green-wall
- World Bank IEG — Scaling the Great Green Wall: https://ieg.worldbankgroup.org/blog/scaling-great-green-wall
- Verra — VCS program: https://verra.org/programs/verified-carbon-standard/
- Verra — Improved Agricultural Land Management Methodology approved by ICVCM: https://verra.org/verras-improved-agricultural-land-management-methodology-approved-by-icvcm/
- ClearBlue Markets — ICVCM approves CAR SEP and Verra VM0042: https://www.clearbluemarkets.com/knowledge-base/icvcm-approves-agriculture-carbon-methodologies-from-car-and-verra
- Senken — Regenerative agriculture carbon methodologies: https://www.senken.io/academy/carbon-methodologies/regenerative-agriculture
- Eagronom — Verra VM0042 methodology: https://blog.eagronom.com/verra-vm0042-methodology-the-most-rigorous-standard-on-the-carbon-credit-market.-what-does-it-really-mean

**FFS و KoboToolbox:**
- FAO — Introduction to Farmer Field Schools (Open Knowledge): https://openknowledge.fao.org/server/api/core/bitstreams/f6058309-60eb-48f5-b006-f95017d5858d/content
- Waddington et al. — FFS systematic review (ResearchGate): https://www.researchgate.net/publication/324738889_Farmer_field_schools_for_improving_farming_practices_and_farmer_outcomes_in_low-and_middle-income_countries_a_systematic_review
- KoboToolbox — Resilience of smallholder farms in Mozambique: https://www.kobotoolbox.org/blog/improving-the-resilience-of-smallholder-farms-in-mozambique-using-kobotoolboxs-geographic-data-features
- KoboToolbox Community — Offline data collection best practices: https://community.kobotoolbox.org/t/best-practices-for-offline-data-collection-in-remote-areas/76424
- FAO Kobo Survey on FFS: https://ee-eu.kobotoolbox.org/x/Fk5D3PJz

**کتیرا و گیاهان دارویی:**
- DataIntelo — Tragacanth Market Report 2034 ($185.4M in 2025): https://dataintelo.com/report/tragacanth-market
- IRNA — Iran major world exporter of tragacanth gum: https://en.irna.ir/news/81356229/Iran-major-world-exporter-of-tragacanth-gum
- FAO Pl@ntUse — Tragacanth (NWFP 6): https://plantuse.plantnet.org/en/Tragacanth_(FAO,_NWFP_6)
- Shariatzadeh et al. — Sustainable development of Iran's medicinal plant exports (Frontiers, 2025): https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2025.1500168/full

**مکمل (از گزارش research-c):**
- UNCCD — Microcatchment Rainwater Harvesting: https://www.unccd.int/land-and-life/sds/toolbox/microcatchment-rainwater-harvesting
- NGWA — Principles of Induced Infiltration and Artificial Recharge: https://www.ngwa.org/what-is-groundwater/About-groundwater/principles-of-induced-infiltration-and-artificial-recharge
