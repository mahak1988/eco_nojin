import { Shield, Award, CheckCircle } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

interface Badge {
  icon: 'shield' | 'award' | 'check';
  title: string;
  desc: string;
}

const BADGES_FA: Badge[] = [
  { icon: 'shield', title: 'رمزنگاری هیبریدی', desc: 'Kyber + Dilithium در مسیر داده' },
  { icon: 'award', title: 'مجوز MIT', desc: 'هسته متن‌باز تحت مجوز MIT' },
  { icon: 'check', title: 'MRV تأییدشده', desc: 'ثبت بلاکچین پالیگون تأیید شده' },
];

const BADGES_EN: Badge[] = [
  { icon: 'shield', title: 'Hybrid Encryption', desc: 'Kyber + Dilithium on data path' },
  { icon: 'award', title: 'MIT Licensed', desc: 'Open source core under MIT' },
  { icon: 'check', title: 'Verified MRV', desc: 'Polygon blockchain confirmed' },
];

/** Certification and trust badges. */
export default function CertBadges() {
  const { lang } = useLang();
  const badges = lang === 'fa' ? BADGES_FA : BADGES_EN;

  const iconMap = { shield: Shield, award: Award, check: CheckCircle };

  return (
    <Reveal>
      <section className="px-4 py-12 sm:px-6" aria-label="Certifications">
        <div className="mx-auto max-w-6xl flex flex-wrap justify-center gap-4">
          {badges.map((badge) => {
            const Icon = iconMap[badge.icon];
            return (
              <div
                key={badge.title}
                className="flex items-center gap-3 rounded-2xl glass px-5 py-3"
              >
                <Icon className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                <div>
                  <p className="text-sm font-bold text-[var(--color-night-100)]">{badge.title}</p>
                  <p className="text-xs text-[var(--color-night-200)]/50">{badge.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </Reveal>
  );
}
