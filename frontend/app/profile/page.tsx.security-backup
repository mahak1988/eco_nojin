"use client";
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '../../components/layout/Navbar';
import Footer from '../../components/layout/Footer';
import { motion } from 'framer-motion';
import { User, Save, Lock, AlertCircle, CheckCircle, Loader2, LogOut, Upload, Globe } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';
import { useAuth } from '../../lib/auth-context';
import { api } from '../../lib/api-client';

const LANGUAGES = [
  { value: 'fa', label: 'ظپط§ط±ط³غŒ' },
  { value: 'en', label: 'English' },
  { value: 'ar', label: 'ط§ظ„ط¹ط±ط¨ظٹط©' },
  { value: 'tr', label: 'Tأ¼rkأ§e' },
];

export default function ProfilePage() {
  const { colors } = useTheme();
  const { user, isAuthenticated, logout, updateUser } = useAuth();
  const router = useRouter();

  const [profile, setProfile] = useState<any>(null);
  const [password, setPassword] = useState({ current: '', new: '', confirm: '' });
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState({ profile: false, password: false });
  const [messages, setMessages] = useState<any>({});
  const [errors, setErrors] = useState<any>({});

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    if (user) {
      setProfile({
        full_name: user.full_name || '',
        phone: user.phone || '',
        date_of_birth: user.date_of_birth || '',
        country: user.country || '',
        city: user.city || '',
        address: user.address || '',
        language: user.language || 'fa',
      });
      setAvatarPreview(user.avatar_url || null);
    }
  }, [isAuthenticated, user, router]);

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const MAX = 300;
        const scale = Math.min(MAX / img.width, MAX / img.height);
        canvas.width = img.width * scale;
        canvas.height = img.height * scale;
        canvas.getContext('2d')?.drawImage(img, 0, 0, canvas.width, canvas.height);
        const compressed = canvas.toDataURL('image/jpeg', 0.7);
        setAvatarPreview(compressed);
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({}); setMessages({});
    setLoading({ ...loading, profile: true });
    try {
      const res = await api.put<any>('/api/v1/auth/profile', {
        ...profile,
        avatar_url: avatarPreview,
      });
      if (res.success) {
        setMessages({ profile: 'Profile updated' });
        if (res.data) updateUser(res.data);
        // If language changed, reload to apply
        if (profile.language !== user?.language) {
          setTimeout(() => window.location.reload(), 1500);
        }
      } else {
        setErrors({ profile: res.error });
      }
    } catch (e: any) {
      setErrors({ profile: e.message });
    } finally {
      setLoading({ ...loading, profile: false });
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({}); setMessages({});
    if (password.new.length < 6) { setErrors({ password: 'Min 6 chars' }); return; }
    if (password.new !== password.confirm) { setErrors({ password: 'Passwords mismatch' }); return; }
    setLoading({ ...loading, password: true });
    try {
      const res = await api.post<any>('/api/v1/auth/change-password', {
        current_password: password.current, new_password: password.new,
      });
      if (res.success) {
        setMessages({ password: 'Password changed' });
        setPassword({ current: '', new: '', confirm: '' });
      } else {
        setErrors({ password: res.error });
      }
    } catch (e: any) {
      setErrors({ password: e.message });
    } finally {
      setLoading({ ...loading, password: false });
    }
  };

  if (!profile) return null;

  return (
    <div dir={profile.language === 'fa' || profile.language === 'ar' ? 'rtl' : 'ltr'} style={{ background: colors.bg, minHeight: '100vh' }}>
      <Navbar />
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 20px' }}>
        <h1 style={{ color: colors.text, fontSize: '2rem', fontWeight: '800', marginBottom: '32px' }}>Profile Settings</h1>

        {/* Avatar + Info */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          style={{ background: colors.cardBg, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}`, marginBottom: '24px' }}>
          <h2 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <User size={20} color={colors.primary} /> Profile Information
          </h2>

          <form onSubmit={handleProfileUpdate}>
            {/* Avatar */}
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <div style={{
                width: '100px', height: '100px', borderRadius: '50%',
                background: colors.bg, border: `2px dashed ${colors.border}`,
                margin: '0 auto 8px', overflow: 'hidden', position: 'relative', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {avatarPreview
                  ? <img src={avatarPreview} alt="Avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <User size={40} color={colors.textMuted} />}
                <input type="file" accept="image/*" onChange={handleImageUpload}
                  style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }} />
              </div>
              <div style={{ fontSize: '0.75rem', color: colors.textMuted }}>
                <Upload size={12} style={{ display: 'inline' }} /> Click to change (auto-compressed)
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Full Name</label>
                <input type="text" value={profile.full_name} onChange={e => setProfile({...profile, full_name: e.target.value})}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Email (read-only)</label>
                <input type="email" value={user?.email} disabled
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: `${colors.bg}80`, color: colors.textMuted, boxSizing: 'border-box' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Phone</label>
                <input type="tel" value={profile.phone} onChange={e => setProfile({...profile, phone: e.target.value})}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Date of Birth</label>
                <input type="date" value={profile.date_of_birth} onChange={e => setProfile({...profile, date_of_birth: e.target.value})}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>Country</label>
                <input type="text" value={profile.country} onChange={e => setProfile({...profile, country: e.target.value})}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>City</label>
                <input type="text" value={profile.city} onChange={e => setProfile({...profile, city: e.target.value})}
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Globe size={14} /> Language (reload on change)
              </label>
              <select value={profile.language} onChange={e => setProfile({...profile, language: e.target.value})}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }}>
                {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
              </select>
            </div>

            {errors.profile && <div style={{ padding: '10px', background: `${colors.danger}15`, borderRadius: '8px', color: colors.danger, fontSize: '0.85rem', marginBottom: '12px' }}><AlertCircle size={16} style={{ display: 'inline' }} /> {errors.profile}</div>}
            {messages.profile && <div style={{ padding: '10px', background: `${colors.success}15`, borderRadius: '8px', color: colors.success, fontSize: '0.85rem', marginBottom: '12px' }}><CheckCircle size={16} style={{ display: 'inline' }} /> {messages.profile}</div>}

            <motion.button type="submit" whileHover={{ scale: 1.02 }} disabled={loading.profile}
              style={{ padding: '12px 24px', borderRadius: '10px', background: colors.primary, color: 'white', border: 'none', cursor: 'pointer', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {loading.profile ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              {loading.profile ? 'Saving...' : 'Save Changes'}
            </motion.button>
          </form>
        </motion.div>

        {/* Change Password */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
          style={{ background: colors.cardBg, padding: '24px', borderRadius: '16px', border: `1px solid ${colors.border}`, marginBottom: '24px' }}>
          <h2 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Lock size={20} color={colors.warm} /> Change Password
          </h2>

          <form onSubmit={handlePasswordChange}>
            {['current', 'new', 'confirm'].map(field => (
              <div key={field} style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '0.8rem', color: colors.text, marginBottom: '4px', display: 'block' }}>
                  {field === 'current' ? 'Current Password' : field === 'new' ? 'New Password' : 'Confirm New Password'}
                </label>
                <input type="password" value={(password as any)[field]} onChange={e => setPassword({...password, [field]: e.target.value})} required
                  style={{ width: '100%', padding: '10px', borderRadius: '8px', border: `1px solid ${colors.border}`, background: colors.bg, color: colors.text, boxSizing: 'border-box' }} />
              </div>
            ))}

            {errors.password && <div style={{ padding: '10px', background: `${colors.danger}15`, borderRadius: '8px', color: colors.danger, fontSize: '0.85rem', marginBottom: '12px' }}><AlertCircle size={16} style={{ display: 'inline' }} /> {errors.password}</div>}
            {messages.password && <div style={{ padding: '10px', background: `${colors.success}15`, borderRadius: '8px', color: colors.success, fontSize: '0.85rem', marginBottom: '12px' }}><CheckCircle size={16} style={{ display: 'inline' }} /> {messages.password}</div>}

            <motion.button type="submit" whileHover={{ scale: 1.02 }} disabled={loading.password}
              style={{ padding: '12px 24px', borderRadius: '10px', background: colors.warm, color: 'white', border: 'none', cursor: 'pointer', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {loading.password ? <Loader2 size={16} className="animate-spin" /> : <Lock size={16} />}
              {loading.password ? 'Changing...' : 'Change Password'}
            </motion.button>
          </form>
        </motion.div>

        <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          onClick={async () => { await logout(); router.push('/login'); }}
          whileHover={{ scale: 1.02 }}
          style={{ width: '100%', padding: '14px', borderRadius: '12px', background: `${colors.danger}15`, color: colors.danger, border: `1px solid ${colors.danger}40`, cursor: 'pointer', fontWeight: '600', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <LogOut size={18} /> Logout
        </motion.button>
      </div>
      <Footer />

      <style jsx global>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
}