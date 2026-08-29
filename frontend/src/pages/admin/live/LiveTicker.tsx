import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import './LiveComponents.css';

interface TickerItem {
  id: string;
  type: 'income' | 'expense' | 'transfer';
  amount: number;
  description: string;
  user: string;
}

export default function LiveTicker() {
  const [items, setItems] = useState<TickerItem[]>([]);

  const templates = [
    { type: 'income', desc: 'Subscription Payment', user: 'farmer_123' },
    { type: 'income', desc: 'Marketplace Sale', user: 'buyer_456' },
    { type: 'expense', desc: 'Payout to Producer', user: 'producer_789' },
    { type: 'transfer', desc: 'EcoWallet Credit', user: 'user_321' },
    { type: 'income', desc: 'Tour Booking', user: 'visitor_654' },
    { type: 'income', desc: 'Carbon Credit Sale', user: 'company_xyz' },
  ];

  useEffect(() => {
    const addNewItem = () => {
      const template = templates[Math.floor(Math.random() * templates.length)];
      const newItem: TickerItem = {
        id: 'tick-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9),
        type: template.type as any,
        amount: Math.floor(Math.random() * 5000000) + 100000,
        description: template.desc,
        user: template.user,
      };
      setItems(prev => [newItem, ...prev].slice(0, 5));
    };

    addNewItem();
    const interval = setInterval(addNewItem, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="live-ticker-container">
      <div className="live-ticker-header">
        <span className="ticker-title">💰 Live Transactions</span>
        <span className="live-indicator">● LIVE</span>
      </div>
      <div className="live-ticker-track">
        <motion.div
          className="ticker-content"
          animate={{ x: ['0%', '-50%'] }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: 'linear',
          }}
        >
          {[...items, ...items].map((item, i) => (
            <div key={item.id + '-' + i} className="ticker-item">
              {item.type === 'income' ? (
                <ArrowUpRight size={14} style={{ color: 'var(--accent-primary)' }} />
              ) : (
                <ArrowDownRight size={14} style={{ color: 'var(--accent-danger)' }} />
              )}
              <span className="ticker-desc">{item.description}</span>
              <span className="ticker-amount" style={{
                color: item.type === 'income' ? 'var(--accent-primary)' : 'var(--accent-danger)'
              }}>
                {item.type === 'income' ? '+' : '-'}{item.amount.toLocaleString('fa-IR')} IRR
              </span>
              <span className="ticker-user">by {item.user}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
