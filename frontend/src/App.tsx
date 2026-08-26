import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Public pages
import { HomePage } from './pages/HomePage';
import { AboutPage } from './pages/AboutPage';
import { MissionPage } from './pages/MissionPage';
import { FeaturesPage } from './pages/FeaturesPage';
import { PricingPage } from './pages/PricingPage';
import { HydromaPage } from './pages/HydromaPage';
import { ContactPage } from './pages/ContactPage';
import { DocsPage } from './pages/DocsPage';
import { TermsPage } from './pages/TermsPage';
import { PrivacyPage } from './pages/PrivacyPage';
import { BlogPage } from './pages/BlogPage';
import HelpDocs from './pages/HelpDocs';
import Support from './pages/Support';

// Auth pages
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';

// App pages (protected)
import { HydromaDashboard } from './pages/HydromaDashboard';
import { SimulatorDashboard } from './pages/SimulatorDashboard';
import { VisualSimulatorsPage } from './pages/VisualSimulatorsPage';
import { VirtualLandLabPage } from './pages/VirtualLandLabPage';
import { ProfilePage } from './pages/ProfilePage';

// Phase 0 — previously orphaned pages, now routed (default exports)
import TerrainAnalysis from './pages/TerrainAnalysis';
import Visualization3D from './pages/Visualization3D';
import ModelsLibrary from './pages/ModelsLibrary';
import RothCModel from './pages/RothCModel';
import SWATModel from './pages/SWATModel';
import WatershedModel from './pages/WatershedModel';
import SystemStatus from './pages/SystemStatus';
import Reports from './pages/Reports';
import DataManagement from './pages/DataManagement';
import LandProfiles from './pages/LandProfiles';
import CapabilityAssessment from './pages/CapabilityAssessment';
import APIDocumentation from './pages/APIDocumentation';
import Settings from './pages/Settings';
import './styles/global.css';

function App() {
  return (
    <AuthProvider>
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
    </AuthProvider>
  );
}

export default App;
