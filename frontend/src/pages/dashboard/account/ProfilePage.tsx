import { useState } from 'react';
import { Check, Copy, KeyRound, User } from 'lucide-react';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { useLang } from '../../../i18n/LanguageContext';
import { getClientId } from '../../../lib/hub';
import { profileSettings } from '../../../content/pages/profilesettings';
import type { ProfileContent } from '../../../content/pages/profiletypes';

const NAME_KEY = 'hydroma-display-name';

/** Dashboard profile page — anonymous client identity + local display name. */
export default function ProfilePage() {
  const { lang, t } = useLang();
  const c: ProfileContent = profileSettings[lang as 'fa' | 'en'].profile;

  const clientKey = getClientId();
  const [copied, setCopied] = useState(false);
  const [name, setName] = useState(() => {
    try {
      return localStorage.getItem(NAME_KEY) ?? '';
    } catch {
      return '';
    }
  });
  const [saved, setSaved] = useState(false);

  const saveName = () => {
    try {
      localStorage.setItem(NAME_KEY, name.trim());
      setSaved(true);
    } catch (error) {
      console.error('display name save failed', error);
    }
  };

  const copyKey = async () => {
    try {
      await navigator.clipboard.writeText(clientKey);
      setCopied(true);
    } catch (error) {
      console.error('copy failed', error);
    }
  };

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/dashboard/profile" />
      <Reveal className="flex flex-col gap-3">
        <span className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--color-leaf-500)]/30 bg-[var(--color-leaf-500)]/10 px-4 py-1 text-xs font-bold text-[var(--color-leaf-300)]">
          <User className="h-3.5 w-3.5" aria-hidden />
          {c.kicker}
        </span>
        <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">{c.title}</h1>
        <p className="max-w-2xl text-sm leading-7 text-[var(--color-night-200)]/60">{c.lead}</p>
      </Reveal>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <Reveal delay={0.05}>
          <div className="glass flex h-full flex-col gap-3 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <KeyRound className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />
              {c.clientKeyTitle}
            </h2>
            <p className="text-xs leading-6 text-[var(--color-night-200)]/55">{c.clientKeyHint}</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 overflow-x-auto rounded-xl bg-black/40 px-3 py-2 text-[11px] text-[var(--color-aqua-300)]" dir="ltr">
                {clientKey}
              </code>
              <button
                type="button"
                onClick={copyKey}
                className="glass glass-hover inline-flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-[11px] font-bold text-[var(--color-night-100)]"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-[var(--color-leaf-300)]" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
                {copied ? c.copied : c.copy}
              </button>
            </div>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="glass flex h-full flex-col gap-3 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <User className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />
              {c.displayNameTitle}
            </h2>
            <label className="flex flex-col gap-1.5">
              <span className="text-xs font-bold text-[var(--color-night-200)]/60">{c.displayNameLabel}</span>
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setSaved(false);
                }}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none"
              />
              <span className="text-[10px] text-[var(--color-night-200)]/35">{c.displayNameHint}</span>
            </label>
            <button
              type="button"
              onClick={saveName}
              className="w-fit rounded-full bg-[var(--color-leaf-500)]/15 px-4 py-1.5 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25"
            >
              {saved ? c.saved : c.save}
            </button>
          </div>
        </Reveal>
      </div>

      <p className="mt-6 rounded-2xl border border-[var(--color-aqua-500)]/25 bg-[var(--color-aqua-500)]/8 p-4 text-center text-xs leading-6 text-[var(--color-aqua-200)]/90">
        {c.privacyNote}
      </p>
    </>
  );
}
