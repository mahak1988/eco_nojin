import React, { useEffect, useState } from 'react';
import { Wallet, Coins, ArrowDownUp } from 'lucide-react';

/**
 * فاز تکمیلی — حسابداری/کیف پول توکن: آمار زنده + گزینه‌های کسب/بازخرید.
 */
export const AccountingCard: React.FC = () => {
  const [stats, setStats] = useState<{
    total_wallets?: number;
    total_tokens_issued?: number;
    total_transactions?: number;
  } | null>(null);
  const [earning, setEarning] = useState<{ options?: string[] } | null>(null);
  const [redeem, setRedeem] = useState<{ options?: string[] } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [s, e, r] = await Promise.all([
          fetch('/api/v1/ecowallet/stats').then((x) => x.json()),
          fetch('/api/v1/ecowallet/earning-options').then((x) => x.json()),
          fetch('/api/v1/ecowallet/redemption-options').then((x) => x.json()),
        ]);
        setStats(s);
        setEarning(e);
        setRedeem(r);
      } catch (ex) {
        setErr(ex instanceof Error ? ex.message : 'خطا');
      }
    })();
  }, []);

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.7rem' }}>
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
          <Wallet size={17} /> حسابداری و کیف پول توکن (ECO)
        </h3>
      </div>

      {err && <p style={{ fontSize: '0.76rem', color: '#ef4444' }}>⚠️ {err}</p>}

      {stats && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: '0.4rem',
            marginBottom: '0.6rem',
          }}
        >
          <div
            style={{
              padding: '0.5rem 0.6rem',
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
              }}
            >
              <Coins size={10} /> کیف پول‌ها
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800 }}>{stats.total_wallets ?? 0}</div>
          </div>
          <div
            style={{
              padding: '0.5rem 0.6rem',
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
              }}
            >
              <Coins size={10} /> توکن صادرشده
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800 }}>
              {stats.total_tokens_issued ?? 0}
            </div>
          </div>
          <div
            style={{
              padding: '0.5rem 0.6rem',
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
              }}
            >
              <ArrowDownUp size={10} /> تراکنش‌ها
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 800 }}>{stats.total_transactions ?? 0}</div>
          </div>
        </div>
      )}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.5rem',
        }}
      >
        <div
          style={{
            border: '1px solid var(--color-border)',
            borderRadius: 10,
            padding: '0.5rem 0.65rem',
            background: 'var(--color-bg)',
          }}
        >
          <div
            style={{
              fontSize: '0.7rem',
              fontWeight: 800,
              marginBottom: '0.3rem',
              color: '#0d9488',
            }}
          >
            گزینه‌های کسب توکن
          </div>
          {(earning?.options ?? []).map((o) => (
            <div
              key={o}
              style={{
                fontSize: '0.72rem',
                color: 'var(--color-text-secondary)',
                marginBottom: '0.15rem',
              }}
            >
              • {o}
            </div>
          ))}
          {earning && earning.options?.length === 0 && (
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              — هنوز تعریف نشده
            </div>
          )}
        </div>
        <div
          style={{
            border: '1px solid var(--color-border)',
            borderRadius: 10,
            padding: '0.5rem 0.65rem',
            background: 'var(--color-bg)',
          }}
        >
          <div
            style={{
              fontSize: '0.7rem',
              fontWeight: 800,
              marginBottom: '0.3rem',
              color: '#0d9488',
            }}
          >
            گزینه‌های بازخرید
          </div>
          {(redeem?.options ?? []).map((o) => (
            <div
              key={o}
              style={{
                fontSize: '0.72rem',
                color: 'var(--color-text-secondary)',
                marginBottom: '0.15rem',
              }}
            >
              • {o}
            </div>
          ))}
          {redeem && redeem.options?.length === 0 && (
            <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>
              — هنوز تعریف نشده
            </div>
          )}
        </div>
      </div>
      <p
        style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}
      >
        داده زنده از اکو‌ولت بک‌اند؛ تراکنش‌ها پس از فعالیت واقعی کاربران ثبت می‌شوند.
      </p>
    </div>
  );
};
