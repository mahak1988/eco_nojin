'use client';
import { motion } from 'framer-motion';
import { Loader2, AlertCircle, CheckCircle2, Info } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';

export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  const { colors } = useTheme();
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '20px', background: `${colors.accent}10`,
        border: `1px solid ${colors.accent}30`,
        borderRadius: '12px', margin: '16px 0',
      }}
    >
      <Loader2 size={20} color={colors.accent} className="animate-spin" />
      <span style={{ color: colors.text }}>{message}</span>
    </motion.div>
  );
}

export function ErrorState({ message }: { message: string }) {
  const { colors } = useTheme();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex', alignItems: 'flex-start', gap: '12px',
        padding: '16px 20px', background: `${colors.danger}10`,
        border: `1px solid ${colors.danger}30`,
        borderRadius: '12px', margin: '16px 0',
      }}
    >
      <AlertCircle size={20} color={colors.danger} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div>
        <div style={{ fontWeight: '600', color: colors.danger, marginBottom: '4px' }}>Error</div>
        <div style={{ color: colors.text, fontSize: '0.875rem' }}>{message}</div>
      </div>
    </motion.div>
  );
}

export function SuccessState({ message }: { message: string }) {
  const { colors } = useTheme();
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex', alignItems: 'center', gap: '12px',
        padding: '16px 20px', background: `${colors.success}10`,
        border: `1px solid ${colors.success}30`,
        borderRadius: '12px', margin: '16px 0',
      }}
    >
      <CheckCircle2 size={20} color={colors.success} />
      <span style={{ color: colors.text }}>{message}</span>
    </motion.div>
  );
}

export function InfoState({ message }: { message: string }) {
  const { colors } = useTheme();
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '12px',
      padding: '16px 20px', background: `${colors.info}10`,
      border: `1px solid ${colors.info}30`,
      borderRadius: '12px', margin: '16px 0',
    }}>
      <Info size={20} color={colors.info} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div style={{ color: colors.text, fontSize: '0.9rem', lineHeight: 1.6 }}>{message}</div>
    </div>
  );
}
