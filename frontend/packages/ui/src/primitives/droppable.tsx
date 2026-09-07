import { type ReactNode, useId } from 'react';
import { cn } from '@eco/utils';
import { useDragContext } from './drag-drop-context';

export type DroppableProps = {
  id: string;
  children: ReactNode;
  className?: string;
  disabled?: boolean;
};

export function Droppable({ id, children, className, disabled = false }: DroppableProps) {
  const generatedId = useId();
  const { state, setDraggedOverId } = useDragContext();
  const dropId = id || generatedId;

  const handleDragOver = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDraggedOverId(dropId);
  };

  const handleDragEnter = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    setDraggedOverId(dropId);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (disabled) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    if (x < 0 || x > rect.width || y < 0 || y > rect.height) {
      setDraggedOverId(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    if (disabled) return;
    e.preventDefault();
    setDraggedOverId(dropId);
  };

  const isOver = state.draggedOverId === dropId;

  return (
    <div
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'transition-colors',
        isOver && 'bg-surface-muted/50 ring-2 ring-brand-500 ring-inset',
        disabled && 'opacity-50',
        className,
      )}
    >
      {children}
    </div>
  );
}
