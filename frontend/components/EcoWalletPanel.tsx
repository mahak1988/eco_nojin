'use client';
import { useEffect, useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import ClientOnly from './ClientOnly';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function EcoWalletPanel() {
  const { t, locale } = useI18n();

  return (
    <div style={{
      marginTop: '32px', padding: '24px', border: '1px solid #ddd',
      borderRadius: '12px',
      background: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
    }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#065f46' }}>
        🌱 {t('ecowallet_title')}
      </h2>
      <p style={{ color: '#047857', marginBottom: '20px' }}>
        {t('ecowallet_subtitle')}
      </p>

      <ClientOnly fallback={
        <div style={{ padding: '16px', background: 'white', borderRadius: '6px', textAlign: 'center', color: '#6b7280' }}>
          Loading wallet...
        </div>
      }>
        <WalletContent locale={locale} t={t} />
      </ClientOnly>
    </div>
  );
}

function WalletContent({ locale, t }) {
  const [wallet, setWallet] = useState(null);
  const [earnings, setEarnings] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState('info'); // info, success, error

  const demoUserId = 'demo-farmer-001';

  useEffect(() => {
    initWallet();
    loadOptions();
  }, []);

  async function initWallet() {
    try {
      // Try to get existing wallet
      let response = await fetch(`${API_BASE}/api/v1/ecowallet/wallets/${demoUserId}`);
      if (!response.ok) {
        // Create if not exists
        await fetch(`${API_BASE}/api/v1/ecowallet/wallets`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({user_id: demoUserId}),
        });
        response = await fetch(`${API_BASE}/api/v1/ecowallet/wallets/${demoUserId}`);
      }
      const data = await response.json();
      setWallet(data);
      await loadTransactions();
    } catch (error) {
      console.error('Wallet init failed:', error);
    }
  }

  async function loadOptions() {
    try {
      const [e, r] = await Promise.all([
        fetch(`${API_BASE}/api/v1/ecowallet/earning/options`).then(r => r.json()),
        fetch(`${API_BASE}/api/v1/ecowallet/redemption/options`).then(r => r.json()),
      ]);
      setEarnings(e.options || []);
      setRedemptions(r.options || []);
    } catch (error) {
      console.error('Options load failed:', error);
    }
  }

  async function loadTransactions() {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ecowallet/wallets/${demoUserId}/transactions?limit=20`);
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error('Transactions load failed:', error);
    }
  }

  async function handleEarn(category) {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ecowallet/earn`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          user_id: demoUserId,
          category,
          quantity: 1.0,
          language: locale,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      setStatusMessage(data.message);
      setStatusType('success');
      await initWallet();
      setTimeout(() => setStatusMessage(''), 5000);
    } catch (error) {
      setStatusMessage(error.message);
      setStatusType('error');
    }
  }

  async function handleRedeem(category) {
    try {
      const response = await fetch(`${API_BASE}/api/v1/ecowallet/redeem`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          user_id: demoUserId,
          category,
          language: locale,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail);

      setStatusMessage(data.message);
      setStatusType('success');
      await initWallet();
      setTimeout(() => setStatusMessage(''), 5000);
    } catch (error) {
      setStatusMessage(error.message);
      setStatusType('error');
    }
  }

  if (!wallet) return <div>Loading...</div>;

  const irrValue = wallet.balance * 10000;
  const translationKey = (key) => {
    const mapping = {
      tree_planting: 'ecowallet_tree_planting',
      training_completion: 'ecowallet_training',
      market_sale: 'ecowallet_market_sale',
      carbon_verification: 'ecowallet_carbon',
      referral: 'ecowallet_referral',
      regenerative_farming: 'ecowallet_regenerative',
      soil_improvement: 'ecowallet_soil',
      water_conservation: 'ecowallet_water',
      seed_purchase: 'ecowallet_seeds',
      consultation: 'ecowallet_consultation',
      insurance_discount: 'ecowallet_insurance',
      market_access: 'ecowallet_market_access',
      training_course: 'ecowallet_training_course',
      equipment_rental: 'ecowallet_equipment',
      veterinary_service: 'ecowallet_veterinary',
    };
    return mapping[key] || key;
  };

  return (
    <>
      {/* Status Message */}
      {statusMessage && (
        <div style={{
          padding: '12px 16px',
          marginBottom: '16px',
          borderRadius: '6px',
          background: statusType === 'success' ? '#d1fae5' : statusType === 'error' ? '#fee2e2' : '#dbeafe',
          color: statusType === 'success' ? '#065f46' : statusType === 'error' ? '#991b1b' : '#1e40af',
          fontSize: '0.875rem',
          fontWeight: '500',
        }}>
          {statusType === 'success' ? '✅ ' : statusType === 'error' ? '⚠️ ' : 'ℹ️ '}
          {statusMessage}
        </div>
      )}

      {/* Balance Card */}
      <div style={{
        padding: '20px', background: 'white', borderRadius: '8px',
        marginBottom: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '4px' }}>
              {t('ecowallet_balance')}
            </div>
            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#065f46' }}>
              {wallet.balance.toFixed(1)} ECO
            </div>
            <div style={{ fontSize: '0.875rem', color: '#047857' }}>
              ≈ {irrValue.toLocaleString()} {locale === 'fa' ? 'تومان' : 'IRR'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '24px', fontSize: '0.875rem' }}>
            <div>
              <div style={{ color: '#6b7280' }}>{t('ecowallet_total_earned')}</div>
              <div style={{ fontWeight: '600', color: '#065f46', fontSize: '1.25rem' }}>
                {wallet.total_earned.toFixed(1)}
              </div>
            </div>
            <div>
              <div style={{ color: '#6b7280' }}>{t('ecowallet_total_used')}</div>
              <div style={{ fontWeight: '600', color: '#065f46', fontSize: '1.25rem' }}>
                {wallet.total_redeemed.toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {['overview', 'earn', 'redeem', 'history'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '8px 16px', borderRadius: '6px', border: 'none',
              background: activeTab === tab ? '#065f46' : '#e5e7eb',
              color: activeTab === tab ? 'white' : '#374151',
              cursor: 'pointer', fontSize: '0.875rem', fontWeight: '500',
            }}
          >
            {tab === 'overview' ? '📊' : tab === 'earn' ? '🌱 ' + t('ecowallet_earn') :
             tab === 'redeem' ? '🎁 ' + t('ecowallet_redeem') : '📜 ' + t('ecowallet_history')}
          </button>
        ))}
      </div>

      {/* Overview */}
      {activeTab === 'overview' && (
        <div style={{ padding: '16px', background: 'white', borderRadius: '8px' }}>
          <p style={{ color: '#047857', margin: '0 0 12px 0' }}>
            {t('ecowallet_welcome')}
          </p>
          {wallet.balance < 20 && (
            <p style={{ color: '#047857', margin: '0', fontStyle: 'italic' }}>
              💡 {t('ecowallet_low_balance')}
            </p>
          )}
        </div>
      )}

      {/* Earn Tab */}
      {activeTab === 'earn' && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
          gap: '12px',
        }}>
          {earnings.map(opt => (
            <div key={opt.category} style={{
              padding: '16px', background: 'white', borderRadius: '8px',
              border: '2px solid #d1fae5',
            }}>
              <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#065f46', marginBottom: '8px' }}>
                {t(translationKey(opt.category))}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '12px' }}>
                {opt.verification_required ? '✓ ' + (locale === 'fa' ? 'تأیید شده' : 'Verified') : ''}
              </div>
              <button
                onClick={() => handleEarn(opt.category)}
                style={{
                  width: '100%', padding: '8px', background: '#10b981',
                  color: 'white', border: 'none', borderRadius: '4px',
                  cursor: 'pointer', fontWeight: '500',
                }}
              >
                +{opt.eco_amount} ECO
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Redeem Tab */}
      {activeTab === 'redeem' && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
          gap: '12px',
        }}>
          {redemptions.map(opt => (
            <div key={opt.category} style={{
              padding: '16px', background: 'white', borderRadius: '8px',
              border: '2px solid #fde68a',
            }}>
              <div style={{ fontSize: '0.875rem', fontWeight: '600', color: '#92400e', marginBottom: '8px' }}>
                {t(translationKey(opt.category))}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '12px' }}>
                {opt.value_irr.toLocaleString()} {locale === 'fa' ? 'تومان' : 'IRR'}
              </div>
              <button
                onClick={() => handleRedeem(opt.category)}
                disabled={wallet.balance < opt.eco_cost}
                style={{
                  width: '100%', padding: '8px',
                  background: wallet.balance >= opt.eco_cost ? '#f59e0b' : '#d1d5db',
                  color: 'white', border: 'none', borderRadius: '4px',
                  cursor: wallet.balance >= opt.eco_cost ? 'pointer' : 'not-allowed',
                  fontWeight: '500',
                }}
              >
                {opt.eco_cost} ECO
              </button>
            </div>
          ))}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div style={{ padding: '16px', background: 'white', borderRadius: '8px' }}>
          {transactions.length === 0 ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '20px 0' }}>
              {t('ecowallet_no_transactions')}
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {transactions.slice().reverse().map(tx => (
                <div key={tx.transaction_id} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px', background: '#f9fafb', borderRadius: '6px',
                }}>
                  <div>
                    <div style={{ fontSize: '0.875rem', fontWeight: '500', color: '#374151' }}>
                      {t(translationKey(tx.category))}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                      {new Date(tx.timestamp).toLocaleString(locale === 'fa' ? 'fa-IR' : 'en-US')}
                    </div>
                  </div>
                  <div style={{
                    fontSize: '1rem', fontWeight: '600',
                    color: tx.type === 'earn' ? '#10b981' : '#f59e0b',
                  }}>
                    {tx.type === 'earn' ? '+' : '-'}{tx.amount.toFixed(1)} ECO
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
