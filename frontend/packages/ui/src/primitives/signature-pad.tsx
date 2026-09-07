import { useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';
import { Button } from '../primitives';

export type SignaturePadProps = {
  className?: string;
  width?: number;
  height?: number;
  penColor?: string;
  penWidth?: number;
  onSave?: (dataUrl: string) => void;
  onClear?: () => void;
};

export function SignaturePad({
  className,
  width = 500,
  height = 200,
  penColor = '#16a34a',
  penWidth = 2,
  onSave,
  onClear,
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isEmpty, setIsEmpty] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.strokeStyle = penColor;
    ctx.lineWidth = penWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, [penColor, penWidth]);

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
    setIsEmpty(false);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    e.preventDefault();

    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    const { x, y } = getCoordinates(e);
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setIsEmpty(true);
    onClear?.();
  };

  const save = () => {
    const canvas = canvasRef.current;
    if (!canvas || isEmpty) return;

    const dataUrl = canvas.toDataURL('image/png');
    onSave?.(dataUrl);
  };

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="rounded-lg border border-ink/10 bg-surface-raised cursor-crosshair touch-none"
        onMouseDown={startDrawing}
        onMouseMove={draw}
        onMouseUp={stopDrawing}
        onMouseLeave={stopDrawing}
        onTouchStart={startDrawing}
        onTouchMove={draw}
        onTouchEnd={stopDrawing}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <label className="text-xs text-ink-muted">رنگ:</label>
          <input
            type="color"
            value={penColor}
            onChange={(e) => {
              const canvas = canvasRef.current;
              const ctx = canvas?.getContext('2d');
              if (ctx) ctx.strokeStyle = e.target.value;
            }}
            className="h-6 w-8 cursor-pointer rounded border border-ink/10"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-ink-muted">ضخامت:</label>
          <input
            type="range"
            min="1"
            max="10"
            value={penWidth}
            onChange={(e) => {
              const canvas = canvasRef.current;
              const ctx = canvas?.getContext('2d');
              const width = parseInt(e.target.value);
              if (ctx) ctx.lineWidth = width;
            }}
            className="h-1 w-20"
          />
        </div>
      </div>

      <div className="flex gap-2">
        <Button variant="secondary" onClick={clear} disabled={isEmpty}>
          پاک کردن
        </Button>
        <Button onClick={save} disabled={isEmpty}>
          ذخیره
        </Button>
      </div>
    </div>
  );
}
