import { lazyPage } from './lazy';
import {
  Outlet,
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router';
const AiCopilotPage = lazyPage(() => import('@/features/ai-copilot/AiCopilotPage'));;
const CropWaterReqPage = lazyPage(() => import('@/features/aquacrop/CropWaterReqPage'));;
import { LoginPage } from '@/features/auth/LoginPage';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
const BlockchainPage = lazyPage(() => import('@/features/blockchain/BlockchainPage'));;
const CarbonOraclePage = lazyPage(() => import('@/features/carbon-oracle/CarbonOraclePage'));;
const CarbonPage = lazyPage(() => import('@/features/carbon/CarbonPage'));;
const ChatPage = lazyPage(() => import('@/features/chat/ChatPage'));;
const ClimatePage = lazyPage(() => import('@/features/climate/ClimatePage'));;
const DashboardHome = lazyPage(() => import('@/features/dashboard/DashboardHome'));;
const LandDrainagePage = lazyPage(() => import('@/features/land-drainage/LandDrainagePage'));;
const LandCapabilityPage = lazyPage(() => import('@/features/land-capability/LandCapabilityPage'));;
const LandTerrainPage = lazyPage(() => import('@/features/land-terrain/LandTerrainPage'));;
const MarketplacePage = lazyPage(() => import('@/features/marketplace/MarketplacePage'));;
const ModelsPage = lazyPage(() => import('@/features/models/ModelsPage'));;
const MotorsPage = lazyPage(() => import('@/features/motors/MotorsPage'));;
const MrvPage = lazyPage(() => import('@/features/mrv/MrvPage'));;
const RunoffPage = lazyPage(() => import('@/features/runoff/RunoffPage'));;
const SatelliteAnalyzePage = lazyPage(() => import('@/features/satellite-analyze/SatelliteAnalyzePage'));;
const SatellitePage = lazyPage(() => import('@/features/satellite/SatellitePage'));;
const ErosionPage = lazyPage(() => import('@/features/erosion/ErosionPage'));;
const Era5Page = lazyPage(() => import('@/features/era5/Era5Page'));;
const GroundwaterPage = lazyPage(() => import('@/features/groundwater/GroundwaterPage'));;
const IrrigationDesignPage = lazyPage(() => import('@/features/irrigation/IrrigationDesignPage'));;
const SoilCarbonPage = lazyPage(() => import('@/features/soil-carbon/SoilCarbonPage'));;
const SoilPage = lazyPage(() => import('@/features/soil/SoilPage'), 'SoilPage');
const StructureDesignPage = lazyPage(() => import('@/features/structure/StructureDesignPage'));;
const TopographyPage = lazyPage(() => import('@/features/topography/TopographyPage'));;
const FarmsPage = lazyPage(() => import('@/features/farms/FarmsPage'));;
const WalletPage = lazyPage(() => import('@/features/wallet/WalletPage'));;
const WaterPage = lazyPage(() => import('@/features/water/WaterPage'));;
import { GlobalErrorBoundary } from '../components/GlobalErrorBoundary';
import { WorkspaceLayout } from './WorkspaceLayout';

const rootRoute = createRootRoute({
  component: () => (
    <GlobalErrorBoundary>
      <Outlet />
    </GlobalErrorBoundary>
  ),
});

const wrap = (C: () => React.ReactElement) => () => <ProtectedRoute><C /></ProtectedRoute>;

const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: wrap(DashboardHome) });
const carbonRoute = createRoute({ getParentRoute: () => rootRoute, path: '/carbon', component: wrap(CarbonPage) });
const waterRoute = createRoute({ getParentRoute: () => rootRoute, path: '/water', component: wrap(WaterPage) });
const soilRoute = createRoute({ getParentRoute: () => rootRoute, path: '/soil', component: wrap(SoilPage) });
const climateRoute = createRoute({ getParentRoute: () => rootRoute, path: '/climate', component: wrap(ClimatePage) });
const satelliteRoute = createRoute({ getParentRoute: () => rootRoute, path: '/satellite', component: wrap(SatellitePage) });
const mrvRoute = createRoute({ getParentRoute: () => rootRoute, path: '/mrv', component: wrap(MrvPage) });
const modelsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/models', component: wrap(ModelsPage) });
const motorsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/motors', component: wrap(MotorsPage) });
const farmsRoute = createRoute({ getParentRoute: () => rootRoute, path: '/farms', component: wrap(FarmsPage) });
const marketplaceRoute = createRoute({ getParentRoute: () => rootRoute, path: '/marketplace', component: wrap(MarketplacePage) });
const walletRoute = createRoute({ getParentRoute: () => rootRoute, path: '/wallet', component: wrap(WalletPage) });
const aiCopilotRoute = createRoute({ getParentRoute: () => rootRoute, path: '/ai-copilot', component: wrap(AiCopilotPage) });
const chatRoute = createRoute({ getParentRoute: () => rootRoute, path: '/chat', component: wrap(ChatPage) });

// Scientific model pages
const aquacropRoute = createRoute({ getParentRoute: () => rootRoute, path: '/aquacrop', component: wrap(CropWaterReqPage) });
const swatRoute = createRoute({ getParentRoute: () => rootRoute, path: '/swat', component: wrap(RunoffPage) });
const rothcRoute = createRoute({ getParentRoute: () => rootRoute, path: '/rothc', component: wrap(SoilCarbonPage) });
const erosionRoute = createRoute({ getParentRoute: () => rootRoute, path: '/erosion', component: wrap(ErosionPage) });
const groundwaterRoute = createRoute({ getParentRoute: () => rootRoute, path: '/groundwater', component: wrap(GroundwaterPage) });
const irrigationRoute = createRoute({ getParentRoute: () => rootRoute, path: '/irrigation', component: wrap(IrrigationDesignPage) });
const structureRoute = createRoute({ getParentRoute: () => rootRoute, path: '/structures', component: wrap(StructureDesignPage) });
const topographyRoute = createRoute({ getParentRoute: () => rootRoute, path: '/topography', component: wrap(TopographyPage) });
const landCapabilityRoute = createRoute({ getParentRoute: () => rootRoute, path: '/land-capability', component: wrap(LandCapabilityPage) });
const landTerrainRoute = createRoute({ getParentRoute: () => rootRoute, path: '/land-terrain', component: wrap(LandTerrainPage) });
const landDrainageRoute = createRoute({ getParentRoute: () => rootRoute, path: '/land-drainage', component: wrap(LandDrainagePage) });
const era5Route = createRoute({ getParentRoute: () => rootRoute, path: '/era5', component: wrap(Era5Page) });
const satelliteAnalyzeRoute = createRoute({ getParentRoute: () => rootRoute, path: '/satellite-analyze', component: wrap(SatelliteAnalyzePage) });
const blockchainRoute = createRoute({ getParentRoute: () => rootRoute, path: '/blockchain', component: wrap(BlockchainPage) });
const carbonOracleRoute = createRoute({ getParentRoute: () => rootRoute, path: '/carbon-oracle', component: wrap(CarbonOraclePage) });

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: () => <LoginPage />,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  carbonRoute,
  waterRoute,
  soilRoute,
  climateRoute,
  satelliteRoute,
  mrvRoute,
  modelsRoute,
  motorsRoute,
  farmsRoute,
  marketplaceRoute,
  walletRoute,
  aiCopilotRoute,
  chatRoute,
  aquacropRoute,
  swatRoute,
  rothcRoute,
  erosionRoute,
  groundwaterRoute,
  irrigationRoute,
  structureRoute,
  topographyRoute,
  landCapabilityRoute,
  landTerrainRoute,
  landDrainageRoute,
  era5Route,
  satelliteAnalyzeRoute,
  blockchainRoute,
  carbonOracleRoute,
  loginRoute,
]);

export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

export { Outlet };