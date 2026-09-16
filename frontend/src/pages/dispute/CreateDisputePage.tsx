import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import { useCreateDispute } from '../../hooks/useBazargahV2';
import Seo from '../../components/ui/Seo';
import { AlertCircle, Loader2, Send } from 'lucide-react';

const CATEGORIES = ['quality', 'delivery', 'payment', 'other'] as const;

export default function CreateDisputePage() {
  const { fa } = useBilingual();
  const navigate = useNavigate();
  const createDispute = useCreateDispute();
  const [form, setForm] = useState({ order_id: '', category: 'quality', description: '' });
  const [error, setError] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.description.trim().length < 10) {
      setError(fa('توضیحات باید حداقل ۱۰ کاراکتر باشد.', 'Description must be at least 10 characters.'));
      return;
    }
    try {
      await createDispute.mutateAsync(form);
      navigate('/marketplace/disputes');
    } catch (err) {
      setError(err instanceof Error ? err.message : fa('خطا در ثبت شکایت', 'Failed to submit dispute'));
    }
  };

  const labels: Record<string, { fa: string; en: string }> = {
    quality: { fa: 'کیفیت کالا', en: 'Product quality' },
    delivery: { fa: 'ارسال و تحویل', en: 'Delivery' },
    payment: { fa: 'پرداخت', en: 'Payment' },
    other: { fa: 'سایر', en: 'Other' },
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <Seo title={fa('ثبت شکایت', 'File a Dispute')} path="/marketplace/disputes/new" />
      <h1 className="font-display text-2xl font-bold text-[var(--color-night-100)] mb-6">
        {fa('ثبت شکایت', 'File a Dispute')}
      </h1>
      <p className="text-sm text-[var(--color-night-200)]/70 mb-8">
        {fa(
          'شکایت شما ابتدا توسط فروشنده (۴۸ ساعت)، سپس بازارچه (۷۲ ساعت) و در نهایت پلتفرم بررسی می‌شود.',
          'Your dispute is first reviewed by the vendor (48h), then the marketplace (72h), and finally the platform.',
        )}
      </p>
      <form onSubmit={submit} className="space-y-5 glass rounded-2xl border border-white/10 p-6">
        <div>
          <label className="block text-sm font-medium mb-2 text-[var(--color-night-100)]">
            {fa('شماره سفارش', 'Order ID')}
          </label>
          <input
            type="text"
            required
            value={form.order_id}
            onChange={(e) => setForm({ ...form, order_id: e.target.value })}
            className="w-full rounded-xl bg-[#f6ecd6] border border-white/10 px-4 py-2.5 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
            dir="ltr"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-[var(--color-night-100)]">
            {fa('نوع شکایت', 'Complaint type')}
          </label>
          <select
            value={form.category}
            onChange={(e) => setForm({ ...form, category: e.target.value })}
            className="w-full rounded-xl bg-[#f6ecd6] border border-white/10 px-4 py-2.5 text-sm text-[#2b2117] outline-none focus:border-[var(--color-leaf-400)]"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c} className="bg-night-900">
                {labels[c].fa} / {labels[c].en}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2 text-[var(--color-night-100)]">
            {fa('توضیحات', 'Description')}
          </label>
          <textarea
            required
            rows={5}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full rounded-xl bg-[#f6ecd6] border border-white/10 px-4 py-2.5 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
          />
        </div>
        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-3 text-sm text-red-300">
            <AlertCircle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}
        <button
          type="submit"
          disabled={createDispute.isPending}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-3 text-sm font-bold text-night-950 transition hover:bg-[var(--color-leaf-400)] disabled:opacity-50"
        >
          {createDispute.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          {fa('ثبت شکایت', 'Submit dispute')}
        </button>
      </form>
    </div>
  );
}