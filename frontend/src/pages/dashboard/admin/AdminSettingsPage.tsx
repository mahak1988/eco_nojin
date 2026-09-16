/** Admin Settings - System configuration */

import { useState, useEffect } from 'react';
import { useBilingual } from '../../../hooks/useBilingual';
import Seo from '../../../components/ui/Seo';
import Reveal from '../../../components/ui/Reveal';
import { Loader2, Save, CheckCircle, AlertCircle, Shield, Globe, CreditCard, Settings, Bell, Palette, Database, Zap, Layers } from 'lucide-react';

interface Setting {
  key: string;
  value: string;
  type: 'string' | 'number' | 'boolean' | 'json';
  category: string;
  description: string;
  is_public: boolean;
}

interface Category {
  key: string;
  label: string;
  icon: any;
  description: string;
}

const CATEGORIES: Category[] = [
  { key: 'general', label: 'عمومی', icon: Settings, description: 'تنظیمات پایه سیستم' },
  { key: 'security', label: 'امنیت', icon: Shield, description: 'احراز هویت و مجوزها' },
  { key: 'payments', label: 'پرداخت‌ها', icon: CreditCard, description: 'درگاه‌ها و کارمزدها' },
  { key: 'notifications', label: 'اعلان‌ها', icon: Bell, description: 'ایمیل، SMS و پوش' },
  { key: 'localization', label: 'بومی‌سازی', icon: Globe, description: 'زبان، ارز و منطقه' },
  { key: 'appearance', label: 'ظاهر', icon: Palette, description: 'تم و برندینگ' },
  { key: 'database', label: 'دیتابیس', icon: Database, description: 'اتصال و بهینه‌سازی' },
  { key: 'performance', label: 'عملکرد', icon: Zap, description: 'کش، صف و مقیاس‌پذیری' },
  { key: 'integrations', label: 'یکپارچه‌سازی', icon: Layers, description: 'سرویس‌های خارجی' },
];

export default function AdminSettingsPage() {
  const { fa } = useBilingual();
  const [activeCategory, setActiveCategory] = useState<string>('general');
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [formData, setFormData] = useState<Record<string, string>>({});

  const loadSettings = async () => {
    setLoading(true);
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${apiBase}/api/v1/admin/settings?category=${activeCategory}`, { headers });
      if (!res.ok) throw new Error('Failed to fetch settings');
      const data = await res.json();
      const loadedSettings = data.settings || [];
      setSettings(loadedSettings);
      const initialData: Record<string, string> = {};
      loadedSettings.forEach((s: Setting) => {
        initialData[s.key] = typeof s.value === 'string' ? s.value : JSON.stringify(s.value);
      });
      setFormData(initialData);
    } catch (err: any) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadSettings(); }, [activeCategory]);

  const handleChange = (key: string, value: string) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(activeCategory);
    setSaveStatus('idle');
    try {
      const apiBase = (window as any).API_BASE_URL || 'http://127.0.0.1:8000';
      const token = localStorage.getItem('hydroma_token');
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const settingsToSave = settings.map(s => ({
        key: s.key,
        value: formData[s.key] ?? s.value,
        type: s.type,
      }));

      await fetch(`${apiBase}/api/v1/admin/settings`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ category: activeCategory, settings: settingsToSave }),
      });
      setSaveStatus('success');
      loadSettings();
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } finally {
      setSaving(null);
    }
  };

  const renderInput = (setting: Setting) => {
    const value = formData[setting.key] ?? setting.value;
    switch (setting.type) {
      case 'boolean':
        return (
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={value === 'true'}
              onChange={e => handleChange(setting.key, e.target.checked.toString())}
              className="w-5 h-5 rounded border-[var(--color-night-200)]/30 text-[var(--color-leaf-500)] focus:ring-[var(--color-leaf-500)]"
            />
            <span className="text-sm text-[var(--color-night-100)]">{fa('فعال', 'Enabled')}</span>
          </label>
        );
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={e => handleChange(setting.key, e.target.value)}
            className="w-full px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
          />
        );
      case 'json':
        return (
          <textarea
            value={value}
            onChange={e => handleChange(setting.key, e.target.value)}
            rows={4}
            className="w-full px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] font-mono focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
            placeholder="JSON format"
          />
        );
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={e => handleChange(setting.key, e.target.value)}
            className="w-full px-3 py-2 bg-[var(--color-night-50)] border border-[var(--color-night-200)]/20 rounded-xl text-sm text-[var(--color-night-100)] focus:outline-none focus:ring-2 focus:ring-[var(--color-leaf-400)]"
          />
        );
    }
  };

  if (loading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-[var(--color-leaf-400)]" /></div>;

  return (
    <>
      <Seo title={fa('تنظیمات سیستم', 'System Settings')} path="/dashboard/admin/settings" />
      <div className="px-4 py-10 sm:px-6">
        <div className="mx-auto max-w-7xl">
          <Reveal>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
              <div>
                <h1 className="text-2xl font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                  <Settings className="h-6 w-6 text-[var(--color-leaf-400)]" />
                  {fa('تنظیمات سیستم', 'System Settings')}
                </h1>
                <p className="mt-1 text-sm text-[var(--color-night-200)]/60">{fa('کانفیگوریشن‌های کلی برنامه', 'Application-wide configuration')}</p>
              </div>
              <button onClick={handleSave} disabled={saving === activeCategory} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-leaf-500)] text-white text-sm font-bold hover:bg-[var(--color-leaf-600)] transition disabled:opacity-50">
                {saving === activeCategory ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {fa('ذخیره تغییرات', 'Save Changes')}
              </button>
            </div>
          </Reveal>

          {saveStatus === 'success' && <Reveal><div className="mb-6 flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 text-sm"><CheckCircle className="h-4 w-4" /> {fa('تنظیمات با موفقیت ذخیره شد', 'Settings saved successfully')}</div></Reveal>}
          {saveStatus === 'error' && <Reveal><div className="mb-6 flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm"><AlertCircle className="h-4 w-4" /> {fa('خطا در ذخیره', 'Failed to save settings')}</div></Reveal>}

          <div className="flex flex-col lg:flex-row gap-6">
            {/* Sidebar Categories */}
            <Reveal delay={0.1}>
              <div className="lg:w-56 flex-shrink-0">
                <div className="glass rounded-2xl overflow-hidden">
                  <nav className="p-2">
                    {CATEGORIES.map(cat => (
                      <button
                        key={cat.key}
                        onClick={() => setActiveCategory(cat.key)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                          activeCategory === cat.key
                            ? 'bg-[var(--color-leaf-500)]/10 text-[var(--color-leaf-400)]'
                            : 'text-[var(--color-night-200)]/60 hover:bg-[var(--color-night-50)] hover:text-[var(--color-night-100)]'
                        }`}
                      >
                        <cat.icon className="h-5 w-5 flex-shrink-0" /> {fa(cat.label, cat.label)}
                      </button>
                    ))}
                  </nav>
                </div>
              </div>
            </Reveal>

            {/* Settings Form */}
            <Reveal delay={0.2}>
              <div className="flex-1 glass rounded-2xl p-6">
                <div className="mb-6">
                  {(() => {
                    const cat = CATEGORIES.find(c => c.key === activeCategory);
                    const Icon = cat?.icon;
                    return (
                      <h2 className="text-lg font-bold text-[var(--color-night-100)] flex items-center gap-2">
                        {Icon && <Icon className="h-5 w-5 text-[var(--color-leaf-400)]" />}
                        {fa(cat?.label || '', cat?.label || '')}
                      </h2>
                    );
                  })()}
                  <p className="text-sm text-[var(--color-night-200)]/60 mt-1">{CATEGORIES.find(c => c.key === activeCategory)?.description}</p>
                </div>

                {settings.length === 0 ? (
                  <div className="text-center py-12 text-[var(--color-night-200)]/50">
                    <Settings className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>{fa('تنظیمی در این دسته وجود ندارد', 'No settings in this category')}</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {settings.map(setting => (
                      <div key={setting.key} className="border-t border-white/5 pt-6 first:border-0 first:pt-0">
                        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <label className="block text-sm font-medium text-[var(--color-night-100)] mb-1">{fa(setting.description, setting.description)}</label>
                            <p className="text-xs text-[var(--color-night-200)]/50 font-mono">{setting.key}</p>
                            {setting.is_public && <span className="inline-block mt-1 px-2 py-0.5 text-[10px] bg-purple-500/20 text-purple-400 rounded">{fa('عمومی', 'Public')}</span>}
                          </div>
                          <div className="w-full sm:w-80 sm:flex-shrink-0">{renderInput(setting)}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </>
  );
}