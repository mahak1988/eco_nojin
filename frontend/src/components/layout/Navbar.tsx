import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Languages, Menu, X, LogIn, LogOut, User, Search, Command } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import DarkModeToggle from '../sections/DarkModeToggle';
import { useAuth } from '../../context/AuthContext';
import Logo from '../visuals/Logo';
import { SearchModal, useGlobalSearchShortcut } from '../ui/SearchModal';

/** Fixed top navigation with glass background on scroll and a mobile sheet. */
export default function Navbar() {
  const { t, toggle, lang } = useLang();
  const { isAuthenticated, user, logout } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const location = useLocation();

  useGlobalSearchShortcut(() => setSearchOpen(true));

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

  const handleLogout = () => {
    logout();
    window.location.href = '/';
  };

  const links = [
    { to: '/', label: t.nav.home },
    { to: '/platform', label: t.nav.platform },
    { to: '/hydroma', label: t.nav.science },
    { to: '/marketplace', label: lang === 'fa' ? 'بازارگاه' : 'Marketplace' },
    { to: '/solutions', label: lang === 'fa' ? 'راهکارها' : 'Solutions' },
    { to: '/dashboard', label: lang === 'fa' ? 'داشبورد' : 'Dashboard' },
    { to: '/blog', label: t.nav.blog },
    { to: '/about', label: t.nav.about },
  ];

  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `rounded-full px-4 py-2 text-sm font-bold transition-colors ${
      isActive
        ? 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-300)]'
        : 'text-[var(--color-night-200)]/70 hover:bg-white/5 hover:text-[var(--color-night-100)]'
    }`;

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:start-2 focus:z-[100] focus:rounded-xl focus:bg-[var(--color-leaf-500)] focus:px-4 focus:py-2 focus:text-sm focus:font-extrabold focus:text-[var(--color-night-950)]"
      >
        {lang === 'fa' ? 'پرش به محتوای اصلی' : 'Skip to main content'}
      </a>
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
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard/profile"
                className="glass glass-hover hidden items-center gap-1.5 rounded-full border border-[var(--color-aqua-500)]/30 bg-[var(--color-aqua-500)]/10 px-4 py-2 text-xs font-extrabold text-[var(--color-aqua-300)] sm:inline-flex"
              >
                <User className="h-4 w-4" aria-hidden />
                {user?.full_name || user?.email?.split('@')[0] || (lang === 'fa' ? 'کاربر' : 'User')}
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="glass glass-hover hidden items-center gap-1.5 rounded-full border border-red-500/30 bg-red-500/10 px-4 py-2 text-xs font-extrabold text-red-300 sm:inline-flex"
              >
                <LogOut className="h-4 w-4" aria-hidden />
                {lang === 'fa' ? 'خروج' : 'Logout'}
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="glass glass-hover hidden items-center gap-1.5 rounded-full border border-[var(--color-leaf-500)]/40 bg-[var(--color-leaf-500)]/10 px-4 py-2 text-xs font-extrabold text-[var(--color-leaf-300)] sm:inline-flex"
            >
              <LogIn className="h-4 w-4" aria-hidden />
              {lang === 'fa' ? 'ورود' : 'Login'}
            </Link>
          )}
          <button
            type="button"
            onClick={() => setSearchOpen(true)}
            aria-label={lang === 'fa' ? 'جستجوی سراسری' : 'Global search'}
            className="glass glass-hover inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-extrabold text-[var(--color-night-100)] hidden sm:flex"
          >
            <Search className="h-4 w-4 text-[var(--color-night-200)]/60" aria-hidden />
            <kbd className="inline-flex items-center gap-1 rounded bg-white/5 px-1.5 py-0.5 font-mono text-[10px]">
              <Command className="h-2.5 w-2.5" />
              <span>K</span>
            </kbd>
          </button>
          <DarkModeToggle />
          <button
            type="button"
            onClick={toggle}
            aria-label={lang === 'fa' ? 'Switch to English' : 'تغییر به فارسی'}
            className="glass glass-hover inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-extrabold text-[var(--color-night-100)]"
          >
            <Languages className="h-4 w-4 text-[var(--color-leaf-300)]" aria-hidden />
            {t.nav.langLabel}
          </button>

          {/* mobile toggle */}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label={open ? 'Close menu' : 'Open menu'}
            className="glass inline-flex rounded-full p-2.5 text-[var(--color-night-100)] lg:hidden"
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
                  isActive ? 'bg-[var(--color-leaf-500)]/15 text-[var(--color-leaf-300)]' : 'text-[var(--color-night-200)]/75 hover:bg-white/5'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          {isAuthenticated ? (
            <>
              <Link
                to="/dashboard/profile"
                className="flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold text-[var(--color-aqua-300)]"
              >
                <User className="h-4 w-4" aria-hidden />
                {user?.full_name || user?.email?.split('@')[0] || (lang === 'fa' ? 'کاربر' : 'User')}
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold text-red-300"
              >
                <LogOut className="h-4 w-4" aria-hidden />
                {lang === 'fa' ? 'خروج' : 'Logout'}
              </button>
            </>
          ) : (
            <Link
              to="/login"
              className="flex items-center gap-2 rounded-xl px-4 py-3 text-sm font-bold text-[var(--color-leaf-300)]"
            >
              <LogIn className="h-4 w-4" aria-hidden />
              {lang === 'fa' ? 'ورود' : 'Login'}
            </Link>
          )}
        </div>
      ) : null}
    </header>
    <SearchModal isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
