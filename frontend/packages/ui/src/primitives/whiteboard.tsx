import { useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';
import { Button } from '../primitives';
import { Pen, Eraser, Undo, Redo, Trash2 } from '../primitives/icon';

export type WhiteboardProps = {
  className?: string;
  width?: number;
  height?: number;
  onSave?: (dataUrl: string) => void;
  onClear?: () => void;
};

export type Tool = 'pen' | 'eraser';

export function Whiteboard({ className, width = 800, height = 600, onSave, onClear }: WhiteboardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [tool, setTool] = useState<Tool>('pen');
  const [penColor, setPenColor] = useState('#16a34a');
  const [penWidth, setPenWidth] = useState(2);
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [isDrawing, setIsDrawing] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);
    saveHistory();
  }, []);

  const saveHistory = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const imageData = ctx.getImageData(0, 0, width, height);
    setHistory((prev) => {
      const newHistory = prev.slice(0, historyIndex + 1);
      return [...newHistory, imageData];
    });
    setHistoryIndex((prev) => prev + 1);
  };

  const getCoordinates = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    if ('touches' in e) {
      const touch = e.touches[0];
      if (!touch) return { x: 0, y: 0 };
      return {
        x: (touch.clientX - rect.left) * scaleX,
        y: (touch.clientY - rect.top) * scaleY,
      };
    }

    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    e.preventDefault();

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.lineTo(x, y);
    ctx.strokeStyle = tool === 'eraser' ? '#ffffff' : penColor;
    ctx.lineWidth = tool === 'eraser' ? penWidth * 5 : penWidth;
    ctx.stroke();
  };

  const stopDrawing = () => {
    if (isDrawing) {
      setIsDrawing(false);
      saveHistory();
    }
  };

  const undo = () => {
    if (historyIndex > 0) {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      const prevState = history[historyIndex - 1];
      if (canvas && ctx && prevState) {
        ctx.putImageData(prevState, 0, 0);
        setHistoryIndex((prev) => prev - 1);
      }
    }
  };

  const redo = () => {
    if (historyIndex < history.length - 1) {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      const nextState = history[historyIndex + 1];
      if (canvas && ctx && nextState) {
        ctx.putImageData(nextState, 0, 0);
        setHistoryIndex((prev) => prev + 1);
      }
    }
  };

  const clear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);
    saveHistory();
    onClear?.();
  };

  const save = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dataUrl = canvas.toDataURL('image/png');
    onSave?.(dataUrl);
  };

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <div className="flex items-center gap-2 rounded-lg border border-ink/10 bg-surface-raised p-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setTool('pen')}
          className={cn(tool === 'pen' && 'bg-surface-muted text-brand-700')}
        >
          <Pen size={16} />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setTool('eraser')}
          className={cn(tool === 'eraser' && 'bg-surface-muted text-brand-700')}
        >
          <Eraser size={16} />
        </Button>
        <div className="h-4 w-px bg-ink/10" />
        <Button variant="ghost" size="sm" onClick={undo} disabled={historyIndex <= 0}>
          <Undo size={16} />
        </Button>
        <Button variant="ghost" size="sm" onClick={redo} disabled={historyIndex >= history.length - 1}>
          <Redo size={16} />
        </Button>
        <div className="h-4 w-px bg-ink/10" />
        <input
          type="color"
          value={penColor}
          onChange={(e) => setPenColor(e.target.value)}
          disabled={tool === 'eraser'}
          className="h-6 w-8 cursor-pointer rounded border border-ink/10 disabled:opacity-50"
        />
        <input
          type="range"
          min="1"
          max="20"
          value={penWidth}
          onChange={(e) => setPenWidth(parseInt(e.target.value))}
          className="h-1 w-20"
        />
        <div className="ms-auto flex gap-2">
          <Button variant="ghost" size="sm" onClick={clear}>
            <Trash2 size={16} />
          </Button>
          <Button size="sm" onClick={save}>ذخیره</Button>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="w-full rounded-lg border border-ink/10 bg-white cursor-crosshair touch-none"
        onMouseDown={startDrawing}
        onMouseMove={draw}
        onMouseUp={stopDrawing}
        onMouseLeave={stopDrawing}
        onTouchStart={startDrawing}
        onTouchMove={draw}
        onTouchEnd={stopDrawing}
      />
    </div>
  );
}
