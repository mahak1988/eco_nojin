import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { useDisputes } from '../../hooks/useBazargahV2';
import Seo from '../../components/ui/Seo';
import { Loader2, MessageSquareWarning, Plus } from 'lucide-react';

const STATUS_STYLES: Record<string, string> = {
  open: 'bg-amber-400/10 text-amber-300 border-amber-400/30',
  under_review: 'bg-sky-400/10 text-sky-300 border-sky-400/30',
  escalated: 'bg-violet-400/10 text-violet-300 border-violet-400/30',
  resolved: 'bg-emerald-400/10 text-emerald-300 border-emerald-400/30',
  rejected: 'bg-red-400/10 text-red-300 border-red-400/30',
};

export default function MyDisputesPage() {
  const { fa } = useBilingual();
  const { data, isLoading, isError, error } = useDisputes();

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <Seo title={fa('شکایات من', 'My Disputes')} path="/marketplace/disputes" />
      <div className="mb-8 flex items-center justify-between gap-4">
        <h1 className="font-display text-2xl font-bold text-[var(--color-night-100)]">
          {fa('شکایات من', 'My Disputes')}
        </h1>
        <Link
          to="/marketplace/disputes/new"
          className="flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2.5 text-sm font-bold text-night-950 transition hover:bg-[var(--color-leaf-400)]"
        >
          <Plus className="h-4 w-4" />
          {fa('شکایت جدید', 'New dispute')}
        </Link>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center gap-2 py-16 text-[var(--color-night-200)]">
          <Loader2 className="h-5 w-5 animate-spin" />
          {fa('در حال بارگذاری...', 'Loading...')}
        </div>
      )}

      {isError && (
        <div className="rounded-2xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
          {fa(
            'برای مشاهده شکایات ابتدا وارد حساب خود شوید (۴۰۱).',
            'Please sign in to view disputes (401).',
          )}
          {error instanceof Error ? ` — ${error.message}` : ''}
        </div>
      )}

      {data && data.count === 0 && (
        <div className="rounded-2xl border border-white/10 bg-[#f6ecd6] px-6 py-12 text-center text-sm text-[var(--color-night-200)]">
          {fa('هنوز شکایتی ثبت نشده است.', 'No disputes filed yet.')}
        </div>
      )}

      {data && data.count > 0 && (
        <ul className="space-y-4">
          {data.disputes.map((d) => (
            <li key={d.id} className="glass rounded-2xl border border-white/10 p-5">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <MessageSquareWarning className="h-4 w-4 text-[var(--color-leaf-400)]" />
                <span className="text-xs text-[var(--color-night-200)]/60" dir="ltr">{d.id.slice(0, 8)}</span>
                <span className="rounded-full border border-white/10 bg-[#f6ecd6] px-2.5 py-0.5 text-xs text-[var(--color-night-200)]">
                  {d.category}
                </span>
                <span className={`rounded-full border px-2.5 py-0.5 text-xs ${STATUS_STYLES[d.status] ?? ''}`}>
                  {d.status}
                </span>
              </div>
              <p className="text-sm text-[var(--color-night-100)]">{d.description}</p>
              {d.resolution && (
                <p className="mt-2 rounded-xl bg-[#f6ecd6] px-3 py-2 text-xs text-emerald-300">
                  {fa('پاسخ:', 'Resolution:')} {d.resolution}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
