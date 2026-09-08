/** Footer navigation groups (bilingual) — single source for footer links. */

export interface MenuGroup {
  title: string;
  links: { to: string; label: string }[];
}

export const footerGroups: Record<'fa' | 'en', MenuGroup[]> = {
  fa: [
    {
      title: 'اصلی',
      links: [
        { to: '/', label: 'خانه' },
        { to: '/platform', label: 'پلتفرم' },
        { to: '/hydroma', label: 'علم هیدروما' },
        { to: '/impact', label: 'تأثیر' },
      ],
    },
    {
      title: 'اطلاعاتی',
      links: [
        { to: '/about', label: 'درباره و تماس' },
        { to: '/declaration', label: 'بیانیهٔ رسمی' },
        { to: '/blog', label: 'بلاگ' },
        { to: '/faq', label: 'پرسش‌های متداول' },
        { to: '/transparency', label: 'شفافیت' },
      ],
    },
    {
      title: 'خدمات',
      links: [
        { to: '/contact', label: 'تماس' },
        { to: '/support', label: 'پشتیبانی و راهنما' },
        { to: '/developers', label: 'توسعه‌دهندگان' },
        { to: '/dashboard', label: 'داشبورد هیدروما' },
        { to: '/eco-coin', label: 'اکوکوین' },
        { to: '/status', label: 'وضعیت سرویس' },
      ],
    },
    {
      title: 'فرصت‌ها',
      links: [
        { to: '/investors', label: 'سرمایه‌گذاران' },
        { to: '/partners', label: 'شرکا' },
        { to: '/careers', label: 'همکاری با ما' },
        { to: '/pilot-iran', label: 'پایلوت ایران' },
        { to: '/academia', label: 'همکاری پژوهشی' },
        { to: '/marketplace', label: 'بازارگاه' },
        { to: '/resources', label: 'منابع' },
      ],
    },
  ],
  en: [
    {
      title: 'Main',
      links: [
        { to: '/', label: 'Home' },
        { to: '/platform', label: 'Platform' },
        { to: '/hydroma', label: 'HyDroMa Science' },
        { to: '/impact', label: 'Impact' },
      ],
    },
    {
      title: 'Information',
      links: [
        { to: '/about', label: 'About & Contact' },
        { to: '/declaration', label: 'Official declaration' },
        { to: '/blog', label: 'Blog' },
        { to: '/faq', label: 'FAQ' },
        { to: '/transparency', label: 'Transparency' },
      ],
    },
    {
      title: 'Services',
      links: [
        { to: '/contact', label: 'Contact' },
        { to: '/support', label: 'Support & guides' },
        { to: '/developers', label: 'Developers' },
        { to: '/dashboard', label: 'HyDroMa dashboard' },
        { to: '/eco-coin', label: 'Eco Coin' },
        { to: '/status', label: 'Service status' },
      ],
    },
    {
      title: 'Opportunities',
      links: [
        { to: '/investors', label: 'Investors' },
        { to: '/partners', label: 'Partners' },
        { to: '/careers', label: 'Careers' },
        { to: '/pilot-iran', label: 'Iran pilot' },
        { to: '/academia', label: 'Research collaboration' },
        { to: '/marketplace', label: 'Marketplace' },
        { to: '/resources', label: 'Resources' },
      ],
    },
  ],
};

export const legalGroup: Record<'fa' | 'en', MenuGroup> = {
  fa: {
    title: 'حقوقی',
    links: [
      { to: '/terms', label: 'شرایط استفاده' },
      { to: '/rules', label: 'قوانین و مقررات' },
      { to: '/privacy', label: 'حریم خصوصی' },
    ],
  },
  en: {
    title: 'Legal',
    links: [
      { to: '/terms', label: 'Terms of Use' },
      { to: '/rules', label: 'Rules & Regulations' },
      { to: '/privacy', label: 'Privacy Policy' },
    ],
  },
};
