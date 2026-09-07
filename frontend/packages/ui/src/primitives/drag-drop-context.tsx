import { createContext, useContext, useState, type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type DragItem = {
  id: string;
  type?: string;
  data?: Record<string, unknown>;
};

export type DragState = {
  draggedItem: DragItem | null;
  draggedOverId: string | null;
};

type DragContextValue = {
  state: DragState;
  setDraggedItem: (item: DragItem | null) => void;
  setDraggedOverId: (id: string | null) => void;
};

const DragContext = createContext<DragContextValue | null>(null);

export function useDragContext() {
  const context = useContext(DragContext);
  if (!context) {
    throw new Error('useDragContext must be used within DragDropProvider');
  }
  return context;
}

export type DragDropProviderProps = {
  children: ReactNode;
  onDragEnd?: (result: { activeId: string; overId: string | null }) => void;
  className?: string;
};

export function DragDropProvider({ children, onDragEnd, className }: DragDropProviderProps) {
  const [state, setState] = useState<DragState>({
    draggedItem: null,
    draggedOverId: null,
  });

  const setDraggedItem = (item: DragItem | null) => {
    setState((prev) => ({ ...prev, draggedItem: item }));
  };

  const setDraggedOverId = (id: string | null) => {
    setState((prev) => ({ ...prev, draggedOverId: id }));
  };

  const handleDragEnd = (activeId: string, overId: string | null) => {
    setState({ draggedItem: null, draggedOverId: null });
    onDragEnd?.({ activeId, overId });
  };

  return (
    <DragContext.Provider value={{ state, setDraggedItem, setDraggedOverId }}>
      <div
        className={cn('relative', className)}
        onDragEnd={() => handleDragEnd(state.draggedItem?.id ?? '', state.draggedOverId)}
      >
        {children}
      </div>
    </DragContext.Provider>
  );
}
