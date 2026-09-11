import { useState } from 'react';
import { Check, Server, Trash2 } from 'lucide-react';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { useLang } from '../../../i18n/LanguageContext';
import { profileSettings } from '../../../content/pages/profilesettings';
import type { SettingsContent } from '../../../content/pages/profiletypes';

const API_KEY = 'hydroma-api-base';
const HUB_KEYS = ['hydroma-client-id', 'hydroma-display-name', 'hydroma-api-base'];

/** Dashboard settings page — gateway URL, language, local data management. */
export default function SettingsPage() {
  const { lang, t, setLang } = useLang();
  const c: SettingsContent = profileSettings[lang as 'fa' | 'en'].settings;

  const [apiBase, setApiBase] = useState(() => {
    try {
      return localStorage.getItem(API_KEY) ?? 'http://localhost:8000';
    } catch {
      return 'http://localhost:8000';
    }
  });
  const [apiSaved, setApiSaved] = useState(false);
  const [apiError, setApiError] = useState(false);
  const [dataDone, setDataDone] = useState(false);

  const saveApi = () => {
    const trimmed = apiBase.trim();
    if (!/^https?:\/\/.+/.test(trimmed)) {
      setApiError(true);
      setApiSaved(false);
      return;
    }
    try {
      localStorage.setItem(API_KEY, trimmed.replace(/\/$/, ''));
      setApiError(false);
      setApiSaved(true);
    } catch (error) {
      console.error('api base save failed', error);
    }
  };

  const clearLocal = () => {
    try {
      HUB_KEYS.forEach((key) => localStorage.removeItem(key));
      setDataDone(true);
      setTimeout(() => window.location.reload(), 800);
    } catch (error) {
      console.error('local data clear failed', error);
    }
  };

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none';

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/dashboard/settings" />
      <Reveal className="flex flex-col gap-3">
        <span className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--color-leaf-500)]/30 bg-[var(--color-leaf-500)]/10 px-4 py-1 text-xs font-bold text-[var(--color-leaf-300)]">
          <Server className="h-3.5 w-3.5" aria-hidden />
          {c.kicker}
        </span>
        <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">{c.title}</h1>
        <p className="max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">{c.lead}</p>
      </Reveal>

      <div className="mt-6 flex flex-col gap-5">
        {/* API base */}
        <Reveal delay={0.05}>
          <div className="glass flex flex-col gap-3 rounded-3xl p-7">
            <h2 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.apiTitle}</h2>
            <p className="text-xs leading-6 text-[var(--color-night-200)]/55">{c.apiHint}</p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                type="url"
                dir="ltr"
                value={apiBase}
                onChange={(e) => {
                  setApiBase(e.target.value);
                  setApiSaved(false);
                  setApiError(false);
                }}
                className={inputCls}
              />
              <button
                type="button"
                onClick={saveApi}
                className="inline-flex shrink-0 items-center gap-1.5 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.02]"
              >
                {apiSaved ? <Check className="h-3.5 w-3.5" aria-hidden /> : null}
                {c.apiSave}
              </button>
            </div>
            {apiSaved ? <p className="text-[11px] font-bold text-[var(--color-leaf-300)]">{c.apiSaved}</p> : null}
            {apiError ? (
              <p role="alert" className="text-[11px] font-bold text-red-300">
                {c.apiInvalid}
              </p>
            ) : null}
          </div>
        </Reveal>

        {/* language */}
        <Reveal delay={0.1}>
          <div className="glass flex flex-col gap-3 rounded-3xl p-7 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col gap-1">
              <h2 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.langTitle}</h2>
              <p className="text-xs text-[var(--color-night-200)]/55">{c.langHint}</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setLang('fa')}
                aria-pressed={lang === 'fa'}
                className={`rounded-full px-4 py-1.5 text-xs font-extrabold ${lang === 'fa' ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]' : 'bg-white/8 text-[var(--color-night-200)]/70'}`}
              >
                فارسی
              </button>
              <button
                type="button"
                onClick={() => setLang('en')}
                aria-pressed={lang === 'en'}
                className={`rounded-full px-4 py-1.5 text-xs font-extrabold ${lang === 'en' ? 'bg-[var(--color-leaf-500)] text-[var(--color-night-950)]' : 'bg-white/8 text-[var(--color-night-200)]/70'}`}
              >
                English
              </button>
            </div>
          </div>
        </Reveal>

        {/* endpoints reference */}
        <Reveal delay={0.12}>
          <div className="glass rounded-3xl p-7">
            <h2 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.endpointsTitle}</h2>
            <div className="mt-3 flex flex-col gap-2">
              {c.endpoints.map((endpoint) => (
                <div key={endpoint.method + endpoint.path} className="flex flex-wrap items-center gap-2 rounded-xl bg-black/25 px-3 py-2">
                  <span
                    className={`rounded-md px-2 py-0.5 text-[10px] font-extrabold ${
                      endpoint.method === 'GET' ? 'bg-[var(--color-aqua-500)]/15 text-[var(--color-aqua-300)]' : 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-300)]'
                    }`}
                    dir="ltr"
                  >
                    {endpoint.method}
                  </span>
                  <span className="text-[11px] text-[var(--color-night-200)]/70" dir="ltr">
                    {endpoint.path}
                  </span>
                  <span className="ms-auto text-[11px] text-[var(--color-night-200)]/45">{endpoint.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* local data */}
        <Reveal delay={0.15}>
          <div className="glass flex flex-col gap-3 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <Trash2 className="h-4 w-4 text-red-300" aria-hidden />
              {c.dataTitle}
            </h2>
            <p className="text-xs leading-6 text-[var(--color-night-200)]/55">{c.dataHint}</p>
            <button
              type="button"
              onClick={clearLocal}
              className="w-fit rounded-full border border-red-400/40 bg-red-400/10 px-4 py-2 text-xs font-extrabold text-red-300 hover:bg-red-400/20"
            >
              {dataDone ? c.dataDone : c.dataButton}
            </button>
          </div>
        </Reveal>
      </div>
    </>
  );
}
