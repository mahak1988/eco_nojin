/**
 * Camera Hook with local storage
 *
 * Uses useEffect for initialization to avoid hydration mismatches.
 */
import { useState, useCallback, useRef, useEffect } from 'react';

interface CapturedPhoto {
  id: string;
  dataUrl: string;
  timestamp: number;
  filename: string;
  size: number;
  geoTag?: { lat: number; lon: number };
}

const LOCAL_PHOTOS_KEY = 'eco-nojin-photos';

export function useCamera() {
  const [photos, setPhotos] = useState<CapturedPhoto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [initialized, setInitialized] = useState(false);

  // Load saved photos ONLY after mount (avoid hydration mismatch)
  useEffect(() => {
    if (typeof localStorage === 'undefined') return;

    try {
      const saved = localStorage.getItem(LOCAL_PHOTOS_KEY);
      if (saved) {
        // Note: We store metadata only, not data URLs (to avoid quota issues)
        // For now, start with empty photos on reload
        setPhotos([]);
      }
    } catch {
      // Ignore
    }
    setInitialized(true);
  }, []);

  const savePhotos = useCallback((newPhotos: CapturedPhoto[]) => {
    setPhotos(newPhotos);
    // Don't persist data URLs to localStorage (quota issues)
    // In production, would use IndexedDB
  }, []);

  const captureFromInput = useCallback(async (
    file: File,
    geoTag?: { lat: number; lon: number }
  ): Promise<CapturedPhoto | null> => {
    try {
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });

      const photo: CapturedPhoto = {
        id: `photo_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
        dataUrl,
        timestamp: Date.now(),
        filename: file.name,
        size: file.size,
        geoTag,
      };

      const newPhotos = [...photos, photo];
      savePhotos(newPhotos);
      return photo;
    } catch (err) {
      setError('Failed to capture photo');
      return null;
    }
  }, [photos, savePhotos]);

  const deletePhoto = useCallback((id: string) => {
    const newPhotos = photos.filter((p) => p.id !== id);
    savePhotos(newPhotos);
  }, [photos, savePhotos]);

  const triggerFileInput = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, []);

  return {
    photos,
    error,
    fileInputRef,
    captureFromInput,
    deletePhoto,
    triggerFileInput,
    initialized,
  };
}
