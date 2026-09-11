import { useCallback, useEffect, useState } from 'react';
import { RefreshCcw, ShieldCheck, WifiOff } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { getApiBase } from '../lib/api';
import { status } from '../content/pages/status';

type Probe = 'checking' | 'online' | 'offline';

/** Status page — polls the real gateway /health endpoint every 30s. */
export default function StatusPage() {
  const { lang, t } = useLang();
  const c = status[lang as 'fa' | 'en'];
  const [probe, setProbe] = useState<Probe>('checking');
  const [latency, setLatency] = useState<number | null>(null);

  const check = useCallback(async () => {
    setProbe('checking');
    const started = performance.now();
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 10000);
      const response = await fetch(`${getApiBase()}/health`, { signal: controller.signal });
      clearTimeout(timer);
      setLatency(Math.round(performance.now() - started));
      setProbe(response.ok ? 'online' : 'offline');
    } catch {
      setLatency(null);
      setProbe('offline');
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, [check]);

  const badge =
    probe === 'online'
      ? 'border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]'
      : probe === 'offline'
        ? 'border-red-400/40 bg-red-400/10 text-red-300'
        : 'border-white/15 bg-white/5 text-[var(--color-night-200)]/70';

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/status" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-3xl">
          <Reveal>
            <div className="glass flex flex-col items-center gap-4 rounded-3xl p-10 text-center">
              <span className={`inline-flex items-center gap-2 rounded-full border px-5 py-2 text-sm font-extrabold ${badge}`}>
                {probe === 'online' ? (
                  <ShieldCheck className="h-4 w-4" aria-hidden />
                ) : probe === 'offline' ? (
                  <WifiOff className="h-4 w-4" aria-hidden />
                ) : null}
                {probe === 'online' ? c.online : probe === 'offline' ? c.offline : c.checking}
              </span>
              {probe !== 'checking' && latency !== null ? (
                <p className="text-xs text-[var(--color-night-200)]/55">
                  {c.latencyLabel}: <span dir="ltr">{latency} ms</span>
                </p>
              ) : null}
              <button
                type="button"
                onClick={check}
                className="glass glass-hover inline-flex items-center gap-2 rounded-full px-5 py-2 text-xs font-extrabold text-[var(--color-night-100)]"
              >
                <RefreshCcw className="h-3.5 w-3.5" aria-hidden />
                {c.refresh}
              </button>
              <p className="text-[11px] text-[var(--color-night-200)]/35">{c.autoNote}</p>
            </div>
          </Reveal>

          <div className="mt-10">
            <SectionHeading kicker={c.kicker} title={c.scopeTitle} />
            <ul className="mt-6 flex flex-col gap-3">
              {c.scope.map((item, index) => (
                <Reveal key={item} delay={index * 0.05}>
                  <li className="glass flex items-start gap-3 rounded-2xl p-4">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-leaf-400)]" aria-hidden />
                    <span className="text-sm leading-7 text-[var(--color-night-200)]/70">{item}</span>
                  </li>
                </Reveal>
              ))}
            </ul>
          </div>

          <div className="mt-10">
            <Reveal>
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.incidentsTitle}</h2>
              <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/55">{c.incidentsNote}</p>
            </Reveal>
          </div>
        </div>
      </section>
    </>
  );
}
