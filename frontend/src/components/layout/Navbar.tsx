import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Languages, Menu, X } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import Logo from '../visuals/Logo';

/** Fixed top navigation with glass background on scroll and a mobile sheet. */
export default function Navbar() {
  const { t, toggle, lang } = useLang();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 14);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close the mobile sheet whenever the route changes.
  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  const links = [
    { to: '/', label: t.nav.home },
    { to: '/platform', label: t.nav.platform },
    { to: '/hydroma', label: t.nav.science },
    { to: '/blog', label: t.nav.blog },
    { to: '/about', label: t.nav.about },
  ];

  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-4 py-2 text-sm font-bold transition-colors ${
      isActive
        ? 'bg-leaf-500/15 text-leaf-300'
        : 'text-emerald-100/70 hover:bg-white/5 hover:text-emerald-50'
    }`;

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled ? 'glass shadow-lg shadow-black/20' : 'bg-transparent'
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link to="/" aria-label={t.brand.name} className="transition-opacity hover:opacity-85">
          <Logo wordmark={t.brand.name} size={38} />
        </Link>

        {/* desktop links */}
        <div className="hidden items-center gap-1 lg:flex">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === '/'} className={linkCls}>
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggle}
            aria-label={lang === 'fa' ? 'Switch to English' : 'تغییر به فارسی'}
            className="glass glass-hover inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-extrabold text-emerald-50"
          >
            <Languages className="h-4 w-4 text-leaf-300" aria-hidden />
            {t.nav.langLabel}
          </button>

          {/* mobile toggle */}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? 'Close menu' : 'Open menu'}
            className="glass inline-flex rounded-full p-2.5 text-emerald-50 lg:hidden"
          >
            {open ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
          </button>
        </div>
      </nav>

      {/* mobile sheet */}
      {open ? (
        <div className="glass mx-4 mb-3 flex flex-col gap-1 rounded-2xl p-3 lg:hidden">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                `rounded-xl px-4 py-3 text-sm font-bold ${
                  isActive ? 'bg-leaf-500/15 text-leaf-300' : 'text-emerald-100/75 hover:bg-white/5'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      ) : null}
    </header>
  );
}
