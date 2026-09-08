/** Dashboard route table — generated page files organized by model category
 * folders (indices/formulas/soil/hydro/simulation/carbon/climate/economics)
 * + account pages. Kept separate from the public route tree.
 * NOTE: this file lives in src/routes/ — imports use ONE level up to src/. */

import type { ReactElement } from 'react';
import DashboardHome from '../pages/DashboardPage';
import ModelDetail from '../components/dashboard/ModelDetail';
import ProfilePage from '../pages/dashboard/account/ProfilePage';
import SettingsPage from '../pages/dashboard/account/SettingsPage';

/* generated model page imports — indices */
import EcsiModelPage from '../pages/dashboard/indices/EcsiModelPage';
import EpiaModelPage from '../pages/dashboard/indices/EpiaModelPage';
import EsriModelPage from '../pages/dashboard/indices/EsriModelPage';
import EwsiModelPage from '../pages/dashboard/indices/EwsiModelPage';
import HdviModelPage from '../pages/dashboard/indices/HdviModelPage';
import HlhsModelPage from '../pages/dashboard/indices/HlhsModelPage';
import HphenoModelPage from '../pages/dashboard/indices/HphenoModelPage';
import HyrueModelPage from '../pages/dashboard/indices/HyrueModelPage';
import RunoffModelPage from '../pages/dashboard/indices/RunoffModelPage';
/* formulas */
import HortonInfiltrationModelPage from '../pages/dashboard/formulas/HortonInfiltrationModelPage';
import ScsCnRunoffModelPage from '../pages/dashboard/formulas/ScsCnRunoffModelPage';
import VanGenuchtenModelPage from '../pages/dashboard/formulas/VanGenuchtenModelPage';
import DarcyLawModelPage from '../pages/dashboard/formulas/DarcyLawModelPage';
import ManningChannelModelPage from '../pages/dashboard/formulas/ManningChannelModelPage';
import ReynoldsNumberModelPage from '../pages/dashboard/formulas/ReynoldsNumberModelPage';
import FroudeNumberModelPage from '../pages/dashboard/formulas/FroudeNumberModelPage';
import FrancisWeirModelPage from '../pages/dashboard/formulas/FrancisWeirModelPage';
import RingStorageModelPage from '../pages/dashboard/formulas/RingStorageModelPage';
import EffectivePorosityModelPage from '../pages/dashboard/formulas/EffectivePorosityModelPage';
/* soil */
import SoilTextureModelPage from '../pages/dashboard/soil/SoilTextureModelPage';
import SoilTaxonomyModelPage from '../pages/dashboard/soil/SoilTaxonomyModelPage';
import SoilWaterRetentionModelPage from '../pages/dashboard/soil/SoilWaterRetentionModelPage';
import PedotransferModelPage from '../pages/dashboard/soil/PedotransferModelPage';
import SoilPhysicsModelPage from '../pages/dashboard/soil/SoilPhysicsModelPage';
import SoilChemistryModelPage from '../pages/dashboard/soil/SoilChemistryModelPage';
import SoilSalinityModelPage from '../pages/dashboard/soil/SoilSalinityModelPage';
import SoilHealthModelPage from '../pages/dashboard/soil/SoilHealthModelPage';
import SoilRecommendationsModelPage from '../pages/dashboard/soil/SoilRecommendationsModelPage';
/* hydro */
import GroundwaterModelPage from '../pages/dashboard/hydro/GroundwaterModelPage';
import GroundwaterServiceModelPage from '../pages/dashboard/hydro/GroundwaterServiceModelPage';
import RunoffSurfaceModelPage from '../pages/dashboard/hydro/RunoffSurfaceModelPage';
/* simulation */
import SimOrchestratorModelPage from '../pages/dashboard/simulation/SimOrchestratorModelPage';
import HecrasModelPage from '../pages/dashboard/simulation/HecrasModelPage';
import WeapModelPage from '../pages/dashboard/simulation/WeapModelPage';
import SimCalibrationModelPage from '../pages/dashboard/simulation/SimCalibrationModelPage';
import SimScenariosModelPage from '../pages/dashboard/simulation/SimScenariosModelPage';
import WeatherSourceModelPage from '../pages/dashboard/simulation/WeatherSourceModelPage';
/* carbon */
import CarbonCalculatorModelPage from '../pages/dashboard/carbon/CarbonCalculatorModelPage';
import MrvSatelliteModelPage from '../pages/dashboard/carbon/MrvSatelliteModelPage';
import MrvIotModelPage from '../pages/dashboard/carbon/MrvIotModelPage';
import MrvCitizenModelPage from '../pages/dashboard/carbon/MrvCitizenModelPage';
import MrvQaModelPage from '../pages/dashboard/carbon/MrvQaModelPage';
import MrvMetricsModelPage from '../pages/dashboard/carbon/MrvMetricsModelPage';
/* climate */
import EtCalculatorModelPage from '../pages/dashboard/climate/EtCalculatorModelPage';
import IrrigationSchedulerModelPage from '../pages/dashboard/climate/IrrigationSchedulerModelPage';
/* economics */
import EconAnalysisModelPage from '../pages/dashboard/economics/EconAnalysisModelPage';
import EconCostingModelPage from '../pages/dashboard/economics/EconCostingModelPage';
import EconRevenueModelPage from '../pages/dashboard/economics/EconRevenueModelPage';
import EconRoiModelPage from '../pages/dashboard/economics/EconRoiModelPage';
import EconEmploymentModelPage from '../pages/dashboard/economics/EconEmploymentModelPage';
import EconRiskModelPage from '../pages/dashboard/economics/EconRiskModelPage';
import EconIntegrationModelPage from '../pages/dashboard/economics/EconIntegrationModelPage';
import MultiObjectiveOptimizerModelPage from '../pages/dashboard/economics/MultiObjectiveOptimizerModelPage';
import DecisionSupportModelPage from '../pages/dashboard/economics/DecisionSupportModelPage';

export interface DashboardRoute {
  path: string;
  element: ReactElement;
}

export const dashboardRoutes: DashboardRoute[] = [
  { path: '', element: <DashboardHome /> },
  { path: 'profile', element: <ProfilePage /> },
  { path: 'settings', element: <SettingsPage /> },

  { path: 'models/ecsi', element: <EcsiModelPage /> },
  { path: 'models/epia', element: <EpiaModelPage /> },
  { path: 'models/esri', element: <EsriModelPage /> },
  { path: 'models/ewsi', element: <EwsiModelPage /> },
  { path: 'models/hdvi', element: <HdviModelPage /> },
  { path: 'models/hlhs', element: <HlhsModelPage /> },
  { path: 'models/hpheno', element: <HphenoModelPage /> },
  { path: 'models/hyrue', element: <HyrueModelPage /> },
  { path: 'models/runoff-model', element: <RunoffModelPage /> },

  { path: 'models/horton-infiltration', element: <HortonInfiltrationModelPage /> },
  { path: 'models/scs-cn-runoff', element: <ScsCnRunoffModelPage /> },
  { path: 'models/van-genuchten', element: <VanGenuchtenModelPage /> },
  { path: 'models/darcy-law', element: <DarcyLawModelPage /> },
  { path: 'models/manning-channel', element: <ManningChannelModelPage /> },
  { path: 'models/reynolds-number', element: <ReynoldsNumberModelPage /> },
  { path: 'models/froude-number', element: <FroudeNumberModelPage /> },
  { path: 'models/francis-weir', element: <FrancisWeirModelPage /> },
  { path: 'models/ring-storage', element: <RingStorageModelPage /> },
  { path: 'models/effective-porosity', element: <EffectivePorosityModelPage /> },

  { path: 'models/soil-texture', element: <SoilTextureModelPage /> },
  { path: 'models/soil-taxonomy', element: <SoilTaxonomyModelPage /> },
  { path: 'models/soil-water-retention', element: <SoilWaterRetentionModelPage /> },
  { path: 'models/pedotransfer', element: <PedotransferModelPage /> },
  { path: 'models/soil-physics', element: <SoilPhysicsModelPage /> },
  { path: 'models/soil-chemistry', element: <SoilChemistryModelPage /> },
  { path: 'models/soil-salinity', element: <SoilSalinityModelPage /> },
  { path: 'models/soil-health', element: <SoilHealthModelPage /> },
  { path: 'models/soil-recommendations', element: <SoilRecommendationsModelPage /> },

  { path: 'models/groundwater-model', element: <GroundwaterModelPage /> },
  { path: 'models/groundwater-service', element: <GroundwaterServiceModelPage /> },
  { path: 'models/runoff-surface', element: <RunoffSurfaceModelPage /> },

  { path: 'models/sim-orchestrator', element: <SimOrchestratorModelPage /> },
  { path: 'models/hecras', element: <HecrasModelPage /> },
  { path: 'models/weap', element: <WeapModelPage /> },
  { path: 'models/sim-calibration', element: <SimCalibrationModelPage /> },
  { path: 'models/sim-scenarios', element: <SimScenariosModelPage /> },
  { path: 'models/weather-source', element: <WeatherSourceModelPage /> },

  { path: 'models/carbon-calculator', element: <CarbonCalculatorModelPage /> },
  { path: 'models/mrv-satellite', element: <MrvSatelliteModelPage /> },
  { path: 'models/mrv-iot', element: <MrvIotModelPage /> },
  { path: 'models/mrv-citizen', element: <MrvCitizenModelPage /> },
  { path: 'models/mrv-qa', element: <MrvQaModelPage /> },
  { path: 'models/mrv-metrics', element: <MrvMetricsModelPage /> },

  { path: 'models/et-calculator', element: <EtCalculatorModelPage /> },
  { path: 'models/irrigation-scheduler', element: <IrrigationSchedulerModelPage /> },

  { path: 'models/econ-analysis', element: <EconAnalysisModelPage /> },
  { path: 'models/econ-costing', element: <EconCostingModelPage /> },
  { path: 'models/econ-revenue', element: <EconRevenueModelPage /> },
  { path: 'models/econ-roi', element: <EconRoiModelPage /> },
  { path: 'models/econ-employment', element: <EconEmploymentModelPage /> },
  { path: 'models/econ-risk', element: <EconRiskModelPage /> },
  { path: 'models/econ-integration', element: <EconIntegrationModelPage /> },
  { path: 'models/multi-objective-optimizer', element: <MultiObjectiveOptimizerModelPage /> },
  { path: 'models/decision-support', element: <DecisionSupportModelPage /> },
];

/** Fallback element used by the layout for unknown dashboard paths. */
export function DashboardUnknown() {
  return <ModelDetail modelId="__unknown__" />;
}
