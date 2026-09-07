import { type ReactNode, createContext, useContext, useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';

type SharedElementContextValue = {
  register: (id: string, element: HTMLElement | null) => void;
  getElement: (id: string) => HTMLElement | null;
};

const SharedElementContext = createContext<SharedElementContextValue | null>(null);

export function useSharedElement(id: string) {
  const context = useContext(SharedElementContext);
  if (!context) throw new Error('useSharedElement must be used within SharedElementProvider');
  return context.getElement(id);
}

export type SharedElementTransitionProps = {
  children: ReactNode;
  className?: string;
};

export function SharedElementTransition({ children, className }: SharedElementTransitionProps) {
  const [elements, setElements] = useState<Map<string, HTMLElement>>(new Map());
  const containerRef = useRef<HTMLDivElement>(null);

  const register = (id: string, element: HTMLElement | null) => {
    setElements((prev) => {
      const next = new Map(prev);
      if (element) next.set(id, element);
      else next.delete(id);
      return next;
    });
  };

  const getElement = (id: string) => elements.get(id) ?? null;

  return (
    <SharedElementContext.Provider value={{ register, getElement }}>
      <div ref={containerRef} className={cn('relative', className)}>
        {children}
      </div>
    </SharedElementContext.Provider>
  );
}

export type SharedElementProps = {
  id: string;
  children: ReactNode;
  className?: string;
};

export function SharedElement({ id, children, className }: SharedElementProps) {
  const ref = useRef<HTMLDivElement>(null);
  const context = useContext(SharedElementContext);

  useEffect(() => {
    if (!context) return;
    context.register(id, ref.current);
  }, [id, context]);

  return (
    <div
      ref={ref}
      id={id}
      className={cn('transition-transform duration-300 ease-out-soft', className)}
    >
      {children}
    </div>
  );
}
