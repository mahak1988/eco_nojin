# گزارش جامع پژوهش: مهندسی آبخیزداری و کشتهای مقاوم

**پروژه:** اکو نوژین (Eco Nojin) — پلتفرم بینالمللی احیای اکوسیستم و کشاورزی هوشمند
**موتور علمی:** HyDroMa
**حوزه پژوهش:** سازههای آبخیزداری، معادلات طراحی هیدرولوژیکی، کشتهای مقاوم به خشکی و شوری، فناوریهای اصلاحنبات، سامانههای زراعی تابآور
**تاریخ:** مرداد ۱۴۰۵ (آگوست ۲۰۲۶)

---

## مقدمه

در مناطق خشک و نیمهخشک جهان — که ایران در قلب آن قرار دارد — کمبود آب، فرسایش خاک و تنشهای خشکی/شوری سه چالش بههمپیوستهاند. راهحل پایدار ترکیبی است از: (۱) مدیریت فیزیکی آب در مقیاس حوزه آبخیز (مهندسی آبخیزداری) برای «جمعکردن، ذخیرهکردن و نفوذدادن» رواناب، و (۲) بهکارگیری ژرمپلاسم و فناوریهای اصلاحنبات برای تولید ارقامی که با آب کمتر و خاک شورتر عملکرد اقتصادی قابل قبولی بدهند. این گزارش، یافتههای پژوهش وب را در پنج بخش ارائه میکند و در پایان، ماژولهای پیشنهادی برای پیادهسازی در موتور علمی HyDroMa معرفی میشوند.

---

## بخش ۱: سازههای آبخیزداری

سازههای آبخیزداری بر اساس هدف به سه دسته کلی تقسیم میشوند: **کنترل فرسایش و رسوب** (بندها)، **کاهش سرعت و افزایش نفوذ رواناب** (تراس، کنتورفارو، نیمههلالی)، و **تغذیه مصنوعی آبخوان** (حوضچه نفوذ، چاه تزریق). در ادامه هر سازه با چهار مشخصه «هدف، ابعاد تقریبی، محل مناسب، هزینه تقریبی» معرفی میشود.

### ۱-۱. بندهای اصلاحی (Check Dams)

بندهای اصلاحی سازههای کوچک و کمهزینهای هستند که عرض آبراهه را قطع میکنند تا سرعت جریان کاهش یابد، رسوب تهنشین شود و نیمرخ طولی بستر به تدریج اصلاح شود. سه نوع رایج:

- **بند سنگچین (Rock/Loose Stone):** سادهترین و ارزانترین نوع؛ از سنگهای رودخانهای بدون ملات. ارتفاع معمول ۰٫۵ تا ۱٫۵ متر و عرض تاج ۰٫۵ تا ۱ متر. مناسب آبراهههای درجه ۱ و ۲ با شیب کم تا متوسط که دسترسی ماشینآلات دشوار است. هزینه آن عمدتاً نیروی کار و حمل سنگ است و در مقایسه با بندهای بنایی به مراتب کمتر برآورد میشود — در یک مطالعه موردی در هند، سازه کمهزینه حدود ۵۵٬۰۰۰ روپیه در برابر ۲۰۰٬۰۰۰ روپیه برآورد اولیه برای بند بنایی همان محل هزینه برداشت (IJC MAS).
- **بند گابیونی (Gabion):** قفسههای توری فلزی (مش معمول ۸×۱۰ سانتیمتر با سیم ۲٫۲ تا ۳ میلیمتر گالوانیزه) پر از سنگ لاشه، با ابعاد استاندارد مانند ۳×۱×۱ متر. مزیت: پایه کوچکتر، مقاومت خوب، انعطافپذیری در نشست و نیاز کم به نگهداری (Penn State / Coconino). ارتفاع تیپیک ۱ تا ۳ متر. محل مناسب: آبراهههای با دبی و شیب متوسط، جایی که سنگ بهصورت محلی در دسترس است. هزینه جهانی گابیون بهطور میانگین ۳۵ تا ۷۰ دلار بر مترمکعب (مواد و نصب) برآورد شده است (Shitaimesh, 2026).
- **بند بتنی (Concrete):** برای آبراهههای اصلی با دبی بالا و عمر طراحی بلند (۵۰+ سال) استفاده میشود. نیاز به پی و قالببندی دارد و گرانترین گزینه است. ابعاد بر اساس هیدرولیک تعیین میشود؛ سرریز باید ظرفیت عبور سیل طراحی را داشته باشد.

**فاصلهگذاری بندها:** قاعده استاندارد این است که فاصله بین دو بند متوالی نباید از «فاصله افقی از پنجه بند بالادست تا نقطهای با همان ارتفاع در بند پاییندست» بیشتر شود؛ بهعبارتی شیب رسوبی بین بندها باید ملایمتر از شیب طبیعی آبراهه باشد (LID SWM Guide). در عمل فاصله از رابطه H/S (ارتفاع مؤثر بند تقسیم بر شیب بستر) محاسبه میشود. در کانالهای آبگرفت شهری، حداقل فاصله بندها معمولاً ۵۰ فوت (حدود ۱۵ متر) و عمق آب در پاییندست نباید از ۴۵ سانتیمتر تجاوز کند (Minnesota Stormwater).

### ۱-۲. تراسبندی (Terracing)

تراسها شیب دامنه را به پلههای تقریباً افقی تبدیل میکنند تا سرعت رواناب و فرسایش کاهش یابد و آب در هر پله نفوذ کند.

- **تراس مخزنی (Bench Terrace):** پلههای پهن با دیواره (سنگی یا خاکی)؛ برای باغات و زراعت روی شیبهای ۱۰ تا ۳۰ درصد. عرض پله ۳ تا ۱۰ متر. هزینه بالا دارد (خاکبرداری زیاد) اما با تبدیل دامنه به سطح قابل کشت، ارزش افزوده ایجاد میکند.
- **تراس کنتوری (Contour/Channel Terrace):** کانال و پشته در امتداد خط تراز ساخته میشود تا رواناب را به سرعت امن به آبراهه چمنی هدایت کند (NRCS Code 600). فاصله عمودی (Vertical Interval) بین تراسها بر اساس شیب، فرسایشپذیری خاک و مدیریت تلفات خاک تعیین میشود؛ در طراحی NRCS، فاصله حداکثر برای کنترل فرسایش بر اساس تحمل تلفات خاک مجاز است و گاهی تا ۱۰٪ برای هماهنگی با حد و مرز زمین افزایش مییابد (NRCS Terrace Standard). تراسهای پهنپایه (Broad-base) در زمینهای زراعی با شیب ۲ تا ۶ درصد و تراسهای پشته-کانالی در دامنههای تندتر بهکار میروند (Nebraska Extension).
- **هزینه:** خاکبرداری و تسطیح حدود ۲۰۰ تا ۸۰۰ مترمکعب در هکتار بسته به شیب؛ هزینه به شدت به دستمزد و ماشینآلات محلی وابسته است.

### ۱-۳. کانالهای انحرافی و کنتور فارو (Contour Trenches / Diversion Channels)

کانالهای انحرافی، رواناب بالادست را از مناطق حساس (روستا، جاده، مزرعه) منحرف میکنند و به یک خروجی امن (آبراهه چمنی یا حوضچه) میرسانند. کنتور فاروها کانالهای باریکی هستند که دقیقاً روی خط تراز حفر میشوند؛ نه برای آبیاری، بلکه برای کاهش سرعت رواناب و افزایش نفوذ در خاک (Akvopedia). ابعاد تیپیک کنتور فارو: عرض ۳۰ تا ۵۰ سانتیمتر، عمق ۳۰ تا ۶۰ سانتیمتر، با خاک حفاریشده بهصورت پشته در سمت پاییندست. فاصله بین ردیفها در دامنههای کم (۵–۱۰٪) حدود ۱۰ تا ۲۰ متر و در دامنههای تندتر کمتر است. این روش برای جنگلکاری و باغات دیم دامنهای بسیار رایج است و هزینه آن عمدتاً نیروی کار (حدود ۱ تا ۲ دلار بر متر طول در کشورهای در حال توسعه، بسته به منطقه) برآورد میشود.

### ۱-۴. نیمههلالی / بانکت (Half-Moon / Banquette / Negarim Microcatchment)

حوضچههای هلالیشکل یا لوزی کوچکی هستند که رأسشان رو به بالادست است و رواناب سطح کوچکی (معمولاً ۱۰ تا ۱۰۰ مترمربع) را به نقطه کاشت (یک درخت یا بوته) متمرکز میکنند. این سازه نوعی **ریزحوزه آبگیر (Microcatchment)** است؛ UNCCD آن را «سازههایی برای به دام انداختن رواناب محلی و تمرکز آن» معرفی میکند (UNCCD Toolbox). ابعاد استاندارد بر اساس نیاز آبی گیاه و نسبت مساحت رواناب به مساحت کاشت (نسبت C:CA که معمولاً بین ۲:۱ تا ۱۰:۱ است) محاسبه میشود؛ در کتابچه FAO، فرمول طراحی نگاریم چنین است: مساحت کل ریزحوزه = مساحت کاشت × {(نیاز آبی − بارش مؤثر) ÷ (بارش مؤثر × ضریب رواناب)} (FAO Water Harvesting Manual). ابعاد مثال: نگاریم با پشته ۲۵ سانتیمتری، مساحت کل حدود ۸۴ مترمربع برای درخت بادام در اقلیم نیمهخشک (FAO manual example). محل مناسب: دامنههای کمشیب (۱ تا ۵٪) با خاک عمیق، مناطق خشک با بارش ۱۰۰ تا ۴۰۰ میلیمتر. هزینه: بسیار پایین؛ تنها نیروی کار (حدود ۰٫۵ تا ۲ دلار بر هر سازه).

### ۱-۵. بندهای گِلی (Gully Plugs)

برای مهار «خندقها» (Gully) — آبراهههای فرسایشی که سریعاً عمیق و پهن میشوند — در محلهای بحرانی خندق، بندهای کوتاه از جنس سنگ، گابیون، کیسه شن یا حتی بافههای گیاهی احداث میشود تا شیب بستر کاهش، رسوبگیری افزایش و توسعه سرسره (Headcut) متوقف شود. ارتفاع تیپیک ۰٫۵ تا ۱ متر با عرض تاج ۱ تا ۲ متر. محل مناسب: ابتدای خندقهای فعال و انشعابات آنها. هزینه پایین تا متوسط؛ در مطالعات، بندهای گابیونی کوچک از مقرونبهصرفهترین اقدامات کنترل فرسایش خندق شناخته شدهاند.

### ۱-۶. آبراهههای چمنی (Grassed Waterways)

کانالهای طبیعی یا احداثی با پوشش چمن چندساله که رواناب جمعشده از تراسها و کانالها را با سرعت مجاز (زیر سرعت فرسایشی پوشش گیاهی، معمولاً ۱٫۵ تا ۲٫۵ متر بر ثانیه بسته به نوع چمن) به خروجی امن منتقل میکنند (Nebraska Extension). ابعاد: کف ۲ تا ۱۰ متر و شیب طولی ۱ تا ۵٪ با مقطع ذوزنقهای یا سهموی. هزینه شامل تسطیح و بذرپاشی (حدود ۵۰۰ تا ۲۰۰۰ دلار در هکتار). این سازه «شریان دفع امن» بقیه سازههای بالا است و در هر طرح آبخیزداری باید پیشبینی شود.

### ۱-۷. سامانههای جمعآوری آب باران (Rainwater Harvesting)

- **پشتبامی (Rooftop):** چهار جزء اصلی: سطح جمعآوری (بام)، سامانه انتقال (ناودان و لوله)، فیلتر/جداکننده نخستین جریان (First-flush diverter)، و مخزن ذخیره (Cistern) (Arizona Water Resources). مخازن پیشساخته فایبرگلاس تا حدود ۱۵۰٬۰۰۰ لیتر و مخازن بتنی زیرزمینی در دسترساند (LID SWM Guide). حجم مخزن از رابطه: حجم قابل جمعآوری = بارش سالانه (mm) × مساحت بام (m²) × ضریب رواناب بام (۰٫۷۵–۰٫۹) محاسبه میشود. هزینه: مخزن بخش اصلی هزینه است (به ازای هر ۱۰۰۰ لیتر، بسته به جنس، حدود ۱۰۰ تا ۳۰۰ دلار).
- **سطحی (Surface/Runoff):** هدایت رواناب سطحی زمینهای زراعی یا سنگریزهای به حوضچهها یا مزارع پاییندست با استفاده از بانکت، کانال و حوضچه. مناسب زمینهای کمشیب با خاک نفوذپذیر.

### ۱-۸. حوضچههای نفوذ (Percolation/Recharge Ponds)

حوضچههای بزرگ کمعمقی که رواناب جمعآوریشده را بهصورت موقت نگه میدارند تا به آب زیرزمینی نفوذ کند. ابعاد: از چندصد تا چند هزار مترمربع، عمق آب ۱ تا ۳ متر. ملاحظات طراحی: کف باید نفوذپذیر (رس کمتر از ۲۰٪) باشد، از رسوبگیری کف باید جلوگیری شود (پیشتصفیه)، و فاصله از چاههای شرب طبق مقررات (معمولاً >۳۰ متر) رعایت شود. روشهای تغذیه مصنوعی شامل حوضچههای نفوذ، کانالهای نفوذ و تزریق مستقیم چاهی است (NGWA). هزینه: حفاری و خاکریزی (حدود ۱ تا ۳ دلار بر مترمکعب حفاری).

### ۱-۹. چاههای تزریق / تغذیه مصنوعی (Injection/Recharge Wells)

برای آبخوانهای عمیق یا محصور که حوضچه سطحی مؤثر نیست، آب از طریق چاه تزریق میشود. چاههای کمعمق برای آبخوانهای تا عمق ۵۰ متر با قطر شفت بیش از ۲ متر برای پذیرش حجم بیشتر طراحی میشوند (Slideshare/lecture materials)؛ چاههای پرفشار (Aquifer Storage and Recovery — ASR) برای آبخوانهای عمیق. آب تزریقی باید تصفیه و عاری از رسوب باشد تا از گرفتگی (Clogging) — چالش اصلی که NGWA به آن اشاره دارد — جلوگیری شود. هزینه: حفاری چاه (به عمق و قطر بستگی دارد، معمولاً دهها هزار دلار) بهعلاوه تجهیزات تزریق و تصفیه؛ در مقیاس شهری بالاترین هزینه سرانهای را دارد اما برای آبخوانهای بحرانی توجیهپذیر است.

### ۱-۱۰. LID و BMP (توسعه کماثر و بهترین شیوههای مدیریت)

رویکرد LID (Low Impact Development) مدیریت رواناب را «تا حد امکان نزدیک به منبع تولید» انجام میدهد: کاهش سطح نفوذناپذیر، حفظ پوشش گیاهی، و استفاده از عناصر پراکنده مانند بام سبز، سنگفرش نفوذپذیر، بشکه باران، بیوریتنشن (Bioretention)، نوارهای فیلتر چمنی و سویل (Swale) (Purdue Extension؛ NVCOG). این رویکرد برای مناطق شهری و حومهای پلتفرم اکو نوژین (شهرهای هوشمند مقاوم) مستقیم کاربرد دارد. هزینه هر BMP متفاوت است: بیوریتنشن کوچک ۵ تا ۱۵ هزار دلار در هر واحد، سنگفرش نفوذپذیر ۱۰ تا ۳۰٪ گرانتر از آسفالت معمولی.

---

## بخش ۲: معادلات طراحی هیدرولوژیکی

### ۲-۱. روش استدلالی (Rational Method)

پرکاربردترین روش برای برآورد دبی اوج رواناب حوزههای کوچک (معمولاً <۸۰ هکتار):

**Q = C × I × A**

- Q: دبی اوج (m³/s یا ft³/s با ضرایب واحد مناسب)
- C: ضریب رواناب (بدون بعد، ۰ تا ۱؛ تابع کاربری اراضی، نوع خاک و شیب؛ مثلاً ۰٫۳ برای مرتع، ۰٫۷–۰٫۹ برای سطوح نفوذناپذیر شهری)
- I: شدت بارش برای مدت برابر با زمان تمرکز حوزه (mm/hr)
- A: مساحت حوزه (ha یا km²)

فرض بنیادی روش: کل حوزه در زمان تمرکز (Tc) در بارش مشارکت میکند و شدت بارش در طول مدت بارش ثابت است. این روش برای طراحی بندهای کوچک، کانالهای انحرافی و سرریز سازههای سبک کافی است.

### ۲-۲. روش SCS-CN (سرویس حفاظت خاک / مرکز ملی منابع — NRCS)

برای برآورد ارتفاع رواناب از بارش با در نظر گرفتن خاک، کاربری اراضی و رطوبت پیشین:

**Q = (P − Ia)² / (P − Ia + S)** ، برای P > Ia

- Q: ارتفاع رواناب (mm)
- P: بارش (mm)
- Ia: تلفات اولیه (نگهداشت سطحی، نفوذ اولیه، ذخیره در فرورفتگیها)؛ استاندارداً Ia = 0.2 × S
- S: حداکثر ظرفیت نگهداشت بالقوه خاک (mm)

S از عدد منحنی (CN) بهدست میآید:

**S = (25400 / CN) − 254** (در سیستم متریک)

CN عددی بین ۰ تا ۱۰۰ است که از جدولهای استاندارد بر اساس گروه هیدرولوژیک خاک (A: شن با نفوذ زیاد تا D: رس با نفوذ کم)، کاربری اراضی و وضعیت پوشش انتخاب میشود (HEC-RAS Technical Reference؛ Bentley SewerCAD؛ WUR Lecture Notes). این روش در HEC-HMS بهعنوان مدل تلفات استاندارد پیاده شده است (HEC-HMS Docs). با جایگذاری Ia=0.2S معادله به شکل سادهشده Q = (P − 0.2S)² / (P + 0.8S) تبدیل میشود (Wikipedia Runoff Curve Number).

### ۲-۳. حجم ذخیره موردنیاز

برای حوضچه نفوذ یا مخزن آبگیر:

**V = Q_رواناب − (نفوذ + تبخیر + مصرف)**

در عمل برای طراحی مخزن آب باران: **V (m³) = P (m) × A_catch (m²) × C × η** که η راندمان سامانه (≈۰٫۸–۰٫۹) و C ضریب رواناب سطح است. برای حوضچه نفوذ، حجم = ارتفاع آب طراحی (معمولاً ۰٫۳ تا ۱ متر) × سطح حوضچه، و زمان تخلیه با نفوذپذیری خاک (K, m/day) و رابطه T = V / (A × K) کنترل میشود.

### ۲-۴. فاصله سازهها

- بند اصلاحی: Spacing = H / (S0 − S_هدف) که H ارتفاع مؤثر بند، S0 شیب طبیعی بستر و S_هدف شیب رسوبی مطلوب (معمولاً ۰٫۵ تا ۱٪ کمتر از شیب طبیعی) است. قاعده جایگزین: فاصله افقی بین پنجه بند بالادست و تاج بند پاییندست (LID SWM Guide).
- تراس: فاصله عمودی (VI) از فرمولهای NRCS: VI = (a × S + b) که ضرایب a, b تابع ناحیه و نوع خاکاند؛ سپس فاصله افقی = VI / (S/100) (NRCS Code 600؛ Nebraska Extension).
- کنتور فارو: با افزایش شیب، فاصله ردیفها کاهش مییابد تا حجم آب متمرکز در هر کانال از ظرفیت آن بیشتر نشود.

### ۲-۵. برآورد هزینه

هزینهها به سه جزء تفکیک میشوند: (۱) مصالح (گابیون ۳۵–۷۰ دلار/m³، بتن، سنگ)، (۲) اجرا (خاکبرداری، نیروی کار)، (۳) نگهداری (سالانه ۱–۳٪ هزینه ساخت برای پاکسازی رسوب). مقایسه موردی: بند کمهزینه در برابر بند بنایی — حدود یکچهارم هزینه (IJC MAS). در مدل HyDroMa باید هزینهها بهصورت توابع پارامتری بر اساس حجم سازه، دسترسی (فاصله از جاده) و نرخهای محلی تعریف شوند.

---

## بخش ۳: کشتهای مقاوم به خشکی و شوری

### ۳-۱. مکانیسمهای مقاومت به خشکی

- **ریشه عمیق و معماری ریشه:** دسترسی به رطوبت لایههای عمیق خاک؛ صفتی که در گندم دیم و سورگوم کلیدی است.
- **کارایی مصرف آب (WUE):** فتوسنتز کارآمدتر بهازای هر واحد آب (مسیر C4 در ارزن، سورگوم و تِف به آنها برتری میدهد؛ ارقام C4 در شرایط گرم نسبت به C3 عملکرد بهتری دارند — Tadele, 2018).
- **تنظیم اسمزی (Osmotic Adjustment):** تجمع پرولین، گلایسینبتائین و قندهای محلول برای حفظ فشار تورژسانس سلول.
- **بستهشدن سریع روزنه و مورفولوژی برگ:** کاهش سطح تبخیر، برگهای مومی (Cuticle ضخیم).
- **فرار از خشکی (Escape):** زودرسی؛ تکمیل چرخه زندگی قبل از پایان رطوبت خاک (مهمترین استراتژی برای گندم دیم مناطق مدیترانهای).

### ۳-۲. هالوفیتها و گیاهان شورپسند

- **کینوا (Chenopodium quinoa):** گیاهی با تحمل شوری استثنایی — توانایی تکمیل چرخه زندگی در غلظتهای تا ۴۰۰ میلیمولار NaCl (معادل حدود ۴۰ dS/m) (Zhang et al., 2026, PMC). مقاوم به خشکی، سرمای سبک و فقر خاک؛ دانه با پروتئین کامل (حاوی لیزین). پژوهشهای ICBA بر تولید کینوا، سالیکورنیا و جوهای متحمل در خاورمیانه متمرکز است (Fanack Water).
- **سالیکورنیا (Salicornia):** ساکولنت ساحلی که با آب دریا آبیاری میشود؛ منبع روغن و سبزی شورپسند. مسیر تجاریسازی آن مشابه کینوا پیشبینی میشود (Resilience.org).
- دیگر هالوفیتها: آتریپلکس (علوفه)، سوئدا، و چغندرقند وحشی.

### ۳-۳. ارقام مقاوم گندم و جو به شوری و خشکی

جو بهطور ذاتی متحملتر از گندم است؛ در آزمایشهای میدانی استرالیا ارقام جو ۵۰٪ بیشتر از گندم در خاک شور عملکرد دادند (GRDC). ژنوتیپهای جو ایرانی (لندریسهای بومی) برای ترکیب عملکرد بالا و تحمل تنش در شرایط نامساعد ارزیابی شدهاند (Barley landraces Iran). در غربالگری شوری گندم ایران، ارقام «آرگ، بم و کویر» بهعنوان شاهدهای متحمل معرفی شدهاند (Sardouie-Nasab et al., Crop Science 2014) و رقم «خارچیا» (Kharchia) در مطالعات یونشناسی گندم متحملترین شناخته شده است (Poustini & Heidari, 2004). در ارزیابی شاخصهای تحمل خشکی، رقم «نصرت» در جو بهعنوان متحملترین ژنوتیپ شناسایی شد (ResearchGate, Iranian barley cultivars). در ایران ارقامی مانند «چمران»، «پیشگام»، «کویر»، «روشن» و «هامون» در پژوهشهای تنش انتهایی خشکی عملکرد قابل قبولی نشان دادهاند.

### ۳-۴. برنج غوطهوریپذیر (Submergence-Tolerant Rice — SUB1)

ژن **SUB1A** از رقم سنتی FR13A به ارقام محبوب پسندیده (Swarna، IR64 و...) با کمک انتخاب نشانگری (MAS) منتقل شده است. رقم **Swarna-Sub1** تا ۲ تا ۳ هفته غوطهوری کامل را تحمل میکند و در شرایط سیل، ۴۵٪ عملکرد بیشتری نسبت به والد حساس دارد و در شرایط عادی عملکردی برابر دارد (Emerick et al., 2019, PMC؛ Poverty Action Lab). این موفقیت الگویی برای مهندسی مقاومت به «تنشهای شدید اما دورهای» است که با سیلابهای ناگهانی در حوزههای آبخیز (پاییندست سازهها) مرتبط میشود.

### ۳-۵. ارقام محلی ایران

ژرمپلاسم غنی ایران شامل: گندمهای دیم زاگرس (سرداری و مشتقهای آن)، جوهای بومی (مانند جوهای محلی فارس و کرمانشاه)، ارزن و سورگوم بومی سیستان، و گلرنگ. این مواد ژنتیکی خزانه صفاتی مانند زودرسی، تحمل خشکی انتهایی و شوریاند و در برنامههای MAS و GS ایران بهکار میروند (مثلاً غربالگری ژنوتیپهای جو بومی ایران برای تنش خشکی و شوری — Shahmoradi et al., Birjand). برای اکو نوژین، «بانک صفات ارقام بومی» یک دارایی کلیدی است.

---

## بخش ۴: فناوریهای اصلاحنبات

### ۴-۱. انتخاب به کمک نشانگر (MAS)

استفاده از نشانگرهای DNA برای ردیابی قطعات کروموزومی حامل ژنهای مطلوب و گزینش ژنوتیپها در مراحل اولیه (Khoshro, IntechOpen 2023). کاربردهای شاخص: انتقال SUB1A به برنج (نمونه واقعی و موفق)، انتقال ژنهای مقاومت به زنگ گندم (Lr34/Sr2)، و بهبود کیفیت دانه. مزیت: صرفهجویی در زمان و هزینه آزمونهای فنوتیپی.

### ۴-۲. انتخاب ژنومی (Genomic Selection — GS)

با دادههای ژنوتیپ گسترده (SNP) و فنوتیپ از جمعیت آموزشی، ارزش اصلاحی ژنوتیپها پیشبینی میشود و چرخه گزینش کوتاه میشود. GS در گندم برای مقاومت به فوزاریوم (FHB) برتری معناداری نشان داده (Nannuru et al., Mol Breeding 2025) و ترکیب GS با سرعتبخشی نسلها بهعنوان «Speed GS» معرفی شده است (Sinha et al., 2023, PMC؛ Ćeran et al., Frontiers 2024).

### ۴-۳. ویرایش ژنوم CRISPR/Cas9

- **گوجهفرنگی:** جهشزایی در ژن MLO مقاومت به سفیدک پودری (Powdery Mildew) ایجاد کرده است؛ همچنین جهش در MAPK3 مقاومت به بوتریتیس (کپک خاکستری) القا کرده (Tyagi et al., 2020, PMC؛ Wan et al., MDPI 2021). گوجه ادیتشده با محتوای GABA بالا (رقم تجاری Sicilian Rouge) از موفقیتهای تجاری است.
- **ذرت:** ناکاوت ژن Wx1 توسط Corteva (DuPont) برای تولید ذرت مومی (Waxy Corn) با آمیلوپکتین بالا برای صنعت نشاسته (DigiComply).
- **گندم:** ویرایش MLO برای مقاومت به سفیدک پودری؛ ویرایش ژنوم هگزاپلوئید با CRISPR کاربرد دارد.
- **برنج:** ویرایش ژنهای خفته (waxy) برای برنج چسبناک و بهبود کیفیت.

### ۴-۴. سرعتبخشی نسلها (Speed Breeding)

کشت در گلخانه با نور ۲۲ ساعت روشنایی/۲ ساعت تاریکی و کنترل دما، دوره نسل گندم و جو را کوتاه میکند: **۴ تا ۶ نسل در سال** (در برابر ۱–۲ نسل در مزرعه) (ILRI؛ SeedWorld). برداشت بذر ۱۵–۲۰ روز پس از گلدهی و جوانهزنی سریع، چرخه را بیشتر کوتاه میکند؛ تا ۶ نسل در ۱۷ ماه گزارش شده (CBGG/Hapres؛ Samantara et al., 2022, PMC).

### ۴-۵. فنوتایپینگ با پهپاد (UAV High-Throughput Phenotyping)

پهپادهای مجهز به دوربین RGB، چندطیفی (Multispectral) و حرارتی، صفاتی مانند ارتفاع بوته، زیستتوده، شاخص سطح برگ، پوشش تاج و تنش رطوبتی را در مقیاس کرتهای اصلاحی اندازهگیری میکنند (ICRISAT؛ Volpato et al., Frontiers 2021 — تخمین ارتفاع گندم؛ Alves et al., Sci Rep 2024 — سویا). این دادهها ورودی مستقیم مدلهای GS و انتخاب G×E هستند.

### ۴-۶. بیوفورتیفیکاسیون (Biofortification)

- **برنج طلایی (Golden Rice):** برنج تراریخته حاوی ژنهای مسیر بیوسنتز بتاکاروتن (psy از نرگس و crtI از باکتری)؛ رنگ طلایی دانه نشانگر غلظت بتاکاروتن است (GoldenRice.org). در فیلیپین با نام **Malusog Rice** برای مقابله با کمبود ویتامین A ثبت شده (PMC 2026).
- دیگر موارد: لوبیا و نخود غنی از آهن/روی (HarvestPlus)، گندم غنی از روی.

### ۴-۷. گیاهان فراموششده و خوشآتیه (Orphan & Underutilized Crops)

- **تِف (Eragrostis tef):** غله ریزدان اتیوپی، بدون گلوتن، مقاوم به خشکی و غرقاب.
- **ارزنها (Millet):** C4، کارایی آب بالا، مقاوم به گرما و خاک فقیر؛ ارزن مرواریدی و انگشتی.
- **سورگوم:** غله C4 با ریشه عمیق و تحمل خشکی/گرما؛ علوفه و دانه.
- **آمارانت (تاجخروس):** دانه و برگ مغذی (پروتئین بالا، آهن و منیزیم) — (Glatzel et al., ZEF Working Paper؛ IFPRI Blog).
- این گیاهان «یتیم» پژوهش کمی دریافت کردهاند اما برای تابآوری اقلیمی حیاتیاند (Tadele, 2018, PMC؛ Ndlovu et al., Frontiers 2024). برای اکو نوژین، ترویج این گیاهان در اراضی حاشیهای فرصت اقتصادی و زیستمحیطی است.

---

## بخش ۵: سامانههای زراعی تابآور

- **تنوعبخشی (Diversification):** کشت چند محصول با فنولوژی متفاوت، ریسک شکست کامل را کاهش میدهد و سلامت خاک را بهبود میبخشد.
- **کشت مخلوط (Intercropping):** همزیستی حبوبات (تثبیت نیتروژن) با غلات؛ استفاده بهتر از نور، آب و عناصر؛ کاهش آفات.
- **آگروفارستری (Agroforestry):** ترکیب درختان با زراعت/دامپروری؛ ریشه عمیق درختان آب لایههای عمیق را بالا میکشد، برگریز مواد آلی میافزاید و بادشکن فرسایش بادی را کاهش میدهد.
- **کشاورزی حفاظتی (Conservation Agriculture — CA):** سه اصل: (۱) اختلال حداقلی خاک (کشت مستقیم/No-till)، (۲) پوشش دایمی خاک با بقایا یا گیاهان پوششی، (۳) تناوب و تنوع (Cornell CA). نتایج: کاهش تلفات خاک تا ۸۶٪ در سیستمهای کشت مستقیم با گیاه پوششی (Jacobs et al., 2022)، کاهش ۹۹٪ رسوب در برخی مزارع و صرفهجویی ۷۲ دلار در هکتار در هزینه کار و ماشینآلات (EESI)؛ کاهش سوخت و نیروی کار و حفاظت خاک در برابر گرما و تبخیر (USDA Climate Hubs).
- **بذرکاری مستقیم (Direct Seeding):** کاشت بدون شخم؛ حفظ ساختمان خاک، افزایش ماده آلی و نفوذپذیری، و کاهش تبخیر سطحی — مکمل طبیعی سازههای آبخیز بالادست.

---

## پیادهسازی در HyDroMa

بر اساس این پژوهش، دو ماژول جدید (و سه خدمت پشتیبان) برای موتور علمی HyDroMa پیشنهاد میشود:

### ماژول A: طراحی خودکار سازههای آبخیز (Auto-Structure Designer)
**ورودی:** DEM (مدل ارتفاعی)، نقشه خاک (گروه هیدرولوژیک A–D)، کاربری اراضی، سری بارش، منحنیهای IDF، قیمتهای محلی مصالح.
**پردازش:**
1. استخراج شبکه آبراهه و مرتبهبندی (Strahler)؛ شناسایی نقاط بحرانی فرسایش (خندقها، سرشاخهها).
2. برآورد دبی اوج با روش Rational برای حوزههای کوچک و SCS-CN برای حوزههای بزرگتر (با محاسبه CN از نقشه خاک/کاربری و Ia=0.2S).
3. انتخاب نوع سازه بر اساس قواعد تصمیم (شیب، مرتبه آبراهه، دسترسی، بودجه): سنگچین ← گابیون ← بتن.
4. ابعاددهی: ارتفاع، عرض تاج، سرریز، فاصله بین سازهها (H/S) و حجم حوضچه نفوذ.
5. برآورد هزینه با توابع پارامتری (حجم × نرخ واحد + دسترسی + نگهداری).
**خروجی:** نقشه جایابی سازهها، فایل طراحی (لوح و مشخصات)، برآورد هزینه، و اولویتبندی اقتصادی (کاهش رسوب به ازای هر دلار هزینه).

### ماژول B: توصیهگر رقم مقاوم (Resilient Cultivar Recommender)
**ورودی:** اقلیم (بارش، دما، خشکی انتهایی)، ویژگی خاک (شوری EC، بافت، عمق)، نوع تنش غالب (خشکی/شوری/غرقاب)، اهداف کشاورز (غلات، علوفه، باغ).
**پردازش:**
1. پایگاه داده صفات ارقام (مشتمل بر: ارقام ایرانی متحمل مانند کویر، آرگ، بم، چمران و نصرت؛ SUB1 برای برنج؛ هالوفیتها مانند کینوا و سالیکورنیا؛ گیاهان فراموششده مانند ارزن، سورگوم، تِف و آمارانت).
2. تطبیق نیاز اقلیمی-خاکی هر رقم با شرایط مزرعه (مدل G×E سادهشده با شاخصهای تحمل خشکی مانند STI/SSI).
3. خروجی: فهرست رتبهبندیشده ارقام با ریسک عملکرد، توصیههای کاشت (تاریخ، تراکم) و نیاز آبی (بر پایه CROPWAT-type محاسبه).
4. در صورت دادههای ژنوتیپی: پیشنهاد والدین برای برنامه MAS/GS و ارجاع به صفات نشانگری.

### خدمات پشتیبان
- **ماژول پایش با پهپاد:** ادغام خط لوله فنوتایپینگ UAV (RGB/چندطیفی/حرارتی) برای پایش سلامت کشت و کارایی سازهها (پایش رسوبگیری بندها).
- **داشبورد LID شهری:** جایابی بهینه BMPها در مناطق شهری با منطق نزدیک به منبع تولید رواناب.
- **ارزیابی تابآوری سامانه زراعی:** امتیازدهی به تنوع، کشت مخلوط، آگروفارستری و کشاورزی حفاظتی در هر قطعه و توصیه بهبود.

---

## جمعبندی

مهندسی آبخیزداری و اصلاحنبات دو بازوی مکمل «کشاورزی مقاوم» هستند: سازهها آب را در منظر نگه میدارند و ارقام مقاوم، آب موجود را به محصول تبدیل میکنند. ترکیب روشهای کلاسیک (Rational/SCS-CN، بندهای اصلاحی، تراس، میکروکچمنت) با فناوریهای نوین (MAS، GS، CRISPR، سرعتبخشی نسل، فنوتایپینگ پهپادی) و گیاهان فراموششده، هسته علمی پلتفرم اکو نوژین را میسازد. پیشنهاد این گزارش، پیادهسازی ماژولهای A و B در HyDroMa بهعنوان گام نخست یکپارچهسازی «مهندسی سازهای» و «مهندسی ژنتیک» در یک سامانه تصمیمیار واحد است.

---

## فهرست منابع (فقط منابع جستجوشده)

**سازهها و آبخیزداری:**
- Gabion Supply — Gabion Rock Check Dams: https://gabionsupply.com/check-dams/
- Minnesota Stormwater — Check Dams for Stormwater Swales: https://stormwater.pca.state.mn.us/check_dams_for_stormwater_swales
- LID SWM Planning & Design Guide — Check Dams: https://wiki.sustainabletechnologies.ca/wiki/Check_dams
- Santa Cruz Permaculture — Brush Check Dams and Gabions: https://santacruzpermaculture.com/2021/01/brush-check-dams-gabions/
- Akvopedia — Contour Trenches: https://akvopedia.org/s_wiki/index.php?title=Water_Portal_/_Rainwater_Harvesting_/_Groundwater_recharge_/_Contour_trenches&mobileaction=toggle_view_mobile
- UNCCD — Microcatchment Rainwater Harvesting: https://www.unccd.int/land-and-life/sds/toolbox/microcatchment-rainwater-harvesting
- FAO — Water Harvesting Manual (AGL/MISC/17/91): https://www.fao.org/4/u3160e/u3160e00.htm
- FAO Manual (نسخه آنلاین مثال محاسبه نگاریم): https://dokumen.pub/a-manual-for-the-design-and-construction-of-water-harvesting-schemes-for-plant-production.html
- NRCS — Terrace Conservation Practice Standard (Code 600): https://efotg.sc.egov.usda.gov/api/CPSFile/31209/600_IL_CPS_Terrace_2021
- Nebraska Extension — Terrace Systems (G85-750): https://digitalcommons.unl.edu/cgi/viewcontent.cgi?article=2340&context=extensionhist
- Arizona Water Resources — Basic Components of Rainwater Storage System: https://wrrc.arizona.edu/sites/default/files/cals%20extension_basic%20components%20of%20a%20rainwater%20storage%20system.pdf
- LID SWM Guide — Rainwater Harvesting: https://wiki.sustainabletechnologies.ca/wiki/Rainwater_harvesting
- NGWA — Principles of Induced Infiltration and Artificial Recharge: https://www.ngwa.org/what-is-groundwater/About-groundwater/principles-of-induced-infiltration-and-artificial-recharge
- EPA NEPIS — Introduction to Artificial Ground Water Recharge: https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=94008KN2.TXT
- IRC/SamSamWater — Small Community Water Supplies: Artificial Recharge (TP40): https://www.samsamwater.com/library/TP40_6_Artificial_recharge.pdf
- Purdue Extension — Urban BMP & LID Practices: https://www.purdue.edu/fnr/extension/urban-best-management-low-impact-development-practices/
- NVCOG — Low Impact Development and Green Infrastructure: https://nvcogct.gov/what-we-do/environment/low-impact-development-and-green-infrastructure/
- Shitaimesh — Average Gabion Price 2026: https://www.shitaimesh.com/average-gabion-price-2026-cost-factors-materials-installation
- IJC MAS — Low Cost Water Harvesting Structures: https://www.ijcmas.com/abstractview.php?ID=20603&vol=9-12-2020&SNo=209

**هیدرولوژی و طراحی:**
- HEC-RAS — Curve Number: https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.4/overview-of-optional-capabilities/modeling-precipitation-and-infiltration/curve-number
- HEC-HMS — SCS Curve Number Loss Model: https://www.hec.usace.army.mil/confluence/hmsdocs/hmstrm/canopy-surface-infiltration-and-runoff-volume/infiltration/scs-curve-number-loss-model
- Bentley — SCS CN Runoff Equation: https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-4E2888B811474420B02E365FE819BEAB.html
- Wageningen UR — The Curve Number Method (Lecture Notes): https://edepot.wur.nl/183157
- Wikipedia — Runoff Curve Number: https://en.wikipedia.org/wiki/Runoff_curve_number

**کشتهای مقاوم:**
- Zhang et al. — Quinoa as a naturally stress-resistant crop (PMC, 2026): https://pmc.ncbi.nlm.nih.gov/articles/PMC12886619/
- Fanack Water — Salt-Tolerant Crops MENA (ICBA): https://water.fanack.com/salt-tolerant-crops-mena/
- Resilience.org — A Crop for a Saltier Future (Salicornia): https://www.resilience.org/stories/2025-01-29/a-crop-for-a-saltier-future/
- Sallam et al. — Drought Stress Tolerance in Wheat and Barley (PMC, 2019): https://pmc.ncbi.nlm.nih.gov/articles/PMC6651786/
- GRDC — Screening wheat and barley for salt tolerance: https://grdc.com.au/research/reports/report?id=1462
- Birjand Univ. — Salinity Stress Tolerance in Barley: https://escs.birjand.ac.ir/article_2728.html?lang=en
- ResearchGate — Iranian barley cultivars drought tolerance (Nosrat): https://www.researchgate.net/publication/307723458_Evaluation_of_drought_tolerance_indices_for_the_selection_of_Iranian_barley_Hordeum_vulgare_cultivars
- Poustini & Heidari — Ion distribution in wheat cultivars under salinity (Kharchia): https://www.sciencedirect.com/science/article/abs/pii/S0378429003001576
- Sardouie-Nasab et al. — Field Screening of Salinity Tolerance in Iranian Bread Wheat (Crop Science, 2014): https://acsess.onlinelibrary.wiley.com/doi/full/10.2135/cropsci2013.06.0359
- Emerick et al. — Sub1 Rice: Engineering Rice for Climate Change (PMC, 2019): https://pmc.ncbi.nlm.nih.gov/articles/PMC6886445/
- Poverty Action Lab — Flood-Tolerant Rice in India (Swarna-Sub1): https://www.povertyactionlab.org/evaluation/reducing-farmers-risk-through-flood-tolerant-rice-india
- Raghu et al. — Adoption and impact of Swarna-Sub1 (ScienceDirect, 2022): https://www.sciencedirect.com/science/article/pii/S2667010022000403

**اصلاحنبات:**
- Khoshro — Application of MAS in Wheat Quality (IntechOpen, 2023): https://www.intechopen.com/chapters/88742
- Sinha et al. — Integrated Genomic Selection (PMC, 2023): https://pmc.ncbi.nlm.nih.gov/articles/PMC10380062/
- Nannuru et al. — Genomic selection and speed breeding for wheat FHB (Springer, 2025): https://link.springer.com/article/10.1007/s11032-024-01527-z
- Ćeran et al. — Genomics-assisted speed breeding (Frontiers, 2024): https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1383302/full
- Tyagi et al. — Engineering disease resistant plants through CRISPR-Cas9 (PMC, 2020): https://pmc.ncbi.nlm.nih.gov/articles/PMC7583490/
- Wan et al. — CRISPR-Cas9 Gene Editing for Fruit and Vegetable Crops (MDPI, 2021): https://www.mdpi.com/2311-7524/7/7/193
- DigiComply — CRISPR Products on the Shelf (waxy corn Wx1/Corteva): https://www.digicomply.com/blog/crispr-products-on-the-shelf
- ILRI — Speed Breeding: https://www.ilri.org/news/speed-breeding-promising-approach-crop-breeding
- CBGG/Hapres — The Imperative of Speed Breeding Technology (Pasala et al., 2024): https://cbgg.hapres.com/htmls/CBGG_1610_Detail.html
- Samantara et al. — Breeding More Crops in Less Time: Speed Breeding (PMC, 2022): https://pmc.ncbi.nlm.nih.gov/articles/PMC8869642/
- Alves et al. — HTP in soybean breeding using UAVs (Scientific Reports, 2024): https://www.nature.com/articles/s41598-024-83807-4
- Volpato et al. — UAV High Throughput Field Phenotyping for Plant Height (PMC, 2021): https://pmc.ncbi.nlm.nih.gov/articles/PMC7921806/
- ICRISAT — Applications of UAVs: Image-Based Plant Phenotyping: https://oar.icrisat.org/12492/
- Golden Rice Information Centre: https://www.goldenrice.org/Content4-Info/info.php
- PMC — Pilot deployment of beta carotene-enriched rice (Malusog Rice, 2026): https://pmc.ncbi.nlm.nih.gov/articles/PMC13328446/
- Tadele — African Orphan Crops under Abiotic Stresses (PMC, 2018): https://pmc.ncbi.nlm.nih.gov/articles/PMC5829434/
- Ndlovu et al. — Underutilized crops for resilient agri-food systems (Frontiers, 2024): https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1498402/full
- IFPRI — Bringing back neglected crops: https://www.ifpri.org/blog/bringing-back-neglected-crops-food-and-climate-solution-africa/

**سامانههای زراعی:**
- Cornell — Conservation Agriculture Advantages: http://conservationagriculture.mannlib.cornell.edu/pages/aboutca/advantages.html
- EESI — No-Till Farming Improves Soil Health: https://www.eesi.org/articles/view/no-till-farming-improves-soil-health-and-mitigates-climate-change
- Jacobs et al. — Cover crops and no-tillage reduce soil loss (Soil & Tillage Research, 2022): https://www.sciencedirect.com/science/article/abs/pii/S0167198721003834
- USDA Climate Hubs — Northwest No-Till Farming for Climate Resilience: https://www.climatehubs.usda.gov/hubs/northwest/topic/northwest-no-till-farming-climate-resilience
