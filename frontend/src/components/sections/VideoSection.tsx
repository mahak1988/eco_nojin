import { useLang } from '../../i18n/LanguageContext';
import { Play, ExternalLink } from 'lucide-react';
import Reveal from '../ui/Reveal';

/** Video/embed section on HomePage. */
export default function VideoSection() {
  const { lang } = useLang();

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="video" aria-labelledby="video-heading">
        <div className="mx-auto max-w-4xl text-center">
          <p className="mb-2 text-sm font-extrabold text-[var(--color-leaf-400)]">ویدیو</p>
          <h2 id="video-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'شاهد اکو نوژین در عمل' : 'See Eco Nojin in Action'}
          </h2>
          <p className="mt-4 text-[var(--color-night-200)]/60">
            {lang === 'fa' ? '۳ دقیقه با موتور علمی هیدروما و نقشه‌های ماهواره‌ای.' : '3 minutes with HyDroMa and satellite maps.'}
          </p>

          <div className="mt-10 mx-auto max-w-3xl">
            <div className="relative aspect-video overflow-hidden rounded-3xl border border-white/10 bg-[var(--color-night-900)]">
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                <button
                  type="button"
                  className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/20 backdrop-blur-sm transition-transform hover:scale-110"
                  aria-label={lang === 'fa' ? 'پخش ویدیو' : 'Play video'}
                >
                  <Play className="h-7 w-7 text-[var(--color-leaf-400)] ml-1" aria-hidden fill="currentColor" />
                </button>
                <p className="text-sm text-[var(--color-night-200)]/50">{lang === 'fa' ? 'ویدیو معرفی پروژه' : 'Project Introduction'}</p>
              </div>
            </div>
          </div>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <a
              href="https://youtube.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full glass glass-hover px-5 py-2.5 text-xs font-bold text-[var(--color-night-100)]"
            >
              YouTube <ExternalLink className="h-3 w-3" aria-hidden />
            </a>
            <a
              href="https://vimeo.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full glass glass-hover px-5 py-2.5 text-xs font-bold text-[var(--color-night-100)]"
            >
              Vimeo <ExternalLink className="h-3 w-3" aria-hidden />
            </a>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
