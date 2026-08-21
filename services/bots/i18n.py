"""Internationalization for the Eco Nojin bot — 14 languages (Phase 1).

The UI strings below are short, farmer-facing labels. The RAG knowledge
corpus is English for now (see weakness W-008); answers are synthesized
into the user's language when a local Ollama model is available, otherwise
they fall back to the English corpus with a clear note.
"""

from __future__ import annotations

LANGUAGES: tuple[str, ...] = (
    "ar", "bn", "de", "en", "es", "fa", "fr", "hi", "it", "ms", "pt", "ru", "ur", "zh",
)

LANGUAGE_NAMES: dict[str, str] = {
    "ar": "العربية",
    "bn": "বাংলা",
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fa": "فارسی",
    "fr": "Français",
    "hi": "हिन्दी",
    "it": "Italiano",
    "ms": "Bahasa Melayu",
    "pt": "Português",
    "ru": "Русский",
    "ur": "اردو",
    "zh": "中文",
}

RTL_LANGUAGES: frozenset[str] = frozenset({"ar", "fa", "ur"})

# ---------------------------------------------------------------------------
# UI strings (per language)
# ---------------------------------------------------------------------------
UI: dict[str, dict[str, str]] = {
    "fa": {
        "greeting": "🌱 به ربات «اکو نوژین» خوش آمدید!\n"
                    "مشاوره علمی کشاورزی، آب و خاک — رایگان و بدون نیاز به اینترنت پرسرعت.\n"
                    "زبان خود را انتخاب کنید:",
        "advice_btn": "💬 مشاوره",
        "farm_btn": "🌾 ثبت مزرعه",
        "about_btn": "ℹ️ درباره",
        "lang_btn": "🌐 زبان",
        "ask_prompt": "سؤال خود را بنویسید (مثلاً: نسبت کربن به نیتروژن کمپوست چقدر باید باشد؟)",
        "farm_name_q": "نام مزرعه را وارد کنید:",
        "farm_area_q": "مساحت مزرعه را به هکتار وارد کنید (مثلاً 5.5):",
        "farm_loc_q": "مختصات مزرعه را بفرستید: یا پیام «عرض, طول» بنویسید (مثلاً 35.6892, 51.3890).",
        "farm_soil_q": "نوع خاک را وارد کنید (اختیاری — برای رد شدن «-» بنویسید):",
        "farm_saved": "✅ مزرعه «{name}» ثبت شد!",
        "no_answer": "⚠️ پاسخی در دانشنامه پیدا نشد. سؤال را سادهتر بپرسید یا با کارشناس محلی مشورت کنید.",
        "ollama_offline_note": "\n\n📌 ترجمه محلی در دسترس نیست (Ollama خاموش است) — پاسخ به زبان انگلیسی ارائه شد.",
        "main_menu": "منوی اصلی:",
        "about": "«اکو نوژین» بستری دانش‌بنیان برای کشاورزی اقلیم‌هوشمند، آب، خاک و کربن است.\n"
                 "پاسخ‌ها بر پایه منابع علمی (FAO و همکاران) و موتور مدل‌سازی HyDroMa ارائه می‌شود.",
    },
    "en": {
        "greeting": "🌱 Welcome to the «Eco Nojin» bot!\n"
                    "Scientific advisory for agriculture, water and soil — free.\n"
                    "Choose your language:",
        "advice_btn": "💬 Advice",
        "farm_btn": "🌾 Register farm",
        "about_btn": "ℹ️ About",
        "lang_btn": "🌐 Language",
        "ask_prompt": "Type your question (e.g.: what should the compost C/N ratio be?)",
        "farm_name_q": "Enter the farm name:",
        "farm_area_q": "Enter the area in hectares (e.g. 5.5):",
        "farm_loc_q": "Send the location or write “lat, lon” (e.g. 35.6892, 51.3890):",
        "farm_soil_q": "Enter soil type (optional — send “-” to skip):",
        "farm_saved": "✅ Farm “{name}” registered!",
        "no_answer": "⚠️ No answer found in the knowledge base. Please rephrase or consult a local expert.",
        "ollama_offline_note": "\n\n📌 Local translation is offline (Ollama not running) — answer provided in English.",
        "main_menu": "Main menu:",
        "about": "«Eco Nojin» is a knowledge-based platform for climate-smart agriculture, water, soil and carbon.\n"
                 "Answers are grounded in scientific sources (FAO and partners) and the HyDroMa modeling engine.",
    },
    "ar": {
        "greeting": "🌱 مرحباً بك في بوت «إيكو نوجين»!\n"
                    "استشارات علمية للزراعة والمياه والتربة — مجاناً.\n"
                    "اختر لغتك:",
        "advice_btn": "💬 استشارة",
        "farm_btn": "🌾 تسجيل مزرعة",
        "about_btn": "ℹ️ حول",
        "lang_btn": "🌐 اللغة",
        "ask_prompt": "اكتب سؤالك (مثال: ما هي نسبة الكربون إلى النيتروجين المثالية للكمبوست؟)",
        "farm_name_q": "أدخل اسم المزرعة:",
        "farm_area_q": "أدخل المساحة بالهكتار (مثال 5.5):",
        "farm_loc_q": "أرسل الموقع أو اكتب «العرض, الطول» (مثال 35.6892, 51.3890):",
        "farm_soil_q": "أدخل نوع التربة (اختياري — أرسل «-» للتخطي):",
        "farm_saved": "✅ تم تسجيل المزرعة «{name}»!",
        "no_answer": "⚠️ لم يُعثر على إجابة في قاعدة المعرفة. أعد صياغة السؤال أو استشر خبيراً محلياً.",
        "ollama_offline_note": "\n\n📌 الترجمة المحلية غير متاحة (Ollama متوقف) — الإجابة بالإنجليزية.",
        "main_menu": "القائمة الرئيسية:",
        "about": "«إيكو نوجين» منصة معرفية للزراعة الذكية مناخياً والمياه والتربة والكربون.\n"
                 "الإجابات مبنية على مصادر علمية (FAO وشركاء) ومحرك HyDroMa للنمذجة.",
    },
    "ur": {
        "greeting": "🌱 بوٹ «ایکو نوجین» میں خوش آمدید!\n"
                    "زراعت، پانی اور مٹی کے لیے سائنسی مشورہ — مفت۔\n"
                    "اپنی زبان منتخب کریں:",
        "advice_btn": "💬 مشورہ",
        "farm_btn": "🌾 فارم رجسٹر کریں",
        "about_btn": "ℹ️ تعارف",
        "lang_btn": "🌐 زبان",
        "ask_prompt": "اپنا سوال لکھیں (مثال: کمپوسٹ کا C/N تناسب کیا ہونا چاہیے؟)",
        "farm_name_q": "فارم کا نام درج کریں:",
        "farm_area_q": "رقبہ ہیکٹر میں درج کریں (مثال 5.5):",
        "farm_loc_q": "مقام بھیجیں یا «عرض, طول» لکھیں (مثال 35.6892, 51.3890):",
        "farm_soil_q": "مٹی کی قسم درج کریں (اختیاری — چھوڑنے کے لیے «-» لکھیں):",
        "farm_saved": "✅ فارم «{name}» رجسٹر ہو گیا!",
        "no_answer": "⚠️ نالج بیس میں جواب نہیں ملا۔ سوال دوبارہ لکھیں یا مقامی ماہر سے مشورہ کریں۔",
        "ollama_offline_note": "\n\n📌 مقامی ترجمہ دستیاب نہیں (Ollama بند ہے) — جواب انگریزی میں دیا گیا۔",
        "main_menu": "مرکزی مینیو:",
        "about": "«ایکو نوجین» موسمیاتی زراعت، پانی، مٹی اور کاربن کے لیے ایک علمی پلیٹ فارم ہے۔\n"
                 "جوابات سائنسی ذرائع (FAO اور شراکت دار) اور HyDroMa انجن پر مبنی ہیں۔",
    },
    "ru": {
        "greeting": "🌱 Добро пожаловать в бот «Эко Ноджин»!\n"
                    "Научные консультации по сельскому хозяйству, воде и почве — бесплатно.\n"
                    "Выберите язык:",
        "advice_btn": "💬 Консультация",
        "farm_btn": "🌾 Регистрация фермы",
        "about_btn": "ℹ️ О нас",
        "lang_btn": "🌐 Язык",
        "ask_prompt": "Напишите вопрос (например: каким должно быть соотношение C/N в компосте?)",
        "farm_name_q": "Введите название фермы:",
        "farm_area_q": "Введите площадь в гектарах (например 5.5):",
        "farm_loc_q": "Отправьте координаты или напишите «широта, долгота» (например 35.6892, 51.3890):",
        "farm_soil_q": "Введите тип почвы (необязательно — отправьте «-» чтобы пропустить):",
        "farm_saved": "✅ Ферма «{name}» зарегистрирована!",
        "no_answer": "⚠️ Ответ в базе знаний не найден. Переформулируйте вопрос или обратитесь к местному эксперту.",
        "ollama_offline_note": "\n\n📌 Локальный перевод недоступен (Ollama выключен) — ответ на английском.",
        "main_menu": "Главное меню:",
        "about": "«Эко Ноджин» — научная платформа для климатически умного сельского хозяйства, воды, почвы и углерода.\n"
                 "Ответы основаны на научных источниках (FAO и партнёры) и движке моделирования HyDroMa.",
    },
    "zh": {
        "greeting": "🌱 欢迎使用「Eco Nojin」机器人！\n农业、水资源与土壤科学咨询 — 免费。\n请选择语言：",
        "advice_btn": "💬 咨询",
        "farm_btn": "🌾 注册农场",
        "about_btn": "ℹ️ 关于",
        "lang_btn": "🌐 语言",
        "ask_prompt": "请输入您的问题（例如：堆肥的碳氮比应该是多少？）",
        "farm_name_q": "请输入农场名称：",
        "farm_area_q": "请输入面积（公顷，例如 5.5）：",
        "farm_loc_q": "请发送位置或输入“纬度, 经度”（例如 35.6892, 51.3890）：",
        "farm_soil_q": "请输入土壤类型（可选 — 发送“-”跳过）：",
        "farm_saved": "✅ 农场「{name}」已注册！",
        "no_answer": "⚠️ 知识库中未找到答案。请重新表述问题或咨询当地专家。",
        "ollama_offline_note": "\n\n📌 本地翻译不可用（Ollama 未运行）— 答案以英文提供。",
        "main_menu": "主菜单：",
        "about": "「Eco Nojin」是一个面向气候智慧农业、水资源、土壤与碳的知识平台。\n答案基于科学来源（FAO 及合作伙伴）和 HyDroMa 建模引擎。",
    },
    "hi": {
        "greeting": "🌱 «इको नोजिन» बॉट में आपका स्वागत है!\nकृषि, जल और मिट्टी के लिए वैज्ञानिक सलाह — मुफ्त।\nअपनी भाषा चुनें:",
        "advice_btn": "💬 सलाह",
        "farm_btn": "🌾 खेत पंजीकृत करें",
        "about_btn": "ℹ️ परिचय",
        "lang_btn": "🌐 भाषा",
        "ask_prompt": "अपना प्रश्न लिखें (जैसे: कम्पोस्ट का C/N अनुपात कितना होना चाहिए?)",
        "farm_name_q": "खेत का नाम दर्ज करें:",
        "farm_area_q": "क्षेत्रफल हेक्टेयर में दर्ज करें (जैसे 5.5):",
        "farm_loc_q": "स्थान भेजें या «अक्षांश, देशांतर» लिखें (जैसे 35.6892, 51.3890):",
        "farm_soil_q": "मिट्टी का प्रकार दर्ज करें (वैकल्पिक — छोड़ने के लिए «-» लिखें):",
        "farm_saved": "✅ खेत «{name}» पंजीकृत हुआ!",
        "no_answer": "⚠️ ज्ञानकोश में उत्तर नहीं मिला। प्रश्न दोबारा लिखें या स्थानीय विशेषज्ञ से सलाह लें।",
        "ollama_offline_note": "\n\n📌 स्थानीय अनुवाद उपलब्ध नहीं (Ollama बंद है) — उत्तर अंग्रेज़ी में दिया गया।",
        "main_menu": "मुख्य मेनू:",
        "about": "«इको नोजिन» जलवायु-स्मार्ट कृषि, जल, मिट्टी और कार्बन के लिए ज्ञान-आधारित मंच है।\nउत्तर वैज्ञानिक स्रोतों (FAO और साझेदार) और HyDroMa इंजन पर आधारित हैं।",
    },
    "bn": {
        "greeting": "🌱 «ইকো নোজিন» বটে স্বাগতম!\nকৃষি, পানি ও মাটির জন্য বৈজ্ঞানিক পরামর্শ — বিনামূল্যে।\nআপনার ভাষা বেছে নিন:",
        "advice_btn": "💬 পরামর্শ",
        "farm_btn": "🌾 খামার নিবন্ধন",
        "about_btn": "ℹ️ পরিচিতি",
        "lang_btn": "🌐 ভাষা",
        "ask_prompt": "আপনার প্রশ্ন লিখুন (যেমন: কম্পোস্টের C/N অনুপাত কত হওয়া উচিত?)",
        "farm_name_q": "খামারের নাম লিখুন:",
        "farm_area_q": "ক্ষেত্রফল হেক্টরে লিখুন (যেমন 5.5):",
        "farm_loc_q": "অবস্থান পাঠান বা «অক্ষাংশ, দ্রাঘিমাংশ» লিখুন (যেমন 35.6892, 51.3890):",
        "farm_soil_q": "মাটির ধরন লিখুন (ঐচ্ছিক — এড়াতে «-» লিখুন):",
        "farm_saved": "✅ খামার «{name}» নিবন্ধিত হয়েছে!",
        "no_answer": "⚠️ নলেজ বেসে উত্তর পাওয়া যায়নি। প্রশ্নটি আবার লিখুন বা স্থানীয় বিশেষজ্ঞের পরামর্শ নিন।",
        "ollama_offline_note": "\n\n📌 স্থানীয় অনুবাদ উপলব্ধ নয় (Ollama বন্ধ) — উত্তর ইংরেজিতে দেওয়া হয়েছে।",
        "main_menu": "প্রধান মেনু:",
        "about": "«ইকো নোজিন» জলবায়ু-স্মার্ট কৃষি, পানি, মাটি ও কার্বনের জন্য জ্ঞানভিত্তিক প্ল্যাটফর্ম।\nউত্তর বৈজ্ঞানিক উৎস (FAO ও অংশীদার) এবং HyDroMa ইঞ্জিনের উপর ভিত্তি করে।",
    },
    "es": {
        "greeting": "🌱 ¡Bienvenido al bot «Eco Nojin»!\nAsesoría científica para agricultura, agua y suelo — gratis.\nElige tu idioma:",
        "advice_btn": "💬 Asesoría",
        "farm_btn": "🌾 Registrar finca",
        "about_btn": "ℹ️ Acerca de",
        "lang_btn": "🌐 Idioma",
        "ask_prompt": "Escribe tu pregunta (ej.: ¿cuál debe ser la relación C/N del compost?)",
        "farm_name_q": "Introduce el nombre de la finca:",
        "farm_area_q": "Introduce el área en hectáreas (ej. 5.5):",
        "farm_loc_q": "Envía la ubicación o escribe «lat, lon» (ej. 35.6892, 51.3890):",
        "farm_soil_q": "Introduce el tipo de suelo (opcional — envía «-» para omitir):",
        "farm_saved": "✅ ¡Finca «{name}» registrada!",
        "no_answer": "⚠️ No se encontró respuesta en la base de conocimiento. Reformula la pregunta o consulta a un experto local.",
        "ollama_offline_note": "\n\n📌 Traducción local no disponible (Ollama apagado) — respuesta en inglés.",
        "main_menu": "Menú principal:",
        "about": "«Eco Nojin» es una plataforma basada en conocimiento para agricultura climáticamente inteligente, agua, suelo y carbono.\nLas respuestas se basan en fuentes científicas (FAO y socios) y el motor HyDroMa.",
    },
    "fr": {
        "greeting": "🌱 Bienvenue sur le bot «Eco Nojin » !\nConseils scientifiques pour l'agriculture, l'eau et le sol — gratuit.\nChoisissez votre langue :",
        "advice_btn": "💬 Conseil",
        "farm_btn": "🌾 Enregistrer une ferme",
        "about_btn": "ℹ️ À propos",
        "lang_btn": "🌐 Langue",
        "ask_prompt": "Écrivez votre question (ex. : quel doit être le rapport C/N du compost ?)",
        "farm_name_q": "Saisissez le nom de la ferme :",
        "farm_area_q": "Saisissez la surface en hectares (ex. 5.5) :",
        "farm_loc_q": "Envoyez la position ou écrivez « lat, lon » (ex. 35.6892, 51.3890) :",
        "farm_soil_q": "Saisissez le type de sol (optionnel — envoyez « - » pour passer) :",
        "farm_saved": "✅ Ferme « {name} » enregistrée !",
        "no_answer": "⚠️ Aucune réponse trouvée dans la base de connaissances. Reformulez ou consultez un expert local.",
        "ollama_offline_note": "\n\n📌 Traduction locale indisponible (Ollama éteint) — réponse en anglais.",
        "main_menu": "Menu principal :",
        "about": "«Eco Nojin» est une plateforme de connaissances pour l'agriculture climato-intelligente, l'eau, le sol et le carbone.\nLes réponses s'appuient sur des sources scientifiques (FAO et partenaires) et le moteur HyDroMa.",
    },
    "de": {
        "greeting": "🌱 Willkommen beim „Eco Nojin“-Bot!\nWissenschaftliche Beratung für Landwirtschaft, Wasser und Boden — kostenlos.\nWähle deine Sprache:",
        "advice_btn": "💬 Beratung",
        "farm_btn": "🌾 Betrieb registrieren",
        "about_btn": "ℹ️ Über uns",
        "lang_btn": "🌐 Sprache",
        "ask_prompt": "Stelle deine Frage (z. B.: Welches C/N-Verhältnis sollte Kompost haben?)",
        "farm_name_q": "Gib den Namen des Betriebs ein:",
        "farm_area_q": "Gib die Fläche in Hektar ein (z. B. 5.5):",
        "farm_loc_q": "Sende den Standort oder schreibe „Lat, Lon“ (z. B. 35.6892, 51.3890):",
        "farm_soil_q": "Gib den Bodentyp ein (optional — sende „-“ zum Überspringen):",
        "farm_saved": "✅ Betrieb „{name}“ registriert!",
        "no_answer": "⚠️ Keine Antwort in der Wissensdatenbank gefunden. Formuliere die Frage um oder frage einen lokalen Experten.",
        "ollama_offline_note": "\n\n📌 Lokale Übersetzung offline (Ollama nicht aktiv) — Antwort auf Englisch.",
        "main_menu": "Hauptmenü:",
        "about": "„Eco Nojin“ ist eine wissensbasierte Plattform für klimafreundliche Landwirtschaft, Wasser, Boden und Kohlenstoff.\nAntworten stützen sich auf wissenschaftliche Quellen (FAO u. a.) und die HyDroMa-Engine.",
    },
    "pt": {
        "greeting": "🌱 Bem-vindo ao bot «Eco Nojin»!\nAconselhamento científico para agricultura, água e solo — gratuito.\nEscolha o seu idioma:",
        "advice_btn": "💬 Aconselhamento",
        "farm_btn": "🌾 Registar exploração",
        "about_btn": "ℹ️ Sobre",
        "lang_btn": "🌐 Idioma",
        "ask_prompt": "Escreva a sua pergunta (ex.: qual deve ser a relação C/N do composto?)",
        "farm_name_q": "Introduza o nome da exploração:",
        "farm_area_q": "Introduza a área em hectares (ex. 5.5):",
        "farm_loc_q": "Envie a localização ou escreva «lat, lon» (ex. 35.6892, 51.3890):",
        "farm_soil_q": "Introduza o tipo de solo (opcional — envie «-» para saltar):",
        "farm_saved": "✅ Exploração «{name}» registada!",
        "no_answer": "⚠️ Não foi encontrada resposta na base de conhecimento. Reformule a pergunta ou consulte um especialista local.",
        "ollama_offline_note": "\n\n📌 Tradução local indisponível (Ollama desligado) — resposta em inglês.",
        "main_menu": "Menu principal:",
        "about": "«Eco Nojin» é uma plataforma baseada em conhecimento para agricultura inteligente face ao clima, água, solo e carbono.\nAs respostas baseiam-se em fontes científicas (FAO e parceiros) e no motor HyDroMa.",
    },
    "it": {
        "greeting": "🌱 Benvenuto nel bot «Eco Nojin»!\nConsulenza scientifica per agricoltura, acqua e suolo — gratis.\nScegli la tua lingua:",
        "advice_btn": "💬 Consulenza",
        "farm_btn": "🌾 Registra azienda",
        "about_btn": "ℹ️ Info",
        "lang_btn": "🌐 Lingua",
        "ask_prompt": "Scrivi la tua domanda (es.: quale dovrebbe essere il rapporto C/N del compost?)",
        "farm_name_q": "Inserisci il nome dell'azienda:",
        "farm_area_q": "Inserisci la superficie in ettari (es. 5.5):",
        "farm_loc_q": "Invia la posizione o scrivi «lat, lon» (es. 35.6892, 51.3890):",
        "farm_soil_q": "Inserisci il tipo di suolo (opzionale — invia «-» per saltare):",
        "farm_saved": "✅ Azienda «{name}» registrata!",
        "no_answer": "⚠️ Nessuna risposta trovata nella base di conoscenza. Riformula la domanda o consulta un esperto locale.",
        "ollama_offline_note": "\n\n📌 Traduzione locale non disponibile (Ollama spento) — risposta in inglese.",
        "main_menu": "Menu principale:",
        "about": "«Eco Nojin» è una piattaforma basata sulla conoscenza per agricoltura intelligente per il clima, acqua, suolo e carbonio.\nLe risposte si basano su fonti scientifiche (FAO e partner) e sul motore HyDroMa.",
    },
    "ms": {
        "greeting": "🌱 Selamat datang ke bot «Eco Nojin»!\nNasihat saintifik untuk pertanian, air dan tanah — percuma.\nPilih bahasa anda:",
        "advice_btn": "💬 Nasihat",
        "farm_btn": "🌾 Daftar ladang",
        "about_btn": "ℹ️ Tentang",
        "lang_btn": "🌐 Bahasa",
        "ask_prompt": "Tulis soalan anda (cth: apakah nisbah C/N kompos yang sepatutnya?)",
        "farm_name_q": "Masukkan nama ladang:",
        "farm_area_q": "Masukkan keluasan dalam hektar (cth 5.5):",
        "farm_loc_q": "Hantar lokasi atau tulis «lat, lon» (cth 35.6892, 51.3890):",
        "farm_soil_q": "Masukkan jenis tanah (pilihan — hantar «-» untuk langkau):",
        "farm_saved": "✅ Ladang «{name}» didaftarkan!",
        "no_answer": "⚠️ Tiada jawapan dalam pangkalan pengetahuan. Ulang soalan atau rujuk pakar tempatan.",
        "ollama_offline_note": "\n\n📌 Terjemahan tempatan tidak tersedia (Ollama mati) — jawapan dalam bahasa Inggeris.",
        "main_menu": "Menu utama:",
        "about": "«Eco Nojin» ialah platform berasaskan pengetahuan untuk pertanian pintar iklim, air, tanah dan karbon.\nJawapan berdasarkan sumber saintifik (FAO dan rakan) serta enjin HyDroMa.",
    },
}

DEFAULT_LANGUAGE = "fa"

# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------
_PERSIAN_CHARS = set("پچژگ")
_URDU_CHARS = set("ٹڈڑںےہ")
_ARABIC_SCRIPT = set("ابتثجحخدذرزسشصضطظعغفقكلمنهويىءآأؤإ")


def detect_language(lang_code: str | None, text: str = "") -> str:
    """Best-effort detection: BCP-47 code first, then script heuristics.

    Returns one of the supported 14 codes. Falls back to ``fa`` (the
    project's primary audience) when there is no signal.
    """
    if lang_code:
        base = lang_code.split("-")[0].split("_")[0].lower()
        if base in LANGUAGES:
            return base

    sample = (text or "").strip()
    if sample:
        if any(c in _URDU_CHARS for c in sample):
            return "ur"
        if any(c in _PERSIAN_CHARS for c in sample):
            return "fa"
        if any(c in _ARABIC_SCRIPT for c in sample):
            return "ar"
        if any("\u0900" <= c <= "\u097F" for c in sample):
            return "hi"
        if any("\u0980" <= c <= "\u09FF" for c in sample):
            return "bn"
        if any("\u0400" <= c <= "\u04FF" for c in sample):
            return "ru"
        if any("\u4E00" <= c <= "\u9FFF" or "\u3040" <= c <= "\u30FF" for c in sample):
            return "zh"
    return DEFAULT_LANGUAGE


def t(lang: str, key: str) -> str:
    """Translate a UI key for the given language (falls back to Persian)."""
    table = UI.get(lang) or UI[DEFAULT_LANGUAGE]
    return table.get(key, UI[DEFAULT_LANGUAGE].get(key, key))
