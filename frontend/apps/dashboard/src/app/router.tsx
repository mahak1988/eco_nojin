import {
  Outlet,
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router';
import { AiCopilotPage } from '@/features/ai-copilot/AiCopilotPage';
import { CropWaterReqPage } from '@/features/aquacrop/CropWaterReqPage';
import { LoginPage } from '@/features/auth/LoginPage';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
import { BlockchainPage } from '@/features/blockchain/BlockchainPage';
import { CarbonOraclePage } from '@/features/carbon-oracle/CarbonOraclePage';
import { CarbonPage } from '@/features/carbon/CarbonPage';
import { ChatPage } from '@/features/chat/ChatPage';
import { ClimatePage } from '@/features/climate/ClimatePage';
import { DashboardHome } from '@/features/dashboard/DashboardHome';
import { LandDrainagePage } from '@/features/land-drainage/LandDrainagePage';
import { LandCapabilityPage } from '@/features/land-capability/LandCapabilityPage';
import { LandTerrainPage } from '@/features/land-terrain/LandTerrainPage';
import { MarketplacePage } from '@/features/marketplace/MarketplacePage';
import { ModelsPage } from '@/features/models/ModelsPage';
import { MotorsPage } from '@/features/motors/MotorsPage';
import { MrvPage } from '@/features/mrv/MrvPage';
import { RunoffPage } from '@/features/runoff/RunoffPage';
import { SatelliteAnalyzePage } from '@/features/satellite-analyze/SatelliteAnalyzePage';
import { SatellitePage } from '@/features/satellite/SatellitePage';
import { ErosionPage } from '@/features/erosion/ErosionPage';
import { Era5Page } from '@/features/era5/Era5Page';
import { GroundwaterPage } from '@/features/groundwater/GroundwaterPage';
import { IrrigationDesignPage } from '@/features/irrigation/IrrigationDesignPage';
import { SoilCarbonPage } from '@/features/soil-carbon/SoilCarbonPage';
import { SoilPage } from '@/features/soil/SoilPage';
import { StructureDesignPage } from '@/features/structure/StructureDesignPage';
import { TopographyPage } from '@/features/topography/TopographyPage';
import { FarmsPage } from '@/features/farms/FarmsPage';
import { WalletPage } from '@/features/wallet/WalletPage';
import { WaterPage } from '@/features/water/WaterPage';
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