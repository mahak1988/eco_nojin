import React from 'react';

interface LoadingSpinnerProps {
  fullScreen?: boolean;
  size?: number;
  label?: string;
}

/**
 * اسپینر بارگذاری — استفاده به‌عنوان fallback برای Suspense (code-splitting) و حالت‌های async.
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ fullScreen = false, size = 40, label }) => {
  const spinner = (
    <div
      role="status"
      aria-label={label ?? 'در حال بارگذاری'}
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.75rem',
        color: 'var(--color-text-secondary)',
        fontSize: '0.9rem',
      }}
    >
      <span
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          border: `3px solid var(--color-border)`,
          borderTopColor: 'var(--color-primary)',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      {label && <span>{label}</span>}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );

  if (!fullScreen) return spinner;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-bg)',
      }}
    >
      {spinner}
    </div>
  );
};

export default LoadingSpinner;
