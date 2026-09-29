import { getTranslations } from 'next-intl/server';
import type { ReactNode } from 'react';

/**
 * The transparency bar of §8 / §4.6, and the reason T07 exists.
 *
 * The master plan's gap table row 6 records "۱۱۰ صفحهٔ مدل علمی تک‌الگو" — a
 * hundred and ten scientific pages on one archetype — and §6 answers it with
 * T07: *پنل ورودی چسبان + صحنهٔ خروجی + نوار نسخه/کالیبراسیون/عدمقطعیت*, a
 * sticky input panel, an output scene, and a bar carrying the model version, the
 * calibration and the uncertainty. The plan's rule is "هر عدد مُهر دارد" — every
 * number carries a stamp.
 *
 * ## Why a slot can be empty
 *
 * A slot with no value in the contract renders the *explicit* "not published by
 * this contract" label rather than a plausible-looking number. That is the whole
 * point. The six HyDroMa tool families publish `{id, name_en, description,
 * reference, params}` and nothing else: no version, no calibration state, no
 * confidence interval, no run identifier. Inventing any of them would be
 * fabricating the exact evidence the bar exists to demand, and the reader would
 * have no way to tell. An empty slot that says so is a finding; a filled slot
 * that is invented is a lie.
 *
 * Where a value *is* published it is read from the response, never composed:
 *
 *   version      `ModelMeta.version`            hydroma_dashboard.py:70
 *   calibration  `ModelMeta.reference` +         hydroma_dashboard.py:72, 75-76
 *                `validation.status` / `last_validated`
 *   uncertainty  `BenchmarkData.accuracy_score` hydroma_dashboard.py:62
 *                or `CheckResult.tolerance`     formula_checks.py:45
 *   run          `ValidationReport.generated_at` hydroma_dashboard.py:115
 *                / `SlaughterhouseStatus.last_run` hydroma_dashboard.py:125
 */
export interface ProvenanceBarProps {
  /** The published version string, or `null` when the contract has no such field. */
  modelVersion?: string | null;
  /**
   * The calibration. Composed from the cited method and the validation state
   * only when the response publishes both; the caller decides, because only the
   * caller knows the response shape.
   */
  calibration?: ReactNode | null;
  /** The uncertainty the contract publishes, already formatted with its unit. */
  confidence?: ReactNode | null;
  /** The run identifier or run timestamp the contract publishes. */
  run?: ReactNode | null;
  className?: string;
}

/** One slot. An empty slot is stated, never padded with a plausible number. */
function Slot({ label, value, missing }: { label: string; value: ReactNode; missing: string }) {
  const empty = value === null || value === undefined || value === false || value === '';
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <dt className="text-xs font-semibold text-ink-faint">{label}</dt>
      <dd className={empty ? 'text-xs text-copper' : 'num text-xs text-ink'}>
        {empty ? missing : value}
      </dd>
    </div>
  );
}

export async function ProvenanceBar({
  modelVersion,
  calibration,
  confidence,
  run,
  className = '',
}: ProvenanceBarProps) {
  const t = await getTranslations('hydroma.provenance');

  return (
    <section
      aria-label={t('heading')}
      data-region-hydroma-provenance="bar"
      className={`rounded-[var(--radius-m)] border border-line bg-surface-2 p-3 ${className}`}
    >
      <h3 className="field-label mb-3">{t('heading')}</h3>
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Slot label={t('version')} value={modelVersion ?? null} missing={t('notPublished')} />
        <Slot label={t('calibration')} value={calibration ?? null} missing={t('notPublished')} />
        <Slot label={t('confidence')} value={confidence ?? null} missing={t('notPublished')} />
        <Slot label={t('run')} value={run ?? null} missing={t('notPublished')} />
      </dl>
    </section>
  );
}

export default ProvenanceBar;
