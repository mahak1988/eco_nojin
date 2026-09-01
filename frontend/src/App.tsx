import Diag3D from './pages/Diag3D';
import { SimulationPipelineProvider } from './contexts/SimulationPipeline';
import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import {
  AdminLayout,
  AdminOverview,
  AdminSecurity,
  AdminUsers,
  AdminAudit,
  AdminFinance,
  AdminErrors,
  AdminContent,
  AdminSettings,
  ThemeProvider,
  SecurityAdvanced,
  MarketplaceDashboard,
  EcoWalletDashboard,
  ContentStudio,
  BotsManagement,
  AIModelsMonitor,
  MotorRunner,
  HyDroMa3D,
} from './pages/admin';
import LiveDashboard from './pages/admin/LiveDashboard';
import CryptoPaymentWidget from './pages/admin/crypto/CryptoPaymentWidget';
import TelegramManager from './pages/admin/telegram/TelegramManager';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

import LoadingSpinner from './components/common/LoadingSpinner';

// Entry page â€” eager for first paint
import { HomePage } from './pages/HomePage';

// Code-splitting (Phase 3): ط¨ظ‚غŒظ‡ طµظپط­ط§طھ lazy â€” ط¨ط§ظ†ط¯ظ„ ط§ظˆظ„غŒظ‡ ع©ظˆع†ع©â€Œطھط±
const HelpDocs = lazy(() => import('./pages/HelpDocs'));
const Support = lazy(() => import('./pages/Support'));


const HyDroMaCenter = lazy(() => import('./pages/HyDroMaCenter'));

// Phase 0 pages (default exports)
const TerrainAnalysis = lazy(() => import('./pages/TerrainAnalysis'));
const SystemStatus = lazy(() => import('./pages/SystemStatus'));
const Reports = lazy(() => import('./pages/Reports'));
const DataManagement = lazy(() => import('./pages/DataManagement'));
const LandProfiles = lazy(() => import('./pages/LandProfiles'));
const APIDocumentation = lazy(() => import('./pages/APIDocumentation'));
const Settings = lazy(() => import('./pages/Settings'));
import './styles/global.css';

// Lazy-loaded heavy modules for performance optimization
import { LazyWrapper } from './components/common/LazyWrapper';

// Heavy 3D modules - loaded on demand

// Admin modules - loaded on demand

// Heavy chart modules

function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <SimulationPipelineProvider>
          <Routes>
            {/* Admin Dashboard Routes - Phase 2 Complete */}
            <Route path="/diag3d" element={<Diag3D />} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AdminOverview />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AdminUsers />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/audit"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AdminAudit />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/security"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <SecurityAdvanced />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/finance"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AdminFinance />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/errors"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AdminErrors />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            {/* Route for ContentStudio removed */}
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/settings"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AdminSettings />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/marketplace"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <MarketplaceDashboard />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/ecowallet"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <EcoWalletDashboard />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            {/* Route for BotsManagement removed */}
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            {/* Route for AIModelsMonitor removed */}
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />

            {/* Public */}
            {/* Route for AboutPage removed */}
            {/* Route for MissionPage removed */}
            {/* Route for PricingPage removed */}
            {/* Route for PrivacyPage removed */}
            {/* Route for LoginPage removed */}
            {/* Route for RegisterPage removed */}

            {/* App (protected) */}
            <Route
              path="/hydroma"
              element={
                <ProtectedRoute>
                  <HyDroMaCenter />
                </ProtectedRoute>
              }
            />
            <Route path="/dashboard" element={<Navigate to="/hydroma" replace />} />
            {/* Route for VisualSimulatorsPage removed */}
                </ProtectedRoute>
              }
            />
            {/* Route for VirtualLandLabPage removed */}
                </ProtectedRoute>
              }
            />
            {/* Route for ProfilePage removed */}
                </ProtectedRoute>
              }
            />

            {/* Models & analysis (protected) */}
            <Route
              path="/terrain"
              element={
                <ProtectedRoute>
                  <TerrainAnalysis />
                </ProtectedRoute>
              }
            />
            <Route path="/visualization-3d" element={<Navigate to="/hydroma" replace />} />
            <Route path="/models" element={<Navigate to="/hydroma" replace />} />
            <Route path="/models/rothc" element={<Navigate to="/hydroma" replace />} />
            <Route path="/models/swat" element={<Navigate to="/hydroma" replace />} />
            <Route path="/models/watershed" element={<Navigate to="/hydroma" replace />} />
            <Route
              path="/land-profiles"
              element={
                <ProtectedRoute>
                  <LandProfiles />
                </ProtectedRoute>
              }
            />
            <Route path="/capability" element={<Navigate to="/hydroma" replace />} />

            {/* Platform (protected) */}
            <Route
              path="/monitoring"
              element={
                <ProtectedRoute>
                  <SystemStatus />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute>
                  <Reports />
                </ProtectedRoute>
              }
            />
            <Route
              path="/data"
              element={
                <ProtectedRoute>
                  <DataManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/api-docs"
              element={
                <ProtectedRoute>
                  <APIDocumentation />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />

            {/* Phase 3: Live Dashboard */}
            <Route
              path="/admin/hydroma-3d"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <HyDroMa3D />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />

            {/* Route for MotorRunner removed */}
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin/live"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <LiveDashboard />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />

            {/* Phase 4: Crypto Payments */}
            <Route
              path="/admin/crypto"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <CryptoPaymentWidget />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />

            {/* Phase 4: Telegram Manager */}
            <Route
              path="/admin/telegram"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <TelegramManager />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
          </Routes>
        </SimulationPipelineProvider>
      </Suspense>
    </AuthProvider>
  );
}

export default App;
