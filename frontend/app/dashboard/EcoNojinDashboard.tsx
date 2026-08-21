'use client';

import { useState, useEffect } from 'react';
import { useI18n } from '../../lib/i18n-context';
import { useTheme } from '../../lib/theme-context';
import { api } from '../../lib/api-client';
import { motion } from 'framer-motion';
import { 
  Leaf, 
  Satellite, 
  Bot, 
  TrendingUp, 
  ShoppingCart,
  TreePine, 
  Droplet, 
  Mic, 
  Wallet, 
  Sparkles, 
  Users,
  Globe2, 
  ArrowRight, 
  Heart,
  Shield, 
  Zap, 
  Award, 
  TrendingDown,
  BarChart3,
  MapPin,
  Calendar
} from 'lucide-react';

// Define TypeScript interfaces matching the backend models
interface FarmData {
  id: string;
  name: string;
  location: string;
  size: number; // hectares
  cropType: string;
  lastUpdate: string;
}

interface WeatherData {
  temperature: number;
  humidity: number;
  precipitation: number;
  condition: string;
}

interface SatelliteData {
  ndvi: number;
  evi: number;
  soilMoisture: number;
  imageDate: string;
}

interface PredictionData {
  yieldPrediction: number;
  riskLevel: 'low' | 'medium' | 'high';
  recommendations: string[];
}

interface DashboardData {
  farm: FarmData;
  weather: WeatherData;
  satellite: SatelliteData;
  predictions: PredictionData;
}

const EcoNojinDashboard = () => {
  const { t } = useI18n();
  const { colors } = useTheme();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get<DashboardData>('/dashboard/data');
      if (response.success) {
        setDashboardData(response.data!);
      } else {
        setError(response.error || 'Failed to fetch data');
      }
    } catch (err) {
      setError('An error occurred while fetching data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: colors.bg 
      }}>
        <div style={{ fontSize: '1.5rem', color: colors.text }}>
          Loading Eco Nojin Dashboard...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: colors.bg,
        color: colors.danger
      }}>
        <div style={{ textAlign: 'center' }}>
          <div>Error: {error}</div>
          <button 
            onClick={fetchData}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              background: colors.primary,
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: colors.bg 
      }}>
        <div style={{ fontSize: '1.5rem', color: colors.text }}>
          No data available
        </div>
      </div>
    );
  }

  const { farm, weather, satellite, predictions } = dashboardData;

  return (
    <div style={{ 
      padding: '2rem', 
      background: colors.bg,
      minHeight: '100vh',
      color: colors.text
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '2rem'
      }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 'bold' }}>
          {t('dashboard_title')} - Eco Nojin
        </h1>
        <button 
          onClick={fetchData}
          style={{
            padding: '0.5rem 1rem',
            background: colors.primary,
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <RefreshIcon />
          Refresh Data
        </button>
      </div>

      {/* Farm Overview Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{
          background: colors.cardBg,
          border: `1px solid ${colors.border}`,
          borderRadius: '12px',
          padding: '1.5rem',
          marginBottom: '1.5rem'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: colors.primary,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <MapPin size={24} color="white" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: 0 }}>{farm.name}</h2>
            <p style={{ margin: 0, color: colors.textMuted }}>{farm.location}</p>
          </div>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <p style={{ margin: 0, color: colors.textMuted }}>Size</p>
            <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{farm.size} ha</p>
          </div>
          <div>
            <p style={{ margin: 0, color: colors.textMuted }}>Crop Type</p>
            <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{farm.cropType}</p>
          </div>
          <div>
            <p style={{ margin: 0, color: colors.textMuted }}>Last Update</p>
            <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{farm.lastUpdate}</p>
          </div>
        </div>
      </motion.div>

      {/* Data Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {/* Weather Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '12px',
            padding: '1.5rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: colors.accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Droplet size={24} color="white" />
            </div>
            <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Weather Conditions</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>Temperature</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{weather.temperature}°C</p>
            </div>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>Humidity</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{weather.humidity}%</p>
            </div>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>Precipitation</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{weather.precipitation}mm</p>
            </div>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>Condition</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{weather.condition}</p>
            </div>
          </div>
        </motion.div>

        {/* Satellite Data Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '12px',
            padding: '1.5rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: '#0d9488', // teal
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Satellite size={24} color="white" />
            </div>
            <h3 style={{ margin: 0, fontSize: '1.25rem' }}>Satellite Data</h3>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>NDVI</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{satellite.ndvi.toFixed(2)}</p>
            </div>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>EVI</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{satellite.evi.toFixed(2)}</p>
            </div>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>Soil Moisture</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{satellite.soilMoisture}%</p>
            </div>
            <div>
              <p style={{ margin: 0, color: colors.textMuted }}>Image Date</p>
              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.2rem' }}>{satellite.imageDate}</p>
            </div>
          </div>
        </motion.div>

        {/* Predictions Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          style={{
            background: colors.cardBg,
            border: `1px solid ${colors.border}`,
            borderRadius: '12px',
            padding: '1.5rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: colors.warm,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Bot size={24} color="white" />
            </div>
            <h3 style={{ margin: 0, fontSize: '1.25rem' }}>AI Predictions</h3>
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ margin: 0, color: colors.textMuted }}>Predicted Yield</p>
            <p style={{ margin: 0, fontWeight: 'bold', fontSize: '1.5rem' }}>{predictions.yieldPrediction} tons/ha</p>
          </div>
          
          <div style={{ marginBottom: '1rem' }}>
            <p style={{ margin: 0, color: colors.textMuted }}>Risk Level</p>
            <p 
              style={{ 
                margin: 0, 
                fontWeight: 'bold', 
                fontSize: '1.2rem',
                color: predictions.riskLevel === 'high' ? colors.danger : 
                       predictions.riskLevel === 'medium' ? colors.warning : colors.success
              }}
            >
              {predictions.riskLevel.charAt(0).toUpperCase() + predictions.riskLevel.slice(1)}
            </p>
          </div>
          
          <div>
            <p style={{ margin: 0, color: colors.textMuted, marginBottom: '0.5rem' }}>Recommendations:</p>
            <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
              {predictions.recommendations.map((rec, index) => (
                <li key={index} style={{ marginBottom: '0.5rem' }}>{rec}</li>
              ))}
            </ul>
          </div>
        </motion.div>
      </div>

      {/* Additional Features Grid */}
      <div style={{ marginTop: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Additional Features</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          {[
            { icon: ShoppingCart, title: 'Marketplace', desc: 'Buy and sell agricultural products' },
            { icon: TreePine, title: 'Carbon Credits', desc: 'Track and trade carbon credits' },
            { icon: Wallet, title: 'EcoWallet', desc: 'Manage digital assets and payments' },
            { icon: BarChart3, title: 'Analytics', desc: 'View farm performance metrics' }
          ].map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + (index * 0.1) }}
              whileHover={{ y: -5 }}
              style={{
                background: colors.cardBg,
                border: `1px solid ${colors.border}`,
                borderRadius: '12px',
                padding: '1.5rem',
                textAlign: 'center',
                cursor: 'pointer'
              }}
            >
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: colors.primary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem'
              }}>
                <feature.icon size={24} color="white" />
              </div>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.25rem' }}>{feature.title}</h3>
              <p style={{ margin: 0, color: colors.textMuted }}>{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Simple refresh icon component
const RefreshIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
    <path d="M21 3v5h-5"/>
    <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
    <path d="M8 16H3v5"/>
  </svg>
);

export default EcoNojinDashboard;