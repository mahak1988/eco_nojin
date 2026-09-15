import { Link } from 'react-router-dom';
import { FileDown, FileText, FileSpreadsheet } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Reveal from '../ui/Reveal';

/** Download reports CTA section. */
export default function DownloadCTA() {
  const { lang } = useLang();

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="download" aria-labelledby="download-heading">
        <div className="mx-auto max-w-4xl text-center">
          <h2 id="download-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'گزارش‌ها و مستندات' : 'Reports & Documents'}
          </h2>
          <p className="mt-3 text-[var(--color-night-200)]/60">
            {lang === 'fa' ? 'دانلود گزارش‌های سالانه، مستندات فنی و اسناد پروژه.' : 'Download annual reports, technical docs, and project files.'}
          </p>

          <div className="mt-8 grid gap-3 sm:grid-cols-3">
            <Link to="/resources" className="group rounded-3xl glass glass-hover p-6 text-left">
              <FileText className="h-8 w-8 text-[var(--color-leaf-400)] mb-3" aria-hidden />
              <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">
                {lang === 'fa' ? 'گزارش سالانه' : 'Annual Report'}
              </h3>
              <p className="mt-1 text-xs text-[var(--color-night-200)]/50">
                {lang === 'fa' ? 'PDF — ۲۰۲۶' : 'PDF — 2026'}
              </p>
              <div className="mt-3 flex items-center gap-1 text-xs font-bold text-[var(--color-leaf-300)] group-hover:text-[var(--color-leaf-200)]">
                <FileDown className="h-3 w-3" aria-hidden /> {lang === 'fa' ? 'دانلود' : 'Download'}
              </div>
            </Link>
            <Link to="/resources" className="group rounded-3xl glass glass-hover p-6 text-left">
              <FileSpreadsheet className="h-8 w-8 text-[var(--color-sand-400)] mb-3" aria-hidden />
              <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">
                {lang === 'fa' ? 'داده‌های خام' : 'Raw Data'}
              </h3>
              <p className="mt-1 text-xs text-[var(--color-night-200)]/50">
                {lang === 'fa' ? 'CSV — Sentinel-2' : 'CSV — Sentinel-2'}
              </p>
              <div className="mt-3 flex items-center gap-1 text-xs font-bold text-[var(--color-leaf-300)] group-hover:text-[var(--color-leaf-200)]">
                <FileDown className="h-3 w-3" aria-hidden /> {lang === 'fa' ? 'دانلود' : 'Download'}
              </div>
            </Link>
            <Link to="/resources" className="group rounded-3xl glass glass-hover p-6 text-left">
              <FileText className="h-8 w-8 text-[var(--color-aqua-400)] mb-3" aria-hidden />
              <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">
                {lang === 'fa' ? 'مستندات فنی' : 'Technical Docs'}
              </h3>
              <p className="mt-1 text-xs text-[var(--color-night-200)]/50">
                {lang === 'fa' ? 'HTML — آنلاین' : 'HTML — Online'}
              </p>
              <div className="mt-3 flex items-center gap-1 text-xs font-bold text-[var(--color-leaf-300)] group-hover:text-[var(--color-leaf-200)]">
                <FileDown className="h-3 w-3" aria-hidden /> {lang === 'fa' ? 'مشاهده' : 'View'}
              </div>
            </Link>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
