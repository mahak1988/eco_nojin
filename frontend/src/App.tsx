import { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';
import { LanguageProvider } from './i18n/LanguageContext';
import { ThemeProvider } from './components/theme/ThemeProvider';
import { AuthProvider } from './context/AuthContext';
import { MarketplaceProvider } from './context/MarketplaceContext';
import { ToastProvider } from './components/ui/Toast';
import { QueryProvider } from './lib/queryClient';
import Backdrop from './components/visuals/Backdrop';
import SmoothScroll from './components/visuals/SmoothScroll';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import RouteFallback from './components/ui/RouteFallback';

const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
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
const CatalogPage = lazy(() => import('./pages/marketplace/CatalogPage'));
const ProductPage = lazy(() => import('./pages/marketplace/ProductPage'));
const VendorPage = lazy(() => import('./pages/marketplace/VendorPage'));
const CartPage = lazy(() => import('./pages/marketplace/CartPage'));
const CheckoutPage = lazy(() => import('./pages/marketplace/CheckoutPage'));
const BuyerDashboard = lazy(() => import('./pages/marketplace/BuyerDashboard'));
const VendorDashboard = lazy(() => import('./pages/marketplace/VendorDashboard'));
const VendorApplication = lazy(() => import('./pages/marketplace/VendorApplication'));
const AdminPanel = lazy(() => import('./pages/marketplace/AdminPanel'));
const MarketplaceNotFound = lazy(() => import('./pages/marketplace/MarketplaceNotFound'));
const CreateMarketplace = lazy(() => import('./pages/marketplace/CreateMarketplace'));
const MarketplaceDirectory = lazy(() => import('./pages/marketplace/MarketplaceDirectory'));
const MarketplaceDetail = lazy(() => import('./pages/marketplace/MarketplaceDetail'));
const MarketplaceDashboard = lazy(() => import('./pages/marketplace/MarketplaceDashboard'));
const OrderTrackingPage = lazy(() => import('./pages/marketplace/OrderTrackingPage'));
const WishlistPage = lazy(() => import('./pages/marketplace/WishlistPage'));
const MarketplaceLayout = lazy(() => import('./layouts/MarketplaceLayout'));
const DashboardLayout = lazy(() => import('./components/dashboard/DashboardLayout'));
const DashboardGate = lazy(() => import('./components/auth/DashboardGate'));
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

/** Public shell — used by tests (renders inside MemoryRouter). */
export function AppShell() {
  return (
    <div className="flex min-h-screen flex-col">
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
        <Route path="/marketplace/create" element={<CreateMarketplace />} />
        <Route path="/marketplace/directory" element={<MarketplaceDirectory />} />
        <Route path="/marketplace/marketplaces/:id" element={<MarketplaceDetail />} />
        <Route path="/marketplace/dashboard" element={<MarketplaceDashboard />} />
        <Route path="/resources" element={<ResourcesPage />} />
        <Route path="/dashboard/*" element={<DashboardGate><DashboardLayout /></DashboardGate>} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/rules" element={<RulesPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}

/** Public layout — Navbar + Footer + Backdrop wrap their children.
   * Dashboard routes (/dashboard/*) are app-like shells and omit the footer. */
function PublicLayout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const isDashboard = pathname.startsWith('/dashboard');
  return (
    <div className="flex min-h-screen flex-col">
      <Backdrop />
      <Navbar />
      <main className="flex-1 pt-16" id="main-content">
        <Suspense fallback={<RouteFallback />}>{children}</Suspense>
      </main>
      {!isDashboard && <Footer />}
    </div>
  );
}

/** Auth layout — bare page, no Navbar / Footer / Backdrop. */
function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Suspense fallback={<RouteFallback />}>{children}</Suspense>
    </div>
  );
}

/** App root: language + auth + toast providers, single router. */
export default function App() {
  return (
    <LanguageProvider>
      <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <MarketplaceProvider>
            <QueryProvider>
              <BrowserRouter>
                <SmoothScroll />
                <ScrollToTop />
                <Routes>
                  {/* auth pages — bare, no Navbar / Footer / Backdrop */}
                  <Route path="/login" element={<AuthLayout><LoginPage /></AuthLayout>} />
                  <Route path="/register" element={<AuthLayout><RegisterPage /></AuthLayout>} />
                  <Route path="/forgot-password" element={<AuthLayout><ForgotPasswordPage /></AuthLayout>} />
                  <Route path="/reset-password" element={<AuthLayout><ResetPasswordPage /></AuthLayout>} />

                  {/* public pages — wrapped in the public shell */}
                  <Route path="/" element={<PublicLayout><HomePage /></PublicLayout>} />
                  <Route path="/platform" element={<PublicLayout><PlatformPage /></PublicLayout>} />
                  <Route path="/hydroma" element={<PublicLayout><HydromaPage /></PublicLayout>} />
                  <Route path="/about" element={<PublicLayout><AboutPage /></PublicLayout>} />
                  <Route path="/blog" element={<PublicLayout><BlogPage /></PublicLayout>} />
                  <Route path="/faq" element={<PublicLayout><FaqPage /></PublicLayout>} />
                  <Route path="/contact" element={<PublicLayout><ContactPage /></PublicLayout>} />
                  <Route path="/transparency" element={<PublicLayout><TransparencyPage /></PublicLayout>} />
                  <Route path="/declaration" element={<PublicLayout><DeclarationPage /></PublicLayout>} />
                  <Route path="/developers" element={<PublicLayout><DevelopersPage /></PublicLayout>} />
                  <Route path="/eco-coin" element={<PublicLayout><EcoCoinPage /></PublicLayout>} />
                  <Route path="/support" element={<PublicLayout><SupportPage /></PublicLayout>} />
                  <Route path="/status" element={<PublicLayout><StatusPage /></PublicLayout>} />
                  <Route path="/impact" element={<PublicLayout><ImpactPage /></PublicLayout>} />
                  <Route path="/carbon" element={<PublicLayout><CarbonPage /></PublicLayout>} />
                  <Route path="/partners" element={<PublicLayout><PartnersPage /></PublicLayout>} />
                  <Route path="/careers" element={<PublicLayout><CareersPage /></PublicLayout>} />
                  <Route path="/investors" element={<PublicLayout><InvestorsPage /></PublicLayout>} />
                  <Route path="/pilot" element={<PublicLayout><PilotPage /></PublicLayout>} />
                  <Route path="/pilot-iran" element={<PublicLayout><PilotPage /></PublicLayout>} />
                  <Route path="/ussd-guide" element={<PublicLayout><UssdGuidePage /></PublicLayout>} />
                  <Route path="/voice-guide" element={<PublicLayout><VoiceGuidePage /></PublicLayout>} />
                  <Route path="/academia" element={<PublicLayout><AcademiaPage /></PublicLayout>} />
                  <Route path="/marketplace" element={<PublicLayout><MarketplaceLayout><CatalogPage /></MarketplaceLayout></PublicLayout>} />
        <Route path="/marketplace/about" element={<PublicLayout><MarketplacePage /></PublicLayout>} />
                  <Route path="/marketplace/products/:id" element={<PublicLayout><MarketplaceLayout><ProductPage /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/vendor/:id" element={<PublicLayout><MarketplaceLayout><VendorPage /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/cart" element={<PublicLayout><MarketplaceLayout><CartPage /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/checkout" element={<PublicLayout><MarketplaceLayout><CheckoutPage /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/orders" element={<PublicLayout><MarketplaceLayout><BuyerDashboard /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/orders/:id/track" element={<PublicLayout><MarketplaceLayout><OrderTrackingPage /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/wishlist" element={<PublicLayout><MarketplaceLayout><WishlistPage /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/sell" element={<PublicLayout><MarketplaceLayout><VendorDashboard /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/apply" element={<PublicLayout><MarketplaceLayout><VendorApplication /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/marketplace/admin" element={<DashboardGate><MarketplaceLayout><AdminPanel /></MarketplaceLayout></DashboardGate>} />
                  <Route path="/marketplace/*" element={<PublicLayout><MarketplaceLayout><MarketplaceNotFound /></MarketplaceLayout></PublicLayout>} />
                  <Route path="/resources" element={<PublicLayout><ResourcesPage /></PublicLayout>} />
                  <Route path="/dashboard/*" element={<PublicLayout><DashboardGate><DashboardLayout /></DashboardGate></PublicLayout>} />
                  <Route path="/terms" element={<PublicLayout><TermsPage /></PublicLayout>} />
                  <Route path="/rules" element={<PublicLayout><RulesPage /></PublicLayout>} />
                  <Route path="/privacy" element={<PublicLayout><PrivacyPage /></PublicLayout>} />
                  <Route path="*" element={<PublicLayout><NotFoundPage /></PublicLayout>} />
                </Routes>
              </BrowserRouter>
            </QueryProvider>
          </MarketplaceProvider>
        </ToastProvider>
      </AuthProvider>
      </ThemeProvider>
    </LanguageProvider>
  );
}