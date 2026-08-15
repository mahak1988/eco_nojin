"use client";
import { motion } from 'framer-motion';
import { CheckCircle2, Clock, AlertCircle, Award, TreePine } from 'lucide-react';
import { useTheme } from '../../lib/theme-context';

interface Project {
  project_id: string;
  name: string;
  project_type: string;
  area_hectares: number;
  status: string;
  credits_issued: number;
  registered_at: string;
}

const STATUS_CONFIG: Record<string, { icon: any; color: string; label: string }> = {
  registered: { icon: Clock, color: '#3b82f6', label: 'Registered' },
  monitoring: { icon: TreePine, color: '#f59e0b', label: 'Monitoring' },
  verified: { icon: CheckCircle2, color: '#10b981', label: 'Verified' },
  issued: { icon: Award, color: '#8b5cf6', label: 'Credits Issued' },
};

export default function ProjectTimeline({ projects }: { projects: Project[] }) {
  const { colors } = useTheme();

  if (projects.length === 0) {
    return (
      <div style={{
        padding: '40px', textAlign: 'center', color: colors.textMuted,
        background: colors.cardBg, borderRadius: '20px',
        border: `1px solid ${colors.border}`,
      }}>
        <TreePine size={48} style={{ marginBottom: '12px', opacity: 0.3 }} />
        <p>No carbon projects yet. Register your first project!</p>
      </div>
    );
  }

  return (
    <div style={{
      background: colors.cardBg, padding: '24px', borderRadius: '20px',
      border: `1px solid ${colors.border}`,
    }}>
      <h3 style={{ color: colors.text, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <TreePine size={20} color={colors.success} />
        Carbon Projects Timeline ({projects.length})
      </h3>

      <div style={{ position: 'relative', paddingLeft: '30px' }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: '10px', top: '0', bottom: '0',
          width: '2px',
          background: `linear-gradient(180deg, ${colors.primary}, ${colors.accent}, ${colors.success})`,
        }} />

        {projects.map((p, i) => {
          const config = STATUS_CONFIG[p.status] || STATUS_CONFIG.registered;
          const Icon = config.icon;

          return (
            <motion.div
              key={p.project_id || i}
              initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              style={{ marginBottom: '20px', position: 'relative' }}
            >
              {/* Dot on timeline */}
              <div style={{
                position: 'absolute', left: '-26px', top: '8px',
                width: '22px', height: '22px', borderRadius: '50%',
                background: config.color, display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: `0 0 0 4px ${colors.cardBg}, 0 0 0 6px ${config.color}40`,
              }}>
                <Icon size={12} color="white" />
              </div>

              <div style={{
                background: colors.bg, padding: '14px 16px',
                borderRadius: '12px', border: `1px solid ${colors.border}`,
                borderLeft: `4px solid ${config.color}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '8px' }}>
                  <h4 style={{ color: colors.text, margin: 0, fontSize: '1rem' }}>{p.name}</h4>
                  <span style={{
                    padding: '2px 10px', borderRadius: '100px',
                    background: `${config.color}20`, color: config.color,
                    fontSize: '0.7rem', fontWeight: '700',
                  }}>
                    {config.label}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: colors.textMuted, marginBottom: '6px', textTransform: 'capitalize' }}>
                  {p.project_type.replace('_', ' ')} â€¢ {p.area_hectares} ha
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                  <span style={{ color: colors.textMuted }}>
                    ًں“… {new Date(p.registered_at).toLocaleDateString()}
                  </span>
                  <span style={{ color: colors.success, fontWeight: '700' }}>
                    ًںŒ± {p.credits_issued.toFixed(1)} credits
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
