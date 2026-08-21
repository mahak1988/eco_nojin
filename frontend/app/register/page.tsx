"use client";
import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { UserPlus, Mail, Lock, User, Phone, MapPin, Globe, Upload, AlertCircle, Loader2, CheckCircle, Building2, GraduationCap, Sprout, Plane } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { useAuth } from '../../lib/auth-context';
import { useI18n } from '../../lib/i18n-context';

const ROLES = [
  { value: 'farmer', label: 'Farmer / Rancher', icon: Sprout, desc: 'Farm management & sustainable practices' },
  { value: 'researcher', label: 'Researcher / Student', icon: GraduationCap, desc: 'Scientific data & analysis tools' },
  { value: 'organization', label: 'Company / Organization', icon: Building2, desc: 'Team management & reports' },
  { value: 'tourist', label: 'Tourist / Host', icon: Plane, desc: 'Discover sustainable farms & stays' },
  { value: 'regular', label: 'Regular User', icon: User, desc: 'General platform access' },
];

const LANGUAGES = [
  { value: 'fa', label: 'ظپط§ط±ط³غŒ', flag: '🇮🇷' },
  { value: 'en', label: 'English', flag: '🇬🇧' },
  { value: 'ar', label: 'ط§ظ„ط¹ط±ط¨ظٹط©', flag: '🇸🇦' },
  { value: 'tr', label: 'Tأ¼rkأ§e', flag: '🇹🇷' },
];

export default function RegisterPage() {
  const { t } = useI18n();
  const { colors } = useTheme();
  const { register } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [compressedAvatar, setCompressedAvatar] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'regular',
    phone: '',
    date_of_birth: '',
    country: 'Iran',
    city: '',
    address: '',
    language: 'fa',
    accept_tos: false,
    accept_privacy: false,
  });

  // Avatar compression using HTML5 Canvas
  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      setError('File too large (max 10MB)');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX_SIZE = 300;
        const scale = Math.min(MAX_SIZE / img.width, MAX_SIZE / img.height);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        const ctx = canvas.getContext('2d');
        ctx?.drawImage(img, 0, 0, canvas.width, canvas.height);
        const compressed = canvas.toDataURL('image/jpeg', 0.7);
        setAvatarPreview(compressed);
        setCompressedAvatar(compressed);
        setError(null);
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  // Validation
  const errors = {
    name: formData.full_name.length < 2 ? 'Name must be at least 2 characters' : null,
    email: !formData.email.includes('@') ? 'Invalid email' : null,
    password: formData.password.length < 6 ? 'Password must be at least 6 characters' : null,
    confirm: formData.password !== formData.confirmPassword ? 'Passwords do not match' : null,
  };

  const isStep1Valid = !errors.name && !errors.email && !errors.password && !errors.confirm && formData.email && formData.password;
  const isStep2Valid = formData.accept_tos && formData.accept_privacy;

  const handleSubmit = async () => {
    if (!isStep2Valid) return;
    setError(null);
    setLoading(true);

    try {
      const res = await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        role: formData.role,
        phone: formData.phone || undefined,
        date_of_birth: formData.date_of_birth || undefined,
        country: formData.country || undefined,
        city: formData.city || undefined,
        address: formData.address || undefined,
        language: formData.language,
        avatar_url: compressedAvatar || undefined,
        accept_tos: formData.accept_tos,
        accept_privacy: formData.accept_privacy,
      });

      if (res.success) {
        router.push('/dashboard?welcome=1');
      } else {
        setError(res.error || 'Registration failed');
      }
    } catch (e: any) {
      setError(e.message || 'Registration error');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = (hasError: boolean | null) => ({
    width: '100%', padding: '10px 14px', borderRadius: '10px',
    border: `1px solid ${hasError ? colors.danger : colors.border}`,
    background: colors.bg, color: colors.text, fontSize: '0.95rem',
    boxSizing: 'border-box' as const,
  });

  return (
    <div dir={formData.language === 'fa' || formData.language === 'ar' ? 'rtl' : 'ltr'} style={{ 
      background: `linear-gradient(135deg, ${colors.bg}, ${colors.bgAlt})`,
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px',
    }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg, padding: '32px', borderRadius: '24px',
          border: `1px solid ${colors.border}`, maxWidth: '600px', width: '100%',
          boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h1 style={{ color: colors.text, fontSize: '1.75rem', fontWeight: '800' }}>Create Account</h1>
          <p style={{ color: colors.textMuted, fontSize: '0.9rem' }}>Step {step} of 2</p>
          {/* Progress bar */}
          <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
            <div style={{ flex: 1, height: '4px', borderRadius: '2px', background: colors.primary }} />
            <div style={{ flex: 1, height: '4px', borderRadius: '2px', background: step >= 2 ? colors.primary : colors.border }} />
          </div>
        </div>

        {step === 1 && (
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
            {/* Role Selection */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: colors.text, marginBottom: '8px', fontWeight: '600' }}>
                Choose your role
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '8px' }}>
                {ROLES.map((role) => {
                  const Icon = role.icon;
                  const active = formData.role === role.value;
                  return (
                    <button key={role.value} type="button"
                      onClick={() => setFormData({ ...formData, role: role.value })}
                      style={{
                        padding: '12px', borderRadius: '12px', textAlign: 'center', cursor: 'pointer',
                        background: active ? `${colors.primary}20` : colors.bg,
                        border: `2px solid ${active ? colors.primary : colors.border}`,
                        color: colors.text,
                      }}>
                      <Icon size={24} color={active ? colors.primary : colors.textMuted} style={{ margin: '0 auto 4px', display: 'block' }} />
                      <div style={{ fontSize: '0.8rem', fontWeight: '600' }}>{role.label}</div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Name & Email */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Full Name *</label>
                <input type="text" value={formData.full_name}
                  onChange={e => setFormData({...formData, full_name: e.target.value})}
                  aria-label={t('register_name')} placeholder="Your name" style={inputStyle(!!errors.name && !!formData.full_name)} />
                {errors.name && formData.full_name && <div style={{ fontSize: '0.75rem', color: colors.danger, marginTop: '4px' }}>{errors.name}</div>}
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Email *</label>
                <input type="email" value={formData.email}
                  onChange={e => setFormData({...formData, email: e.target.value})}
                  aria-label={t('register_email')} placeholder="you@example.com" style={inputStyle(!!errors.email && !!formData.email)} />
              </div>
            </div>

            {/* Passwords */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Password *</label>
                <input type="password" value={formData.password}
                  onChange={e => setFormData({...formData, password: e.target.value})}
                  aria-label={t('register_password')} placeholder="Min 6 characters" style={inputStyle(!!errors.password && !!formData.password)} />
                {formData.password && (
                  <div style={{ display: 'flex', gap: '4px', marginTop: '6px' }}>
                    {[1,2,3,4].map(i => (
                      <div key={i} style={{
                        flex: 1, height: '4px', borderRadius: '2px',
                        background: formData.password.length >= i * 3
                          ? formData.password.length >= 12 ? colors.success
                            : formData.password.length >= 8 ? colors.warm : colors.danger
                          : colors.border,
                      }} />
                    ))}
                  </div>
                )}
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Confirm *</label>
                <input type="password" value={formData.confirmPassword}
                  onChange={e => setFormData({...formData, confirmPassword: e.target.value})}
                  aria-label={t('register_password_confirm')} placeholder="Repeat password" style={inputStyle(!!errors.confirm && !!formData.confirmPassword)} />
              </div>
            </div>

            <motion.button type="button" onClick={() => isStep1Valid && setStep(2)}
              whileHover={isStep1Valid ? { scale: 1.02 } : {}}
              disabled={!isStep1Valid}
              style={{
                width: '100%', padding: '12px', borderRadius: '10px',
                background: isStep1Valid ? colors.primary : colors.textMuted,
                color: 'white', border: 'none', fontWeight: '600',
                cursor: isStep1Valid ? 'pointer' : 'not-allowed',
              }}>
              Next â†’
            </motion.button>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
            {/* Avatar */}
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <div style={{
                width: '100px', height: '100px', borderRadius: '50%',
                background: colors.bg, border: `2px dashed ${colors.border}`,
                margin: '0 auto 8px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                overflow: 'hidden', position: 'relative', cursor: 'pointer',
              }}>
                {avatarPreview
                  ? <img src={avatarPreview} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <Upload size={32} color={colors.textMuted} />}
                <input type="file" accept="image/*" aria-label={t('profile_upload_avatar')} onChange={handleImageUpload}
                  style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} />
              </div>
              <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                Avatar (auto-compressed to ~50KB)
              </div>
            </div>

            {/* KYC fields */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Phone</label>
                <input type="tel" value={formData.phone}
                  onChange={e => setFormData({...formData, phone: e.target.value})}
                  aria-label={t('register_phone')} placeholder="+98..." style={inputStyle(null)} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Date of Birth</label>
                <input type="date" value={formData.date_of_birth}
                  onChange={e => setFormData({...formData, date_of_birth: e.target.value})}
                  style={inputStyle(null)} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Country</label>
                <input type="text" value={formData.country}
                  onChange={e => setFormData({...formData, country: e.target.value})}
                  style={inputStyle(null)} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>City</label>
                <input type="text" value={formData.city}
                  onChange={e => setFormData({...formData, city: e.target.value})}
                  style={inputStyle(null)} />
              </div>
            </div>

            {/* Language */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Globe size={14} /> Platform Language
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                {LANGUAGES.map(lang => (
                  <button key={lang.value} type="button"
                    onClick={() => setFormData({...formData, language: lang.value})}
                    style={{
                      padding: '10px', borderRadius: '8px', cursor: 'pointer',
                      background: formData.language === lang.value ? `${colors.primary}20` : colors.bg,
                      border: `2px solid ${formData.language === lang.value ? colors.primary : colors.border}`,
                      color: colors.text, fontSize: '0.85rem',
                    }}>
                    <div>{lang.flag}</div>
                    <div style={{ fontSize: '0.7rem', marginTop: '2px' }}>{lang.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Legal checkboxes */}
            <div style={{ marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.85rem', color: colors.text, cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.accept_tos}
                  onChange={e => setFormData({...formData, accept_tos: e.target.checked})}
                  style={{ marginTop: '3px' }} />
                <span>I accept the <a href="/legal/terms" target="_blank" style={{ color: colors.primary }}>Terms of Service</a> and agree to abide by them.</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.85rem', color: colors.text, cursor: 'pointer' }}>
                <input type="checkbox" checked={formData.accept_privacy}
                  onChange={e => setFormData({...formData, accept_privacy: e.target.checked})}
                  style={{ marginTop: '3px' }} />
                <span>I have read and accept the <a href="/legal/privacy" target="_blank" style={{ color: colors.primary }}>Privacy Policy</a> and consent to processing my personal data for identity verification and platform services.</span>
              </label>
            </div>

            {error && (
              <div style={{
                padding: '10px', background: `${colors.danger}15`, borderRadius: '8px',
                color: colors.danger, fontSize: '0.85rem', marginBottom: '12px',
                display: 'flex', gap: '8px', alignItems: 'center',
              }}>
                <AlertCircle size={16} /> {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button type="button" onClick={() => setStep(1)}
                style={{
                  flex: 1, padding: '12px', borderRadius: '10px',
                  background: colors.bg, color: colors.text, border: `1px solid ${colors.border}`,
                  cursor: 'pointer', fontWeight: '600',
                }}>
                â†گ Back
              </button>
              <motion.button type="button" onClick={handleSubmit}
                whileHover={isStep2Valid && !loading ? { scale: 1.02 } : {}}
                disabled={loading || !isStep2Valid}
                style={{
                  flex: 2, padding: '12px', borderRadius: '10px',
                  background: loading || !isStep2Valid ? colors.textMuted : `linear-gradient(135deg, ${colors.primary}, ${colors.accent})`,
                  color: 'white', border: 'none', cursor: loading || !isStep2Valid ? 'not-allowed' : 'pointer',
                  fontWeight: '600', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                }}>
                {loading ? <><Loader2 size={18} className="animate-spin" /> Creating...</> : <><CheckCircle size={18} /> Create Account</>}
              </motion.button>
            </div>
          </motion.div>
        )}

        <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.9rem', color: colors.textMuted }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: colors.primary, fontWeight: '600' }}>Login</Link>
        </div>
      </motion.div>

      <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}