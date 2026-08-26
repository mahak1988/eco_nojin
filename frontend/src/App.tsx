import { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import LoadingSpinner from './components/common/LoadingSpinner';

// Entry page — eager for first paint
import { HomePage } from './pages/HomePage';

// Code-splitting (Phase 3): بقیه صفحات lazy — باندل اولیه کوچک‌تر
const AboutPage = lazy(() => import('./pages/AboutPage').then((m) => ({ default: m.AboutPage })));
const MissionPage = lazy(() => import('./pages/MissionPage').then((m) => ({ default: m.MissionPage })));
const FeaturesPage = lazy(() => import('./pages/FeaturesPage').then((m) => ({ default: m.FeaturesPage })));
const PricingPage = lazy(() => import('./pages/PricingPage').then((m) => ({ default: m.PricingPage })));
const HydromaPage = lazy(() => import('./pages/HydromaPage').then((m) => ({ default: m.HydromaPage })));
const ContactPage = lazy(() => import('./pages/ContactPage').then((m) => ({ default: m.ContactPage })));
const DocsPage = lazy(() => import('./pages/DocsPage').then((m) => ({ default: m.DocsPage })));
const TermsPage = lazy(() => import('./pages/TermsPage').then((m) => ({ default: m.TermsPage })));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage').then((m) => ({ default: m.PrivacyPage })));
const BlogPage = lazy(() => import('./pages/BlogPage').then((m) => ({ default: m.BlogPage })));
const HelpDocs = lazy(() => import('./pages/HelpDocs'));
const Support = lazy(() => import('./pages/Support'));

const LoginPage = lazy(() => import('./pages/auth/LoginPage').then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage').then((m) => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })));

const HydromaDashboard = lazy(() => import('./pages/HydromaDashboard').then((m) => ({ default: m.HydromaDashboard })));
const SimulatorDashboard = lazy(() => import('./pages/SimulatorDashboard').then((m) => ({ default: m.SimulatorDashboard })));
const VisualSimulatorsPage = lazy(() => import('./pages/VisualSimulatorsPage').then((m) => ({ default: m.VisualSimulatorsPage })));
const VirtualLandLabPage = lazy(() => import('./pages/VirtualLandLabPage').then((m) => ({ default: m.VirtualLandLabPage })));
const ProfilePage = lazy(() => import('./pages/ProfilePage').then((m) => ({ default: m.ProfilePage })));

// Phase 0 pages (default exports)
const TerrainAnalysis = lazy(() => import('./pages/TerrainAnalysis'));
const Visualization3D = lazy(() => import('./pages/Visualization3D'));
const ModelsLibrary = lazy(() => import('./pages/ModelsLibrary'));
const RothCModel = lazy(() => import('./pages/RothCModel'));
const SWATModel = lazy(() => import('./pages/SWATModel'));
const WatershedModel = lazy(() => import('./pages/WatershedModel'));
const SystemStatus = lazy(() => import('./pages/SystemStatus'));
const Reports = lazy(() => import('./pages/Reports'));
const DataManagement = lazy(() => import('./pages/DataManagement'));
const LandProfiles = lazy(() => import('./pages/LandProfiles'));
const CapabilityAssessment = lazy(() => import('./pages/CapabilityAssessment'));
const APIDocumentation = lazy(() => import('./pages/APIDocumentation'));
const Settings = lazy(() => import('./pages/Settings'));
import './styles/global.css';

function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<LoadingSpinner fullScreen />}>
        <Routes>
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
          <Route path="/hydroma" element={<ProtectedRoute><HydromaDashboard /></ProtectedRoute>} />
          <Route path="/dashboard" element={<Navigate to="/hydroma" replace />} />
          <Route path="/simulator" element={<ProtectedRoute><SimulatorDashboard /></ProtectedRoute>} />
          <Route path="/simulators" element={<ProtectedRoute><VisualSimulatorsPage /></ProtectedRoute>} />
          <Route path="/virtual-lab" element={<ProtectedRoute><VirtualLandLabPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />

          {/* Models & analysis (protected) */}
          <Route path="/terrain" element={<ProtectedRoute><TerrainAnalysis /></ProtectedRoute>} />
          <Route path="/visualization-3d" element={<ProtectedRoute><Visualization3D /></ProtectedRoute>} />
          <Route path="/models" element={<ProtectedRoute><ModelsLibrary /></ProtectedRoute>} />
          <Route path="/models/rothc" element={<ProtectedRoute><RothCModel /></ProtectedRoute>} />
          <Route path="/models/swat" element={<ProtectedRoute><SWATModel /></ProtectedRoute>} />
          <Route path="/models/watershed" element={<ProtectedRoute><WatershedModel /></ProtectedRoute>} />
          <Route path="/land-profiles" element={<ProtectedRoute><LandProfiles /></ProtectedRoute>} />
          <Route path="/capability" element={<ProtectedRoute><CapabilityAssessment /></ProtectedRoute>} />

          {/* Platform (protected) */}
          <Route path="/monitoring" element={<ProtectedRoute><SystemStatus /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
          <Route path="/data" element={<ProtectedRoute><DataManagement /></ProtectedRoute>} />
          <Route path="/api-docs" element={<ProtectedRoute><APIDocumentation /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </AuthProvider>
  );
}

export default App;
