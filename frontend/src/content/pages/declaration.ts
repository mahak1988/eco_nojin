/** Declaration page content — the official statement, published verbatim
 * (fa) with a faithful EN translation. Legal articles (ماده ۱-۵) live in
 * /terms and /rules per report 64; the narrative lives here. */

export interface DeclarationSection {
  heading: string;
  paragraphs: string[];
  bullets?: string[];
}

export interface DeclarationContent {
  kicker: string;
  title: string;
  lead: string;
  version: string;
  updated: string;
  legalNote: string;
  refsNote: string;
  sections: DeclarationSection[];
  signoff: string[];
}

export const declaration = {
  fa: {
    kicker: 'بیانیهٔ رسمی',
    title: 'بیانیهٔ رسمی شرکت کشت و صنعت دشت امید نارون / اکو نوژین',
    lead: 'نسخهٔ توسعه‌یافته، حقوقی و روان‌شناختی — روایت گذار از ناامیدی به امید، از تخریب به احیا.',
    version: 'v1.1',
    updated: 'مهر ۱۴۰۵ (۲۰۲۶)',
    legalNote:
      'این بیانیه سند روایی و ارزشی است؛ چارچوب حقوقی الزام‌آور (تعاریف، تعهدات، مسئولیت کاربران و حل اختلاف) در شرایط استفاده و قوانین و مقررات منتشر و به‌روز می‌شود.',
    refsNote:
      'ارجاع‌های آماری این بیانیه به گزارش‌های UNCCD (۲۰۲۴)، IPCC و بانک جهانی است؛ جزئیات و لینک گزارش‌ها در صفحهٔ شفافیت تکمیل می‌شود.',
    sections: [
      {
        heading: 'مقدمه: از دلِ خاکِ تشنه تا افقِ سبزِ امید',
        paragraphs: [
          'شرکت کشت و صنعت دشت امید نارون، برخاسته از آرمانِ دیرینِ مردمان این سرزمین است؛ آرمانِ آبادانی، باروری زمین و پاسداری از میراثِ هزاران ساله کشاورزی. ما، همچون دیگر بنگاه‌های کشاورزی و صنایع تبدیلی، با انگیزه تولید محصولات متنوع، ایجاد زنجیره ارزش در صنعت غذا، اشتغال‌زایی پایدار، توسعه روستایی، تأمین امنیت غذایی و صیانت از منابع طبیعی شکل گرفتیم. اما مسیر ما، مسیری نبود که در طرح‌های توجیهی اولیه ترسیم شده بود؛ مسیر ما از دلِ بحرانی گذشت که سایه‌اش امروز بر سرتاسر کره زمین سنگینی می‌کند.',
          'ما با حقیقتی تلخ روبه‌رو شدیم: زمین، دیگر آن زمینِ مادرِ بخشنده نبود. خاک، دیگر خاکِ زنده نبود. آسمان، دیگر بارانِ رحمت نمی‌بارید. و انسان، در میانه این ویرانی، سرگردان میان گذشته‌ای پرافتخار و آینده‌ای مبهم ایستاده بود.',
          'این بیانیه، روایتِ ماست؛ روایتِ گذار از ناامیدی به امید، از تخریب به احیا، و از انفعال به کنش. این بیانیه، دعوتنامه‌ای است به همه انسان‌هایی که زمین را خانه خود می‌دانند و نمی‌خواهند شاهدِ خاموشیِ تمدن در بسترِ بیابان‌های پیشرو باشند.',
        ],
      },
      {
        heading: 'بخش اول: زمینه تاریخی و مسئله — وقتی زمین قوت خود را از دست می‌دهد',
        paragraphs: [
          'با رایزنی‌ها و ارائه طرح‌های توجیهی فنی و اقتصادی برای واگذاری زمین به منظور زراعت و باغات، سال‌ها برنامه‌ریزی کردیم؛ اما با نخستین پرسش بنیادین مواجه شدیم: کدام زمین مرغوب؟ کدام آب؟ کدام بارش و نزولات آسمانی؟',
          'هر جا برای بازدید می‌رفتیم، زمین بود اما خاک نبود؛ خاک بود اما خاکِ مرده بود؛ حاصلخیزی از میان رفته بود و آبی در دسترس نبود. زمین قوت خود را از دست داده بود و آسمان با ما قهر کرده بود. واژه‌های تغییر اقلیم، خشکسالی، فرسایش خاک، فرونشست زمین و مهاجرت اقلیمی، دیگر واژه‌هایی انتزاعی در گزارش‌های بین‌المللی نبودند؛ آن‌ها به واقعیتِ روزمره زندگی مردم تبدیل شده بودند.',
          'کنوانسیون مبارزه با بیابان‌زایی ملل متحد (UNCCD) هشدار داده است که بیش از نیمی از مراتع جهان تخریب شده‌اند و امنیت غذایی یک‌ششم بشریت در خطر است. هیئت بین‌دولتی تغییر اقلیم (IPCC) اعلام کرده است که در صورت تداوم روند کنونی، میلیاردها نفر تا سال ۲۰۵۰ با کمبود شدید آب مواجه خواهند شد. این آمارها، برای ما فقط اعداد نیستند؛ آن‌ها چهره روستاییانی هستند که زمین‌هایشان را ترک کرده‌اند، چهره جوانانی که آینده خود را در مهاجرت جست‌وجو می‌کنند، و چهره زنانی که بارِ سنگینِ معیشتِ ازدست‌رفته را بر دوش می‌کشند.',
          'در حافظه تاریخی ما، خشکسالی همیشه حضوری مرگبار داشته است. از نیایش کوروش بزرگ که از پروردگار می‌خواست سرزمینش را از خشکسالی، دروغ و دشمن مصون دارد، تا روایت‌های مکتوب در متون کهن، همگی گواهی می‌دهند که خشکسالی، دشمنِ تمدن بوده و هست. اما امروز، این دشمن تنها یک پدیده طبیعی نیست؛ این دشمن، نتیجه انتخاب‌های نادرست ماست: مصرف بی‌رویه آب، مدیریت ناپایدار زمین، و بی‌توجهی به ظرفیت‌های اکولوژیک.',
        ],
      },
      {
        heading: 'بخش دوم: از شکست تا آموختن — روان‌شناسی یک بحران و عبور از آن',
        paragraphs: [
          'وقتی با این غول بی‌شاخ و دم مواجه شدیم، از فاز پیمانکاری صرف، کشاورزی متکی بر حفر چاه‌های بی‌رویه و انتقال بین‌حوضه‌ای آب — که عواقب هولناکی چون فرونشست زمین و تخریب اکوسیستم دارد — فاصله گرفتیم. ما در روستاها فقط می‌شنیدیم: آمدند و رفتند؛ شکست خوردند و امید را از ما گرفتند و رفتند؛ و ما ماندیم با بیکاری، گردوغبار و معیشت ازدست‌رفته.',
          'این جمله، تنها یک شکایت روستایی نیست؛ این بیانِ یک زخم جمعی است. زخمِ بی‌اعتمادی به طرح‌هایی که از بیرون می‌آیند، زخمِ احساس رها شدن، زخمِ از دست دادنِ هویت تولیدکنندگی و تبدیل شدن به مصرف‌کننده‌ای وابسته و بی‌ریشه. ما دریافتیم که هر راه‌حلی که به این زخم‌ها بی‌توجه باشد، محکوم به شکست است. بنابراین، پیش از آنکه به دنبال راه‌حل فنی باشیم، باید به دنبال التیامِ روانی و بازسازی اعتماد می‌گشتیم.',
          'به کشاورز می‌گوییم محصول ارگانیک تولید کن؛ می‌گوید کدام گواهی و کدام صبر؟ به جوان می‌گوییم درخت بکار؛ می‌گوید کدام سرمایه و انگیزه؟ این پرسش‌ها برحق‌اند. آن‌ها نشانه‌ی ناامیدی نیستند؛ نشانه‌ی نیاز به انگیزه واقعی، نیاز به احترام، و نیاز به سهم عادلانه از توسعه هستند.',
          'ما بر آن شدیم از نیاکان خود بیاموزیم؛ از قنات‌هایی که هزاران سال نبض تمدن را در دل کویر زنده نگه داشتند؛ از نظام‌های بهره‌برداری عادلانه از آب؛ و از احترامی که نیاکان ما برای زمین قائل بودند. پس از سال‌ها مطالعه، پژوهش و شبیه‌سازی، به این نتیجه رسیدیم که می‌توان با مدیریت هوشمند آب و زمین، طبیعت را زنده کرد. این‌گونه به فلسفه «هیدروما نوژین» دست یافتیم: آب، زندگی، و نو شدن. و اکنون «اکو نوژین» را برای همه مردم آفریده‌ایم — بستری دیجیتال و مردمی که در آن، هر فرد می‌تواند سهمی در احیای زمین داشته باشد.',
        ],
      },
      {
        heading: 'بخش سوم: راه‌حل — احیای اکوسیستم و اقتصاد کربن',
        paragraphs: [
          'ما در چالش‌های جهانی سهمی ایفا می‌کنیم؛ سهم ما احیای مناظر خشک و نیمه‌خشک است. این سهم، نه از سرِ تفنن، بلکه از سرِ ضرورت است. ضرورتی که از دلِ واقعیت‌های اقلیمی و اجتماعی بیرون آمده است.',
          'شنیدیم و خواندیم که در کشورهای پیشرو، اعتباراتی به نام اعتبارات کربن برای ترسیب کربن پرداخت می‌شود. اما آیا به شهروند سومالیایی، ایرانی، عراقی یا یمنی اعتباری پرداخت می‌شود؟ خیر؛ زیرا نه گواهی صادر می‌شود، نه راستی‌آزمایی ممکن است و نه سازوکاری برای پرداخت وجود دارد. بنابراین، اعتبار کربن در جهانِ ما، به کالایی تبدیل شده که تنها برای عده‌ای معدود قابل دسترس است. این بی‌عدالتی اقلیمی را باید پایان داد.',
          'ما بر آن شدیم خود دست به ابتکار بزنیم و با حمایت شما مردم در سراسر جهان، اعتباری تنظیم و ثبت کنیم که بدون مصرف انرژی، صرفاً با احیای اکوسیستم، زمین زخمی و آسمان نابسامان، به احیای زندگی ما کمک کند. این اعتبار «اکو کوین» نام دارد.',
          'اکو کوین، اعتبار کربنی است که با کمک شما تولید می‌شود، در حساب شما ذخیره می‌شود و با حمایت شما می‌توانیم آن را فهرست و عرضه کنیم، بدون واسطه، بی‌آنکه هزینه‌ای برای ضرب آن بپردازید — تنها با احیای اکوسیستم و نجات زمین، یعنی نجات زندگی.',
        ],
      },
      {
        heading: 'بخش چهارم: شفافیت و دانش — پشتوانهٔ علمی امید',
        paragraphs: [
          'امیدِ بی‌پشتوانه، تبلیغ است؛ امیدِ باپشتوانه، پیمان. ما در اکو نوژین پیمان بسته‌ایم که هیچ ادعایی را بدون ابزار سنجش بر زبان نیاوریم؛ از همین رو، پیش از آنکه از شما بخواهیم باور کنیم، ابزارِ دیدن و اندازه‌گیری را ساخته‌ایم.',
          'موتور علمی «هیدروما» را برای همین آفریدیم: به‌جای حدس و گمان، فیزیک زمین را محاسبه کند. ریچاردز می‌داند آب در خاکِ خاموش چه می‌کند؛ سنت‌ونان مسیر سیلاب را پیش‌بینی می‌کند؛ FAO-56 تشنگی گیاه را می‌فهمد؛ روسل و SWAT مرز فرسایش را می‌کشند و روت‌سی گنجِ کربنِ خاک را می‌شمارد. هر عدد در این زنجیره قابل بازبینی است و هیچ‌چیز در تاریکی نمی‌ماند.',
          'اما محاسبه، بی‌چشمِ ناظر ناتمام است. چشم ماهواره‌های سنتینلِ کوپرنیکوس هر چند روز یک‌بار زمین را می‌بیند و ما از نگاه او، پوشش گیاهی، آب و خاک را با شاخص‌هایی چون NDVI و NBR پایش می‌کنیم؛ و دستِ کشاورز، با ثبت‌های سادهٔ میدانی (کوبو)، آن نگاه آسمانی را به خاکِ واقعیت گره می‌زند.',
          'هر پروژهٔ احیا، مختصات دارد؛ هر گزارش، تاریخ؛ و هر ادعا، سند. نتایج گام‌به‌گام در صفحهٔ شفافیت منتشر می‌شود و مسیر اعتبار کربن — از اندازه‌گیری تا ثبت بر بستر بلاکچین — برای هر شهروندی قابل دنبال‌کردن است. فردا که استانداردهای بین‌المللی (ISO 14064-2 و اصول ICVCM) را پشت‌سر گذاشتیم، اعتبارهایمان را به داورِ مستقل نیز می‌سپاریم؛ چراکه اعتمادِ تو، سرمایه‌ای است که با زور به دست نمی‌آید.',
          'و این، راز پیوند بخش پیشین با بخش آینده است: امید ما نه از جنس ایمانِ کور، که از جنس مشاهدهٔ تکرارشونده است. جایی که آب به خاک برگردد، خاک نفس می‌کشد؛ جایی که خاک نفس بکشد، گیاه می‌ایستد؛ و جایی که گیاه بایستد، انسان دوباره برمی‌خیزد. ما این حلقه را هر روز می‌بینیم — و از همین‌روست که با اطمینان از «امید» سخن می‌گوییم.',
        ],
      },
      {
        heading: 'بخش پنجم: روان‌شناسی امید — چرا باید باور کنیم که می‌شود؟',
        paragraphs: [
          'ما در میانه تاریک‌ترین سناریوهای اقلیمی، از «امید» سخن می‌گوییم. اما این امید، امیدی ساده‌لوحانه نیست؛ این امید، برخواسته از دانش، تجربه و اراده جمعی است.',
          'زمین، بارها در تاریخ خود، زخم خورده و باز زنده شده است. قنات‌های خشک، اگر دوباره آب بگیرند، جاری می‌شوند. خاک‌های فرسوده، اگر با گیاهان بومی تثبیت شوند، دوباره نفس می‌کشند. انسان‌هایی که حس کنند دیده می‌شوند، سهم دارند و آینده‌ای برایشان متصور است، دوباره برمی‌خیزند.',
          'ما در اکو نوژین، به دنبال بازگرداندن معنا به زندگی کشاورزانی هستیم که سال‌هاست خود را شکست‌خورده می‌دانند. به دنبال بازگرداندن عزت نفس به جوانانی هستیم که تصور می‌کنند آینده‌شان تنها در مهاجرت است. به دنبال بازگرداندن سهم زنان از توسعه هستیم؛ زنانی که همواره ستون‌های پنهان خانواده و زمین بوده‌اند.',
          'این یک پروژه فنی نیست؛ این یک جنبش اجتماعی برای التیام روانی و اکولوژیک است. جنبشی که در آن، هر درخت کاشته‌شده، فقط یک درخت نیست؛ یک «باور» است. هر اکو کوین، فقط یک اعتبار مالی نیست؛ یک «گواهی امید» است.',
        ],
      },
      {
        heading: 'بخش ششم: دعوت نهایی — به سوی قراردادی نو با زمین',
        paragraphs: [
          'ما، شرکت کشت و صنعت دشت امید نارون و اکو نوژین، از همه انسان‌ها دعوت می‌کنیم تا در این مسیر، سهم خود را ایفا کنند.',
          'زمین، خانه مشترک ماست. ما نمی‌توانیم مرزهای سیاسی را مانع نجات آن کنیم. طوفان گردوغبار، ویزا نمی‌خواهد. خشکسالی، گذرنامه نمی‌طلبد. بحران اقلیمی، دشمن مشترک همه ماست و تنها با همبستگی جهانی می‌توان بر آن غلبه کرد.',
          'ما در اکو نوژین، بر آنیم که قراردادی نو با زمین بنویسیم؛ قراردادی که در آن، انسان دیگر نه اربابِ زمین، بلکه همکارِ زمین است. قراردادی که در آن، هر عمل کوچک، معنایی بزرگ دارد. قراردادی که در آن، نجات زمین، نجات زندگی است.',
        ],
        bullets: [
          'اگر شهروند هستید، می‌توانید با حمایت مالی، مشارکت در پایش، یا حتی آموزش دیگران، بخشی از این جنبش شوید.',
          'اگر سرمایه‌گذار هستید، می‌توانید در پروژه‌های احیا سرمایه‌گذاری کنید و از بازده اقتصادی و اکولوژیک آن بهره‌مند شوید.',
          'اگر نهاد دولتی یا بین‌المللی هستید، می‌توانید با پذیرش اکو کوین به عنوان ابزار رسمی ترسیب کربن، به عدالت اقلیمی کمک کنید.',
          'اگر شرکت آلاینده هستید، می‌توانید با خرید اکو کوین، مسئولیت اجتماعی و محیط زیستی خود را ایفا کنید و ردپای کربنی خود را جبران نمایید.',
        ],
      },
      {
        heading: 'جمع‌بندی',
        paragraphs: [
          'شرکت کشت و صنعت دشت امید نارون، با راه‌اندازی اکو نوژین و اکو کوین، گامی عملی در مسیر احیای اکوسیستم، عدالت اقلیمی و مشارکت مردمی برداشته است. این بیانیه، هم یک سند حقوقی است و هم یک پیام انسانی؛ هم یک فراخوان اقتصادی است و هم یک التیام روانی. ما از همه می‌خواهیم که با ما همراه شوند، زیرا هیچ کس به تنهایی نمی‌تواند زمین را نجات دهد، اما هر کس می‌تواند سهمی در نجات آن داشته باشد.',
          'با احیای اکوسیستم و نجات زمین، زندگی را نجات دهیم.',
        ],
      },
    ],
    signoff: ['اکو نوژین', 'هیدرومای زندگی', 'شرکت کشت و صنعت دشت امید نارون', 'مهر ۱۴۰۵ (۲۰۲۶)'],
  },
  en: {
    kicker: 'Official declaration',
    title: 'Official declaration of Dasht-e Omid Naroon Agro-Industry Co. / Eco Nojin',
    lead: 'The developed, legal and psychological edition — a narrative of moving from despair to hope, from degradation to restoration.',
    version: 'v1.1',
    updated: 'October 2026 (Mehr 1405)',
    legalNote:
      'This declaration is a narrative and values document; the binding legal framework (definitions, commitments, user responsibilities and dispute resolution) is published and maintained in the Terms of Use and Platform Rules.',
    refsNote:
      'The statistics cited refer to the reports of UNCCD (2024), the IPCC and the World Bank; details and report links are completed on the transparency page.',
    sections: [
      {
        heading: 'Introduction: from thirsty soil to a green horizon of hope',
        paragraphs: [
          'Dasht-e Omid Naroon Agro-Industry Co. rises from the ancient ideal of the people of this land: the ideal of prosperity, fertile soil and stewardship of a thousands-of-years-old agricultural heritage. Like other agricultural enterprises and processing industries, we were founded to produce diverse products, build value chains in the food industry, create sustainable employment, drive rural development, ensure food security and protect natural resources. But our path was not the one drawn in the early feasibility plans; our path passed through a crisis whose shadow today weighs on the whole planet.',
          'We faced a bitter truth: the land was no longer the generous mother-earth. The soil was no longer living soil. The sky no longer poured the rain of mercy. And humanity, amid this destruction, stood suspended between a glorious past and an uncertain future.',
          'This declaration is our narrative: the narrative of moving from despair to hope, from degradation to restoration, and from passivity to action. It is an invitation to every human being who considers the Earth their home and does not want to witness the silencing of civilization in the advancing deserts.',
        ],
      },
      {
        heading: 'Part one: historical context and the problem — when the land loses its strength',
        paragraphs: [
          'Through consultations and technical-economic feasibility plans for land allocation for crops and orchards, we planned for years — and then faced the first fundamental question: which fertile land? Which water? Which rainfall?',
          'Everywhere we went for site visits, there was land but no soil; there was soil but dead soil; fertility was gone and no water was available. The land had lost its strength and the sky was estranged from us. The words climate change, drought, soil erosion, land subsidence and climate migration were no longer abstractions in international reports; they had become the daily reality of people’s lives.',
          'The United Nations Convention to Combat Desertification (UNCCD) has warned that more than half of the world’s rangelands are degraded, endangering the food security of one-sixth of humanity. The Intergovernmental Panel on Climate Change (IPCC) has stated that if the current trend continues, billions of people will face severe water scarcity by 2050. For us, these figures are not just numbers; they are the faces of villagers who left their land, the faces of young people searching for a future in migration, and the faces of women carrying the heavy burden of lost livelihoods.',
          'In our historical memory, drought has always had a deadly presence. From the prayer of Cyrus the Great — asking to shield his land from drought, lies and enemies — to the written accounts in ancient texts, everything testifies that drought has been, and remains, the enemy of civilization. But today, this enemy is not merely a natural phenomenon; it is the result of our wrong choices: excessive water use, unsustainable land management, and disregard for ecological capacities.',
        ],
      },
      {
        heading: 'Part two: from failure to learning — the psychology of a crisis and moving through it',
        paragraphs: [
          'When we faced this nameless giant, we moved away from pure contracting and agriculture reliant on reckless well-drilling and inter-basin water transfer — practices with catastrophic consequences such as land subsidence and ecosystem destruction. In the villages we only heard: “They came and left; they failed, took our hope with them, and left; and we stayed with unemployment, dust and lost livelihoods.”',
          'That sentence is not merely a villager’s complaint; it describes a collective wound. The wound of distrust toward plans that arrive from outside, the wound of feeling abandoned, the wound of losing the identity of being producers and becoming dependent, rootless consumers. We understood that any solution ignoring these wounds is doomed to fail. Therefore, before seeking a technical solution, we had to seek psychological healing and the rebuilding of trust.',
          'We tell the farmer: produce organic products. He asks: which certification, and which patience? We tell the young person: plant trees. He asks: which capital, and which motivation? These questions are legitimate. They are not signs of hopelessness; they are signs of the need for real motivation, for respect, and for a fair share of development.',
          'We chose to learn from our ancestors: from the qanats that kept the pulse of civilization alive in the desert for thousands of years; from fair water-use systems; and from the respect our ancestors held for the land. After years of study, research and simulation, we concluded that with intelligent management of water and land, nature can be brought back to life. Thus we arrived at the philosophy of “HyDroMa Nojin”: water, life, and renewal. And now we have created “Eco Nojin” for all people — a digital, people-powered platform where everyone can have a share in restoring the land.',
        ],
      },
      {
        heading: 'Part three: the solution — ecosystem restoration and the carbon economy',
        paragraphs: [
          'We play our part in the global challenges; our share is restoring dry and semi-dry landscapes. This share comes not from amusement but from necessity — a necessity born of climatic and social realities.',
          'We heard and read that in leading countries, credits called carbon credits are paid for carbon sequestration. But is a credit paid to a citizen of Somalia, Iran, Iraq or Yemen? No — because no certification is issued, verification is impossible, and there is no payment mechanism. Carbon credits, in our world, have become a commodity accessible only to a select few. This climate injustice must end.',
          'We resolved to take the initiative ourselves and, with the support of people across the world, to shape and register a credit that — without consuming energy, purely through ecosystem restoration of wounded land and a troubled sky — helps restore our life. This credit is called “Eco Coin”.',
          'Eco Coin is a carbon credit produced with your help, stored in your account, and with your support we can list and offer it — without middlemen, without paying any cost for minting — purely by restoring ecosystems and saving the land, that is, saving life.',
        ],
      },
      {
        heading: 'Part four: transparency and knowledge — the scientific foundation of hope',
        paragraphs: [
          'Hope without support is advertising; hope with support is a covenant. At Eco Nojin we have pledged not to utter any claim without the tools to measure it. That is why, before asking you to believe, we built the instruments of seeing and measuring.',
          'We created the HyDroMa scientific engine precisely for this: to compute the physics of the land instead of guessing. Richards knows what water does in silent soil; Saint-Venant predicts the path of floods; FAO-56 understands the thirst of the plant; RUSLE and SWAT draw the frontier of erosion; and RothC counts the carbon treasure of the soil. Every number in this chain can be re-examined; nothing remains in the dark.',
          'But calculation is incomplete without an observing eye. The eyes of Copernicus’ Sentinel satellites see the Earth every few days, and from their gaze we monitor vegetation, water and soil with indices such as NDVI and NBR; and the farmer’s hand — through simple field records (KoBo) — ties that heavenly gaze to the soil of reality.',
          'Every restoration project has coordinates; every report has a date; and every claim has a document. Results are published step by step on the transparency page, and the carbon-credit path — from measurement to registration on the blockchain — can be followed by every citizen. Tomorrow, once we have passed the international standards (ISO 14064-2 and the ICVCM Core Carbon Principles), we will also hand our credits to an independent judge; for your trust is a capital that cannot be won by force.',
          'And this is the secret that binds the previous part to the next: our hope is not blind faith, but repeated observation. Where water returns to the soil, the soil breathes; where the soil breathes, the plant stands; and where the plant stands, humanity rises again. We see this circle every day — and that is why we speak of “hope” with confidence.',
        ],
      },
      {
        heading: 'Part five: the psychology of hope — why believe it is possible?',
        paragraphs: [
          'Amid the darkest climate scenarios, we speak of “hope”. But this hope is not naive; it rises from knowledge, experience and collective will.',
          'The Earth has been wounded many times in its history and has come back to life. Dried qanats flow again if watered. Eroded soils breathe again if stabilized with native plants. People who feel seen, who have a share and an imaginable future, rise again.',
          'At Eco Nojin, we seek to restore meaning to the lives of farmers who have considered themselves failures for years. We seek to restore self-respect to young people who imagine their future lies only in migration. We seek to restore women’s share of development — women who have always been the hidden pillars of family and land.',
          'This is not merely a technical project; it is a social movement for psychological and ecological healing. In this movement, every planted tree is not just a tree; it is a “belief”. Every Eco Coin is not just a financial credit; it is a “certificate of hope”.',
        ],
      },
      {
        heading: 'Part six: the final invitation — toward a new covenant with the Earth',
        paragraphs: [
          'We — Dasht-e Omid Naroon Agro-Industry Co. and Eco Nojin — invite all human beings to play their part on this path.',
          'The Earth is our common home. We cannot make political borders an obstacle to saving it. Dust storms need no visa. Drought asks for no passport. The climate crisis is our common enemy, and only global solidarity can overcome it.',
          'At Eco Nojin, we are determined to write a new covenant with the Earth: a covenant in which humanity is no longer the master of the land but its partner. A covenant in which every small act carries great meaning. A covenant in which saving the land is saving life.',
        ],
        bullets: [
          'If you are a citizen, you can join the movement through financial support, participation in monitoring, or even teaching others.',
          'If you are an investor, you can invest in restoration projects and benefit from their economic and ecological returns.',
          'If you are a government or international institution, you can help climate justice by recognizing Eco Coin as an official sequestration instrument.',
          'If you are a polluting company, you can purchase Eco Coins to fulfill your social and environmental responsibility and offset your carbon footprint.',
        ],
      },
      {
        heading: 'Conclusion',
        paragraphs: [
          'Dasht-e Omid Naroon Agro-Industry Co., by launching Eco Nojin and Eco Coin, has taken a practical step toward ecosystem restoration, climate justice and people’s participation. This declaration is both a legal document and a human message; both an economic call and a psychological healing. We ask everyone to join us, because no one can save the land alone — but everyone can have a share in saving it.',
          'By restoring ecosystems and saving the land, let us save life.',
        ],
      },
    ],
    signoff: ['Eco Nojin', 'HyDroMa of Life', 'Dasht-e Omid Naroon Agro-Industry Co.', 'October 2026 (Mehr 1405)'],
  },
} satisfies Record<'fa' | 'en', DeclarationContent>;
