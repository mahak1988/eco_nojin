/** Regional Settings Page — Pakistan, Afghanistan localization. */

import { useState } from 'react';
import { useBilingual } from '../../hooks/useBilingual';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import SectionHeading from '../../components/ui/SectionHeading';
import { Globe, Smartphone, MapPin, CreditCard, Shield, Zap } from 'lucide-react';

const REGIONAL_CONTENT = {
  fa: {
    title: 'تنظیمات منطقه‌ای',
    lead: 'تنظیمات ویژه برای پاکستان و افغانستان — محلی‌سازی، پشتیبانی زبانی، و قوانین منطقه‌ای.',
    zones: {
      pakistan: 'پاکستان',
      afghanistan: 'افغانستان',
    },
    languages: 'زبان‌های پشتیبانی‌شده',
    urdu: 'اردو',
    pashto: 'پښتو',
    english: 'انگریزی',
    pricing: 'قیمت‌گذاری منطقه‌ای',
    compliance: 'انطباق قانونی',
    regionalRouting: 'مسیریابی منطقه‌ای',
    currency: 'واحد پول',
    units: 'واحدهای اندازه‌گیری',
  },
  en: {
    title: 'Regional Settings',
    lead: 'Settings for Pakistan and Afghanistan — localization, language support, and regional compliance.',
    zones: {
      pakistan: 'Pakistan',
      afghanistan: 'Afghanistan',
    },
    languages: 'Supported Languages',
    urdu: 'Urdu',
    pashto: 'Pashto',
    english: 'English',
    pricing: 'Regional Pricing',
    compliance: 'Legal Compliance',
    regionalRouting: 'Regional Routing',
    currency: 'Currency',
    units: 'Measurement Units',
  },
  ur: {
    title: 'علاقہ‌وار ترتیبات',
    lead: 'پاکستان اور افغانستان کے لیے ترتیبات — مقامی سازی، زبان حمایت، اور علاقہ وار منظوری.',
    zones: {
      pakistan: 'پاکستان',
      afghanistan: 'افغانستان',
    },
    languages: 'حمایت شدہ زبانیں',
    urdu: 'اردو',
    pashto: 'پشتو',
    english: 'انگریزی',
    pricing: 'علاقہ وار شماریات',
    compliance: 'قانونی پابندی',
    regionalRouting: 'علاقہ وار راستہ دہی',
    currency: 'کرنسی',
    units: 'پیمائش کی اکائیاں',
  },
  ps: {
    title: 'د سیمه ترتیبات',
    lead: 'د پاکستان او افغانستان لپاره ترتیبات — سیمه‌ای سازي، ژبه ملاتړ، او سیمه‌ای پابندی.',
    zones: {
      pakistan: 'پاکستان',
      afghanistan: 'افغانستان',
    },
    languages: 'پښته ژبنې',
    urdu: 'اردو',
    pashto: 'پښتو',
    english: 'انگلیسي',
    pricing: 'سیمه‌ای پلې',
    compliance: 'قانوني پابندی',
    regionalRouting: 'سیمه‌ای تېرگاه',
    currency: 'د پول واحد',
    units: 'د اندازې واحدونه',
  },
};

export default function RegionalSettingsPage() {
  const { t, lang } = useBilingual();
  const c = REGIONAL_CONTENT[lang as keyof typeof REGIONAL_CONTENT] ?? REGIONAL_CONTENT.fa;
  const isFa = lang === 'fa';
  const f = (persian: string, english: string) => (isFa ? persian : english);
  const [selectedRegion, setSelectedRegion] = useState<'pakistan' | 'afghanistan'>('pakistan');

  return (
    <>
      <Seo
        title={`${c.title} | ${t.brand.name}`}
        description={c.lead}
        path="/dashboard/regional"
      />
      <PageHeader
        kicker={f('پلتفرم', 'Platform')}
        title={c.title}
        lead={c.lead}
      />

      <section className="px-4 py-12 sm:px-6" id="regional">
        <div className="mx-auto flex max-w-5xl flex-col gap-8">
          <Reveal>
            <div className="mx-auto max-w-2xl text-center">
              <SectionHeading
                kicker={f('منطقه‌ای تنظیمات', 'Regional Config')}
                title={f('پاکستان و افغانستان', 'Pakistan & Afghanistan')}
                lead={f('زمینه‌های مخصوص هر منطقه را پیکربندی کنید.', 'Configure region-specific settings.')}
              />
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="grid gap-4 md:grid-cols-2">
              <button
                type="button"
                onClick={() => setSelectedRegion('pakistan')}
                className={`glass rounded-2xl p-6 text-left transition hover:shadow-lg ${
                  selectedRegion === 'pakistan' ? 'ring-2 ring-[var(--color-leaf-500)]' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                  <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{c.zones.pakistan}</h3>
                </div>
                <p className="text-xs text-[var(--color-night-200)]/60">{isFa ? 'اردو، پنجاب، سند، بلوچستان' : 'Urdu, Punjab, Sindh, Balochistan'}</p>
              </button>

              <button
                type="button"
                onClick={() => setSelectedRegion('afghanistan')}
                className={`glass rounded-2xl p-6 text-left transition hover:shadow-lg ${
                  selectedRegion === 'afghanistan' ? 'ring-2 ring-[var(--color-leaf-500)]' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                  <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{c.zones.afghanistan}</h3>
                </div>
                <p className="text-xs text-[var(--color-night-200)]/60">{isFa ? 'پښتو، دری، کابل، مزار' : 'Pashto, Dari, Kabul, Mazar'}</p>
              </button>
            </div>
          </Reveal>

          <Reveal delay={0.2}>
            <div className="grid gap-4 md:grid-cols-3">
              <FeatureCard icon={<Globe className="h-5 w-5" />} title={c.languages} detail={`${c.urdu} · ${c.pashto} · ${c.english}`} />
              <FeatureCard icon={<Smartphone className="h-5 w-5" />} title={c.regionalRouting} detail={isFa ? 'USSD/SMS/IVR' : 'USSD/SMS/IVR'} />
              <FeatureCard icon={<Shield className="h-5 w-5" />} title={c.compliance} detail={isFa ? 'قوانین محلی' : 'Local laws'} />
              <FeatureCard icon={<CreditCard className="h-5 w-5" />} title={c.currency} detail={isFa ? 'PKR/AFN' : 'PKR/AFN'} />
              <FeatureCard icon={<Zap className="h-5 w-5" />} title={c.pricing} detail={isFa ? 'محلی قیمت‌ها' : 'Local prices'} />
              <FeatureCard icon={<MapPin className="h-5 w-5" />} title={c.units} detail={isFa ? 'متريک/امپريال' : 'Metric/Imperial'} />
            </div>
          </Reveal>

          <Reveal delay={0.3}>
            <div className="glass rounded-2xl p-6">
              <h3 className="text-base font-extrabold text-[var(--color-night-100)] mb-3">
                {isFa ? 'فعال‌سازی زبان' : 'Language Activation'}
              </h3>
              <p className="text-sm text-[var(--color-night-200)]/60 mb-4">
                {isFa ? 'اردو و پښتو به‌زودی در فرانت‌اند فعال خواهند شد. در حال حاضر از فارسی و انگلیسی استفاده کنید.' : 'Urdu and Pashto will be available soon. Currently use Persian or English.'}
              </p>
              <code className="block rounded-lg bg-black/5 p-3 text-[10px] dir-ltr text-left overflow-x-auto">
                {`// Content structure ready in site.ts (fa/en)
// Translations loading from backend i18n (14 langs)
// Frontend ur/ps support: In Progress`}
              </code>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}

function FeatureCard({ icon, title, detail }: { icon: React.ReactNode; title: string; detail: string }) {
  return (
    <div className="glass rounded-2xl p-5">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[var(--color-leaf-400)]">{icon}</span>
        <h4 className="text-sm font-extrabold text-[var(--color-night-100)]">{title}</h4>
      </div>
      <p className="text-xs text-[var(--color-night-200)]/60">{detail}</p>
    </div>
  );
}
