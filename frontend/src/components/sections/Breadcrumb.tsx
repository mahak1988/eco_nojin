import { Link } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';

/** Breadcrumb navigation. */
export default function Breadcrumb() {
  const { lang } = useLang();

  const homeLabel = lang === 'fa' ? 'خانه' : 'Home';

  return (
    <nav aria-label="Breadcrumb" className="px-4 pt-4 sm:px-6">
      <ol className="mx-auto max-w-6xl flex items-center gap-2 text-xs text-[var(--color-night-200)]/40">
        <li>
          <Link
            to="/"
            className="inline-flex items-center gap-1 hover:text-[var(--color-leaf-300)] transition-colors"
          >
            <Home className="h-3 w-3" aria-hidden />
            {homeLabel}
          </Link>
        </li>
        <li>
          <ChevronRight className="h-3 w-3" aria-hidden />
        </li>
        <li className="text-[var(--color-night-100)] font-bold">پلتفرم</li>
      </ol>
    </nav>
  );
}
