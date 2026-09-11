"""Curated knowledge base for agricultural and ecological guidance.

Each document is aligned with FAO standards and scientific references.
This serves as the retrieval corpus for the RAG system.
"""

from dataclasses import dataclass


@dataclass
class KnowledgeDocument:
    id: str
    title: str
    content: str
    source: str
    category: str


# Scientific guidance aligned with FAO-56, FAO AquaCrop, and IPM principles
KNOWLEDGE_BASE: list[KnowledgeDocument] = [
    KnowledgeDocument(
        id="doc_001",
        title="Compost C/N Ratio Optimization",
        content=(
            "The optimal Carbon to Nitrogen (C/N) ratio for composting is between 25:1 and 35:1. "
            "A ratio above 40 slows decomposition significantly, while a ratio below 20 causes nitrogen "
            "loss as ammonia and produces odor. Straw (C/N 80:1) should be mixed with cow manure (C/N 20:1) "
            "in approximately 2:1 mass ratio to achieve optimal balance."
        ),
        source="FAO Composting Guidelines",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_002",
        title="Biochar Application in Sandy Soils",
        content=(
            "Biochar improves water retention in sandy soils by increasing Cation Exchange Capacity (CEC). "
            "Recommended application rate is 10-20 tons per hectare. Biochar should be 'charged' with "
            "compost or manure before application to prevent initial nutrient immobilization. "
            "Pyrolysis temperature should be 400-600°C for optimal porosity."
        ),
        source="International Biochar Initiative",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_003",
        title="FAO-56 Reference Evapotranspiration (ET0)",
        content=(
            "The Hargreaves-Samani method estimates ET0 using only temperature data: "
            "ET0 = 0.0023 × 0.408 × Ra × (Tmean + 17.8) × √(Tmax - Tmin), where Ra is extraterrestrial "
            "radiation in MJ/m²/day. This method is recommended by FAO when humidity and wind data "
            "are unavailable. Typical ET0 ranges from 2-8 mm/day depending on climate."
        ),
        source="FAO Irrigation and Drainage Paper 56",
        category="water_management",
    ),
    KnowledgeDocument(
        id="doc_004",
        title="Drought-Resistant Crops for Arid Regions",
        content=(
            "For regions with annual rainfall below 300mm, recommended crops include: "
            "millet (Pennisetum glaucum), sorghum (Sorghum bicolor), chickpea (Cicer arietinum), "
            "and prickly pear cactus (Opuntia ficus-indica). These crops require 200-400mm of water "
            "per season and can tolerate temperatures up to 40°C. Prickly pear is particularly valuable "
            "as both food source and soil stabilization plant."
        ),
        source="FAO Crop Production Guidelines",
        category="crop_selection",
    ),
    KnowledgeDocument(
        id="doc_005",
        title="RUSLE Soil Erosion Model",
        content=(
            "The Revised Universal Soil Loss Equation (RUSLE) estimates annual soil loss: "
            "A = R × K × LS × C × P, where R is rainfall erosivity, K is soil erodibility, "
            "LS is slope length/steepness factor, C is cover management, and P represents "
            "conservation practices. Tolerable soil loss is typically 5-10 tons/hectare/year."
        ),
        source="USDA/RUSLE Handbook",
        category="erosion_control",
    ),
    KnowledgeDocument(
        id="doc_006",
        title="Small-Scale Watershed Structures",
        content=(
            "Check dams, contour trenches, and half-moons are effective low-cost structures. "
            "Check dams should be built in series with spacing 5-10 times the dam height. "
            "Contour trenches (50cm × 50cm cross-section) increase infiltration by 30-50% in "
            "sloping terrain. Half-moons (2-4m diameter) are ideal for seedling establishment "
            "in degraded rangelands."
        ),
        source="FAO Watershed Management Field Manual",
        category="watershed",
    ),
    KnowledgeDocument(
        id="doc_007",
        title="Integrated Pest Management (IPM)",
        content=(
            "IPM prioritizes biological control over chemical pesticides. Key strategies include: "
            "(1) Use of Trichoderma for soil-borne fungal diseases, (2) Release of ladybugs and "
            "lacewings for aphid control, (3) Pheromone traps for monitoring, (4) Crop rotation "
            "to break pest cycles. Economic threshold levels should guide intervention timing."
        ),
        source="FAO IPM Guidelines",
        category="pest_management",
    ),
    KnowledgeDocument(
        id="doc_008",
        title="Soil Salinity Management",
        content=(
            "Soils with EC > 4 dS/m are considered saline. Management strategies: "
            "(1) Leaching with 15-30cm of good-quality water, (2) Gypsum application for sodic soils "
            "(SAR > 13), (3) Planting salt-tolerant species like barley, sugar beet, or Atriplex, "
            "(4) Drip irrigation to maintain low salinity in root zone. Avoid ash application "
            "on already saline soils as it increases pH and EC."
        ),
        source="FAO Irrigation Paper 32",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_009",
        title="Carbon Sequestration in Agricultural Soils",
        content=(
            "Agricultural soils can sequester 0.5-2.0 tons CO2/ha/year through: "
            "(1) No-till farming (0.3-0.5 t/ha/yr), (2) Cover cropping (0.2-0.4 t/ha/yr), "
            "(3) Biochar application (stable for centuries), (4) Agroforestry systems. "
            "Soil organic carbon should be measured annually to verify sequestration rates "
            "for carbon credit programs (Verra VCS, Gold Standard)."
        ),
        source="IPCC Guidelines for Agriculture",
        category="carbon",
    ),
    KnowledgeDocument(
        id="doc_010",
        title="Medicinal Plants for Arid Climates",
        content=(
            "High-value medicinal plants adapted to dry conditions include: "
            "thyme (Thymus vulgaris), rosemary (Rosmarinus officinalis), sage (Salvia officinalis), "
            "lavender (Lavandula angustifolia), and cumin (Cuminum cyminum). These require "
            "300-500mm annual rainfall and well-drained soils. Market value can be 5-10x higher "
            "than conventional crops, making them ideal for smallholder economic diversification."
        ),
        source="WHO Traditional Medicine Strategy",
        category="crop_selection",
    ),
]


# Persian (Farsi) knowledge base for RAG - aligned with FAO standards
KNOWLEDGE_BASE_FA: list[KnowledgeDocument] = [
    KnowledgeDocument(
        id="doc_fa_001",
        title="بهینه‌سازی نسبت کربن به نیتروژن در کمپوست",
        content=(
            "نسبت بهینه کربن به نیتروژن (C/N) برای کمپوست‌سازی بین ۲۵:۱ تا ۳۵:۱ است. "
            "نسبت بالاتر از ۴۰ تجزیه را به شدت کند می‌کند، در حالی که نسبت زیر ۲۰ باعث از دست رفتن "
            "نیتروژن به صورت آمونیاک و بوی بد می‌شود. کاه (C/N ۸۰:۱) باید با گوبر گاو (C/N ۲۰:۱) "
            "به نسبت تقریبی ۲:۱ وزنی مخلوط شود تا تعادل بهینه برقرار شود."
        ),
        source="راهنمای کمپوست‌سازی FAO",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_fa_002",
        title="ابزار هوشمند آبیاری و مدیریت آب",
        content=(
            "سیستم‌های هوشمند آبیاری با استفاده از سنسور رطوبت خاک، داده‌های هواشناسی و مدل FAO-56 "
            "نیاز آبی دقیق گیاهان را محاسبه می‌کنند. آبیاری قطره‌ای با کنترل‌کننده‌های هوشمند می‌تواند "
            "مصرف آب را ۳۰-۵۰٪ کاهش دهد. زمان‌بندی بر اساس اتراپیراسیون ارجاع (ET0) و ضریب گیاه (Kc) "
            "عملکرد بهینه را تضمین می‌کند. FAO اکواکراپ (AquaCrop) برای مدل‌سازی عملکرد گیاه تحت استرس آب توصیه می‌شود."
        ),
        source="FAO Irrigation and Drainage Paper 56",
        category="water_management",
    ),
    KnowledgeDocument(
        id="doc_fa_003",
        title="مدیریت شوری خاک در مناطق خشک",
        content=(
            "خاک‌هایی با EC > ۴ dS/m شوری محسوب می‌شوند. راهکارهای مدیریت شامل: "
            "(۱) شستشو با ۱۵-۳۰ سانتی‌متر آب با کیفیت مناسب، (۲) کاربرد ژیپس برای خاک‌های سدی (SAR > ۱۳)، "
            "(۳) کاشت گونه‌های تحمل‌شور مانند جو، قندریز یا آتریپلیکس، "
            "(۴) آبیاری قطره‌ای برای حفظ شوری پایین در ناحیه ریشه. از کاربرد زغال روی خاک‌های شوری خودداری کنید "
            "چون pH و EC را افزایش می‌دهد."
        ),
        source="FAO Irrigation Paper 32",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_fa_004",
        title="گیاهان مقاوم به خشک‌سالی برای مناطق کم‌آب",
        content=(
            "برای مناطق با بارندگی سالانه زیر ۳۰۰ میلی‌متر، گیاهان پیشنهادی شامل: "
            "غال (Pennisetum glaucum)، ذره‌سرخ (Sorghum bicolor)، نخود (Cicer arietinum)، "
            "و کاکتوس انارک (Opuntia ficus-indica) می‌باشند. این گیاهان ۲۰۰-۴۰۰ میلی‌متر آب در فصل رشد نیاز دارند "
            "و می‌توانند دماهای تا ۴۰ درجه سانتی‌گراد را تحمل کنند. انارک به‌ویژه به عنوان منبع غذایی "
            "و گیاه تثبیت خاک ارزشمند است."
        ),
        source="راهنمای تولید گیاهان FAO",
        category="crop_selection",
    ),
    KnowledgeDocument(
        id="doc_fa_005",
        title="سازماندهی آبخیز با سازه‌های کوچک",
        content=(
            "بندهای کنترلی، خندقهای الكنوری و نیم‌دایره‌ها سازه‌های کم‌مصرف و اثربخش هستند. "
            "بندهای کنترلی باید به صورت سری با فاصله ۵ تا ۱۰ برابر ارتفاع بند ساخته شوند. "
            "خندقهای الكنوری (مقطع ۵۰ در ۵۰ سانتی‌متر) نفوذ آب را در زمین‌های شیب‌دار ۳۰-۵۰٪ افزایش می‌دهند. "
            "نیم‌دایره‌ها (قطر ۲ تا ۴ متر) برای استقرار نهال‌ها در مراتع تخریب‌شده ایده‌آل هستند."
        ),
        source="دستورالعمل میدانی مدیریت آبخیز FAO",
        category="watershed",
    ),
    KnowledgeDocument(
        id="doc_fa_006",
        title="مدیریت یکپارچه آفت‌ها (IPM) در کشاورزی پایدار",
        content=(
            "IPM کنترل بیولوژیکی را بر مبيدات شیمیایی ارجح می‌دارد. استراتژی‌های کلیدی شامل: "
            "(۱) استفاده از تریoderma برای بیماری‌های قارچی ریشه، (۲) رها کردن کبوترک‌های تل و گنجشک‌کش برای کنترل مشر، "
            "(۳) تله‌های فرومون برای پایش، (۴) چرخه کشت برای شکستن چرخه آفت. "
            "آستانه‌های اقتصادی باید زمان مداخله را هدایت کنند."
        ),
        source="راهنمای IPM سازمان FAO",
        category="pest_management",
    ),
    KnowledgeDocument(
        id="doc_fa_007",
        title="حبس کربن در خاک‌های کشاورزی",
        content=(
            "خاک‌های کشاورزی می‌توانند ۰.۵ تا ۲.۰ تن CO2 در هکتار در سال حبس کنند از طریق: "
            "(۱) کشاورزی بدون کاشت (۰.۳-۰.۵ تن/هکتار/سال)، (۲) گیاهان پوشش‌دهنده (۰.۲-۰.۴ تن/هکتار/سال)، "
            "(۳) کاربرد بیوچار (مثبت برای قرن‌ها)، (۴) سیستم‌های جنگل‌کشت. "
            "کربن آلی خاک باید سالانه اندازه‌گیری شود تا نرخ‌های حبس برای برنامه‌های اعتبار کربن "
            "(Verra VCS، Gold Standard) تایید شود."
        ),
        source="راهنمای IPCC برای کشاورزی",
        category="carbon",
    ),
    KnowledgeDocument(
        id="doc_fa_008",
        title="گیاهان دارویی سازگار با اقلیم خشک",
        content=(
            "گیاهان دارویی با ارزش بالا و سازگار با خشکی شامل: "
            "آویشن (Thymus vulgaris)، رزماری (Rosmarinus officinalis)، مرمری (Salvia officinalis)، "
            "استخودوس (Lavandula angustifolia)، و زیره (Cuminum cyminum) می‌باشند. این گیاهان "
            "۳۰۰-۵۰۰ میلی‌متر بارندگی سالانه و خاک‌های به‌خیر رایشده نیاز دارند. ارزش بازار می‌تواند "
            "۵ تا ۱۰ برابر گیاهان معمولی باشد، که آنها را برای تنوع اقتصادی صاحبان زمین‌های کوچک ایده‌آل می‌سازد."
        ),
        source="استراتژی طب سنتی WHO",
        category="crop_selection",
    ),
    KnowledgeDocument(
        id="doc_fa_009",
        title="مدل RUSLE برای برآورد فرسایش خاک",
        content=(
            "معادله جهانی بازنگری شده فرسایش خاک (RUSLE) از دست رفتن سالانه خاک را برآورد می‌کند: "
            "A = R × K × LS × C × P، که در آن R فرسایش‌پذیری بارندگی، K فرسایش‌پذیری خاک، "
            "LS فاکтор طول/شیب، C مدیریت پوشش، و P عملیات حفاظتی را نشان می‌دهد. "
            "از دست رفتن قابل تحمل خاک معمولاً ۵-۱۰ تن در هکتار در سال است."
        ),
        source="دستورالعمل USDA/RUSLE",
        category="erosion_control",
    ),
    KnowledgeDocument(
        id="doc_fa_010",
        title="کاربرد بیوچار در خاک‌های شنی و مرزی",
        content=(
            "بیوچار با افزایش ظرفیت تبادل کاتیونی (CEC) نگهداری آب در خاک‌های شنی را بهبود می‌بخشد. "
            "نرخ کاربرد توصیه‌شده ۱۰ تا ۲۰ تن در هکتار است. بیوچار باید قبل از کاربرد با کمپوست یا گوبر "
            "'شارژ' شود تا از بی‌عرضه‌سازی اولیه مغذیات پیشگیری شود. "
            "دمای پیرولیز باید ۴۰۰-۶۰۰ درجه سانتی‌گراد برای تخلخل بهینه باشد."
        ),
        source="مبادرة بین‌المللی بیوچار",
        category="soil_amendment",
    ),
]


# Arabic knowledge base for RAG - aligned with FAO standards
KNOWLEDGE_BASE_AR: list[KnowledgeDocument] = [
    KnowledgeDocument(
        id="doc_ar_001",
        title="نسبة الكربون إلى النيتروجين المثلى للتسميد",
        content=(
            "النسبة المثلى للكربون إلى النيتروجين (C/N) للتسميد تتراوح بين 25:1 و 35:1. "
            "النسبة فوق 40 تبطئ التحلل بشكل كبير، بينما النسبة تحت 20 تسبب فقدان النيتروجين "
            "على شكل أمونيا وتنتج رائحة كريهة. يجب خلط القش (C/N 80:1) مع روث البقر (C/N 20:1) "
            "بنسبة كتلة تقريبية 2:1 لتحقيق التوازن الأمثل."
        ),
        source="إرشادات التسميد FAO",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_ar_002",
        title="إدارة ملوحة التربة في المناطق الجافة",
        content=(
            "التربة التي تزيد فيها EC عن 4 dS/m تعتبر مالحة. استراتيجيات الإدارة تشمل: "
            "(1) الغسل بـ 15-30 سم من المياه ذات النوعية الجيدة، (2) تطبيق الجبس للتربة الصودية "
            "(SAR > 13)، (3) زراعة أنواع مقاومة للملح مثل الشعير، بنجر السكر، أو الأثل، "
            "(4) الري بالتنقيط للحفاظ على ملوحة منخفضة في منطقة الجذور. تجنب تطبيق الرماد "
            "على التربة المالحة بالفعل لأنه يزيد الـ pH والـ EC."
        ),
        source="FAO Irrigation Paper 32",
        category="soil_amendment",
    ),
    KnowledgeDocument(
        id="doc_ar_003",
        title="المحاصيل المقاومة للجفاف في المناطق القاحلة",
        content=(
            "للمناطق التي يقل فيها هطول الأمطار السنوي عن 300 مم، المحاصيل الموصى بها تشمل: "
            "الذرة الرفيعة (Sorghum bicolor)، الدخن (Pennisetum glaucum)، الحمص (Cicer arietinum)، "
            "وصبار التين الشوكي (Opuntia ficus-indica). هذه المحاصيل تحتاج 200-400 مم من الماء "
            "لكل موسم وتتحمل درجات حرارة تصل إلى 40°C. صبار التين الشوكي ذو قيمة خاصة "
            "كمصدر غذائي ونبات لتثبيت التربة."
        ),
        source="إرشادات إنتاج المحاصيل FAO",
        category="crop_selection",
    ),
    KnowledgeDocument(
        id="doc_ar_004",
        title="هياكل حوض المياه صغيرة النطاق",
        content=(
            "السدود التحكمية، الخنادق الكنتورية، وأنصاف الدوائر هي هياكل فعالة منخفضة التكلفة. "
            "يجب بناء السدود التحكمية على سلسلة مع تباعد 5-10 أضعاف ارتفاع السد. "
            "الخنادق الكنتورية (مقطع 50x50 سم) تزيد التسرب بنسبة 30-50% في "
            "التضاريس المائلة. أنصاف الدوائر (قطر 2-4 متر) مثالية لتأسيس الشتلات "
            "في المراعي المتدهورة."
        ),
        source="دليل إدارة أحواض المياه الميداني FAO",
        category="watershed",
    ),
    KnowledgeDocument(
        id="doc_ar_005",
        title="الإدارة المتكاملة للآفات (IPM)",
        content=(
            "الإدارة المتكاملة للآفات تعطي الأولوية للمكافحة البيولوجية على المبيدات الكيميائية. "
            "الاستراتيجيات الرئيسية تشمل: (1) استخدام الترايكودرما للأمراض الفطرية المنقولة "
            "بالتربة، (2) إطلاق الخنافس واليرقات المفترسة للسيطرة على المن، "
            "(3) مصائد الفيرومون للرصد، (4) تدوير المحاصيل لكسر دورات الآفات. "
            "يجب أن ترشد المستويات الاقتصادية الحدية توقيت التدخل."
        ),
        source="إرشادات IPM المنظمة FAO",
        category="pest_management",
    ),
]