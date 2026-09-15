import { Link } from 'react-router-dom';
import { useBilingual } from '../../hooks/useBilingual';
import Seo from '../../components/ui/Seo';
import Reveal from '../../components/ui/Reveal';
import { Home, Search } from 'lucide-react';

export default function MarketplaceNotFound() {
  const { fa } = useBilingual();

  return (
    <>
      <Seo title="صفحه یافت نشد" path="/marketplace/*" />
      <div className="min-h-screen bg-[var(--color-sand-50)] flex items-center justify-center px-4">
        <Reveal className="text-center max-w-md">
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-[var(--color-sand-100)] flex items-center justify-center">
            <Search className="w-12 h-12 text-[var(--color-sand-400)]" aria-hidden />
          </div>
          <h1 className="text-4xl font-bold text-[var(--color-night-100)] mb-3">
            {fa('۴۰۴', '404')}
          </h1>
          <h2 className="text-2xl font-semibold text-[var(--color-night-100)] mb-4">
            {fa('صفحه یافت نشد', 'Page Not Found')}
          </h2>
          <p className="text-[var(--color-night-200)] mb-8">
            {fa('صفحه‌ای که به دنبال آن هستید وجود ندارد یا منتقل شده است.', 'The page you are looking for does not exist or has been moved.')}
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/marketplace"
              className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--color-gold-500)] hover:bg-[var(--color-gold-600)] text-white font-medium rounded-xl transition-colors"
            >
              <Search className="w-5 h-5" aria-hidden />
              {fa('بازگشت به بازارگاه', 'Back to Marketplace')}
            </Link>
            <Link
              to="/"
              className="inline-flex items-center gap-2 px-6 py-3 border border-[var(--color-sand-300)] hover:border-[var(--color-sand-400)] text-[var(--color-night-100)] font-medium rounded-xl transition-colors"
            >
              <Home className="w-5 h-5" aria-hidden />
              {fa('صفحه اصلی', 'Home')}
            </Link>
          </div>
        </Reveal>
      </div>
    </>
  );
}