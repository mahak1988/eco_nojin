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
const AboutPage = lazy(() => import('./pages/AboutPage').then((m) => ({ default: m.AboutPage })));
const MissionPage = lazy(() =>
  import('./pages/MissionPage').then((m) => ({ default: m.MissionPage }))
);
const FeaturesPage = lazy(() =>
  import('./pages/FeaturesPage').then((m) => ({ default: m.FeaturesPage }))
);
const PricingPage = lazy(() =>
  import('./pages/PricingPage').then((m) => ({ default: m.PricingPage }))
);
const HydromaPage = lazy(() =>
  import('./pages/HydromaPage').then((m) => ({ default: m.HydromaPage }))
);
const ContactPage = lazy(() =>
  import('./pages/ContactPage').then((m) => ({ default: m.ContactPage }))
);
const DocsPage = lazy(() => import('./pages/DocsPage').then((m) => ({ default: m.DocsPage })));
const TermsPage = lazy(() => import('./pages/TermsPage').then((m) => ({ default: m.TermsPage })));
const PrivacyPage = lazy(() =>
  import('./pages/PrivacyPage').then((m) => ({ default: m.PrivacyPage }))
);
const BlogPage = lazy(() => import('./pages/BlogPage').then((m) => ({ default: m.BlogPage })));
const HelpDocs = lazy(() => import('./pages/HelpDocs'));
const Support = lazy(() => import('./pages/Support'));

const LoginPage = lazy(() =>
  import('./pages/auth/LoginPage').then((m) => ({ default: m.LoginPage }))
);
const RegisterPage = lazy(() =>
  import('./pages/auth/RegisterPage').then((m) => ({ default: m.RegisterPage }))
);
const ForgotPasswordPage = lazy(() =>
  import('./pages/auth/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage }))
);

const HyDroMaCenter = lazy(() => import('./pages/HyDroMaCenter'));
const HydromaDashboard = lazy(() =>
  import('./pages/HydromaDashboard').then((m) => ({ default: m.HydromaDashboard }))
);
const SimulatorDashboard = lazy(() =>
  import('./pages/SimulatorDashboard').then((m) => ({ default: m.SimulatorDashboard }))
);
const VisualSimulatorsPage = lazy(() =>
  import('./pages/VisualSimulatorsPage').then((m) => ({ default: m.VisualSimulatorsPage }))
);
const VirtualLandLabPage = lazy(() =>
  import('./pages/VirtualLandLabPage').then((m) => ({ default: m.VirtualLandLabPage }))
);
const ProfilePage = lazy(() =>
  import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage }))
);

// Phase 0 pages (default exports)
const TerrainAnalysis = lazy(() => import('./pages/TerrainAnalysis'));
const SystemStatus = lazy(() => import('./pages/SystemStatus'));
const Reports = lazy(() => import('./pages/Reports'));
const DataManagement = lazy(() => import('./pages/DataManagement'));
const LandProfiles = lazy(() => import('./pages/LandProfiles'));
const APIDocumentation = lazy(() => import('./pages/APIDocumentation'));
const Settings = lazy(() => import('./pages/Settings'));
import './styles/global.css';

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
            <Route
              path="/admin/content"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <ContentStudio />
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
            <Route
              path="/admin/bots"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <BotsManagement />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/ai-models"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <AIModelsMonitor />
                    </AdminLayout>
                  </ThemeProvider>
                </ProtectedRoute>
              }
            />

            {/* Public */}
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/mission" element={<MissionPage />} />
            <Route path="/features" element={<FeaturesPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="/blog" element={<BlogPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/docs" element={<DocsPage />} />
            <Route path="/hydroma-about" element={<HydromaPage />} />
            <Route path="/help" element={<HelpDocs />} />
            <Route path="/support" element={<Support />} />

            {/* Auth */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />

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
            <Route path="/simulator" element={<Navigate to="/hydroma" replace />} />
            <Route
              path="/simulators"
              element={
                <ProtectedRoute>
                  <VisualSimulatorsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/virtual-lab"
              element={
                <ProtectedRoute>
                  <VirtualLandLabPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
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

            <Route
              path="/admin/motor-runner"
              element={
                <ProtectedRoute requiredRole="admin">
                  <ThemeProvider>
                    <AdminLayout>
                      <MotorRunner />
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
