import { type ReactNode, useId } from 'react';
import { cn } from '@eco/utils';
import { useDragContext } from './drag-drop-context';

export type DraggableProps = {
  id: string;
  children: ReactNode;
  className?: string;
  disabled?: boolean;
  data?: Record<string, unknown>;
};

export function Draggable({ id, children, className, disabled = false, data }: DraggableProps) {
  const generatedId = useId();
  const { setDraggedItem } = useDragContext();
  const dragId = id || generatedId;

  const handleDragStart = (e: React.DragEvent) => {
    if (disabled) {
      e.preventDefault();
      return;
    }
    setDraggedItem({ id: dragId, data });
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', dragId);
  };

  return (
    <div
      draggable={!disabled}
      onDragStart={handleDragStart}
      onDragEnd={() => setDraggedItem(null)}
      className={cn('touch-none', disabled && 'cursor-not-allowed', className)}
    >
      {children}
    </div>
  );
}
