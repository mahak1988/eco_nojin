import { useEffect, useRef, useState } from 'react';
import { cn } from '@eco/utils';
import { Button } from '../primitives';
import { UploadCloud } from '../primitives/icon';

export type QRScannerProps = {
  onScan?: (result: string) => void;
  onError?: (error: Error) => void;
  className?: string;
};

export function QRScanner({ onScan, onError, className }: QRScannerProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startScanning = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsScanning(true);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'خطا در دسترسی به دوربین';
      setError(errorMessage);
      onError?.(err instanceof Error ? err : new Error(errorMessage));
    }
  };

  const stopScanning = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsScanning(false);
  };

  useEffect(() => {
    return () => stopScanning();
  }, []);

  return (
    <div className={cn('flex flex-col items-center gap-4', className)}>
      {error && (
        <div className="text-sm text-danger">{error}</div>
      )}

      <div className="relative aspect-square w-full max-w-sm overflow-hidden rounded-lg border border-ink/10 bg-surface-muted">
        {isScanning ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full w-full flex-col items-center justify-center gap-3 p-4 text-center">
            <UploadCloud size={48} className="text-ink-subtle" />
            <p className="text-sm text-ink-muted">دوربین برای اسکن QR Code</p>
          </div>
        )}

        {isScanning && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="h-48 w-48 border-2 border-brand-600 rounded-lg" />
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {!isScanning ? (
          <Button onClick={startScanning} className="flex items-center gap-2">
            📷 شروع اسکن
          </Button>
        ) : (
          <Button variant="secondary" onClick={stopScanning}>
            توقف اسکن
          </Button>
        )}
      </div>

      <p className="text-xs text-ink-muted">
        QR Code را در محدوده کادر قرار دهید
      </p>
    </div>
  );
}
