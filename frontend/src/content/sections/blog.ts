import type { SiteContent } from './types';

export interface BlogContent {
  fa: SiteContent['blog'];
  en: SiteContent['blog'];
}

export const blog = {
  fa: {
    kicker: 'بلاگ',
    title: 'یادداشت‌های اکو نوژین',
    lead: 'این بخش تازه متولد شده؛ فعلاً فقط دربارهٔ خودِ پروژه می‌نویسیم و به‌تدریج تکمیلش می‌کنیم.',
    note: 'نسخهٔ نخست بلاگ — یادداشت‌های بعدی: پشت‌صحنهٔ فازهای توسعه، داده و سنجش، و داستان‌های میدانی.',
    posts: [
      {
        category: 'پروژه',
        title: 'چرا اکو نوژین؟',
        date: 'شهریور ۱۴۰۵',
        excerpt:
          'دو و نیم میلیارد کشاورز خرد هنوز به علم کشاورزی دسترسی ندارند؛ اکو نوژین دقیقاً برای همین شکاف ساخته شد.',
        paragraphs: [
          'حدود ۷۰٪ کشاورزان خرد جهان هیچ ابزار دیجیتال کشاورزی ندارند؛ پلتفرم‌های موجود یا گران‌اند یا به گوشی هوشمند و سواد دیجیتال تکیه دارند. نتیجه این است که علمِ داوری‌شده (peer-reviewed) هرگز به مزرعه نمی‌رسد.',
          'اکو نوژین با پنج کانال دسترسی — وب/PWA، USSD، SMS، ربات پیام‌رسان و دستیار صوتی — و چهارده زبان، علم را به هر گوشی و هر سطح سواد می‌رساند؛ آن‌هم نه به‌شکل اطلاعات پراکنده، بلکه به‌شکل نتیجهٔ مدل‌های علمی.',
          'این وب‌سایت دروازهٔ عمومی همین پروژه است: صفحهٔ «پلتفرم» ماژول‌ها را معرفی می‌کند و صفحهٔ «علم هیدروما» موتور محاسباتی را.',
        ],
      },
      {
        category: 'علم',
        title: 'هیدروما: وقتی فیزیک به مزرعه می‌آید',
        date: 'شهریور ۱۴۰۵',
        excerpt:
          'به‌جای تخمین، مدل‌های فیزیکی قطعی؛ نگاهی به این‌که موتور علمی اکو نوژین چگونه کار می‌کند.',
        paragraphs: [
          'هیدروما مدل‌های بنیادی علوم زمین را کنار هم می‌چیند: ریچاردز برای آب در خاک غیراشباع، سنت‌ونان برای جریان سطحی، FAO-56 برای تبخیر-تعرق، روسل و SWAT برای فرسایش و حوزهٔ آبخیز، و روت‌سی برای پویایی کربن خاک.',
          'برای سرعت، بخشی از محاسبات روی هستهٔ عددی C++20 با اتصال pybind11 اجرا می‌شود. داده‌ها از سنتینل-۲، بازتحلیل اقلیمی ERA5 و SoilGrids می‌آیند.',
          'خروجی نهایی «درجهٔ تصمیم» دارد: سناریوها با NSGA-II بهینه و مقایسه می‌شوند و گزارشی تولید می‌شود که می‌توان به آن اعتماد کرد و برای آن پاسخ داشت.',
        ],
      },
      {
        category: 'کربن',
        title: 'کربنی که قابل اثبات است',
        date: 'شهریور ۱۴۰۵',
        excerpt:
          'MRV شفاف، پایش میدانی و ثبت بلاکچینی؛ چرا «اثبات» قلب اقتصاد کربن است.',
        paragraphs: [
          'بازار کربن وقتی اعتماد می‌سازد که هر اعتبار، قابل اندازه‌گیری و راستی‌آزمایی باشد. اکو نوژین پایش ماهواره‌ای را با داده‌های میدانی (فرم‌های KoBo) ترکیب می‌کند تا اندازه‌گیری واقعی شود.',
          'اعتبار کربن با ثبت تأییدشده روی بلاکچین پالیگون ثبت می‌شود و گزارش MRV برای خریداران و نهادهای توسعه شفاف ارائه می‌گردد.',
          'نتیجه برای جامعهٔ محلی روشن است: احیای زمین باید درآمد بسازد — و این درآمد باید قابل اثبات باشد، نه وعده.',
        ],
      },
      {
        category: 'چشم‌انداز',
        title: 'سال ۲۰۵۰: وقتی زمین زیر پای ما خالی می‌شود',
        date: 'مهر ۱۴۰۵',
        excerpt:
          'مرزهای جدید جهان ۲۰۵۰، مرزهای آب و خاک‌اند؛ و ایران در این نقشه، نقطه‌ای پررنگ است — قناری در معدن زغال‌سنگ.',
        paragraphs: [
          'تصور کنید سال ۲۰۵۰ فرارسیده است. از پنجره هواپیما که به زمین نگاه می‌کنید، دیگر آن سیاره آبی و سبز آشنای کتاب‌های جغرافیا را نمی‌بینید. در خاورمیانه، طوفان‌های گردوغبار آسمان را برای هفته‌ها می‌بلعند. در آفریقا، دریاچه چاد به گودالی نمکی تبدیل شده و ماهیگیران دیروز، امروز آوارگانی در حاشیه شهرهای شلوغ‌اند. در جنوب آسیا، رودخانه سند و گنگ در ماه‌های گرم سال به بسترهایی ترک‌خورده بدل می‌شوند و صدها میلیون نفر برای یک لیوان آب آشامیدنی صف می‌کشند. در غرب آمریکا، لاس‌وگاس و فینیکس تابستان‌هایی با دمای بالای ۵۰ درجه را تجربه می‌کنند و شبکه برق زیر بار کولرهای عظیم از نفس می‌افتد. در مدیترانه، آتش‌سوزی‌های جنگلی دیگر «فصل» نمی‌شناسند؛ از یونان تا اسپانیا، روستاها یک‌به‌یک تخلیه می‌شوند.',
          'ایران اما فقط یکی از همین تصویرهاست. تهران، اصفهان، شیراز و مشهد دیگر شهرهایی قابل‌سکونت نیستند. اما این سرنوشتِ تنها ایران نیست؛ این سرنوشتِ کمربند خشک زمین است که از مراکش تا مغولستان کشیده شده و اکنون حالا حالاها می‌خواهد مرزهایش را به اروپا، به چین، به قلب آفریقا و حتی به آمریکای شمالی برساند.',
          'کنوانسیون مبارزه با بیابان‌زایی ملل متحد در گزارش ۲۰۲۴ خود اعلام کرد که ۵۰ درصد از کل مراتع جهان تخریب شده‌اند و این تخریب، ذخیره غذایی یک‌ششم بشریت را به خطر انداخته است. هیئت بین‌دولتی تغییر اقلیم (IPCC) هشدار داده که اگر روند فعلی ادامه یابد، تا سال ۲۰۵۰ بیش از پنج میلیارد نفر با کمبود آب مواجه خواهند شد. بانک جهانی برآورد کرده است که تنها در سه منطقه جنوب صحرای آفریقا، جنوب آسیا و آمریکای لاتین، تا سال ۲۰۵۰ حدود ۲۱۶ میلیون نفر به دلیل تغییرات اقلیمی آواره خواهند شد. این‌ها عدد نیستند؛ این‌ها انسان‌اند.',
        ],
        sections: [
          {
            heading: 'نقشه جهانی خشکیدگی',
            paragraphs: [
              'جهان ۲۰۵۰ دیگر با مرزهای سیاسی تقسیم نمی‌شود؛ مرزهای جدید، مرزهای آب و خاک‌اند. مناطقی که روزگاری انبار غله جهان بودند، اکنون واردکننده غذا شده‌اند. دشت‌های حاصلخیز اوکراین و روسیه درگیر جنگ و خشکسالی‌اند. دشت بزرگ آمریکا با فرسایش خاک و خشکیدن سفره آب زیرزمینی اوگالالا دست‌وپنجه نرم می‌کند. شمال چین، که زمانی «سبد نان» این کشور بود، اکنون با طوفان‌های شن از صحرای گبی مبارزه می‌کند و میلیون‌ها کشاورز به شهرها پناه آورده‌اند.',
              'دریاچه آرال، بزرگ‌ترین فاجعه زیست‌محیطی قرن بیستم، دیگر به یک بیابان نمکی تبدیل شده و طوفان‌های نمک، زمین‌های کشاورزی ازبکستان و قزاقستان را نابارور کرده‌اند. در شرق آفریقا، شاخ آفریقا با بدترین خشکسالی در ۴۰ سال اخیر مواجه است و میلیون‌ها نفر در آستانه قحطی‌اند. در آمریکای جنوبی، آمازون که روزگاری ریه زمین بود، اکنون به نقطه بی‌بازگشت نزدیک شده و خشکیدگی آن، الگوهای بارندگی را در سراسر قاره مختل کرده است.',
              'ایران در این نقشه، نقطه‌ای پررنگ است. کشوری که روزگاری با قنات‌های هزارساله‌اش تمدن را در دل کویر زنده نگه می‌داشت، اکنون با خشکیدن دریاچه ارومیه، هامون و گاوخونی، به کانون تولید گردوغبار تبدیل شده است. اما این فقط یک تراژدی ملی نیست؛ این یک هشدار جهانی است. آنچه در ایران رخ می‌دهد، پیش‌نمایشی از آینده‌ای است که در انتظار بسیاری از مناطق نیمه‌خشک جهان است.',
            ],
          },
          {
            heading: 'بهای انسانی یک سیاره تشنه',
            paragraphs: [
              'در سال ۲۰۵۰، مدارس نه به دلیل جنگ یا بیماری، بلکه به دلیل تعطیلی ناشی از طوفان گردوغبار تعطیل می‌شوند. بیمارستان‌ها مملو از کودکانی است که با ماسک به دنیا آمده‌اند و ریه‌هایشان هرگز هوای پاک را تجربه نکرده‌اند. پروازها لغو می‌شوند، نه به خاطر تحریم یا بحران سیاسی، بلکه به این دلیل که آسمان آن‌قدر تیره است که خلبان نمی‌تواند باند فرود را ببیند.',
              'روستاها خالی از سکنه شده‌اند. کشاورزانی که روزگاری مغرورانه گندم و زعفران و برنج تولید می‌کردند، اکنون در حاشیه کلان‌شهرها در حلبی‌آبادها زندگی می‌کنند. آن‌ها دیگر تولیدکننده نیستند؛ مصرف‌کنندگانی فقیرند که برای یک وعده غذای یارانه‌ای صف می‌کشند. این تصویر از ایران تا مصر، از پاکستان تا مکزیک، از نیجریه تا هند تکرار می‌شود.',
              'خشکسالی فقط یک پدیده اقلیمی نیست؛ یک بمب اجتماعی است. جایی که آب نباشد، غذا نیست. جایی که غذا نباشد، امنیت نیست. جنگ‌های آینده، جنگ بر سر نفت نخواهند بود؛ جنگ بر سر آب خواهند بود. رودخانه نیل، دجله و فرات، سند، گنگ و کلرادو به خطوط مقدم تنش‌های ژئوپلیتیکی تبدیل شده‌اند. در سوریه، خشکسالی طولانی دهه ۲۰۰۰ یکی از جرقه‌های جنگ داخلی بود. در سال ۲۰۵۰، چنین جرقه‌هایی می‌توانند به آتش‌سوزی‌های منطقه‌ای و جهانی بدل شوند.',
            ],
          },
          {
            heading: 'ایران؛ آینه‌ای برای جهان',
            paragraphs: [
              'ایران را می‌توان «قناری در معدن زغال‌سنگ» نامید. کشوری با تمدنی چند هزار ساله، بر روی کمربند خشک زمین، با مدیریت ناپایدار آب، فرسایش خاک، خشکیدن سفره‌های زیرزمینی و مهاجرت اقلیمی دست‌به‌گریبان است. اما همین علائم در سراسر جهان دیده می‌شود. خشکیدن دریاچه ارومیه، همتای خشکیدن دریاچه چاد در آفریقا، دریاچه پوپو در بولیوی، و دریاچه مید در آمریکاست. فرونشست زمین در دشت‌های ایران، شبیه فرونشست در کالیفرنیا، مکزیکوسیتی، جاکارتا و دهلی است.',
              'آنچه ایران را متمایز می‌کند، سرعت فاجعه است. اما این سرعت می‌تواند به هر نقطه دیگری از جهان سرایت کند. اگر جهان امروز به داد ایران نرسد، فردا باید به داد خودش برسد. مرزها نمی‌توانند طوفان گردوغبار را متوقف کنند. دیوارهای مرزی نمی‌توانند جلوی مهاجران اقلیمی را بگیرند. ویروس خشکیدگی، ویزا نمی‌خواهد.',
            ],
          },
          {
            heading: 'این یک پیش‌گویی آخرالزمانی نیست',
            paragraphs: [
              'این یک سناریوی علمی است. سناریویی که بر اساس روندهای فعلی فرسایش خاک، نشست زمین، خشکیدن سفره‌های آب زیرزمینی و مهاجرت‌های اقلیمی، توسط معتبرترین نهادهای بین‌المللی ترسیم شده است. اما سناریو به معنای سرنوشت محتوم نیست. سناریو یعنی «اگر این‌گونه ادامه دهیم، به آنجا می‌رسیم.» و «اگر» یعنی هنوز انتخاب داریم.',
              'راه‌حل‌ها وجود دارند. احیای زمین‌های تخریب‌شده، بازگرداندن آب به تالاب‌ها، کشاورزی احیاگر، مدیریت هوشمند منابع آب، سرمایه‌گذاری در انرژی‌های تجدیدپذیر، و مهم‌تر از همه، همکاری بین‌المللی. هیچ کشوری به تنهایی نمی‌تواند با بحران آب و خاک مقابله کند. همان‌طور که ویروس‌ها مرز نمی‌شناسند، طوفان‌های گردوغبار، خشکسالی و مهاجرت اقلیمی نیز مرز نمی‌شناسند.',
              'جهان ۲۰۵۰ هنوز نوشته نشده است. ما امروز، با انتخاب‌هایمان، آن را می‌نویسیم. آیا می‌خواهیم سیاره‌ای بیابانی را به فرزندانمان تحویل دهیم، یا میراث سبز تمدن‌هایی را که هزاران سال در هماهنگی با طبیعت زیسته‌اند، زنده نگه داریم؟',
              'پاسخ این پرسش را نه در سال ۲۰۵۰، بلکه همین امروز باید داد.',
            ],
          },
        ],
      },
    ],
  },
  en: {
    kicker: 'Blog',
    title: 'Eco Nojin notes',
    lead: 'This section is brand new; for now we only write about the project itself and will expand it over time.',
    note: 'First release — upcoming notes: behind the scenes of development phases, data & measurement, and field stories.',
    posts: [
      {
        category: 'Project',
        title: 'Why Eco Nojin?',
        date: 'September 2026',
        excerpt:
          '2.5 billion smallholder farmers still lack access to agricultural science; Eco Nojin was built precisely for that gap.',
        paragraphs: [
          'Roughly 70% of the world’s smallholder farmers have no digital AgTech tools; existing platforms are either expensive or depend on smartphones and digital literacy. The result: peer-reviewed science never reaches the field.',
          'Eco Nojin delivers science to any phone and any literacy level through five access channels — web/PWA, USSD, SMS, messaging bots and a voice assistant — in fourteen languages; not as scattered information, but as the output of scientific models.',
          'This website is the project’s public gateway: the “Platform” page introduces the modules, and the “HyDroMa Science” page presents the computational engine.',
        ],
      },
      {
        category: 'Science',
        title: 'HyDroMa: when physics reaches the farm',
        date: 'September 2026',
        excerpt:
          'Instead of guesses, deterministic physical models — how the Eco Nojin scientific engine works.',
        paragraphs: [
          'HyDroMa chains fundamental earth-science models: Richards for water in unsaturated soil, Saint-Venant for surface flow, FAO-56 for evapotranspiration, RUSLE and SWAT for erosion and watersheds, and RothC for soil carbon dynamics.',
          'For speed, part of the computation runs on a C++20 numerical core via pybind11. Data comes from Sentinel-2, the ERA5 reanalysis and SoilGrids.',
          'The final output is decision-grade: scenarios are optimized and compared with NSGA-II, producing a report you can trust and be accountable for.',
        ],
      },
      {
        category: 'Carbon',
        title: 'Carbon you can prove',
        date: 'September 2026',
        excerpt:
          'Transparent MRV, field monitoring and blockchain registration — why “proof” is the heart of the carbon economy.',
        paragraphs: [
          'The carbon market builds trust only when every credit is measurable and verifiable. Eco Nojin combines satellite monitoring with field data (KoBo forms) to make measurement real.',
          'Carbon credits are registered with blockchain verification on Polygon, and MRV reports are delivered transparently to buyers and development institutions.',
          'The outcome for local communities is clear: restoring land must generate income — and that income must be provable, not promised.',
        ],
      },
      {
        category: 'Perspective',
        title: '2050: When the Ground Beneath Us Gives Way',
        date: 'October 2026',
        excerpt:
          'The new borders of the 2050 world are borders of water and soil — and on that map, Iran is a bold dot: a canary in the coal mine.',
        paragraphs: [
          'Imagine it is 2050. Looking down from an airplane window, you no longer see the familiar blue-and-green planet of the geography books. In the Middle East, dust storms swallow the sky for weeks at a time. In Africa, Lake Chad has become a pit of salt, and yesterday’s fishermen are today’s displaced people on the edge of crowded cities. In South Asia, the Indus and the Ganges turn into cracked riverbeds during the hot months, and hundreds of millions queue for a single glass of drinking water. In the western United States, Las Vegas and Phoenix endure summers above 50°C, and the power grid falters under the load of vast air conditioners. Around the Mediterranean, wildfires no longer know a “season”; from Greece to Spain, villages are evacuated one by one.',
          'But Iran is only one of these pictures. Tehran, Isfahan, Shiraz and Mashhad are no longer livable cities. Yet this is not only Iran’s fate; it is the fate of the Earth’s dry belt — the belt that stretches from Morocco to Mongolia and now intends to push its borders toward Europe, toward China, into the heart of Africa and even into North America.',
          'In its 2024 report, the United Nations Convention to Combat Desertification stated that 50% of the world’s rangelands are degraded, putting the food reserves of one-sixth of humanity at risk. The Intergovernmental Panel on Climate Change (IPCC) warns that if current trends continue, more than five billion people will face water scarcity by 2050. The World Bank estimates that by 2050, around 216 million people in just three regions — sub-Saharan Africa, South Asia and Latin America — will be displaced by climate change. These are not numbers; these are people.',
        ],
        sections: [
          {
            heading: 'The global map of drying',
            paragraphs: [
              'The 2050 world is no longer divided by political borders; the new borders are borders of water and soil. Regions that were once the world’s granaries are now food importers. The fertile plains of Ukraine and Russia are caught between war and drought. The American Great Plains wrestle with soil erosion and the draining of the Ogallala aquifer. Northern China — once the country’s “breadbasket” — now fights sandstorms from the Gobi Desert, and millions of farmers have taken refuge in the cities.',
              'The Aral Sea, the greatest environmental disaster of the twentieth century, has already become a salt desert, and salt storms have left the farmlands of Uzbekistan and Kazakhstan barren. In East Africa, the Horn of Africa faces its worst drought in 40 years, with millions on the brink of famine. In South America, the Amazon — once the lungs of the planet — is approaching a point of no return, and its drying is disrupting rainfall patterns across the whole continent.',
              'On this map, Iran is a bold dot. A country that once kept civilization alive in the heart of the desert with its thousand-year-old qanats is now — with Lake Urmia, Hamoun and Gavkhouni drying up — becoming a source of dust. But this is not only a national tragedy; it is a global warning. What is happening in Iran is a preview of the future awaiting many semi-arid regions of the world.',
            ],
          },
          {
            heading: 'The human price of a thirsty planet',
            paragraphs: [
              'In 2050, schools close not because of war or disease, but because of dust storms. Hospitals are full of children born with masks, whose lungs have never known clean air. Flights are cancelled — not by sanctions or political crisis, but because the sky is too dark for a pilot to see the runway.',
              'Villages are emptied of people. Farmers who once proudly grew wheat, saffron and rice now live in shantytowns on the edge of megacities. They are no longer producers; they are poor consumers queuing for a single subsidized meal. The picture repeats from Iran to Egypt, from Pakistan to Mexico, from Nigeria to India.',
              'Drought is not only a climatic phenomenon; it is a social bomb. Where there is no water, there is no food. Where there is no food, there is no security. The wars of the future will not be fought over oil; they will be fought over water. The Nile, the Tigris and Euphrates, the Indus, the Ganges and the Colorado have become front lines of geopolitical tension. In Syria, the prolonged drought of the 2000s was one of the sparks of the civil war. In 2050, such sparks can grow into regional and global fires.',
            ],
          },
          {
            heading: 'Iran: a mirror for the world',
            paragraphs: [
              'Iran can be called “the canary in the coal mine”. A country with a civilization thousands of years old, sitting on the Earth’s dry belt, wrestling with unsustainable water management, soil erosion, draining aquifers and climate migration. But the same symptoms appear across the world. The drying of Lake Urmia mirrors the drying of Lake Chad in Africa, Lake Poopó in Bolivia and Lake Mead in America. Land subsidence on Iran’s plains resembles the subsidence of California, Mexico City, Jakarta and Delhi.',
              'What sets Iran apart is the speed of the disaster. But that speed can spread to any other corner of the world. If the world does not come to Iran’s aid today, tomorrow it will have to come to its own aid. Borders cannot stop dust storms. Border walls cannot hold back climate migrants. The virus of drying asks for no visa.',
            ],
          },
          {
            heading: 'This is not an apocalyptic prophecy',
            paragraphs: [
              'This is a scientific scenario. A scenario drawn by the most credible international institutions from the current trends of soil erosion, land subsidence, draining aquifers and climate migration. But a scenario is not a predetermined fate. A scenario means: “if we continue this way, we will get there.” And “if” means we still have a choice.',
              'Solutions exist. Restoring degraded lands, returning water to wetlands, regenerative agriculture, intelligent management of water resources, investment in renewable energy and — above all — international cooperation. No country can tackle the water and soil crisis alone. Just as viruses know no borders, neither do dust storms, droughts and climate migration.',
              'The 2050 world has not been written yet. We are writing it today, with our choices. Do we want to hand our children a desert planet, or keep alive the green legacy of civilizations that lived in harmony with nature for thousands of years?',
              'The answer to this question must be given not in 2050, but today.',
            ],
          },
        ],
      },
    ],
  },
} as const;

export type BlogLang = 'fa' | 'en';
