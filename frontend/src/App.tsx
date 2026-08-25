import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import faIR from 'antd/locale/fa_IR';
import AppLayout from './components/layout/AppLayout';

// صفحات (فعلاً placeholder)
import Dashboard from './pages/Dashboard';
import TerrainAnalysis from './pages/TerrainAnalysis';
import Reports from './pages/Reports';
import Settings from './pages/Settings'; // اگر وجود ندارد، می‌توانیم حذف کنیم

const App: React.FC = () => {
  return (
    <ConfigProvider direction="rtl" locale={faIR}>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/terrain-analysis" element={<TerrainAnalysis />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<div>تنظیمات</div>} /> {/* موقت */}
        </Route>
      </Routes>
    </ConfigProvider>
  );
};

export default App;