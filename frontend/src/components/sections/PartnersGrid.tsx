import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';
import SectionHeading from '../ui/SectionHeading';

interface Partner { title: string; icon: string; }

const PARTNERS_FA: Partner[] = [
  { title: 'شرکت ملی گاز', icon: 'globe' },
  { title: 'سازمان محیط زیست', icon: 'shield' },
  { title: 'دانشگاه تهران', icon: 'people' },
  { title: 'مؤسسه خوارزمی', icon: 'globe' },
  { title: 'سازمان فضایی', icon: 'shield' },
];

const PARTNERS_EN: Partner[] = [
  { title: 'National Gas Co.', icon: 'globe' },
  { title: 'Environment Org.', icon: 'shield' },
  { title: 'University of Tehran', icon: 'people' },
  { title: 'Khorasani Inst.', icon: 'globe' },
  { title: 'Space Org.', icon: 'shield' },
];

/** Partners and sponsors grid. */
export default function PartnersGrid() {
  const { lang } = useLang();
  const partners = lang === 'fa' ? PARTNERS_FA : PARTNERS_EN;

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="partners" aria-labelledby="partners-heading">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          kicker={lang === 'fa' ? 'شرکای ما' : 'Our Partners'}
          title={lang === 'fa' ? 'شبکه همکاران' : 'Partner Network'}
          lead={lang === 'fa' ? 'ما با نهادهای سرشناس در سطح ملی و بین‌المللی همکاری می‌کنیم.' : 'We collaborate with leading organizations.'}
        />

        <div className="mt-8 grid gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
          {partners.map((partner, index) => (
            <Reveal key={partner.title} delay={index * 0.05}>
              <div className="group flex items-center justify-center gap-3 rounded-3xl glass glass-hover p-6">
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-400)] text-lg" aria-hidden>
                  {partner.icon === 'globe' ? '🌐' : partner.icon === 'shield' ? '🛡️' : partner.icon === 'people' ? '👥' : '🤝'}
                </div>
                <span className="text-sm font-bold text-[var(--color-night-100)] group-hover:text-[var(--color-leaf-300)] transition-colors">
                  {partner.title}
                </span>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
