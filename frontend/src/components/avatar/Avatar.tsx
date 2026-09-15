/** Avatar component with upload, interactive crop, and preview — vanilla Canvas crop. */

import { useRef, useState } from 'react';

interface AvatarProps {
  src?: string;
  alt?: string;
  size?: number;
  onUpload?: (dataUrl: string) => void;
  editable?: boolean;
}

export default function Avatar({ src, alt = 'Avatar', size = 96, onUpload, editable = false }: AvatarProps) {
  const [preview, setPreview] = useState<string | undefined>(src);
  const [isHovering, setIsHovering] = useState(false);
  const [isCropping, setIsCropping] = useState(false);
  const [cropSrc, setCropSrc] = useState<string | undefined>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const [cropState, setCropState] = useState({
    scale: 1,
    offsetX: 0,
    offsetY: 0,
    isDragging: false,
    dragStart: { x: 0, y: 0 },
  });

  const [imgNatural, setImgNatural] = useState<{ w: number; h: number }>({ w: 0, h: 0 });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => {
        setImgNatural({ w: img.width, h: img.height });
        setCropState({
          scale: Math.max(size / Math.min(img.width, img.height), 1),
          offsetX: 0,
          offsetY: 0,
          isDragging: false,
          dragStart: { x: 0, y: 0 },
        });
        setCropSrc(reader.result as string);
        setIsCropping(true);
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  };

  const computeDisplayDims = (): { w: number; h: number } => {
    const { w, h } = imgNatural;
    if (!w || !h) return { w: size, h: size };
    const ratio = Math.min(size / w, size / h);
    return { w: w * ratio, h: h * ratio };
  };

  const applyCrop = () => {
    if (!cropSrc || !canvasRef.current) return;

    const img = new Image();
    img.onload = () => {
      const canvas = canvasRef.current!;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      canvas.width = size;
      canvas.height = size;

      const cropScale = cropState.scale;
      const offsetX = cropState.offsetX;
      const offsetY = cropState.offsetY;

      const actualScale = (img.width * cropScale) / size;
      const cropW = size * actualScale;
      const cropH = size * actualScale;

      ctx.save();
      ctx.beginPath();
      ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
      ctx.closePath();
      ctx.clip();

      ctx.drawImage(
        img,
        offsetX,
        offsetY,
        cropW,
        cropH,
        0,
        0,
        size,
        size,
      );
      ctx.restore();

      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      setPreview(dataUrl);
      onUpload?.(dataUrl);
      setIsCropping(false);
      setCropSrc(undefined);
    };
    img.src = cropSrc;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!editable || !cropSrc) return;
    const rect = e.currentTarget.getBoundingClientRect();
    setCropState((prev) => ({
      ...prev,
      isDragging: true,
      dragStart: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    }));
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cropState.isDragging || !cropSrc) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const dx = e.clientX - rect.left - cropState.dragStart.x;
    const dy = e.clientY - rect.top - cropState.dragStart.y;
    setCropState((prev) => ({
      ...prev,
      offsetX: prev.offsetX + dx,
      offsetY: prev.offsetY + dy,
      dragStart: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    }));
  };

  const handleMouseUp = () => {
    setCropState((prev) => ({ ...prev, isDragging: false }));
  };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    if (!cropSrc) return;
    e.preventDefault();
    const delta = -e.deltaY * 0.001;
    setCropState((prev) => ({
      ...prev,
      scale: Math.min(Math.max(prev.scale + delta, 1), 5),
    }));
  };

  const handleClick = () => {
    if (editable && !isCropping) fileInputRef.current?.click();
  };

  const initials = alt
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const renderCropOverlay = () => {
    if (!cropSrc) return null;

    const disp = computeDisplayDims();

    return (
      <div className="flex flex-col items-center gap-2 rounded-2xl border border-[var(--color-sand-500)] bg-black/40 p-3">
        <div
          className="relative cursor-move rounded-lg border-2 border-white/30"
          style={{ width: disp.w, height: disp.h, overflow: 'hidden' }}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          <img
            ref={imgRef}
            src={cropSrc}
            alt="Crop preview"
            className="select-none"
            style={{
              width: disp.w,
              height: disp.h,
              objectFit: 'cover',
              transform: `scale(${cropState.scale}) translate(${cropState.offsetX / cropState.scale}px, ${cropState.offsetY / cropState.scale}px)`,
              transformOrigin: 'center',
            }}
            draggable={false}
          />
          {/* Circular crop mask overlay */}
          <div
            className="pointer-events-none absolute rounded-full"
            style={{
              top: '50%',
              left: '50%',
              width: size,
              height: size,
              marginTop: -size / 2,
              marginLeft: -size / 2,
              border: '2px dashed rgba(255,255,255,0.5)',
              boxShadow:
                'rgba(0,0,0,0.6) 0 0 0 9999px 0inset',
            }}
          />
        </div>
        <canvas ref={canvasRef} className="hidden" />
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-[11px] text-[var(--color-night-200)]">
            <span>Zoom:</span>
            <input
              type="range"
              min={1}
              max={5}
              step={0.1}
              value={cropState.scale}
              onChange={(e) => setCropState((prev) => ({ ...prev, scale: parseFloat(e.target.value) }))}
              className="w-24"
            />
            <span>{Math.round(cropState.scale * 100)}%</span>
          </div>
          <button
            type="button"
            onClick={applyCrop}
            className="rounded-full bg-[var(--color-leaf-500)] px-4 py-1.5 text-xs font-extrabold text-[var(--color-night-950)]"
          >
            Apply Crop
          </button>
          <button
            type="button"
            onClick={() => {
              setIsCropping(false);
              setCropSrc(undefined);
            }}
            className="rounded-full bg-[var(--color-sand-500)] px-4 py-1.5 text-xs font-extrabold text-[var(--color-night-200)]"
          >
            Cancel
          </button>
        </div>
        <p className="text-[10px] text-[var(--color-night-200)]">Drag to reposition. Scroll to zoom.</p>
      </div>
    );
  };

  return (
    <div className="relative inline-block" style={{ width: size, height: size }}>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        aria-label="Upload avatar"
      />

      {isCropping && cropSrc ? (
        renderCropOverlay()
      ) : (
        <div
          onClick={handleClick}
          onMouseEnter={() => editable && setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          className={`flex items-center justify-center overflow-hidden rounded-full border-2 ${
            editable ? 'cursor-pointer' : ''
          }`}
          style={{
            width: size,
            height: size,
            borderColor: editable ? 'rgba(34, 197, 94, 0.4)' : 'rgba(255,255,255,0.1)',
          }}
        >
          {preview ? (
            <img src={preview} alt={alt} loading="lazy" className="h-full w-full object-cover" />
          ) : (
            <span
              className="flex items-center justify-center bg-[var(--color-sand-500)] text-lg font-extrabold text-[var(--color-night-200)]"
              style={{ width: size, height: size }}
            >
              {initials}
            </span>
          )}

          {editable && isHovering && !isCropping && (
            <div
              className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 backdrop-blur-sm"
              style={{ width: size, height: size }}
            >
              <span className="text-xs font-extrabold text-white">Upload</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}