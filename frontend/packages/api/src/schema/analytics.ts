import { z } from 'zod';

export const DashboardKPISchema = z.object({
  id: z.string(),
  label: z.string(),
  value: z.number(),
  unit: z.string().optional(),
  delta_pct: z.number().optional(),
  trend: z.enum(['up', 'down', 'flat']).optional(),
  tone: z.enum(['success', 'warning', 'danger', 'info', 'neutral']).optional(),
});
export type DashboardKPI = z.infer<typeof DashboardKPISchema>;

export const DashboardAlertSchema = z.object({
  id: z.string(),
  severity: z.enum(['info', 'warning', 'critical']),
  title: z.string(),
  message: z.string(),
  raised_at: z.string(),
});
export type DashboardAlert = z.infer<typeof DashboardAlertSchema>;

export const DashboardSnapshotSchema = z.object({
  kpis: z.array(DashboardKPISchema),
  alerts: z.array(DashboardAlertSchema),
  generated_at: z.string(),
});
export type DashboardSnapshot = z.infer<typeof DashboardSnapshotSchema>;

export const DashboardKPI = DashboardKPISchema;
export const DashboardSnapshot = DashboardSnapshotSchema;