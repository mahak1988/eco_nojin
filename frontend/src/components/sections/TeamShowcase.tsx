import { useLang } from '../../i18n/LanguageContext';
import { Users } from 'lucide-react';
import Reveal from '../ui/Reveal';

interface TeamMember {
  name: string;
  role: string;
  bio: string;
}

const TEAM_FA: TeamMember[] = [
  { name: 'دکتر امیر حسینی', role: 'مدیرعامل و بنیان‌گذار', bio: 'مهندس محیط زیست با ۱۵ سال تجربه در مدل‌سازی هیدرولوژی.' },
  { name: 'دکتر سارا مهرپور', role: 'مدیر علمی', bio: 'دانشمند ارشد پایش ماهواره‌ای و تغییرات اقلیمی.' },
  { name: 'مهندس رضا کریمی', role: 'مدیر فنی', bio: 'مهندس نرم‌افزار با تخصص در دیجیتال‌توان و داده‌های بزرگ.' },
];

const TEAM_EN: TeamMember[] = [
  { name: 'Dr. Amir Hosseini', role: 'CEO & Founder', bio: 'Environmental engineer with 15 years in hydrological modeling.' },
  { name: 'Dr. Sara Mehripour', role: 'Science Director', bio: 'Senior scientist in satellite monitoring and climate change.' },
  { name: 'Eng. Reza Karimi', role: 'CTO', bio: 'Software engineer specializing in digital twins and big data.' },
];

/** Team members showcase. */
export default function TeamShowcase() {
  const { lang } = useLang();
  const team = lang === 'fa' ? TEAM_FA : TEAM_EN;

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="team" aria-labelledby="team-heading">
        <div className="mx-auto max-w-6xl">
          <div className="mb-8 flex items-center gap-3">
            <Users className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
            <p className="text-sm font-extrabold text-[var(--color-leaf-400)]">{lang === 'fa' ? 'تیم' : 'Team'}</p>
          </div>
          <h2 id="team-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'پشت پرده اکو نوژین' : 'Behind Eco Nojin'}
          </h2>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {team.map((member) => (
              <div key={member.name} className="rounded-3xl glass p-6 flex flex-col gap-2">
                <div className="h-12 w-12 rounded-full bg-[var(--color-leaf-500)]/15 flex items-center justify-center text-lg font-extrabold text-[var(--color-leaf-400)]">
                  {member.name.split(' ').pop()?.charAt(0) ?? '?'}
                </div>
                <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{member.name}</h3>
                <p className="text-xs font-bold text-[var(--color-aqua-300)]">{member.role}</p>
                <p className="text-sm leading-6 text-[var(--color-night-200)]/60">{member.bio}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </Reveal>
  );
}
