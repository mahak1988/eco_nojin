"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { api } from './api-client';
import { useAuth } from './auth-context';

export interface Farm {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  elevation_m?: number;
  area_hectares: number;
  soil_type?: string;
  climate_zone?: string;
}

interface FarmContextType {
  farms: Farm[];
  selectedFarm: Farm | null;
  loading: boolean;
  selectFarm: (farm: Farm | null) => void;
  refreshFarms: () => Promise<void>;
  createFarm: (data: Omit<Farm, 'id'>) => Promise<{ success: boolean; farm?: Farm; error?: string }>;
}

const FarmContext = createContext<FarmContextType | undefined>(undefined);

export function FarmProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [farms, setFarms] = useState<Farm[]>([]);
  const [selectedFarm, setSelectedFarm] = useState<Farm | null>(null);
  const [loading, setLoading] = useState(false);

  const refreshFarms = async () => {
    if (!isAuthenticated) {
      setFarms([]);
      setSelectedFarm(null);
      return;
    }
    setLoading(true);
    const res = await api.get<Farm[]>('/api/v1/farms/');
    if (res.success && res.data) {
      setFarms(res.data);
      const savedId = localStorage.getItem('selected_farm_id');
      if (savedId) {
        const saved = res.data.find(f => f.id === parseInt(savedId));
        if (saved) setSelectedFarm(saved);
        else if (res.data.length > 0) setSelectedFarm(res.data[0]);
      } else if (res.data.length > 0) {
        setSelectedFarm(res.data[0]);
      }
    }
    setLoading(false);
  };

  useEffect(() => { refreshFarms(); }, [isAuthenticated]);

  const selectFarm = (farm: Farm | null) => {
    setSelectedFarm(farm);
    if (farm) localStorage.setItem('selected_farm_id', String(farm.id));
    else localStorage.removeItem('selected_farm_id');
  };

  const createFarm = async (data: Omit<Farm, 'id'>) => {
    const res = await api.post<Farm>('/api/v1/farms/', data);
    if (res.success && res.data) {
      await refreshFarms();
      setSelectedFarm(res.data);
      return { success: true, farm: res.data };
    }
    return { success: false, error: res.error };
  };

  return (
    <FarmContext.Provider value={{ farms, selectedFarm, loading, selectFarm, refreshFarms, createFarm }}>
      {children}
    </FarmContext.Provider>
  );
}

export function useFarm() {
  const ctx = useContext(FarmContext);
  if (!ctx) throw new Error('useFarm must be used within FarmProvider');
  return ctx;
}
