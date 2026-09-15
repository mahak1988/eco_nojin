/** Organization management UI — Phase 5.2 continued. */

import { useState, useCallback, useEffect } from 'react';
import { useBilingual } from '../../hooks/useBilingual';
import Seo from '../../components/ui/Seo';
import PageHeader from '../../components/sections/PageHeader';
import Reveal from '../../components/ui/Reveal';
import { Users, Building2, UserPlus, Trash2, Edit3, RefreshCw } from 'lucide-react';
import { getApiBase } from '../../lib/api';

interface Organization {
  id: string;
  name: string;
  slug: string;
  country: string;
  description: string;
  role: string;
  created_at: string;
}

export default function OrganizationManagementPage() {
  const { lang } = useBilingual();
  const isFa = lang === 'fa';
  const f = (p: string, e: string) => (isFa ? p : e);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newCountry, setNewCountry] = useState('');

  const loadOrgs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/organizations`);
      if (res.ok) {
        const data = await res.json();
        setOrganizations(data.organizations ?? []);
      }
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrgs();
  }, [loadOrgs]);

  const handleCreate = async () => {
    if (!newName.trim() || !newCountry.trim()) return;
    try {
      const res = await fetch(`${getApiBase()}/api/v1/organizations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName,
          slug: newName.toLowerCase().replace(/\s+/g, '-'),
          country: newCountry,
          description: '',
        }),
      });
      if (res.ok) {
        setShowCreate(false);
        setNewName('');
        setNewCountry('');
        loadOrgs();
      }
    } catch {
      /* ignore */
    }
  };

  const handleDelete = async (orgId: string) => {
    try {
      await fetch(`${getApiBase()}/api/v1/organizations/${orgId}`, { method: 'DELETE' });
      loadOrgs();
    } catch {
      /* ignore */
    }
  };

  return (
    <>
      <Seo title={f('سازمان‌ها', 'Organizations')} path="/dashboard/organizations" />
      <PageHeader
        kicker={f('پلتفرم', 'Platform')}
        title={f('مدیریت سازمان‌ها', 'Organization Management')}
        lead={f('مدیریت کاربران، نقش‌ها و دسترسی‌ها در سازمان‌های شما.', 'Manage users, roles, and access in your organizations.')}
      />

      <section className="px-4 py-12 sm:px-6" id="organizations">
        <div className="mx-auto flex max-w-4xl flex-col gap-8">
          <Reveal>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
                <Building2 className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                {f('سازمان‌های من', 'My Organizations')}
              </h2>
              <button
                type="button"
                onClick={() => setShowCreate(!showCreate)}
                className="inline-flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2 text-xs font-extrabold text-white transition hover:bg-[var(--color-leaf-400)]"
              >
                <UserPlus className="h-3.5 w-3.5" aria-hidden />
                {f('سازمان جدید', 'New Org')}
              </button>
            </div>
          </Reveal>

          {showCreate && (
            <Reveal delay={0.1}>
              <div className="glass rounded-2xl p-5">
                <h3 className="text-sm font-extrabold text-[var(--color-night-100)] mb-3">
                  {f('ایجاد سازمان جدید', 'Create New Organization')}
                </h3>
                <div className="flex flex-col gap-3">
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder={f('نام سازمان', 'Organization Name')}
                    className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
                  />
                  <input
                    type="text"
                    value={newCountry}
                    onChange={(e) => setNewCountry(e.target.value)}
                    placeholder={f('کشور (کد ۲ حرفی)', 'Country (2-letter code)')}
                    className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
                  />
                  <button
                    type="button"
                    onClick={handleCreate}
                    disabled={!newName.trim() || !newCountry.trim()}
                    className="rounded-xl bg-[var(--color-leaf-500)] px-4 py-2.5 text-sm font-extrabold text-white transition hover:bg-[var(--color-leaf-400)] disabled:opacity-50"
                  >
                    {f('ایجاد', 'Create')}
                  </button>
                </div>
              </div>
            </Reveal>
          )}

          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 mx-auto animate-spin text-[var(--color-leaf-400)]" aria-hidden />
            </div>
          ) : organizations.length === 0 ? (
            <div className="glass rounded-2xl p-6 text-center">
              <Building2 className="h-8 w-8 mx-auto mb-3 text-[var(--color-night-200)]/20" aria-hidden />
              <p className="text-sm text-[var(--color-night-200)]/50">{f('هیچ سازمانی یافت نشد', 'No organizations found')}</p>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {organizations.map((org) => (
                <div key={org.id} className="glass rounded-2xl p-5">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-[var(--color-leaf-500)]/15 flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-extrabold text-[var(--color-night-100)] truncate">{org.name}</h4>
                      <p className="text-[10px] text-[var(--color-night-200)]/50">
                        {f('نقش', 'Role')}: {org.role} · {org.country}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDelete(org.id)}
                      className="rounded-lg p-2 text-[var(--color-night-200)]/30 hover:text-red-400 hover:bg-red-400/10 transition"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Reveal delay={0.2}>
            <div className="glass rounded-2xl p-5">
              <h3 className="text-base font-extrabold text-[var(--color-night-100)] flex items-center gap-2 mb-3">
                <Users className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
                {f('مدیریت اعضا', 'Member Management')}
              </h3>
              <p className="text-sm text-[var(--color-night-200)]/60">
                {f('برای مدیریت اعضا، وارد سازمان خود شوید و از منوی تنظیمات استفاده کنید.', 'To manage members, enter your organization and use settings menu.')}
              </p>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl bg-white/5 p-4 text-center">
                  <UserPlus className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-xs font-bold text-[var(--color-night-100)]">{f('دعوت عضو', 'Invite')}</p>
                </div>
                <div className="rounded-xl bg-white/5 p-4 text-center">
                  <Edit3 className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-xs font-bold text-[var(--color-night-100)]">{f('ویرایش نقش', 'Edit Role')}</p>
                </div>
                <div className="rounded-xl bg-white/5 p-4 text-center">
                  <Trash2 className="h-6 w-6 mx-auto mb-2 text-[var(--color-leaf-400)]" aria-hidden />
                  <p className="text-xs font-bold text-[var(--color-night-100)]">{f('حذف عضو', 'Remove')}</p>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
