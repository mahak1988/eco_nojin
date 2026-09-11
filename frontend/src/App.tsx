import { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';
import { LanguageProvider } from './i18n/LanguageContext';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Backdrop from './components/visuals/Backdrop';
import RouteFallback from './components/ui/RouteFallback';

const HomePage = lazy(() => import('./pages/HomePage'));
const PlatformPage = lazy(() => import('./pages/PlatformPage'));
const HydromaPage = lazy(() => import('./pages/HydromaPage'));
const AboutPage = lazy(() => import('./pages/AboutPage'));
const BlogPage = lazy(() => import('./pages/BlogPage'));
const FaqPage = lazy(() => import('./pages/FaqPage'));
const ContactPage = lazy(() => import('./pages/ContactPage'));
const TransparencyPage = lazy(() => import('./pages/TransparencyPage'));
const DeclarationPage = lazy(() => import('./pages/DeclarationPage'));
const DevelopersPage = lazy(() => import('./pages/DevelopersPage'));
const EcoCoinPage = lazy(() => import('./pages/EcoCoinPage'));
const SupportPage = lazy(() => import('./pages/SupportPage'));
const StatusPage = lazy(() => import('./pages/StatusPage'));
const ImpactPage = lazy(() => import('./pages/ImpactPage'));
const CarbonPage = lazy(() => import('./pages/CarbonPage'));
const PartnersPage = lazy(() => import('./pages/PartnersPage'));
const CareersPage = lazy(() => import('./pages/CareersPage'));
const InvestorsPage = lazy(() => import('./pages/InvestorsPage'));
const PilotPage = lazy(() => import('./pages/PilotPage'));
const UssdGuidePage = lazy(() => import('./pages/UssdGuidePage'));
const VoiceGuidePage = lazy(() => import('./pages/VoiceGuidePage'));
const AcademiaPage = lazy(() => import('./pages/AcademiaPage'));
const MarketplacePage = lazy(() => import('./pages/MarketplacePage'));
const ResourcesPage = lazy(() => import('./pages/ResourcesPage'));
const DashboardLayout = lazy(() => import('./components/dashboard/DashboardLayout'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const RulesPage = lazy(() => import('./pages/RulesPage'));
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

/** Scrolls the window back to the top on every route change. */
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
  }, [pathname]);
  return null;
}

/** Route tree + shared chrome. Exported for tests (rendered inside MemoryRouter). */
export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <Backdrop />
      <Navbar />
      <main className="flex-1 pt-16">
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/platform" element={<PlatformPage />} />
            <Route path="/hydroma" element={<HydromaPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/blog" element={<BlogPage />} />
            <Route path="/faq" element={<FaqPage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/transparency" element={<TransparencyPage />} />
            <Route path="/declaration" element={<DeclarationPage />} />
            <Route path="/developers" element={<DevelopersPage />} />
            <Route path="/eco-coin" element={<EcoCoinPage />} />
            <Route path="/support" element={<SupportPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/impact" element={<ImpactPage />} />
            <Route path="/carbon" element={<CarbonPage />} />
            <Route path="/partners" element={<PartnersPage />} />
            <Route path="/careers" element={<CareersPage />} />
            <Route path="/investors" element={<InvestorsPage />} />
            <Route path="/pilot" element={<PilotPage />} />
            <Route path="/pilot-iran" element={<PilotPage />} />
            <Route path="/ussd-guide" element={<UssdGuidePage />} />
            <Route path="/voice-guide" element={<VoiceGuidePage />} />
            <Route path="/academia" element={<AcademiaPage />} />
            <Route path="/marketplace" element={<MarketplacePage />} />
            <Route path="/resources" element={<ResourcesPage />} />
            <Route path="/dashboard/*" element={<DashboardLayout />} />
            <Route path="/terms" element={<TermsPage />} />
            <Route path="/rules" element={<RulesPage />} />
            <Route path="/privacy" element={<PrivacyPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}

/** App root: language provider + router. */
export default function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <ScrollToTop />
        <AppShell />
      </BrowserRouter>
    </LanguageProvider>
  );
}
