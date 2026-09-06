import { Link } from '@tanstack/react-router';
import { useState } from 'react';

type NavItem = {
  path: '/';
  label: string;
  labelFa: string;
  icon: string;
};

const NAV_ITEMS: readonly NavItem[] = [
  { path: '/', label: 'Overview', labelFa: 'نمای کلی', icon: '📊' },
] as const;

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <aside
      className={`${collapsed ? 'w-16' : 'w-64'} flex shrink-0 flex-col border-e border-ink/5 bg-surface-inverse text-white transition-all`}
    >
      <div className="flex items-center justify-between border-b border-white/10 p-4">
        {!collapsed && (
          <div>
            <h1 className="text-xl font-bold">🎯 HyDroMa</h1>
            <p className="text-xs text-white/60">Scientific Dashboard</p>
          </div>
        )}
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className="text-white/60 hover:text-white"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className="flex items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-white/5"
            activeProps={{ className: 'bg-brand-600 text-white' }}
            activeOptions={{ exact: item.path === '/' }}
          >
            <span className="text-xl">{item.icon}</span>
            {!collapsed && (
              <span className="flex flex-col leading-tight">
                <span>{item.label}</span>
                <span className="text-xs text-white/60">{item.labelFa}</span>
              </span>
            )}
          </Link>
        ))}
      </nav>

      {!collapsed && (
        <div className="border-t border-white/10 p-4 text-xs text-white/50">
          v2.0.0 | Phase 2
        </div>
      )}
    </aside>
  );
}