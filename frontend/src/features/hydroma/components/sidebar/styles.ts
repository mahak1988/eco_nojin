/**
 * Sidebar Shared Styles
 * ======================
 * Common style objects for sidebar components.
 *
 * @module features/hydroma/components/sidebar/styles
 */

import type { CSSProperties } from 'react';

export const sidebarStyles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    overflowY: 'auto',
    paddingRight: '4px',
  } as CSSProperties,

  section: {
    background: 'rgba(15, 23, 42, 0.9)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    padding: '12px',
    border: '1px solid rgba(255,255,255,0.1)',
  } as CSSProperties,

  sectionCyan: {
    background: 'rgba(6, 182, 212, 0.1)',
    backdropFilter: 'blur(10px)',
    borderRadius: '12px',
    padding: '12px',
    border: '1px solid rgba(6, 182, 212, 0.3)',
    marginBottom: '12px',
  } as CSSProperties,

  label: {
    fontSize: '12px',
    color: 'rgba(255,255,255,0.6)',
    marginBottom: '8px',
    fontWeight: 700,
    textTransform: 'uppercase',
  } as CSSProperties,

  labelInline: {
    fontSize: '11px',
    color: 'rgba(255,255,255,0.7)',
    display: 'block',
    marginBottom: '4px',
  } as CSSProperties,

  button: (active: boolean, activeColor = '#3b82f6') => ({
    padding: '8px 4px',
    borderRadius: '8px',
    background: active ? activeColor : 'rgba(255,255,255,0.05)',
    color: active ? 'white' : 'rgba(255,255,255,0.6)',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    fontSize: '11px',
    fontWeight: 600,
  } as CSSProperties),

  toolButton: (active: boolean, color: string) => ({
    padding: '10px 12px',
    borderRadius: '8px',
    background: active ? color : 'rgba(255,255,255,0.03)',
    color: active ? 'white' : 'rgba(255,255,255,0.7)',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  } as CSSProperties),

  opButton: (active: boolean) => ({
    padding: '8px 6px',
    borderRadius: '6px',
    background: active ? '#8b5cf6' : 'rgba(255,255,255,0.03)',
    color: active ? 'white' : 'rgba(255,255,255,0.7)',
    border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
    cursor: 'pointer',
    fontSize: '10px',
    fontWeight: 600,
  } as CSSProperties),

  grid4: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '6px',
  } as CSSProperties,

  grid2: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '6px',
  } as CSSProperties,

  column: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  } as CSSProperties,

  listItem: (color: string) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 8px',
    background: `${color}15`,
    borderRadius: '6px',
    marginBottom: '4px',
    fontSize: '11px',
    border: `1px solid ${color}40`,
  } as CSSProperties),

  deleteButton: {
    padding: '4px 6px',
    borderRadius: '4px',
    background: 'rgba(239, 68, 68, 0.3)',
    color: '#fca5a5',
    border: 'none',
    cursor: 'pointer',
  } as CSSProperties,

  alertBox: (color: string) => ({
    marginTop: '8px',
    padding: '8px',
    background: `${color}26`,
    borderRadius: '6px',
    fontSize: '11px',
    color,
  } as CSSProperties),
} as const;
