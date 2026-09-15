import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { Send, CheckCircle2 } from 'lucide-react';
import Reveal from '../ui/Reveal';

/** Quick feedback widget with star rating. */
export default function FeedbackWidget() {
  const { lang } = useLang();
  const [rating, setRating] = useState(5);
  const [submitted, setSubmitted] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="feedback" aria-labelledby="feedback-heading">
        <div className="mx-auto max-w-lg">
          <div className="rounded-3xl glass p-8">
            <h2 id="feedback-heading" className="text-xl font-extrabold text-[var(--color-night-100)]">
              {lang === 'fa' ? 'نظرسنجی سریع' : 'Quick Feedback'}
            </h2>
            <p className="mt-2 text-sm text-[var(--color-night-200)]/60">
              {lang === 'fa' ? 'نظرتان برای ما ارزشمند است.' : 'Your opinion matters to us.'}
            </p>

            {submitted ? (
              <div className="mt-6 flex items-center gap-2 text-[var(--color-leaf-400)]">
                <CheckCircle2 className="h-5 w-5" aria-hidden />
                <span className="font-bold">{lang === 'fa' ? 'ممنون از نظر شما!' : 'Thank you!'}</span>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
                <div className="flex gap-1" role="radiogroup" aria-label={lang === 'fa' ? 'امتیاز' : 'Rating'}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setRating(star)}
                      className={`text-2xl transition-colors ${star <= rating ? 'text-yellow-400' : 'text-[var(--color-night-200)]/20'}`}
                      aria-label={`${star} ${lang === 'fa' ? 'ستاره' : 'stars'}`}
                      role="radio"
                      aria-checked={rating === star}
                    >
                      ★
                    </button>
                  ))}
                </div>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={3}
                  placeholder={lang === 'fa' ? 'نظر خود را بنویسید...' : 'Write your feedback...'}
                  className="w-full rounded-2xl bg-white/5 border border-white/10 p-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)] focus:outline-none resize-none"
                />
                <button
                  type="submit"
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-6 py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
                >
                  <Send className="h-3 w-3" aria-hidden />
                  {lang === 'fa' ? 'ارسال' : 'Send'}
                </button>
              </form>
            )}
          </div>
        </div>
      </section>
    </Reveal>
  );
}
