import { useCallback, useEffect, useState } from 'react';
import Seo from '../../../components/ui/Seo';
import { fetchAllHealth, type HealthEntry } from '../../../lib/hydromaApi';
import { useLang } from '../../../i18n/LanguageContext';

/** A8 — live status: parallel probe of every gateway health endpoint. */
export default function LiveStatusPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [entries, setEntries] = useState<HealthEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setEntries(await fetchAllHealth());
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [load]);

  const online = entries.filter((entry) => entry.ok).length;

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'وضعیت زندهٔ درگاه' : 'Live gateway status'} | ${t.brand.name}`} path="/dashboard/live/status" />
      <h1 className="text-2xl font-extrabold text-ink-1">
        {isFa ? 'وضعیت زندهٔ درگاه' : 'Live gateway status'}
      </h1>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <div className="glass rounded-[21px] p-4 text-center">
          <p className="text-2xl font-extrabold text-leaf-300">
            {loading ? '…' : `${online}/${entries.length}`}
          </p>
          <p className="text-[11px] text-ink-3">{isFa ? 'سرویس سالم' : 'services healthy'}</p>
        </div>
      </div>

      {loading ? (
        <p className="text-xs text-ink-3">{isFa ? 'در حال بررسی…' : 'Probing…'}</p>
      ) : (
        <div className="flex flex-col gap-2">
          {entries.map((entry) => (
            <div key={entry.key} className="glass flex items-center gap-3 rounded-2xl px-4 py-3">
              <span
                className={`h-2.5 w-2.5 rounded-full ${entry.ok ? 'bg-leaf-400' : 'bg-red-400'}`}
                aria-hidden
              />
              <span className="text-xs font-extrabold text-ink-1" dir="ltr">
                {entry.key}
              </span>
              <code className="text-[11px] text-ink-3" dir="ltr">
                {entry.path}
              </code>
              <span className="ms-auto flex items-center gap-3 text-[11px] text-ink-3" dir="ltr">
                <span className={entry.ok ? 'text-leaf-300' : 'text-red-300'}>{entry.status || '—'}</span>
                <span>{entry.latencyMs}ms</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
