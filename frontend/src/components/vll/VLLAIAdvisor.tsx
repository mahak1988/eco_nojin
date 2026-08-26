import React from 'react';
import { motion } from 'framer-motion';
import { Zap, CheckCircle, AlertCircle, Info, Sparkles } from 'lucide-react';
import { Card, Button } from '../ui';

interface VLLAIAdvisorProps {
  recommendations: any[];
  onApply: (action: string) => void;
}

export const VLLAIAdvisor: React.FC<VLLAIAdvisorProps> = ({ recommendations, onApply }) => {
  const priorityIcon = (p: string) => {
    switch (p) {
      case 'high': return <AlertCircle size={16} color="#ef4444" />;
      case 'medium': return <Info size={16} color="#f59e0b" />;
      default: return <CheckCircle size={16} color="#10b981" />;
    }
  };

  return (
    <Card title="🤖 دستیار AI" icon={<Sparkles size={18} />} className="mb-4">
      <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginBottom: '1rem' }}>
        پیشنهادات هوشمند بر اساس نتایج شبیه‌سازی
      </p>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {recommendations.map((rec, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            style={{
              padding: '0.75rem',
              background: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              borderRight: `4px solid ${rec.priority === 'high' ? '#ef4444' : rec.priority === 'medium' ? '#f59e0b' : '#10b981'}`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              {priorityIcon(rec.priority)}
              <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>{rec.category}</span>
            </div>
            <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{rec.title}</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: '0 0 0.5rem 0' }}>
              {rec.description}
            </p>
            {rec.action && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onApply(rec.action)}
                style={{ fontSize: '0.75rem', padding: '0.25rem 0.75rem' }}
              >
                <Zap size={12} /> اعمال پیشنهاد
              </Button>
            )}
          </motion.div>
        ))}
      </div>
    </Card>
  );
};
