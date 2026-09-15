import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { ChevronDown, ChevronUp } from 'lucide-react';
import Reveal from '../ui/Reveal';
import { getFaq } from '../../content/contentHelpers';

interface FAQItemData {
  q: string;
  a: string;
}

/** Accordion FAQ preview on HomePage. */
export default function FAQAccordion() {
  const { lang } = useLang();
  const faq = getFaq(lang);
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  if (!faq?.items || faq.items.length === 0) return null;

  const items: FAQItemData[] = faq.items.slice(0, 5);

  return (
    <section className="px-4 py-16 sm:px-6 lg:py-24" id="faq-preview" aria-labelledby="faq-heading">
      <div className="mx-auto max-w-3xl">
        <p className="mb-2 text-center text-sm font-extrabold text-[var(--color-leaf-400)]">{faq.kicker}</p>
        <h2 id="faq-heading" className="mb-12 text-center text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
          {lang === 'fa' ? 'پرسش‌های متداول' : 'Frequently Asked'}
        </h2>

        <div className="flex flex-col gap-3">
          {items.map((item, index) => {
            const isOpen = openIndex === index;
            return (
              <Reveal key={item.q} delay={index * 0.05}>
                <div className="rounded-3xl glass overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setOpenIndex(isOpen ? null : index)}
                    className="flex w-full items-center justify-between gap-4 px-6 py-4 text-right"
                    aria-expanded={isOpen}
                  >
                    <span className="text-sm font-bold text-[var(--color-night-100)]">{item.q}</span>
                    {isOpen ? (
                      <ChevronUp className="h-4 w-4 shrink-0 text-[var(--color-leaf-400)]" aria-hidden />
                    ) : (
                      <ChevronDown className="h-4 w-4 shrink-0 text-[var(--color-night-200)]/50" aria-hidden />
                    )}
                  </button>
                  {isOpen && (
                    <div className="px-6 pb-4">
                      <p className="text-sm leading-7 text-[var(--color-night-200)]/70">{item.a}</p>
                    </div>
                  )}
                </div>
              </Reveal>
            );
          })}
        </div>

        <p className="mt-6 text-center text-sm">
          <a href="/faq" className="text-[var(--color-leaf-300)] hover:text-[var(--color-leaf-200)] font-bold transition-colors">
            {lang === 'fa' ? '👉 تمام پرسش‌ها →' : '👉 All questions →'}
          </a>
        </p>
      </div>
    </section>
  );
}
