import React, { Suspense, ComponentType } from 'react';
import { Spin } from 'antd';

interface LazyWrapperProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * LazyWrapper - Provides Suspense boundary with loading indicator
 * Usage: Wrap lazy-loaded components with this for consistent loading UX
 */
export const LazyWrapper: React.FC<LazyWrapperProps> = ({ 
  children, 
  fallback 
}) => {
  const defaultFallback = (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '200px' 
    }}>
      <Spin size="large" tip="Loading..." />
    </div>
  );

  return (
    <Suspense fallback={fallback || defaultFallback}>
      {children}
    </Suspense>
  );
};

/**
 * createLazyComponent - Factory for creating lazy-loaded components
 * Usage: const MyComponent = createLazyComponent(() => import('./MyComponent'));
 */
export function createLazyComponent<T extends ComponentType<any>>(
  importFn: () => Promise<{ default: T }>
) {
  const LazyComponent = React.lazy(importFn);
  
  const WrappedComponent: React.FC<React.ComponentProps<T>> = (props) => (
    <LazyWrapper>
      <LazyComponent {...props} />
    </LazyWrapper>
  );
  
  WrappedComponent.displayName = `Lazy(${LazyComponent.displayName || 'Component'})`;
  
  return WrappedComponent;
}

export default LazyWrapper;
