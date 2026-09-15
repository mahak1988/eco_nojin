/** Formula verification page — runs the independent engine check suite and
 * shows the internal database health (journal mode, size, key tables). */

import { useCallback, useEffect, useState } from 'react';
import { CheckCircle2, Database, RefreshCcw, ShieldCheck, TriangleAlert, XCircle } from 'lucide-react';
import Seo from '../../../components/ui/Seo';
import { getApiBase } from '../../../lib/api';
import { useLang } from '../../../i18n/LanguageContext';

interface Check {
  id: string;
  label: string;
  kind: 'identity' | 'reference' | 'consistency' | string;
  source: string;
  expected: number | string;
  actual: number | string;
  tolerance: number;
  unit: string;
  passed: boolean;
  note: string;
}

interface ValidationReport {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  checks: Check[];
}

interface DbStats {
  dialect: string;
  journal_mode?: string;
  foreign_keys?: number;
  db_size_mb?: number;
  tables?: string[];
  total_rows?: number;
  indexes?: string[];
  row_counts?: Record<string, number>;
}

const KIND_LABEL: Record<string, { fa: string; en: string; cls: string }> = {
  identity: { fa: 'اتحاد ریاضی', en: 'identity', cls: 'bg-leaf-500/15 text-leaf-300' },
  reference: { fa: 'مرجع منتشرشده', en: 'reference', cls: 'bg-aqua-500/15 text-aqua-300' },
  consistency: { fa: 'سازگاری مدل‌ها', en: 'consistency', cls: 'bg-sand-500/15 text-sand-300' },
};

/** A5 — formula verification + database health (hydroma-ops API). */
export default function ValidationPage() {
  const { lang, t } = useLang();
  const isFa = lang === 'fa';
  const [report, setReport] = useState<ValidationReport | null>(null);
  const [db, setDb] = useState<DbStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [vr, dr] = await Promise.all([
        fetch(`${getApiBase()}/api/v1/hydroma/validation`),
        fetch(`${getApiBase()}/api/v1/hydroma/db-stats`),
      ]);
      if (!vr.ok) throw new Error(`validation_${vr.status}`);
      setReport((await vr.json()) as ValidationReport);
      if (dr.ok) setDb((await dr.json()) as DbStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-5">
      <Seo title={`${isFa ? 'راستی‌آزمایی فرمول‌ها' : 'Formula verification'} | ${t.brand.name}`} path="/dashboard/validation" />
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-display text-3xl font-semibold text-ink-1">
          {isFa ? 'راستی‌آزمایی فرمول‌ها و سلامت دیتابیس' : 'Formula verification & database health'}
        </h1>
        <button
          type="button"
          onClick={load}
          className="inline-flex items-center gap-2 rounded-full bg-white/5 px-4 py-2 text-xs font-bold text-ink-2 hover:text-leaf-300"
        >
          <RefreshCcw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} aria-hidden />
          {isFa ? 'اجرای مجدد' : 'Re-run'}
        </button>
      </div>

      {error ? (
        <p role="alert" className="rounded-2xl border border-red-400/30 bg-red-400/10 p-4 text-sm font-bold text-red-300" dir="ltr">
          {isFa ? 'اتصال به سرویس برقرار نشد — بک‌اند را بررسی کنید: ' : 'Service unreachable: '}{error}
        </p>
      ) : null}

      {/* summary */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="glass rounded-2xl p-4 text-center">
          <p className="font-display text-3xl font-semibold text-leaf-200" dir="ltr">
            {report ? `${report.passed}/${report.total}` : '—'}
          </p>
          <p className="text-[11px] text-ink-3">{isFa ? 'چک موفق' : 'checks passed'}</p>
        </div>
        <div className="glass rounded-2xl p-4 text-center">
          <p className="font-display text-3xl font-semibold text-aqua-300" dir="ltr">
            {report ? `${Math.round(report.pass_rate * 100)}%` : '—'}
          </p>
          <p className="text-[11px] text-ink-3">{isFa ? 'نرخ موفقیت' : 'pass rate'}</p>
        </div>
        <div className="glass rounded-2xl p-4 text-center">
          <p className="font-display text-3xl font-semibold text-ink-1" dir="ltr">{db?.journal_mode ?? '—'}</p>
          <p className="text-[11px] text-ink-3">{isFa ? 'حالت ژورنال SQLite' : 'SQLite journal'}</p>
        </div>
        <div className="glass rounded-2xl p-4 text-center">
          <p className="font-display text-3xl font-semibold text-ink-1" dir="ltr">
            {db ? `${db.db_size_mb ?? 0} MB` : '—'}
          </p>
          <p className="text-[11px] text-ink-3">
            {isFa ? `${db?.tables?.length ?? 0} جدول · ${db?.total_rows ?? 0} ردیف` : `${db?.tables?.length ?? 0} tables · ${db?.total_rows ?? 0} rows`}
          </p>
        </div>
      </div>

      {loading ? (
        <p className="glass rounded-2xl p-5 text-center text-sm text-ink-3">
          {isFa ? 'در حال اجرای چک‌ها…' : 'Running checks…'}
        </p>
      ) : null}

      {/* checks */}
      {report ? (
        <div className="glass rounded-2xl p-5">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-extrabold text-ink-1">
            <ShieldCheck className="h-4 w-4 text-leaf-400" aria-hidden />
            {isFa ? 'چک‌های مستقل فرمول‌ها' : 'Independent formula checks'}
            <span className="text-[11px] font-bold text-ink-3">
              ({report.passed} ✓ / {report.failed} ✗)
            </span>
          </h2>
          <div className="flex flex-col gap-2">
            {report.checks.map((check) => {
              const kind = KIND_LABEL[check.kind] ?? { fa: check.kind, en: check.kind, cls: 'bg-white/10 text-ink-3' };
              return (
                <div key={check.id} className="rounded-xl bg-white/4 p-3.5">
                  <div className="flex flex-wrap items-center gap-2">
                    {check.passed ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-leaf-400" aria-hidden />
                    ) : (
                      <XCircle className="h-4 w-4 shrink-0 text-red-400" aria-hidden />
                    )}
                    <span className="text-xs font-extrabold text-ink-1" dir="ltr">{check.id}</span>
                    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${kind.cls}`}>
                      {isFa ? kind.fa : kind.en}
                    </span>
                    <span className="ms-auto font-mono text-[10px] text-ink-3" dir="ltr">
                      exp {String(check.expected)} → act {String(check.actual)} {check.unit}
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs leading-6 text-ink-2">{check.label}</p>
                  <p className="mt-0.5 text-[10px] leading-5 text-ink-3" dir="ltr">
                    {check.source}
                  </p>
                  {check.note ? (
                    <p className="mt-0.5 flex items-start gap-1 text-[10px] leading-5 text-sand-300/90">
                      <TriangleAlert className="mt-0.5 h-3 w-3 shrink-0" aria-hidden />
                      <span dir="ltr">{check.note}</span>
                    </p>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* database detail */}
      {db ? (
        <div className="glass rounded-2xl p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-extrabold text-ink-1">
            <Database className="h-4 w-4 text-aqua-400" aria-hidden />
            {isFa ? 'سلامت دیتابیس داخلی' : 'Internal database health'}
          </h2>
          <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
            <div className="flex items-baseline justify-between gap-3 rounded-lg bg-black/20 px-3 py-2">
              <dt className="text-[11px] font-bold text-ink-3" dir="ltr">journal_mode</dt>
              <dd className="font-mono text-xs text-leaf-300" dir="ltr">{db.journal_mode}</dd>
            </div>
            <div className="flex items-baseline justify-between gap-3 rounded-lg bg-black/20 px-3 py-2">
              <dt className="text-[11px] font-bold text-ink-3" dir="ltr">foreign_keys</dt>
              <dd className="font-mono text-xs text-leaf-300" dir="ltr">{String(db.foreign_keys)}</dd>
            </div>
            <div className="flex items-baseline justify-between gap-3 rounded-lg bg-black/20 px-3 py-2">
              <dt className="text-[11px] font-bold text-ink-3" dir="ltr">indexes</dt>
              <dd className="font-mono text-xs text-ink-1" dir="ltr">{db.indexes?.length ?? 0}</dd>
            </div>
            <div className="flex items-baseline justify-between gap-3 rounded-lg bg-black/20 px-3 py-2">
              <dt className="text-[11px] font-bold text-ink-3" dir="ltr">tables</dt>
              <dd className="font-mono text-xs text-ink-1" dir="ltr">{db.tables?.length ?? 0}</dd>
            </div>
          </dl>
          <p className="mt-3 text-[10px] leading-5 text-ink-3">
            {isFa
              ? 'هفت‌ترین جدول‌ها: '
              : 'Hottest tables: '}
            <span dir="ltr">
              {Object.entries(db.row_counts ?? {})
                .sort((a, b) => b[1] - a[1])
                .slice(0, 6)
                .map(([k, v]) => `${k}:${v}`)
                .join(' · ')}
            </span>
          </p>
        </div>
      ) : null}
    </div>
  );
}
