'use client';
import { useEffect, useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import ClientOnly from './ClientOnly';

export default function MobileFeaturesPanel() {
  const { t } = useI18n();

  return (
    <section
      aria-labelledby="mobile-features-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#fee2e2',
      }}
    >
      <h2 id="mobile-features-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#991b1b' }}>
        📱 Mobile Features
      </h2>

      <ClientOnly fallback={
        <div style={{ padding: '16px', background: 'white', borderRadius: '6px', textAlign: 'center', color: '#6b7280' }}>
          Loading mobile features...
        </div>
      }>
        <MobileFeaturesContent />
      </ClientOnly>
    </section>
  );
}

function MobileFeaturesContent() {
  const { t } = useI18n();
  const [isOnline, setIsOnline] = useState(true);
  const [swRegistered, setSwRegistered] = useState(false);
  const [queueSize] = useState(0);
  const [syncResult, setSyncResult] = useState<{ synced: number; failed: number } | null>(null);
  const [position, setPosition] = useState<{ lat: number; lon: number; accuracy: number } | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [photos, setPhotos] = useState<Array<{ id: string; dataUrl: string; filename: string }>>([]);
  const [secureContextWarning, setSecureContextWarning] = useState(false);

  useEffect(() => {
    if (typeof navigator === 'undefined') return;
    setIsOnline(navigator.onLine);

    // Check if we're in a secure context (required for Geolocation API)
    const isSecureContext = window.isSecureContext;
    if (!isSecureContext) {
      setSecureContextWarning(true);
    }

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
    navigator.serviceWorker.register('/sw.js').then(
      () => setSwRegistered(true),
      (err) => console.warn('[SW] Registration failed:', err)
    );
  }, []);

  const getCurrentPosition = async () => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setGeoError('Geolocation is not supported by this browser.');
      return;
    }

    // Pre-check: secure context required
    if (typeof window !== 'undefined' && !window.isSecureContext) {
      setGeoError(
        '⚠️ Location access requires a secure context.\n\n' +
        'Please open http://localhost:3000 instead of using the network IP.\n' +
        'Browsers only allow geolocation on HTTPS or localhost.'
      );
      return;
    }

    setGeoLoading(true);
    setGeoError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPosition({
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
        setGeoLoading(false);
      },
      (err) => {
        // User-friendly error messages
        let friendlyMessage = err.message;

        if (err.message.includes('secure origin') || err.message.includes('Secure context')) {
          friendlyMessage =
            '🔒 Location requires secure context (HTTPS or localhost).\n\n' +
            '→ Please open: http://localhost:3000\n' +
            '→ Do NOT use the IP address (192.168.x.x)';
        } else if (err.code === 1) {
          friendlyMessage = '❌ Location permission denied. Please enable location access in your browser settings.';
        } else if (err.code === 2) {
          friendlyMessage = '📡 Location unavailable. Check your GPS/network connection.';
        } else if (err.code === 3) {
          friendlyMessage = '⏱️ Location request timed out. Please try again.';
        }

        setGeoError(friendlyMessage);
        setGeoLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const dataUrl = await new Promise<string>((resolve) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.readAsDataURL(file);
    });

    setPhotos((prev) => [
      ...prev,
      { id: `photo_${Date.now()}`, dataUrl, filename: file.name },
    ]);
    if (e.target) e.target.value = '';
  };

  const deletePhoto = (id: string) => setPhotos((prev) => prev.filter((p) => p.id !== id));

  return (
    <>
      {/* Secure Context Warning */}
      {secureContextWarning && (
        <div
          role="alert"
          style={{
            padding: '12px',
            background: '#fef3c7',
            border: '2px solid #f59e0b',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '0.875rem',
          }}
        >
          <strong>⚠️ Non-Secure Context Detected</strong>
          <p style={{ margin: '4px 0 0 0' }}>
            Geolocation and some mobile features require <code>localhost</code> or HTTPS.
            Please use <a href="http://localhost:3000" style={{ color: '#0c4a6e' }}>http://localhost:3000</a> instead of the network IP.
          </p>
        </div>
      )}

      {/* Online Status Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '12px',
        marginBottom: '16px',
      }}>
        <div style={{
          padding: '12px',
          background: isOnline ? '#dcfce7' : '#fef2f2',
          borderRadius: '6px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '1.5rem' }} aria-hidden="true">{isOnline ? '🟢' : '🔴'}</div>
          <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>
            {isOnline ? 'Online' : 'Offline'}
          </div>
        </div>

        <div style={{
          padding: '12px',
          background: swRegistered ? '#dcfce7' : '#fef3c7',
          borderRadius: '6px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '1.5rem' }} aria-hidden="true">{swRegistered ? '✅' : '⏳'}</div>
          <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>
            Service Worker
          </div>
        </div>

        <div style={{
          padding: '12px',
          background: queueSize > 0 ? '#fef3c7' : '#f3f4f6',
          borderRadius: '6px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{queueSize}</div>
          <div style={{ fontSize: '0.875rem', fontWeight: '600' }}>
            Pending Sync
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <button
          onClick={getCurrentPosition}
          disabled={geoLoading}
          aria-busy={geoLoading}
          style={{
            padding: '10px 20px',
            background: '#991b1b',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
          }}
        >
          📍 {geoLoading ? 'Locating...' : 'Get Location'}
        </button>

        <label style={{
          padding: '10px 20px',
          background: '#0c4a6e',
          color: 'white',
          borderRadius: '6px',
          cursor: 'pointer',
          display: 'inline-block',
        }}>
          📷 Take Photo
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
        </label>

        <button
          onClick={() => {
            setSyncResult({ synced: 0, failed: 0 });
            setTimeout(() => setSyncResult(null), 3000);
          }}
          disabled={!isOnline || queueSize === 0}
          style={{
            padding: '10px 20px',
            background: (!isOnline || queueSize === 0) ? '#9ca3af' : '#15803d',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: (!isOnline || queueSize === 0) ? 'not-allowed' : 'pointer',
          }}
        >
          🔄 Sync Now
        </button>
      </div>

      {syncResult && (
        <div
          aria-live="polite"
          style={{
            padding: '8px 12px',
            background: '#ecfdf5',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '0.875rem',
          }}
        >
          ✅ Synced: {syncResult.synced} | ❌ Failed: {syncResult.failed}
        </div>
      )}

      {position && (
        <div
          aria-live="polite"
          style={{
            padding: '12px',
            background: 'white',
            borderRadius: '6px',
            marginBottom: '16px',
          }}
        >
          <strong>📍 Current Location:</strong>
          <div style={{ fontSize: '0.875rem', color: '#4b5563', marginTop: '4px' }}>
            Lat: {position.lat.toFixed(6)}° | Lon: {position.lon.toFixed(6)}°
            <br />
            Accuracy: ±{position.accuracy.toFixed(0)}m
          </div>
        </div>
      )}

      {geoError && (
        <div
          role="alert"
          style={{
            padding: '12px',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            marginBottom: '16px',
            color: '#991b1b',
            fontSize: '0.875rem',
            whiteSpace: 'pre-wrap',
          }}
        >
          <strong>Geolocation Notice:</strong>
          <div style={{ marginTop: '4px' }}>{geoError}</div>
        </div>
      )}

      {photos.length > 0 && (
        <div>
          <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '8px' }}>
            📸 Captured Photos ({photos.length})
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
            gap: '8px',
          }}>
            {photos.map((photo) => (
              <div key={photo.id} style={{ position: 'relative' }}>
                <img
                  src={photo.dataUrl}
                  alt={photo.filename}
                  style={{
                    width: '100%',
                    height: '100px',
                    objectFit: 'cover',
                    borderRadius: '6px',
                  }}
                />
                <button
                  onClick={() => deletePhoto(photo.id)}
                  aria-label={t('delete_photo')}
                  title={t('delete_photo')}
                  style={{
                    position: 'absolute',
                    top: '4px',
                    insetInlineEnd: '4px',
                    background: '#dc2626',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: '24px',
                    height: '24px',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    lineHeight: '24px',
                    textAlign: 'center',
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
