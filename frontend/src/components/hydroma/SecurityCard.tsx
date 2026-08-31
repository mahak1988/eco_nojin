import React, { useEffect, useState } from 'react';
import { ShieldCheck, Search, Globe, KeyRound, Activity, AlertOctagon } from 'lucide-react';

interface LayerStatus {
  active?: boolean;
  rules?: number;
  blocks?: number;
  hits?: number;
  available?: boolean;
  kem?: string;
  signature?: string;
  note?: string;
}

interface StatusData {
  status?: string;
  layers?: {
    waf?: LayerStatus;
    rate_limit?: LayerStatus;
    headers?: LayerStatus;
    jwt_rls?: LayerStatus;
    anti_phishing?: LayerStatus;
    post_quantum?: LayerStatus;
    self_healing?: LayerStatus;
    honeypot?: LayerStatus;
    anomaly?: LayerStatus;
    encryption?: LayerStatus;
    rbac_audit?: LayerStatus;
  };
  error?: string;
}

/**
 * فاز ۸-ج — وضعیت فایروال عنکبوتی (۱۰+ لایه) + بررسی ضد فیشینگ زنده.
 */
export const SecurityCard: React.FC = () => {
  const [data, setData] = useState<StatusData | null>(null);
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [domain, setDomain] = useState('');
  const [check, setCheck] = useState<{
    verdict?: string;
    email_auth?: { verdict?: string; spf?: string[]; dkim?: string[]; dmarc?: string[] };
  } | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/v1/security/status');
        const d = (await res.json()) as StatusData;
        setData(d);
        setStatus('ok');
      } catch (e) {
        setStatus('error');
        setData({ error: e instanceof Error ? e.message : 'خطا' });
      }
    })();
  }, []);

  const runCheck = async () => {
    const d = domain.trim();
    if (!d) return;
    try {
      const res = await fetch('/api/v1/security/anti-phishing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: d.replace(/^https?:\/\//, '').split('/')[0] }),
      });
      setCheck((await res.json()) as typeof check);
    } catch {
      setCheck({ verdict: 'error' });
    }
  };

  const L = data?.layers;
  const pq = L?.post_quantum?.available ? 'کیبر/دیلیتیوم' : 'رایگان (لبه Cloudflare)';

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginBottom: '0.7rem',
        }}
      >
        <h3
          style={{
            fontSize: '1.05rem',
            fontWeight: 800,
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: '#0d9488',
          }}
        >
          <ShieldCheck size={17} /> فایروال عنکبوتی (۱۰+ لایه)
        </h3>
        {status === 'ok' && (
          <span style={{ fontSize: '0.72rem', color: '#10b981', fontWeight: 700 }}>
            ● فعال — {L?.waf?.rules ?? 0} قاعده WAF
          </span>
        )}
      </div>

      {status === 'loading' && (
        <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          در حال دریافت وضعیت لایه‌ها…
        </p>
      )}
      {status === 'error' && (
        <p style={{ fontSize: '0.82rem', color: '#ef4444' }}>⚠️ {data?.error}</p>
      )}

      {status === 'ok' && L && (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
              gap: '0.4rem',
              marginBottom: '0.7rem',
            }}
          >
            <Mini label="WAF" icon={<Activity size={11} />} value={`${L.waf?.blocks ?? 0} بلاک`} />
            <Mini label="Rate limit" icon={<Activity size={11} />} value="پنجره لغزان" />
            <Mini label="هدرهای امنیتی" icon={<ShieldCheck size={11} />} value="CSP+HSTS" />
            <Mini label="JWT/RLS" icon={<KeyRound size={11} />} value="Supabase" />
            <Mini label="پساکوانتوم" icon={<KeyRound size={11} />} value={pq} />
            <Mini
              label="Honeypot"
              icon={<AlertOctagon size={11} />}
              value={`${L.honeypot?.hits ?? 0} تله`}
            />
            <Mini label="خودترمیمی" icon={<Activity size={11} />} value="watchdog" />
            <Mini label="رفتارشناسی" icon={<Activity size={11} />} value="آنومالی" />
            <Mini label="رمزنگاری" icon={<KeyRound size={11} />} value="TLS+at-rest" />
            <Mini label="RBAC/ممیزی" icon={<ShieldCheck size={11} />} value="zero-trust" />
          </div>

          <div
            style={{
              border: '1px solid var(--color-border)',
              borderRadius: 10,
              padding: '0.6rem 0.7rem',
              background: 'var(--color-bg)',
            }}
          >
            <div
              style={{
                fontSize: '0.78rem',
                fontWeight: 800,
                marginBottom: '0.4rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
              }}
            >
              <Globe size={13} /> بررسی ضد فیشینگ (دامنه)
            </div>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <input
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="مثلاً econojin-com.com"
                style={{
                  flex: 1,
                  padding: '0.35rem 0.55rem',
                  borderRadius: 8,
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-surface)',
                  color: 'var(--color-text)',
                  fontSize: '0.75rem',
                }}
              />
              <button
                onClick={() => void runCheck()}
                style={{
                  padding: '0.35rem 0.8rem',
                  borderRadius: 8,
                  border: 'none',
                  cursor: 'pointer',
                  background: 'var(--color-primary)',
                  color: '#fff',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                }}
              >
                <Search size={12} /> بررسی
              </button>
            </div>
            {check && (
              <p
                style={{
                  fontSize: '0.72rem',
                  margin: '0.45rem 0 0',
                  color:
                    check.verdict === 'suspicious'
                      ? '#b45309'
                      : check.verdict === 'error'
                        ? '#ef4444'
                        : 'var(--color-text-secondary)',
                }}
              >
                {check.verdict === 'suspicious' &&
                  '⚠️ دامنه شبیه‌سازی‌شده (سکوت‌سازی) تشخیص داده شد'}
                {check.verdict === 'ok' &&
                  'دامنه معتبر است · ایمیل: ' + (check.email_auth?.verdict ?? '—')}
                {check.verdict === 'error' && 'خطا در بررسی'}
              </p>
            )}
          </div>

          {L.post_quantum?.note && (
            <p
              style={{
                fontSize: '0.68rem',
                color: 'var(--color-text-secondary)',
                margin: '0.5rem 0 0',
              }}
            >
              {L.post_quantum.note}
            </p>
          )}
        </>
      )}
    </div>
  );
};

const Mini: React.FC<{ label: string; icon: React.ReactNode; value: string }> = ({
  label,
  icon,
  value,
}) => (
  <div
    style={{
      padding: '0.45rem 0.55rem',
      borderRadius: 10,
      border: '1px solid var(--color-border)',
      background: 'var(--color-bg)',
    }}
  >
    <div
      style={{
        fontSize: '0.62rem',
        color: 'var(--color-text-secondary)',
        display: 'flex',
        alignItems: 'center',
        gap: '0.25rem',
        marginBottom: '0.15rem',
      }}
    >
      {icon} {label}
    </div>
    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--color-text)' }}>{value}</div>
  </div>
);
