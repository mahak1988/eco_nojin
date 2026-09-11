import { Globe, Landmark, Mail, Scale } from 'lucide-react';
import { Link } from 'react-router-dom';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import StatsBand from '../components/sections/StatsBand';
import CtaBand from '../components/sections/CtaBand';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';

/** About page: mission, phase timeline, key numbers, invitation and contact endpoints. */
export default function AboutPage() {
  const { t, lang } = useLang();

  const contacts = [
    { icon: Mail, label: t.about.emailLabel, value: t.about.email, href: `mailto:${t.about.email}` },
    { icon: Globe, label: t.about.siteLabel, value: t.about.site, href: 'https://econojin.org' },
    { icon: Scale, label: t.about.licenseLabel, value: t.about.license, href: null },
    { icon: Landmark, label: t.about.legalEntityLabel, value: t.about.legalEntity, href: null },
  ];

  return (
    <>
      <Seo title={`${t.about.title} | ${t.brand.name}`} description={t.about.lead} path="/about" />
      <PageHeader kicker={t.about.kicker} title={t.about.title} lead={t.about.lead} />

      {/* mission */}
      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[1.3fr_1fr]">
          <div className="flex flex-col gap-5">
            {t.about.paragraphs.map((paragraph, index) => (
              <Reveal key={index} delay={index * 0.08}>
                <p className="glass rounded-3xl p-7 text-base leading-9 text-[var(--color-night-100)]/80">
                  {paragraph}
                </p>
              </Reveal>
            ))}

            {/* open-source contribution */}
            <Reveal delay={0.16}>
              <div className="glass rounded-3xl p-7">
                <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">
                  {t.about.contributingTitle}
                </h2>
                <p className="mt-2 text-sm leading-8 text-[var(--color-night-200)]/65">
                  {t.about.contributingBody}
                </p>
                <Link
                  to="/developers"
                  className="mt-3 inline-flex w-fit items-center gap-2 text-sm font-extrabold text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)]"
                >
                  {lang === 'fa' ? 'برای توسعه‌دهندگان' : 'For developers'}
                </Link>
              </div>
            </Reveal>
          </div>

          {/* invite + contact */}
          <div className="flex flex-col gap-5">
            <Reveal delay={0.1}>
              <div className="ring-glow flex flex-col gap-3 rounded-3xl bg-gradient-to-b from-leaf-600/20 to-night-900 p-7">
                <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{t.about.inviteTitle}</h2>
                <p className="text-sm leading-8 text-[var(--color-night-200)]/70">{t.about.invite}</p>
                <Link
                  to="/contact"
                  className="mt-1 w-fit rounded-full bg-[var(--color-leaf-500)] px-5 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
                >
                  {t.about.contactPageLink}
                </Link>
              </div>
            </Reveal>

            <Reveal delay={0.18}>
              <div className="glass flex flex-col gap-4 rounded-3xl p-7">
                <h2 className="text-sm font-extrabold text-[var(--color-night-100)]">{t.about.contactTitle}</h2>
                {contacts.map((item) => {
                  const Inner = (
                    <>
                      <item.icon className="h-4 w-4 shrink-0 text-[var(--color-leaf-400)]/80" aria-hidden />
                      <span className="text-xs text-[var(--color-night-200)]/45">{item.label}</span>
                      <span className="ms-auto text-sm font-bold text-[var(--color-night-100)]/90" dir="ltr">
                        {item.value}
                      </span>
                    </>
                  );
                  return item.href ? (
                    <a
                      key={item.label}
                      href={item.href}
                      className="glass glass-hover flex items-center gap-2.5 rounded-2xl px-4 py-3"
                    >
                      {Inner}
                    </a>
                  ) : (
                    <div key={item.label} className="glass flex items-center gap-2.5 rounded-2xl px-4 py-3">
                      {Inner}
                    </div>
                  );
                })}
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <StatsBand />

      {/* phase timeline */}
      <section className="px-4 py-12 sm:px-6" id="timeline">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <Reveal className="flex flex-col gap-2">
            <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
              {t.about.timelineTitle}
            </h2>
            <p className="text-xs leading-6 text-[var(--color-night-200)]/45">{t.about.timelineNote}</p>
          </Reveal>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {t.about.timeline.map((item, index) => (
              <Reveal key={item.id} delay={(index % 3) * 0.06}>
                <div className="glass glass-hover flex h-full flex-col gap-2 rounded-2xl p-5">
                  <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/15 text-xs font-extrabold text-[var(--color-leaf-300)]">
                    {item.id}
                  </span>
                  <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{item.title}</h3>
                  <p className="text-xs leading-6 text-[var(--color-night-200)]/60">{item.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <CtaBand />
    </>
  );
}
