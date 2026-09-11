export interface GuideContent {
  kicker: string;
  title: string;
  lead: string;
  dialLabel: string;
  dialCode: string;
  menuIntro: string;
  menuTitle: string;
  menuItems: { key: string; label: string; desc: string }[];
  smsTitle: string;
  smsLead: string;
  smsCommands: { cmd: string; desc: string }[];
  smsLimits: string;
  tipsTitle: string;
  tips: string[];
}

export const ussdGuide = {
  fa: {
    kicker: 'راهنمای USSD',
    title: 'دسترسی USSD برای گوشی‌های ساده',
    lead: 'بدون اینترنت، بدون اپلیکیشن؛ فقط شمارهٔ تلفن و عدد. USSD مستقیماً روی شبکهٔ موبایل کار می‌کند.',
    dialLabel: 'شمارهٔ تماس',
    dialCode: '*384*73#',
    menuIntro: 'بر روی گوشی خود فرمان بزنید؛ منوی زیر نمایش داده می‌شود:',
    menuTitle: 'منوی USSD',
    menuItems: [
      { key: '1', label: 'تحلیل خاک', desc: 'نمایش پروفایل خاک و توصیهٔ خوراکی برای مزرعه‌تان.' },
      { key: '2', label: 'مشاورهٔ محصول', desc: 'توصیهٔ کاشت، آبیاری و مراقبت بر اساس شرایط محلی.' },
      { key: '3', label: 'قیمت محصول', desc: 'قیمت لحظه‌ای و پیش‌بینی ۱۴ روزهٔ محصولات کشاورزی.' },
      { key: '4', label: 'هوا', desc: 'هشدار اقلیمی ۷ روزه و پیش‌بینی دقیق محلی.' },
      { key: '5', label: 'پرسش از متخصص', desc: 'سوال خود را بفرستید؛ هوش مصنوعی اکو نوژین پاسخ می‌دهد.' },
      { key: '0', label: 'خروج', desc: 'خروج از منو.' },
    ],
    smsTitle: 'دستورات SMS',
    smsLead: 'در صورت عدم امکان USSD، پیامک بزنید:',
    smsCommands: [
      { cmd: 'SOIL 36.8 54.4', desc: 'تحلیل خاک برای نقطهٔ جغرافیایی (طول/عرض)' },
      { cmd: 'PRICE wheat', desc: 'قیمت لحظه‌ای گندم' },
      { cmd: 'WEATHER مشهد', desc: 'هوای مشهد' },
      { cmd: 'ASK هرساله نگهداری؟', desc: 'پرسش از متخصص — هوش مصنوعی پاسخ می‌دهد' },
      { cmd: 'LANG fa', desc: 'تغییر زبان به فارسی' },
      { cmd: 'LANG en', desc: 'تغییر زبان به انگلیسی' },
      { cmd: 'HELP', desc: 'نمایش همهٔ دستورات' },
    ],
    smsLimits: 'محدودیت ۱۶۰ کاراکتر برای پیامک؛ پاسخ USSD حداکثر ۱۸۰ کاراکتر.',
    tipsTitle: 'نکات مهم',
    tips: [
      'USSD رایگان است؛ فقط حجم دادهٔ محدود مصرف می‌کند.',
      'زبان پیامک انتخابی است — از LANG fa یا LANG en استفاده کنید.',
      'برای SOIL، مختصات را بدون فاصلهٔ اضافی وارد کنید: "SOIL 36.8 54.4".',
    ],
  },
  en: {
    kicker: 'USSD guide',
    title: 'USSD access for feature phones',
    lead: 'No internet, no app needed — just a phone number and numbers. USSD works directly on the mobile network.',
    dialLabel: 'Dial',
    dialCode: '*384*73#',
    menuIntro: 'Dial the code above; the menu below appears:',
    menuTitle: 'USSD menu',
    menuItems: [
      { key: '1', label: 'Soil Analysis', desc: 'View your soil profile and fertilizer recommendations for your field.' },
      { key: '2', label: 'Crop Advice', desc: 'Planting, irrigation and care recommendations based on local conditions.' },
      { key: '3', label: 'Market Prices', desc: 'Real-time prices and 14-day forecast for agricultural products.' },
      { key: '4', label: 'Weather', desc: '7-day weather alerts and local forecast.' },
      { key: '5', label: 'Ask Expert', desc: 'Send your question; the Eco Nojin AI answers.' },
      { key: '0', label: 'Exit', desc: 'Exit the menu.' },
    ],
    smsTitle: 'SMS commands',
    smsLead: 'If USSD is not available, send an SMS:',
    smsCommands: [
      { cmd: 'SOIL 36.8 54.4', desc: 'Soil analysis for a GPS coordinate (lat lon)' },
      { cmd: 'PRICE wheat', desc: 'Live wheat price' },
      { cmd: 'WEATHER tehran', desc: 'Tehran weather' },
      { cmd: 'ASK how to make compost?', desc: 'Ask an expert — the AI answers' },
      { cmd: 'LANG fa', desc: 'Switch to Persian' },
      { cmd: 'LANG en', desc: 'Switch to English' },
      { cmd: 'HELP', desc: 'Show all commands' },
    ],
    smsLimits: '160-character SMS limit; USSD responses max 180 characters.',
    tipsTitle: 'Important tips',
    tips: [
      'USSD is free — only minimal data volume is consumed.',
      'Language is selectable — use LANG fa or LANG en.',
      'For SOIL, enter coordinates without extra spaces: "SOIL 36.8 54.4".',
    ],
  },
} satisfies Record<'fa' | 'en', GuideContent>;

export interface VoiceGuideContent {
  kicker: string;
  title: string;
  lead: string;
  dialLabel: string;
  dialNumber: string;
  menuIntro: string;
  menuTitle: string;
  menuItems: { key: string; label: string; desc: string }[];
  voiceCommands: { phrase: string; desc: string }[];
  languages: string[];
  commandsTitle: string;
  commandsLead: string;
  tipsTitle: string;
  tips: string[];
}

export const voiceGuide = {
  fa: {
    kicker: 'راهنمای صوتی IVR',
    title: 'دسترسی صوتی برای کاربران کم‌سواد',
    lead: 'فراموش کنید که باید بخوانید؛ فقط تماس بگیرید و با فشار دادن عدد یا حرف زدن، سؤال بپرسید.',
    dialLabel: 'شمارهٔ تماس',
    dialNumber: '021-XXX-XXXX',
    menuIntro: 'تماس بگیرید؛ گواهی صوتی شما را هدایت می‌کند.',
    menuTitle: 'منوی صوتی',
    menuItems: [
      { key: '1', label: 'تحلیل خاک', desc: 'گزارش خاک و توصیهٔ خوراکی' },
      { key: '2', label: 'مشاورهٔ محصول', desc: 'راهنمایی کاشت و آبیاری' },
      { key: '3', label: 'قیمت محصول', desc: 'قیمت و پیش‌بینی بازار' },
      { key: '4', label: 'هوا', desc: 'هشدار و پیش‌بینی هوا' },
      { key: '5', label: 'پرسش از متخصص', desc: 'سؤال خود را بگویید' },
      { key: '6', label: 'حمایت', desc: 'تماس با پشتیبانی' },
      { key: '0', label: 'خروج', desc: 'پایان تماس' },
    ],
    voiceCommands: [
      { phrase: 'تحلیل خاک در مشهد', desc: 'تحلیل خاک برای شهر یا نقطهٔ جغرافیایی' },
      { phrase: 'قیمت گندم چنده؟', desc: 'قیمت لحظه‌ای هر محصول' },
      { phrase: 'فردا هوای شیراز چطوره؟', desc: 'پیش‌بینی هوا به زبان عام' },
      { phrase: 'چطور کامپوست درست کنم؟', desc: 'پرسش از متخصص — هوش مصنوعی پاسخ می‌دهد' },
    ],
    languages: ['فارسی', 'انگلیسی', 'عربی', 'ازبیک', 'سوئدی'],
    commandsTitle: 'دستورات صوتی',
    commandsLead: 'به‌جای منو، می‌توانید مستقیماً بگویید:',
    tipsTitle: 'نکات مهم',
    tips: [
      'پس از «صدای بعدی بزنید»، واضح بگویید؛ هوش مصنوعی سؤال‌تان را تشخیص می‌دهد.',
      'زبان می‌تواند در هر مرحلهٔ منو انتخاب شود.',
      'تماس‌های صوتی رایگان هستند؛ فقط زمان تماس شمارش می‌شود.',
    ],
  },
  en: {
    kicker: 'Voice IVR guide',
    title: 'Voice access for low-literacy users',
    lead: 'Forget reading — just call and ask with a keypad number or by speaking.',
    dialLabel: 'Dial',
    dialNumber: '021-XXX-XXXX',
    menuIntro: 'Call the number above; you will be guided by voice prompts.',
    menuTitle: 'Voice menu',
    menuItems: [
      { key: '1', label: 'Soil Analysis', desc: 'Soil report and fertilizer advice' },
      { key: '2', label: 'Crop Advice', desc: 'Planting and irrigation guidance' },
      { key: '3', label: 'Market Prices', desc: 'Prices and market forecast' },
      { key: '4', label: 'Weather', desc: 'Weather alerts and forecast' },
      { key: '5', label: 'Ask Expert', desc: 'Speak your question' },
      { key: '6', label: 'Support', desc: 'Contact support' },
      { key: '0', label: 'Exit', desc: 'End call' },
    ],
    voiceCommands: [
      { phrase: 'Soil analysis in Mashhad', desc: 'Soil analysis for a city or coordinate' },
      { phrase: 'What is the wheat price?', desc: 'Live price for any crop' },
      { phrase: 'What is the weather in Shiraz tomorrow?', desc: 'Weather forecast in natural language' },
      { phrase: 'How do I make compost?', desc: 'Ask an expert — the AI answers' },
    ],
    languages: ['Persian', 'English', 'Arabic', 'Uzbek', 'Swedish'],
    commandsTitle: 'Voice commands',
    commandsLead: 'Instead of the menu, you can speak directly:',
    tipsTitle: 'Important tips',
    tips: [
      'After the beep, speak clearly — the AI recognises your question.',
      'Language can be changed at any menu step.',
      'Voice calls are free; only call duration is counted.',
    ],
  },
} satisfies Record<'fa' | 'en', VoiceGuideContent>;
