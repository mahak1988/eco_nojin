import { createContext, useContext, useState, type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type ModalStackItem = {
  id: string;
  content: ReactNode;
  title?: string;
};

type ModalStackContextValue = {
  modals: ModalStackItem[];
  pushModal: (modal: ModalStackItem) => void;
  popModal: (id: string) => void;
};

const ModalStackContext = createContext<ModalStackContextValue | null>(null);

export function useModalStack() {
  const context = useContext(ModalStackContext);
  if (!context) {
    throw new Error('useModalStack must be used within ModalStackProvider');
  }
  return context;
}

export type ModalStackProviderProps = {
  children: ReactNode;
  className?: string;
};

export function ModalStackProvider({ children, className }: ModalStackProviderProps) {
  const [modals, setModals] = useState<ModalStackItem[]>([]);

  const pushModal = (modal: ModalStackItem) => {
    setModals((prev) => [...prev, modal]);
  };

  const popModal = (id: string) => {
    setModals((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <ModalStackContext.Provider value={{ modals, pushModal, popModal }}>
      <div className={cn('relative', className)}>
        {children}
      </div>
    </ModalStackContext.Provider>
  );
}

export type ModalStackItemProps = {
  modal: ModalStackItem;
  onClose?: () => void;
  className?: string;
};

export function ModalStackItem({ modal, onClose, className }: ModalStackItemProps) {
  const { popModal } = useModalStack();

  const handleClose = () => {
    popModal(modal.id);
    onClose?.();
  };

  return (
    <div
      className={cn(
        'fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-sm',
        className,
      )}
      onClick={handleClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-lg overflow-auto rounded-lg bg-surface-raised p-6 shadow-elevated"
        onClick={(e) => e.stopPropagation()}
      >
        {modal.title && (
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-ink">{modal.title}</h2>
            <button
              type="button"
              onClick={handleClose}
              className="rounded-md p-1 text-ink-muted hover:bg-surface-muted"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        )}
        <div className="text-sm text-ink">{modal.content}</div>
      </div>
    </div>
  );
}
