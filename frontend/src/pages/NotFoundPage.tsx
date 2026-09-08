import { Link } from 'react-router-dom';
import { Home, SearchX } from 'lucide-react';
import Seo from '../components/ui/Seo';
import { useLang } from '../i18n/LanguageContext';

/** Dedicated 404 page (replaces the silent redirect to home). */
export default function NotFoundPage() {
  const { t } = useLang();

  return (
    <section className="flex min-h-[70vh] flex-col items-center justify-center gap-6 px-4 text-center">
      <Seo title={`${t.notFound.title} | ${t.brand.name}`} description={t.notFound.lead} path="/404" />
      <span className="glass inline-flex h-16 w-16 items-center justify-center rounded-3xl text-leaf-300">
        <SearchX className="h-8 w-8" aria-hidden />
      </span>
      <h1 className="text-3xl font-extrabold text-emerald-50 sm:text-4xl">{t.notFound.title}</h1>
      <p className="max-w-md text-sm leading-7 text-emerald-100/60">{t.notFound.lead}</p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          to="/"
          className="ring-glow inline-flex items-center gap-2 rounded-full bg-leaf-500 px-6 py-3 text-sm font-extrabold text-night-950 transition-transform hover:scale-[1.03]"
        >
          <Home className="h-4 w-4" aria-hidden />
          {t.notFound.homeButton}
        </Link>
        <Link
          to="/blog"
          className="glass glass-hover inline-flex items-center gap-2 rounded-full px-6 py-3 text-sm font-extrabold text-emerald-50"
        >
          {t.nav.blog}
        </Link>
      </div>
    </section>
  );
}
