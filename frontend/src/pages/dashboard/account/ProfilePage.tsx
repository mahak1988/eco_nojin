import { useEffect, useState, useRef } from 'react';
import {
  User, Camera, Edit3, Leaf, Activity, Wallet, KeyRound, FolderKanban, Settings, Lock, Shield, LogIn, Check, Copy, Loader2, MapPin, Building2
} from 'lucide-react';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import Skeleton from '../../../components/ui/Skeleton';
import { useLang } from '../../../i18n/LanguageContext';
import { useAuth } from '../../../context/AuthContext';
import { useToast } from '../../../components/ui/Toast';
import { getApiBase } from '../../../lib/api';
import { getClientId } from '../../../lib/hub';
import { profileSettings } from '../../../content/pages/profilesettings';
import type { ProfileContent } from '../../../content/pages/profiletypes';

const NAME_KEY = 'hydroma-display-name';

interface LoadingState { identity: boolean; legacy: boolean; assets: boolean; preferences: boolean; security: boolean; }
interface LegacyData { carbonSequestered: number | null; areaRestored: number | null; waterSaved: number | null; activityCount: number; updated: string | null; }
interface AssetsData {
  lands: Array<{ name: string; detail: string; status?: string }>;
  sensors: Array<{ name: string; detail: string; status?: string }>;
  wallet: Array<{ name: string; detail: string; status?: string }>;
  apiKeys: Array<{ name: string; detail: string; status?: string }>;
  projects: Array<{ name: string; detail: string; status?: string }>;
}
interface AchievementsData {
  achievements: Array<{ icon: string; title: string; description: string; date: string }>;
  milestones: Array<{ icon: string; title: string; date: string }>;
}
interface ExtendedPrefs {
  timezone: string;
  units: string;
  theme: string;
  dashboardWidgets: Record<string, unknown> | null;
  language: string;
}

function fmtNum(n: number | null | undefined, u: string): string { if (n == null) return "—"; return n.toLocaleString() + " " + u; }
function fmtDate(iso: string | null | undefined): string { if (!iso) return "—"; try { return new Date(iso).toLocaleDateString(); } catch { return iso; } }

export default function ProfilePage() {
  const { lang, t } = useLang();
  const { user, token, isAuthenticated, logout, updateUser } = useAuth();
  const { showToast } = useToast();
  const toast = (t: string): void => showToast({ type: 'success' as const, title: t });
  const c: ProfileContent = profileSettings[lang as 'fa' | 'en'].profile;
  const clientKey = getClientId();
  const apiBase = getApiBase();
  const [copied, setCopied] = useState(false);
  const [name, setName] = useState(() => { try { return localStorage.getItem(NAME_KEY) ?? ''; } catch { return ''; } });
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [loading, setLoading] = useState<LoadingState>({ identity: true, legacy: true, assets: true, preferences: true, security: true });
  const [legacyData, setLegacyData] = useState<LegacyData | null>(null);
  const [assetsData, setAssetsData] = useState<AssetsData | null>(null);
  const [achievementsData, setAchievementsData] = useState<AchievementsData | null>(null);
  const [extendedPrefs, setExtendedPrefs] = useState<ExtendedPrefs | null>(null);
      const [deactivateConfirm, setDeactivateConfirm] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [accountStatus, setAccountStatus] = useState<Record<string, unknown> | null>(null);
    const [twoFactor, setTwoFactor] = useState<{ enabled: boolean; method: string | null } | null>(null);
  const [toggling2fa, setToggling2fa] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [pwForm, setPwForm] = useState({ current: '', next: '', confirm: '' });
  const [pwError, setPwError] = useState('');
  const [pwSaving, setPwSaving] = useState(false);
  const [notifications, setNotifications] = useState<Record<string, boolean>>({ email: true, push: true, sms: false, marketing: false });
  const [themePref, setThemePref] = useState<'light' | 'dark' | 'system'>('system');
  const [languagePref, setLanguagePref] = useState<'fa' | 'en'>('fa');
  const [bio, setBio] = useState('');
  const [org, setOrg] = useState('');
  const [location, setLocation] = useState('');
  const [bioEdit, setBioEdit] = useState(false);
  const [bioSaving, setBioSaving] = useState(false);
  const [bioError, setBioError] = useState('');
  const navRefs = useRef<Record<string, HTMLElement | null>>({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteStep, setDeleteStep] = useState(0);
  const [deleteEmail, setDeleteEmail] = useState('');
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [exporting, setExporting] = useState(false);
  const [showDataExport, setShowDataExport] = useState(false);
    const [prefsSaving, setPrefsSaving] = useState(false);
        const [deactivateError, setDeactivateError] = useState('');

  const avatarUrl = (user as any)?.avatar_url || null;
  const identityInFlight = useRef(false);

  const loadIdentity = async () => {
    if (identityInFlight.current) return;
    identityInFlight.current = true;
    try {
      if (isAuthenticated) {
        setAccountStatus(null);
        const res = await fetch(`${apiBase}/api/v1/auth/account/status`, { headers: { Authorization: `Bearer ${token}` } });
        if (res.ok) { const d = await res.json(); setAccountStatus(d.data || null); }
        const prefRes = await fetch(`${apiBase}/api/v1/auth/preferences`, { headers: { Authorization: `Bearer ${token}` } });
        if (prefRes.ok) { const d = await prefRes.json(); if (d.data) { setThemePref(d.data.theme || 'system'); setLanguagePref((d.data.language || 'fa') as 'fa' | 'en'); } }
        const notifRes = await fetch(`${apiBase}/api/v1/auth/notifications`, { headers: { Authorization: `Bearer ${token}` } });
        if (notifRes.ok) { const d = await notifRes.json(); if (d.data) setNotifications(d.data); }
        const extRes = await fetch(`${apiBase}/api/v1/auth/preferences/extended`, { headers: { Authorization: `Bearer ${token}` } });
        if (extRes.ok) { const d = await extRes.json(); if (d.data) setExtendedPrefs(d.data); }
        const refRes = await fetch(`${apiBase}/api/v1/auth/referral`, { headers: { Authorization: `Bearer ${token}` } });
        if (refRes.ok) { await refRes.json(); }
        const sesRes = await fetch(`${apiBase}/api/v1/auth/sessions`, { headers: { Authorization: `Bearer ${token}` } });
        if (sesRes.ok) { await sesRes.json(); }
        const tfRes = await fetch(`${apiBase}/api/v1/auth/2fa/status`, { headers: { Authorization: `Bearer ${token}` } });
        if (tfRes.ok) { const d = await tfRes.json(); if (d.data) setTwoFactor(d.data); }
        const akRes = await fetch(`${apiBase}/api/v1/auth/api-keys`, { headers: { Authorization: `Bearer ${token}` } });
        if (akRes.ok) { await akRes.json(); }
        if (user?.id) {
          const pubRes = await fetch(`${apiBase}/api/v1/auth/profile/public?user_id=${user.id}`);
          if (pubRes.ok) {
            const pub = await pubRes.json();
            const d = pub?.data || pub;
            if (d) {
              if (d.bio) setBio(d.bio);
              if (d.organization) setOrg(d.organization);
              if (d.location) setLocation(d.location);
            }
          }
        }
      }
    } catch { /* ignore */ }
    finally { identityInFlight.current = false; setLoading(l => ({ ...l, identity: false })); }
  };

  const loadLegacy = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/legacy`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); if (d.data) setLegacyData(d.data); }
    } catch { /* ignore */ }
    finally { setLoading(l => ({ ...l, legacy: false })); }
  };

  const loadAssets = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/assets`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); if (d.data) setAssetsData(d.data); }
    } catch { /* ignore */ }
    finally { setLoading(l => ({ ...l, assets: false })); }
  };

  const loadAchievements = async () => {
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/achievements`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); if (d.data) setAchievementsData(d.data); }
    } catch { /* ignore */ }
    finally { setLoading(l => ({ ...l, preferences: false })); }
  };

  useEffect(() => { setLoading(l => ({ ...l, identity: true })); loadIdentity(); }, []);
  useEffect(() => { if (isAuthenticated) { setLoading(l => ({ ...l, legacy: true })); loadLegacy(); } }, [isAuthenticated]);
  useEffect(() => { if (isAuthenticated) { setLoading(l => ({ ...l, assets: true })); loadAssets(); } }, [isAuthenticated]);
  useEffect(() => { if (isAuthenticated) { setLoading(l => ({ ...l, preferences: true })); loadAchievements(); } }, [isAuthenticated]);

  const saveName = () => { setSaving(true); try { localStorage.setItem(NAME_KEY, name.trim()); setSaved(true); setTimeout(() => setSaved(false), 2000); } catch { setSaving(false); } };
  const copyKey = async () => { try { await navigator.clipboard.writeText(clientKey); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* ignore */ } };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]; if (!file) return;
    setAvatarUploading(true);
    try {
      const form = new FormData(); form.append('avatar', file);
      const res = await fetch(`${apiBase}/api/v1/auth/profile`, { method: 'PUT', headers: { Authorization: `Bearer ${token}` }, body: form });
      if (res.ok) { const d = await res.json(); updateUser(d); setAvatarPreview(URL.createObjectURL(file)); toast(lang === 'fa' ? 'عکس پروفایل آپدیت شد' : 'Avatar updated'); }
    } catch { toast(lang === 'fa' ? 'آپلود ناموفق' : 'Upload failed'); }
    setAvatarUploading(false);
  };

  const handleLogout = () => { logout(); toast(lang === 'fa' ? 'خروج موفقیت‌آمیز بود' : 'Logged out'); };

  const saveBio = async () => {
    setBioSaving(true); setBioError('');
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/account/bio`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ bio, organization: org, location }) });
      if (res.ok) { toast(lang === 'fa' ? 'پروفایل ذخیره شد' : 'Profile saved'); setBioEdit(false); }
      else { const d = await res.json(); setBioError(d.detail || (lang === 'fa' ? 'خطا در ذخیره' : 'Save failed')); }
    } catch { setBioError(lang === 'fa' ? 'خطا در برقراری ارتباط' : 'Connection error'); }
    setBioSaving(false);
  };

  const handleChangePassword = async () => {
    setPwSaving(true); setPwError('');
    if (pwForm.next !== pwForm.confirm) { setPwError(lang === 'fa' ? 'رمزها مطابقت ندارند' : 'Passwords do not match'); setPwSaving(false); return; }
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/change-password`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ current_password: pwForm.current, new_password: pwForm.next }) });
      if (res.ok) { toast(lang === 'fa' ? 'رمز عبور تغییر کرد' : 'Password changed'); setShowChangePassword(false); setPwForm({ current: '', next: '', confirm: '' }); }
      else { const d = await res.json(); setPwError(d.detail || (lang === 'fa' ? 'رمز فعلی اشتباه است' : 'Current password is wrong')); }
    } catch { setPwError(lang === 'fa' ? 'خطا در برقراری ارتباط' : 'Connection error'); }
    setPwSaving(false);
  };

  const toggle2fa = async () => {
    setToggling2fa(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/2fa/toggle`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); setTwoFactor(d.data); toast(d.data?.enabled ? (lang === 'fa' ? '2FA فعال شد' : '2FA enabled') : (lang === 'fa' ? '2FA غیرفعال شد' : '2FA disabled')); }
    } catch { toast(lang === 'fa' ? 'خطا' : 'Error'); }
    setToggling2fa(false);
  };

  const updateNotificationPref = async (key: string, value: boolean) => {
    const next = { ...notifications, [key]: value }; setNotifications(next);
    try { await fetch(`${apiBase}/api/v1/auth/notifications`, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(next) }); } catch { /* ignore */ }
  };

  const savePreferences = async () => {
    setPrefsSaving(true);
    try {
      await fetch(`${apiBase}/api/v1/auth/preferences`, { method: 'PUT', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ language: languagePref, theme: themePref }) });
      toast(c.prefsSaved);
    } catch { toast(lang === 'fa' ? 'خطا' : 'Error'); }
    setPrefsSaving(false);
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/export-data`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { const d = await res.json(); toast(d.message || (lang === 'fa' ? 'خروجی آماده شد' : 'Export ready')); setShowDataExport(false); }
    } catch { toast(lang === 'fa' ? 'خطا' : 'Error'); }
    setExporting(false);
  };

  const handleDeactivate = async () => {
    setDeactivating(true); setDeactivateError('');
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/deactivate`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) { toast(lang === 'fa' ? 'حساب غیرفعال شد' : 'Account deactivated'); setDeactivateConfirm(false); }
      else { const d = await res.json(); setDeactivateError(d.detail || (lang === 'fa' ? 'خطا' : 'Error')); }
    } catch { setDeactivateError(lang === 'fa' ? 'خطا' : 'Error'); }
    setDeactivating(false);
  };

  const handleDeleteAccount = async () => {
    setDeleting(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/auth/account/delete`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify({ email: deleteEmail, confirm: deleteConfirmText }) });
      if (res.ok) { toast(lang === 'fa' ? 'حساب حذف شد' : 'Account deleted'); logout(); }
      else { const d = await res.json(); toast(d.detail || (lang === 'fa' ? 'خطا' : 'Error')); }
    } catch { toast(lang === 'fa' ? 'خطا' : 'Error'); }
    setDeleting(false); setShowDeleteConfirm(false); setDeleteStep(0); setDeleteEmail(''); setDeleteConfirmText('');
  };

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/dashboard/profile" />
      <Reveal className="flex flex-col gap-3">
        <span className="inline-flex w-fit items-center gap-2 rounded-full border border-[var(--color-leaf-500)]/30 bg-[var(--color-leaf-500)]/10 px-4 py-1 text-xs font-bold text-[var(--color-leaf-300)]">
          <User className="h-3.5 w-3.5" aria-hidden />{c.kicker}
        </span>
        <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">{c.title}</h1>
      </Reveal>

      {/* HERO BANNER */}
      <Reveal delay={0.04} className="mt-5">
        <div className="relative overflow-hidden rounded-3xl border border-white/10">
          <div className="absolute inset-0 bg-gradient-to-l from-[var(--color-leaf-500)]/30 via-[var(--color-aqua-500)]/20 to-transparent" aria-hidden />
          <div className="relative flex flex-col items-start gap-4 p-6 sm:p-8">
            <div className="flex items-center gap-4">
              <label className="group relative cursor-pointer">
                {avatarPreview || avatarUrl ? (
                  <img src={avatarPreview || avatarUrl} alt={String(user?.full_name || user?.email)} loading="lazy" className="h-20 w-20 rounded-2xl object-cover shadow-lg" />
                ) : (
                  <span className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[var(--color-aqua-500)]/25 text-[var(--color-aqua-300)]"><User className="h-9 w-9" aria-hidden /></span>
                )}
                <span className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full bg-[var(--color-night-900)]/80 backdrop-blur">
                  {avatarUploading ? (<div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />) : (<Camera className="h-3.5 w-3.5 text-white" aria-hidden />)}
                </span>
                <input type="file" accept="image/*" className="hidden" onChange={handleAvatarUpload} aria-label={lang === 'fa' ? 'آپلود عکس پروفایل' : 'Upload avatar'} />
              </label>
              <div className="min-w-0">
                <p className="text-lg font-extrabold text-[var(--color-night-100)] truncate">{String(user?.full_name || user?.name || user?.email || (lang === 'fa' ? 'کاربر' : 'User'))}</p>
                <p className="text-[11px] text-[var(--color-night-200)]/70 truncate" dir="ltr">{String(user?.email || '')}</p>
                {user?.role ? (<span className="inline-flex mt-1 rounded-full bg-white/10 px-2.5 py-0.5 text-[10px] font-bold text-[var(--color-night-200)]/80" dir="ltr">{user.role}</span>) : null}
              </div>
            </div>
            <p className="text-sm leading-6 text-[var(--color-night-200)]/80 max-w-2xl">{c.lead}</p>
          </div>
        </div>
      </Reveal>

      {/* IDENTITY */}
      <section id="section-identity" ref={el => { navRefs.current.identity = el; }}>
        <Reveal delay={0.05} className="mt-5">
          <div className="glass flex flex-col gap-5 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <Shield className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />{c.identityTitle}
            </h2>
            {loading.identity ? (
              <div className="flex flex-col gap-4"><Skeleton title lines={2} /><div className="h-24 rounded-xl bg-white/5 animate-pulse" /></div>
            ) : isAuthenticated && user ? (
              <>
                <div className="flex items-center justify-end">
                  <button type="button" onClick={handleLogout} className="inline-flex items-center gap-1.5 rounded-full border border-red-400/30 bg-red-400/10 px-3.5 py-1.5 text-[11px] font-bold text-red-300 hover:bg-red-400/20"><LogIn className="h-3.5 w-3.5" aria-hidden />{lang === 'fa' ? 'خروج' : 'Logout'}</button>
                </div>
                <div className="glass flex flex-col gap-3 rounded-2xl p-5">
                  <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.displayNameTitle}</h3>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/60">{c.displayNameLabel}</span>
                    <input type="text" value={name} onChange={(e) => { setName(e.target.value); setSaved(false); }} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" />
                    <span className="text-[10px] text-[var(--color-night-200)]/35">{c.displayNameHint}</span>
                  </label>
                  <button type="button" onClick={saveName} disabled={saving} className="w-fit rounded-full bg-[var(--color-leaf-500)]/15 px-4 py-1.5 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25 disabled:opacity-50">{saving ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال ذخیره...' : 'Saving...'}</span>) : (saved ? c.saved : c.save)}</button>
                </div>
                <div className="glass flex flex-col gap-3 rounded-2xl p-5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.identityTitle}</h3>
                    <button type="button" onClick={() => setBioEdit(!bioEdit)} className="glass glass-hover inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-bold text-[var(--color-night-100)]"><Edit3 className="h-3.5 w-3.5" aria-hidden />{c.identityEdit}</button>
                  </div>
                  {bioEdit ? (
                    <div className="flex flex-col gap-3">
                      <div className="flex flex-col gap-1.5"><span className="text-xs font-bold text-[var(--color-night-200)]/60">{c.identityBioLabel}</span><textarea value={bio} onChange={(e) => setBio(e.target.value)} placeholder={c.identityBioPlaceholder} rows={3} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" /></div>
                      <div className="flex flex-col gap-1.5"><span className="text-xs font-bold text-[var(--color-night-200)]/60">{c.identityOrgLabel}</span><input type="text" value={org} onChange={(e) => setOrg(e.target.value)} placeholder={c.identityOrgPlaceholder} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" /></div>
                      <div className="flex flex-col gap-1.5"><span className="text-xs font-bold text-[var(--color-night-200)]/60">{c.identityLocationLabel}</span><input type="text" value={location} onChange={(e) => setLocation(e.target.value)} placeholder={c.identityLocationPlaceholder} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" /></div>
                      <div className="flex items-center gap-2">
                        <button type="button" onClick={saveBio} disabled={bioSaving} className="rounded-full bg-[var(--color-leaf-500)]/15 px-4 py-1.5 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25 disabled:opacity-50">{bioSaving ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال ذخیره...' : 'Saving...'}</span>) : (lang === 'fa' ? 'ذخیره' : 'Save')}</button>
                        <button type="button" onClick={() => { setBioEdit(false); setBio(''); setOrg(''); setLocation(''); }} className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-extrabold text-[var(--color-night-100)] hover:bg-white/10">{lang === 'fa' ? 'لغو' : 'Cancel'}</button>
                      </div>
                      {bioError ? (<p className="text-xs text-red-400">{bioError}</p>) : null}
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {bio ? (<p className="text-xs leading-6 text-[var(--color-night-200)]/70">{bio}</p>) : (<p className="text-xs text-[var(--color-night-200)]/35">{c.identityBioHint}</p>)}
                      {(org || location) ? (<div className="flex flex-wrap gap-2">{org ? (<span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 px-2.5 py-0.5 text-[10px] font-bold text-[var(--color-night-200)]/70"><Building2 className="h-3 w-3" aria-hidden /> {org}</span>) : null}{location ? (<span className="inline-flex items-center gap-1.5 rounded-full bg-white/5 px-2.5 py-0.5 text-[10px] font-bold text-[var(--color-night-200)]/70"><MapPin className="h-3 w-3" aria-hidden /> {location}</span>) : null}</div>) : null}
                      {accountStatus ? (<span className="text-[10px] text-[var(--color-night-200)]/40">{c.identityMemberSince}: {fmtDate(accountStatus.created_at || (user as any)?.created_at || null)}</span>) : null}
                    </div>
                  )}
                </div>
                <div className="glass flex flex-col gap-3 rounded-2xl p-5">
                  <h3 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]"><KeyRound className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />{c.clientKeyTitle}</h3>
                  <p className="text-xs leading-6 text-[var(--color-night-200)]/55">{c.clientKeyHint}</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 overflow-x-auto rounded-xl bg-black/40 px-3 py-2 text-[11px] text-[var(--color-aqua-300)]" dir="ltr">{clientKey}</code>
                    <button type="button" onClick={copyKey} className="glass glass-hover inline-flex shrink-0 items-center gap-1.5 rounded-xl px-3 py-2 text-[11px] font-bold text-[var(--color-night-100)]">{copied ? <Check className="h-3.5 w-3.5 text-[var(--color-leaf-300)]" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}{copied ? c.copied : c.copy}</button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center gap-3 py-6">
                <User className="h-10 w-10 text-[var(--color-night-200)]/30" aria-hidden />
                <p className="text-sm text-[var(--color-night-200)]/50">{lang === 'fa' ? 'برای مشاهده پروفایل وارد شوید' : 'Sign in to view your profile'}</p>
              </div>
            )}
          </div>
        </Reveal>
      </section>

      {/* LEGACY */}
      <section id="section-legacy" ref={el => { navRefs.current.legacy = el; }}>
        <Reveal delay={0.1} className="mt-5">
          <div className="glass flex flex-col gap-5 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <Leaf className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />{c.legacyTitle}
            </h2>
            <p className="text-xs leading-6 text-[var(--color-night-200)]/60">{c.legacySubtitle}</p>
            {loading.legacy ? (
              <div className="flex flex-col gap-4"><Skeleton title lines={2} /><div className="grid grid-cols-2 gap-3"><div className="h-20 rounded-xl bg-white/5 animate-pulse" /><div className="h-20 rounded-xl bg-white/5 animate-pulse" /></div></div>
            ) : legacyData ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="rounded-2xl border border-[var(--color-leaf-500)]/20 bg-[var(--color-leaf-500)]/5 p-5">
                    <p className="text-[10px] font-bold text-[var(--color-leaf-300)]/70">{c.legacyCarbon.title}</p>
                    <p className="mt-1 text-xl font-extrabold text-[var(--color-night-100)]">{fmtNum(legacyData.carbonSequestered, c.legacyCarbon.unit)}</p>
                    <p className="text-[10px] text-[var(--color-night-200)]/40">{c.legacyCarbon.source}</p>
                  </div>
                  <div className="rounded-2xl border border-[var(--color-aqua-500)]/20 bg-[var(--color-aqua-500)]/5 p-5">
                    <p className="text-[10px] font-bold text-[var(--color-aqua-300)]/70">{c.legacyArea.title}</p>
                    <p className="mt-1 text-xl font-extrabold text-[var(--color-night-100)]">{fmtNum(legacyData.areaRestored, c.legacyArea.unit)}</p>
                    <p className="text-[10px] text-[var(--color-night-200)]/40">{c.legacyArea.source}</p>
                  </div>
                  <div className="rounded-2xl border border-[var(--color-leaf-500)]/20 bg-[var(--color-leaf-500)]/5 p-5">
                    <p className="text-[10px] font-bold text-[var(--color-leaf-300)]/70">{c.legacyWater.title}</p>
                    <p className="mt-1 text-xl font-extrabold text-[var(--color-night-100)]">{fmtNum(legacyData.waterSaved, c.legacyWater.unit)}</p>
                    <p className="text-[10px] text-[var(--color-night-200)]/40">{c.legacyWater.source}</p>
                  </div>
                  <div className="rounded-2xl border border-[var(--color-aqua-500)]/20 bg-[var(--color-aqua-500)]/5 p-5">
                    <p className="text-[10px] font-bold text-[var(--color-aqua-300)]/70">{c.legacyActivity.title}</p>
                    <p className="mt-1 text-xl font-extrabold text-[var(--color-night-100)]">{fmtNum(legacyData.activityCount, c.legacyActivity.unit)}</p>
                    <p className="text-[10px] text-[var(--color-night-200)]/40">{c.legacyActivity.source}</p>
                  </div>
                </div>
                {isAuthenticated && user ? (
                  <>
                    <AchievementList title={c.legacyAchievements} data={achievementsData?.achievements || []} empty={c.legacyAchievementEmpty} />
                    <MilestoneList title={c.legacyMilestones} data={achievementsData?.milestones || []} empty={c.legacyEmpty} />
                  </>
                ) : null}
              </>
            ) : (
              <p className="text-sm text-[var(--color-night-200)]/40">{lang === 'fa' ? 'داده‌ای در دسترس نیست' : 'No data available'}</p>
            )}
          </div>
        </Reveal>
      </section>

      {/* ASSETS */}
      <section id="section-assets" ref={el => { navRefs.current.assets = el; }}>
        <Reveal delay={0.15} className="mt-5">
          <div className="glass flex flex-col gap-5 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <Wallet className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />{c.assetsTitle}
            </h2>
            {loading.assets ? (
              <div className="flex flex-col gap-4"><Skeleton title lines={2} /><div className="grid grid-cols-2 gap-3"><div className="h-20 rounded-xl bg-white/5 animate-pulse" /><div className="h-20 rounded-xl bg-white/5 animate-pulse" /></div></div>
            ) : assetsData ? (
              <>
                <AssetGroupCard title={c.assetsLands.title} data={assetsData.lands} empty={c.assetsLands.empty} icon={<MapPin className="h-4 w-4" aria-hidden />} />
                <AssetGroupCard title={c.assetsSensors.title} data={assetsData.sensors} empty={c.assetsSensors.empty} icon={<Activity className="h-4 w-4" aria-hidden />} />
                <AssetGroupCard title={c.assetsWallet.title} data={assetsData.wallet} empty={c.assetsWallet.empty} icon={<Wallet className="h-4 w-4" aria-hidden />} />
                <AssetGroupCard title={c.assetsApiKeys.title} data={assetsData.apiKeys} empty={c.assetsApiKeys.empty} icon={<KeyRound className="h-4 w-4" aria-hidden />} />
                <AssetGroupCard title={c.assetsProjects.title} data={assetsData.projects} empty={c.assetsProjects.empty} icon={<FolderKanban className="h-4 w-4" aria-hidden />} />
              </>
            ) : (
              <p className="text-sm text-[var(--color-night-200)]/40">{lang === 'fa' ? 'داده‌ای در دسترس نیست' : 'No data available'}</p>
            )}
          </div>
        </Reveal>
      </section>

      {/* PREFERENCES */}
      <section id="section-preferences" ref={el => { navRefs.current.preferences = el; }}>
        <Reveal delay={0.2} className="mt-5">
          <div className="glass flex flex-col gap-5 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <Settings className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />{c.prefsTitle}
            </h2>
            {loading.preferences ? (
              <div className="flex flex-col gap-4"><Skeleton title lines={2} /><div className="h-24 rounded-xl bg-white/5 animate-pulse" /></div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="glass rounded-2xl p-4">
                    <p className="text-xs font-bold text-[var(--color-night-200)]/60">{c.prefsLanguage.label}</p>
                    <select value={languagePref} onChange={(e) => { setLanguagePref(e.target.value as 'fa' | 'en'); setSaved(false); }} className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none">
                      <option value="fa">فارسی</option>
                      <option value="en">English</option>
                    </select>
                  </div>
                  <div className="glass rounded-2xl p-4">
                    <p className="text-xs font-bold text-[var(--color-night-200)]/60">{c.prefsTimezone.label}</p>
                    <select value={extendedPrefs?.timezone || 'Asia/Tehran'} onChange={(e) => { setExtendedPrefs(prev => prev ? { ...prev, timezone: e.target.value } : { timezone: e.target.value, units: 'metric', theme: 'system', dashboardWidgets: null, language: languagePref }); setSaved(false); }} className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none">
                      <option>Asia/Tehran</option>
                      <option>UTC</option>
                      <option>America/New_York</option>
                      <option>Europe/London</option>
                      <option>Asia/Tokyo</option>
                      <option>Europe/Berlin</option>
                    </select>
                  </div>
                  <div className="glass rounded-2xl p-4">
                    <p className="text-xs font-bold text-[var(--color-night-200)]/60">{c.prefsUnits.label}</p>
                    {extendedPrefs ? (
                      <select value={extendedPrefs.units} onChange={(e) => { setExtendedPrefs(prev => prev ? { ...prev, units: e.target.value } : prev); setSaved(false); }} className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none">
                        <option>metric</option>
                        <option>imperial</option>
                      </select>
                    ) : null}
                    <p className="mt-1 text-[10px] text-[var(--color-night-200)]/40">{c.prefsUnitsWarning}</p>
                  </div>
                  <div className="glass rounded-2xl p-4">
                    <p className="text-xs font-bold text-[var(--color-night-200)]/60">{c.prefsTheme.label}</p>
                    <select value={themePref} onChange={(e) => { setThemePref(e.target.value as 'light' | 'dark' | 'system'); setSaved(false); }} className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none">
                      <option value="system">System</option>
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                    </select>
                  </div>
                </div>
                <div className="glass rounded-2xl p-4">
                  <p className="text-xs font-bold text-[var(--color-night-200)]/60">{c.prefsNotifications.label}</p>
                  <div className="mt-2 flex flex-col gap-2">
                    {Object.entries(notifications).map(([key, value]) => (
                      <label key={key} className="flex items-center gap-2">
                        <input type="checkbox" checked={value} onChange={(e) => updateNotificationPref(key, e.target.checked)} className="h-4 w-4 rounded border-white/20 bg-white/5" />
                        <span className="text-sm text-[var(--color-night-100)]">{key}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="flex justify-end">
                  <button type="button" onClick={savePreferences} disabled={prefsSaving} className="rounded-full bg-[var(--color-leaf-500)]/15 px-6 py-2 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25 disabled:opacity-50">{prefsSaving ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال ذخیره...' : 'Saving...'}</span>) : c.prefsSaved}</button>
                </div>
              </>
            )}
          </div>
        </Reveal>
      </section>

      {/* SECURITY */}
      <section id="section-security" ref={el => { navRefs.current.security = el; }}>
        <Reveal delay={0.25} className="mt-5">
          <div className="glass flex flex-col gap-5 rounded-3xl p-7">
            <h2 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">
              <Lock className="h-4 w-4 text-[var(--color-leaf-400)]" aria-hidden />{c.securityTitle}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button type="button" onClick={() => setShowChangePassword(!showChangePassword)} className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left">
                <span className="text-sm font-extrabold text-[var(--color-night-100)]">{c.securityPassword.label}</span>
                <span className="text-[10px] text-[var(--color-night-200)]/50">{c.securityPassword.description}</span>
              </button>
              <button type="button" onClick={toggle2fa} disabled={toggling2fa} className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left">
                <span className="text-sm font-extrabold text-[var(--color-aqua-300)]">{c.security2fa.label}</span>
                <span className="text-[10px] text-[var(--color-night-200)]/70">{c.security2fa.description} {twoFactor?.enabled ? '(ON)' : '(OFF)'}</span>
              </button>
              <button type="button" className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left">
                <span className="text-sm font-extrabold text-[var(--color-aqua-300)]">{c.securitySessions.label}</span>
                <span className="text-[10px] text-[var(--color-night-200)]/70">{c.securitySessions.description}</span>
              </button>
              <button type="button" className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left">
                <span className="text-sm font-extrabold text-[var(--color-aqua-300)]">{c.securityApiKeys.label}</span>
                <span className="text-[10px] text-[var(--color-night-200)]/70">{c.securityApiKeys.description}</span>
              </button>
              <button type="button" onClick={() => setShowDataExport(true)} className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left">
                <span className="text-sm font-extrabold text-[var(--color-leaf-300)]">{c.securityExport.label}</span>
                <span className="text-[10px] text-[var(--color-night-200)]/70">{c.securityExport.description}</span>
              </button>
              <button type="button" className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left">
                <span className="text-sm font-extrabold text-[var(--color-leaf-300)]">{c.securityPrivacy.label}</span>
                <span className="text-[10px] text-[var(--color-night-200)]/70">{c.securityPrivacy.description}</span>
              </button>
              <button type="button" onClick={() => setDeactivateConfirm(true)} className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left border border-amber-400/20">
                <span className="text-sm font-extrabold text-amber-300">{c.securityDeactivate.label}</span>
                <span className="text-[10px] text-amber-300/70">{c.securityDeactivate.description}</span>
              </button>
              <button type="button" onClick={() => { setShowDeleteConfirm(true); setDeleteStep(1); }} className="glass glass-hover flex flex-col gap-1.5 rounded-2xl p-5 text-left border border-red-400/20">
                <span className="text-sm font-extrabold text-red-300">{c.securityDelete.label}</span>
                <span className="text-[10px] text-red-300/70">{c.securityDelete.description}</span>
              </button>
            </div>

            {showChangePassword && (
              <div className="glass rounded-2xl p-5">
                <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.securityPassword.label}</h3>
                <div className="mt-3 flex flex-col gap-3">
                  <input type="password" value={pwForm.current} onChange={(e) => setPwForm(p => ({ ...p, current: e.target.value }))} placeholder={lang === 'fa' ? 'رمز فعلی' : 'Current password'} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" />
                  <input type="password" value={pwForm.next} onChange={(e) => setPwForm(p => ({ ...p, next: e.target.value }))} placeholder={lang === 'fa' ? 'رمز جدید' : 'New password'} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" />
                  <input type="password" value={pwForm.confirm} onChange={(e) => setPwForm(p => ({ ...p, confirm: e.target.value }))} placeholder={lang === 'fa' ? 'تأیید رمز' : 'Confirm password'} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-[var(--color-leaf-400)]/60 focus:outline-none" />
                  {pwError ? (<p className="text-xs text-red-400">{pwError}</p>) : null}
                  <button type="button" onClick={handleChangePassword} disabled={pwSaving} className="w-fit rounded-full bg-[var(--color-leaf-500)]/15 px-4 py-1.5 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25 disabled:opacity-50">{pwSaving ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال تغییر...' : 'Changing...'}</span>) : lang === 'fa' ? 'تغییر رمز' : 'Change'}</button>
                </div>
              </div>
            )}

            {showDataExport && (
              <div className="glass rounded-2xl p-5">
                <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{c.securityExport.label}</h3>
                <div className="mt-3 flex items-center gap-2">
                  <button type="button" onClick={handleExportData} disabled={exporting} className="rounded-full bg-[var(--color-leaf-500)]/15 px-4 py-1.5 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25 disabled:opacity-50">{exporting ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال خروجی...' : 'Exporting...'}</span>) : lang === 'fa' ? 'خروجی دانلود' : 'Download'}</button>
                  <button type="button" onClick={() => setShowDataExport(false)} className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-extrabold text-[var(--color-night-100)] hover:bg-white/10">{lang === 'fa' ? 'لغو' : 'Cancel'}</button>
                </div>
              </div>
            )}

            {deactivateConfirm && (
              <div className="glass rounded-2xl p-5 border border-amber-400/30">
                <h3 className="text-sm font-extrabold text-amber-300">{c.securityDeactivate.label}</h3>
                <p className="mt-2 text-xs text-[var(--color-night-200)]/60">{c.securityDeactivate.description}</p>
                {deactivateError ? (<p className="mt-2 text-xs text-red-400">{deactivateError}</p>) : null}
                <div className="mt-3 flex items-center gap-2">
                  <button type="button" onClick={handleDeactivate} disabled={deactivating} className="rounded-full bg-amber-400/15 px-4 py-1.5 text-xs font-extrabold text-amber-300 hover:bg-amber-400/25 disabled:opacity-50">{deactivating ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال غیرفعال‌سازی...' : 'Processing...'}</span>) : lang === 'fa' ? 'غیرفعال کردن' : 'Deactivate'}</button>
                  <button type="button" onClick={() => setDeactivateConfirm(false)} className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-extrabold text-[var(--color-night-100)] hover:bg-white/10">{lang === 'fa' ? 'لغو' : 'Cancel'}</button>
                </div>
              </div>
            )}

            {showDeleteConfirm && (
              <div className="glass rounded-2xl p-5 border border-red-400/30">
                <h3 className="text-sm font-extrabold text-red-300">{c.securityDelete.label}</h3>
                <p className="mt-2 text-xs text-[var(--color-night-200)]/60">{c.securityDeleteConfirm}</p>
                {deleteStep === 1 && (
                  <div className="mt-3 flex flex-col gap-2">
                    <input type="email" value={deleteEmail} onChange={(e) => setDeleteEmail(e.target.value)} placeholder={c.securityDeleteFinal} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-red-400/60 focus:outline-none" />
                    <button type="button" onClick={() => setDeleteStep(2)} className="w-fit rounded-full bg-red-400/15 px-4 py-1.5 text-xs font-extrabold text-red-300 hover:bg-red-400/25">{lang === 'fa' ? 'ادامه' : 'Continue'}</button>
                    <button type="button" onClick={() => { setShowDeleteConfirm(false); setDeleteStep(0); setDeleteEmail(''); }} className="text-[10px] text-[var(--color-night-200)]/40">{c.securityDeleteCancelled}</button>
                  </div>
                )}
                {deleteStep === 2 && (
                  <div className="mt-3 flex flex-col gap-2">
                    <input type="text" value={deleteConfirmText} onChange={(e) => setDeleteConfirmText(e.target.value)} placeholder={lang === 'fa' ? 'برای تأیید، DELETE را تایپ کنید' : 'Type DELETE to confirm'} className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-[var(--color-night-100)] focus:border-red-400/60 focus:outline-none" />
                    <button type="button" onClick={handleDeleteAccount} disabled={deleting} className="w-fit rounded-full bg-red-400/15 px-4 py-1.5 text-xs font-extrabold text-red-300 hover:bg-red-400/25 disabled:opacity-50">{deleting ? (<span className="inline-flex items-center gap-1.5"><Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />{lang === 'fa' ? 'در حال حذف...' : 'Deleting...'}</span>) : lang === 'fa' ? 'حذف دائمی' : 'Delete'}</button>
                    <button type="button" onClick={() => { setShowDeleteConfirm(false); setDeleteStep(0); setDeleteEmail(''); setDeleteConfirmText(''); }} className="text-[10px] text-[var(--color-night-200)]/40">{c.securityDeleteCancelled}</button>
                  </div>
                )}
              </div>
            )}
          </div>
        </Reveal>
      </section>
    </>
  );
}

function AchievementList({ title, data, empty }: { title: string; data: Array<{ icon: string; title: string; description: string; date: string }>; empty: string }) {
  if (!data.length) return <p className="text-xs text-[var(--color-night-200)]/40">{empty}</p>;
  return (
    <div>
      <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{title}</h3>
      <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {data.map((a, i) => (
          <div key={i} className="rounded-xl bg-white/5 p-3">
            <p className="text-xs font-extrabold text-[var(--color-night-100)]">{a.title}</p>
            <p className="text-[10px] text-[var(--color-night-200)]/50">{a.description}</p>
            <p className="text-[10px] text-[var(--color-night-200)]/30">{fmtDate(a.date)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function MilestoneList({ title, data, empty }: { title: string; data: Array<{ icon: string; title: string; date: string }>; empty: string }) {
  if (!data.length) return <p className="text-xs text-[var(--color-night-200)]/40">{empty}</p>;
  return (
    <div className="mt-3">
      <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">{title}</h3>
      <div className="mt-2 flex flex-col gap-2">
        {data.map((m, i) => (
          <div key={i} className="rounded-xl bg-white/5 p-3 flex items-center justify-between">
            <span className="text-xs font-extrabold text-[var(--color-night-100)]">{m.title}</span>
            <span className="text-[10px] text-[var(--color-night-200)]/30">{fmtDate(m.date)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AssetGroupCard({ title, data, empty, icon }: { title: string; data: Array<{ name: string; detail: string; status?: string }> | undefined; empty: string; icon: React.ReactNode }) {
  if (!data || !data.length) return <p className="text-xs text-[var(--color-night-200)]/40">{empty}</p>;
  return (
    <div>
      <h3 className="flex items-center gap-2 text-sm font-extrabold text-[var(--color-night-100)]">{icon}{title}</h3>
      <div className="mt-2 flex flex-col gap-2">
        {data.map((item, i) => (
          <div key={i} className="rounded-xl bg-white/5 p-3 flex items-center justify-between">
            <div>
              <p className="text-xs font-extrabold text-[var(--color-night-100)]">{item.name}</p>
              <p className="text-[10px] text-[var(--color-night-200)]/50">{item.detail}</p>
            </div>
            {item.status ? (<span className="inline-flex rounded-full bg-white/5 px-2 py-0.5 text-[9px] font-bold text-[var(--color-night-200)]/70">{item.status}</span>) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
