import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Mail, Lock, User, Check, Phone, MapPin, Calendar, ChevronDown } from 'lucide-react';
import Seo from '../components/ui/Seo';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import { getApiBase } from '../lib/api';
import RainBackground from '../components/auth/RainBackground';

const translations = {
  fa: {
    kicker: 'ایجاد حساب',
    title: 'ثبت‌نام',
    subtitle: 'برای شروع در اکونوژین حساب کاربری ایجاد کنید',
    fullName: 'نام و نام خانوادگی',
    phone: 'شماره تلفن',
    email: 'ایمیل',
    password: 'رمز عبور',
    confirmPassword: 'تکرار رمز عبور',
    birthYear: 'سال تولد',
    country: 'کشور',
    city: 'شهر',
    address: 'آدرس',
    role: 'نقش شما',
    register: 'ثبت‌نام',
    loading: 'در حال ثبت‌نام...',
    hasAccount: 'قبلاً حساب کاربری دارید؟',
    login: 'ورود',
    fullNamePlaceholder: 'نام و نام خانوادگی',
    phonePlaceholder: '+98 912 345 6789',
    emailPlaceholder: 'email@example.com',
    passwordPlaceholder: 'حداقل ۸ کاراکتر',
    confirmPasswordPlaceholder: 'تکرار رمز عبور',
    birthYearPlaceholder: 'مثلاً ۱۳۷۰',
    countryPlaceholder: 'مثلاً ایران',
    cityPlaceholder: 'مثلاً تهران',
    addressPlaceholder: 'آدرس پستی (اختیاری)',
    roleFarmer: 'کشاورز',
    roleResearcher: 'پژوهشگر',
    roleOrganization: 'سازمان',
    roleTourist: 'گردشگر',
    roleRegular: 'کاربر عادی',
    showPassword: 'نمایش رمز',
    hidePassword: 'مخفی کردن رمز',
    ageGateTitle: 'تایید سن',
    ageGateText: 'برای ثبت‌نام باید حداقل ۱۸ سال (۱۳۰۴ شمسی یا ۲۰۰۶ میلادی) باشید. با ادامه، این مسئولیت را می‌پذیرید.',
    ageGateLabel: 'تایید می‌کنم که حداقل ۱۸ سال هستم',
    ageGateError: 'برای ثبت‌نام باید حداقل ۱۸ سال باشید.',
    success: 'ثبت‌نام موفقیت‌آمیز',
    termsText: 'با ثبت‌نام، قوانین و مقررات را می‌پذیرید',
    passwordRequirements: [
      'حداقل ۸ کاراکتر',
      'حداقل یک حرف بزرگ',
      'حداقل یک عدد',
      'حداقل یک حرف خاص',
    ],
    acceptTerms: 'قانون‌ها و مقررات را می‌پذیرم',
    acceptTermsLink: 'قانون‌ها و مقررات',
    acceptPrivacy: 'سیاست حریم خصوصی را می‌پذیرم',
    acceptPrivacyLink: 'سیاست حریم خصوصی',
    ecoNojinTitle: 'اکونوژین را بساز، زیست را بکار.',
    ecoNojinDesc: '۱۲ بستهٔ فنی-مهندسی، ۶۱ مدل علمی و یک پایلوت زنده برای احیای خاک، آب و کربن. ثبت‌نام رایگان است و هیچ دادهٔ شخصی ذخیره نمی‌شود.',
    ecoNojinTags: ['رایگان', 'بدون IP', 'بدون داده شخصی'],
  },
  en: {
    kicker: 'Create Account',
    title: 'Sign up',
    subtitle: 'Create your Eco Nojin account to get started',
    fullName: 'Full name',
    phone: 'Phone number',
    email: 'Email',
    password: 'Password',
    confirmPassword: 'Confirm password',
    birthYear: 'Birth year',
    country: 'Country',
    city: 'City',
    address: 'Address',
    role: 'Your role',
    register: 'Sign up',
    loading: 'Creating account...',
    hasAccount: 'Already have an account?',
    login: 'Sign in',
    fullNamePlaceholder: 'John Doe',
    phonePlaceholder: '+1 555 123 4567',
    emailPlaceholder: 'email@example.com',
    passwordPlaceholder: 'At least 8 characters',
    confirmPasswordPlaceholder: 'Repeat password',
    birthYearPlaceholder: 'e.g. 1990',
    countryPlaceholder: 'e.g. United States',
    cityPlaceholder: 'e.g. San Francisco',
    addressPlaceholder: 'Postal address (optional)',
    roleFarmer: 'Farmer',
    roleResearcher: 'Researcher',
    roleOrganization: 'Organization',
    roleTourist: 'Tourist',
    roleRegular: 'Regular user',
    showPassword: 'Show password',
    hidePassword: 'Hide password',
    ageGateTitle: 'Age verification',
    ageGateText: 'You must be at least 18 years old (born in 2006 or earlier) to register. By continuing, you accept this responsibility.',
    ageGateLabel: 'I confirm that I am at least 18 years old',
    ageGateError: 'You must be at least 18 years old to register.',
    success: 'Registration successful',
    termsText: 'By signing up, you agree to our Terms and Privacy Policy',
    passwordRequirements: [
      'At least 8 characters',
      'At least one uppercase letter',
      'At least one number',
      'At least one special character',
    ],
    acceptTerms: 'I accept the Terms of Service',
    acceptTermsLink: 'Terms of Service',
    acceptPrivacy: 'I accept the Privacy Policy',
    acceptPrivacyLink: 'Privacy Policy',
    ecoNojinTitle: 'Build Eco Nojin, restore life.',
    ecoNojinDesc: '12 engineering packages, 61 scientific models, and one live pilot for soil, water, and carbon restoration. Registration is free — no IP, no personal data stored.',
    ecoNojinTags: ['Free', 'No IP', 'No personal data'],
  },
};

export default function RegisterPage() {
  const { lang } = useLang();
  const { login } = useAuth();
  const { showToast } = useToast();
  const t = translations[lang as 'fa' | 'en'];
  const isFa = lang === 'fa';

  const currentYear = new Date().getFullYear();
  const minBirthYear = currentYear - 18;

  const [formData, setFormData] = useState({
    fullName: '',
    phone: '',
    email: '',
    password: '',
    confirmPassword: '',
    birthYear: '',
    country: '',
    city: '',
    address: '',
    role: 'farmer',
    ageConfirmed: false,
    acceptTerms: false,
    acceptPrivacy: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const setField = (key: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const ageValid = () => {
    const year = Number(formData.birthYear);
    if (!formData.birthYear) return true; // birth year is optional
    if (!Number.isFinite(year)) return false;
    return year <= minBirthYear;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.ageConfirmed) {
      setError(t.ageGateError);
      return;
    }
    if (!ageValid()) {
      setError(t.ageGateError);
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError(isFa ? 'رمز عبورها مطابقت ندارند' : 'Passwords do not match');
      return;
    }
    if (!formData.acceptTerms || !formData.acceptPrivacy) {
      setError(
        isFa
          ? 'باید قوانین و سیاست حریم خصوصی را بپذیرید'
          : 'You must accept both terms and privacy policy',
      );
      return;
    }

    setIsLoading(true);

try {
      const base = getApiBase();
      const response = await fetch(`${base}/api/v1/auth/supabase/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.fullName,
          phone: formData.phone || undefined,
          birth_year: formData.birthYear || undefined,
          country: formData.country || undefined,
          city: formData.city || undefined,
          address: formData.address || undefined,
          role: formData.role,
          language: lang,
        }),
      });

      const data = await response.json();
      if (data.status !== 'ok') {
        throw new Error(data.error || (isFa ? ' ثبت‌نام ناموفق بود' : 'Registration failed'));
      }

      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: formData.fullName,
        role: formData.role,
        language: lang,
      });
      showToast({ type: 'success', title: t.success, description: data.email });
      window.location.href = '/dashboard';
    } catch (err) {
      const msg = err instanceof Error ? err.message : (isFa ? ' ثبت‌نام ناموفق بود' : 'Registration failed');
      setError(msg);
      showToast({ type: 'error', title: 'Error', description: msg });
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength =
    formData.password.length >= 8 &&
    /[A-Z]/.test(formData.password) &&
    /[0-9]/.test(formData.password);

  return (
    <>
      <Seo title={`${t.title} | Eco Nojin`} description={t.subtitle} path="/register" />
      <div className="flex min-h-screen items-center justify-center px-4 py-10">
        <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl lg:grid-cols-2">
        <div className="hidden lg:block">
          <RainBackground lang={lang} />
        </div>
        <div className="p-6 sm:p-8">
          <Reveal className="mb-8 text-center">
            <h1 className="text-3xl font-extrabold text-[var(--color-night-100)]">{t.title}</h1>
            <p className="mt-2 text-sm text-[var(--color-night-200)]">{t.subtitle}</p>
          </Reveal>

          <Reveal delay={0.1}>
            <form onSubmit={handleSubmit} className="glass flex flex-col gap-4 rounded-3xl p-7">
              {error && (
                <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-4 py-2 text-xs text-red-300">
                  {error}
                </div>
              )}

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.fullName}</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="text"
                    value={formData.fullName}
                    onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                    placeholder={t.fullNamePlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.phone}</label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setField('phone', e.target.value)}
                    placeholder={t.phonePlaceholder}
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.email}</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder={t.emailPlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.birthYear}</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="number"
                    value={formData.birthYear}
                    onChange={(e) => setField('birthYear', e.target.value)}
                    placeholder={t.birthYearPlaceholder}
                    min={1900}
                    max={minBirthYear}
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
                <p className="text-[10px] text-[var(--color-night-200)]/35">
                  {isFa ? `حداقل ${minBirthYear} (۱۸ سال)` : `Must be ${minBirthYear} or earlier`}
                </p>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.country}</label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type="text"
                    value={formData.country}
                    onChange={(e) => setField('country', e.target.value)}
                    placeholder={t.countryPlaceholder}
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.city}</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setField('city', e.target.value)}
                  placeholder={t.cityPlaceholder}
                  dir="ltr"
                  className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 px-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.address}</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setField('address', e.target.value)}
                  placeholder={t.addressPlaceholder}
                  dir="ltr"
                  className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 px-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.role}</label>
                <div className="relative">
                  <select
                    value={formData.role}
                    onChange={(e) => setField('role', e.target.value)}
                    dir={isFa ? 'rtl' : 'ltr'}
                    className="w-full appearance-none rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-3 pr-10 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  >
                    <option value="farmer">{t.roleFarmer}</option>
                    <option value="researcher">{t.roleResearcher}</option>
                    <option value="organization">{t.roleOrganization}</option>
                    <option value="tourist">{t.roleTourist}</option>
                    <option value="regular">{t.roleRegular}</option>
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" aria-hidden />
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.password}</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder={t.passwordPlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-10 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] hover:text-[var(--color-night-100)]"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {formData.password && (
                  <div className="flex flex-col gap-1">
                    {t.passwordRequirements.map((req, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <Check className={`h-3 w-3 ${passwordStrength ? 'text-[var(--color-leaf-300)]' : 'text-[var(--color-night-200)]'}`} />
                        <span className="text-[11px] text-[var(--color-night-200)]">{req}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-[var(--color-night-200)]">{t.confirmPassword}</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]" />
                  <input
                    type={showConfirm ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) => setField('confirmPassword', e.target.value)}
                    placeholder={t.confirmPasswordPlaceholder}
                    required
                    dir="ltr"
                    className="w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] py-2.5 pl-10 pr-10 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-night-200)] hover:text-[var(--color-night-100)]"
                    aria-label={showConfirm ? t.hidePassword : t.showPassword}
                  >
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* age gate */}
              <div className="flex flex-col gap-2 rounded-xl border border-[var(--color-leaf-500)]/25 bg-[var(--color-leaf-500)]/8 p-4">
                <div className="flex items-start gap-3">
                  <input
                    id="age-gate"
                    type="checkbox"
                    checked={formData.ageConfirmed}
                    onChange={(e) => setField('ageConfirmed', e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-[var(--color-sand-500)] bg-[var(--color-night-900)] text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-400)]"
                  />
                  <div className="flex-1">
                    <label
                      htmlFor="age-gate"
                      className="cursor-pointer text-xs font-bold text-[var(--color-night-100)]"
                    >
                      {t.ageGateLabel}
                    </label>
                    <p className="mt-1 text-[10px] leading-5 text-[var(--color-night-200)]/60">
                      {t.ageGateText}
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <label className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={formData.acceptTerms}
                    onChange={(e) => setField('acceptTerms', e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-[var(--color-sand-500)] bg-[var(--color-night-900)] text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-400)]"
                  />
                  <span className="text-xs text-[var(--color-night-200)]">
                    {isFa ? (
                      <>
                        {'قانون‌ها و مقررات را می‌پذیرم — '}
                        <Link
                          to="/terms"
                          className="font-bold text-[var(--color-leaf-300)] hover:underline"
                        >
                          {t.acceptTermsLink}
                        </Link>
                      </>
                    ) : (
                      <>
                        {'I accept the '}
                        <Link
                          to="/terms"
                          className="font-bold text-[var(--color-leaf-300)] hover:underline"
                        >
                          {t.acceptTermsLink}
                        </Link>
                      </>
                    )}
                  </span>
                </label>
                <label className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={formData.acceptPrivacy}
                    onChange={(e) => setField('acceptPrivacy', e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-[var(--color-sand-500)] bg-[var(--color-night-900)] text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-400)]"
                  />
                  <span className="text-xs text-[var(--color-night-200)]">
                    {isFa ? (
                      <>
                        {'سیاست حریم خصوصی را می‌پذیرم — '}
                        <Link
                          to="/privacy"
                          className="font-bold text-[var(--color-leaf-300)] hover:underline"
                        >
                          {t.acceptPrivacyLink}
                        </Link>
                      </>
                    ) : (
                      <>
                        {'I accept the '}
                        <Link
                          to="/privacy"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-bold text-[var(--color-leaf-300)] hover:underline"
                        >
                          {t.acceptPrivacyLink}
                        </Link>
                      </>
                    )}
                  </span>
                </label>
              </div>

              <button
                type="submit"
                disabled={
                  isLoading ||
                  !formData.acceptTerms ||
                  !formData.acceptPrivacy ||
                  !formData.ageConfirmed ||
                  !ageValid()
                }
                className="mt-2 w-full rounded-xl bg-[var(--color-leaf-500)] py-2.5 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.01] disabled:opacity-50"
              >
                {isLoading ? t.loading : t.register}
              </button>

              <p className="mt-2 text-center text-xs text-[var(--color-night-200)]">
                {t.hasAccount}{' '}
                <Link to="/login" className="font-bold text-[var(--color-leaf-300)] hover:underline">
                  {t.login}
                </Link>
              </p>
            </form>
          </Reveal>
        </div>
      </div>
    </div>
  </>
  );
}