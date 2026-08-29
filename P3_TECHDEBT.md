# 🧾 بدهی فنی: خطاهای typecheck (غیرمسدودکننده)

*استخراج از baseline — 2026-08-29 — لاگ کامل: _quarantine/p2/build_baseline.log*

اجرای دوره‌ای: `pnpm typecheck`

```text
src/App.tsx(8,3): error TS6133: 'AdminSecurity' is declared but its value is never read.
src/App.tsx(13,3): error TS6133: 'AdminContent' is declared but its value is never read.
src/App.tsx(56,7): error TS6133: 'HydromaDashboard' is declared but its value is never read.
src/App.tsx(57,7): error TS6133: 'SimulatorDashboard' is declared but its value is never read.
src/components/auth/ProtectedRoute.tsx(11,10): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/common/ErrorBoundary.tsx(5,8): error TS6133: 'React' is declared but its value is never read.
src/components/common/ErrorBoundary.tsx(5,28): error TS1484: 'ErrorInfo' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/common/ErrorBoundary.tsx(5,39): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/common/LoadingSpinner.test.tsx(7,1): error TS2593: Cannot find name 'test'. Do you need to install type definitions for a test runner? Try `npm i --save-dev @types/jest` or `npm i --save-dev @types/mocha` and then add 'jest' or 'mocha' to the types field in your tsconfig.
src/components/common/LoadingSpinner.test.tsx(9,3): error TS2304: Cannot find name 'expect'.
src/components/farmsim/SceneExtras.tsx(3,1): error TS6133: 'THREE' is declared but its value is never read.
src/components/simulators/ClimatePanel.tsx(1,10): error TS6133: 'useState' is declared but its value is never read.
src/components/simulators/CropsPanel.tsx(3,18): error TS6133: 'TreePine' is declared but its value is never read.
src/components/simulators/EngineeringOpsPanel.tsx(1,10): error TS6133: 'useState' is declared but its value is never read.
src/components/simulators/EngineeringOpsPanel.tsx(32,41): error TS6133: 'onMoveOperation' is declared but its value is never read.
src/components/simulators/EngineeringOpsPanel.tsx(33,3): error TS6133: 'onAddPolygon' is declared but its value is never read.
src/components/simulators/LayerPanel.tsx(3,31): error TS6133: 'Droplet' is declared but its value is never read.
src/components/simulators/LayerPanel.tsx(3,40): error TS6133: 'TreePine' is declared but its value is never read.
src/components/simulators/LayerPanel.tsx(3,50): error TS6133: 'Mountain' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(9,3): error TS6133: 'LineChart' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(9,14): error TS6133: 'Line' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(9,37): error TS6133: 'BarChart' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(9,47): error TS6133: 'Bar' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(10,62): error TS6133: 'Legend' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(14,35): error TS6133: 'Zap' is declared but its value is never read.
src/components/simulators/MotorSimulator.tsx(16,25): error TS1484: 'Motor' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/simulators/MotorSimulator.tsx(16,32): error TS1484: 'MotorParameter' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/components/simulators/OperationsPanel.tsx(21,81): error TS6133: 'terrain' is declared but its value is never read.
src/components/simulators/ViewControls.tsx(3,10): error TS6133: 'Box' is declared but its value is never read.
src/contexts/SimulationPipeline.tsx(7,47): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/i18n/LanguageContext.tsx(1,58): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/lib/RealDEM.ts(83,3): error TS6133: 'sizeKm' is declared but its value is never read.
src/pages/admin/AdminLayout.tsx(1,10): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/pages/admin/AdminSettings.tsx(5,16): error TS6133: 'Clock' is declared but its value is never read.
src/pages/admin/AdminSettings.tsx(5,29): error TS6133: 'Users' is declared but its value is never read.
src/pages/admin/AdminSettings.tsx(6,17): error TS6133: 'XCircle' is declared but its value is never read.
src/pages/admin/AdminSettings.tsx(6,26): error TS6133: 'AlertCircle' is declared but its value is never read.
src/pages/admin/AdminSettings.tsx(6,50): error TS6133: 'Palette' is declared but its value is never read.
src/pages/admin/AIModelsMonitor.tsx(3,10): error TS6133: 'Cpu' is declared but its value is never read.
src/pages/admin/AIModelsMonitor.tsx(4,25): error TS6133: 'AlertCircle' is declared but its value is never read.
src/pages/admin/AIModelsMonitor.tsx(4,38): error TS6133: 'TrendingUp' is declared but its value is never read.
src/pages/admin/AIModelsMonitor.tsx(4,50): error TS6133: 'Clock' is declared but its value is never read.
src/pages/admin/BotsManagement.tsx(3,8): error TS6133: 'Power' is declared but its value is never read.
src/pages/admin/BotsManagement.tsx(3,25): error TS6133: 'Clock' is declared but its value is never read.
src/pages/admin/BotsManagement.tsx(3,32): error TS6133: 'Zap' is declared but its value is never read.
src/pages/admin/BotsManagement.tsx(4,35): error TS6133: 'AlertCircle' is declared but its value is never read.
src/pages/admin/BotsManagement.tsx(34,41): error TS6133: 'currentStatus' is declared but its value is never read.
src/pages/admin/ContentStudio.tsx(3,41): error TS6133: 'Clock' is declared but its value is never read.
src/pages/admin/ContentStudio.tsx(3,48): error TS6133: 'CheckCircle' is declared but its value is never read.
src/pages/admin/ContentStudio.tsx(4,3): error TS6133: 'AlertCircle' is declared but its value is never read.
src/pages/admin/ContentStudio.tsx(5,3): error TS6133: 'History' is declared but its value is never read.
src/pages/admin/ContentStudio.tsx(5,33): error TS6133: 'XCircle' is declared but its value is never read.
src/pages/admin/ContentStudio.tsx(5,42): error TS6133: 'Zap' is declared but its value is never read.
src/pages/admin/crypto/CryptoPaymentWidget.tsx(5,36): error TS6133: 'ExternalLink' is declared but its value is never read.
src/pages/admin/crypto/CryptoPaymentWidget.tsx(35,10): error TS6133: 'lastUpdate' is declared but its value is never read.
src/pages/admin/EcoWalletDashboard.tsx(8,23): error TS6133: 'TrendingDown' is declared but its value is never read.
src/pages/admin/EcoWalletDashboard.tsx(9,3): error TS6133: 'Users' is declared but its value is never read.
src/pages/admin/EcoWalletDashboard.tsx(10,23): error TS6133: 'CheckCircle' is declared but its value is never read.
src/pages/admin/EcoWalletDashboard.tsx(60,10): error TS6133: 'error' is declared but its value is never read.
src/pages/admin/HyDroMa3D.tsx(6,10): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/pages/admin/HyDroMa3D.tsx(90,18): error TS2304: Cannot find name 'ref'.
src/pages/admin/HyDroMa3D.tsx(280,65): error TS2304: Cannot find name 'off'.
src/pages/admin/HyDroMa3D.tsx(339,10): error TS6133: 'aiStatus' is declared but its value is never read.
src/pages/admin/live/useLiveMetrics.ts(21,9): error TS6133: 'eventSourceRef' is declared but its value is never read.
src/pages/admin/LiveDashboard.tsx(1,1): error TS6192: All imports in import declaration are unused.
src/pages/admin/LiveDashboard.tsx(12,11): error TS6133: 'Shield' is declared but its value is never read.
src/pages/admin/LiveDashboard.tsx(12,24): error TS6133: 'TrendingUp' is declared but its value is never read.
src/pages/admin/LiveDashboard.tsx(13,3): error TS6133: 'Cpu' is declared but its value is never read.
src/pages/admin/LiveDashboard.tsx(13,8): error TS6133: 'HardDrive' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(3,3): error TS6133: 'BarChart' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(3,13): error TS6133: 'Bar' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(3,18): error TS6133: 'LineChart' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(3,29): error TS6133: 'Line' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(4,3): error TS6133: 'XAxis' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(4,10): error TS6133: 'YAxis' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(4,17): error TS6133: 'CartesianGrid' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(4,62): error TS6133: 'Legend' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(7,37): error TS6133: 'Users' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(8,23): error TS6133: 'XCircle' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(9,3): error TS6133: 'MapPin' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(19,10): error TS6133: 'stats' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(98,9): error TS6133: 'completedOrders' is declared but its value is never read.
src/pages/admin/MarketplaceDashboard.tsx(198,31): error TS6133: 'entry' is declared but its value is never read.
src/pages/admin/MotorRunner.tsx(5,7): error TS6133: 'API_BASE' is declared but its value is never read.
src/pages/admin/MotorRunner.tsx(150,90): error TS2339: Property 'elevation_m' does not exist on type 'SiteRow'.
src/pages/admin/SecurityAdvanced.tsx(3,3): error TS6133: 'LineChart' is declared but its value is never read.
src/pages/admin/SecurityAdvanced.tsx(3,14): error TS6133: 'Line' is declared but its value is never read.
src/pages/admin/SecurityAdvanced.tsx(7,26): error TS6133: 'Lock' is declared but its value is never read.
src/pages/admin/SecurityAdvanced.tsx(7,32): error TS6133: 'Unlock' is declared but its value is never read.
src/pages/admin/SecurityAdvanced.tsx(7,45): error TS6133: 'EyeOff' is declared but its value is never read.
src/pages/admin/SecurityAdvanced.tsx(9,23): error TS6133: 'Fingerprint' is declared but its value is never read.
src/pages/admin/telegram/TelegramManager.tsx(4,36): error TS6133: 'Power' is declared but its value is never read.
src/pages/admin/telegram/TelegramManager.tsx(5,40): error TS6133: 'Globe' is declared but its value is never read.
src/pages/admin/telegram/TelegramManager.tsx(6,16): error TS6133: 'Clock' is declared but its value is never read.
src/pages/admin/ThemeContext.tsx(1,58): error TS1484: 'ReactNode' is a type and must be imported using a type-only import when 'verbatimModuleSyntax' is enabled.
src/pages/HyDroMaCenter.tsx(1,20): error TS6133: 'useRef' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(2,28): error TS6133: 'useFrame' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(3,36): error TS6133: 'PerspectiveCamera' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(3,67): error TS6133: 'useTexture' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(7,13): error TS6133: 'Play' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(7,19): error TS6133: 'Pause' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(7,26): error TS6133: 'GitCompare' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(7,38): error TS6133: 'FileText' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(7,48): error TS6133: 'Loader2' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,3): error TS6133: 'Activity' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,13): error TS6133: 'Cpu' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,18): error TS6133: 'Layers' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,26): error TS6133: 'TreePine' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,36): error TS6133: 'Cloud' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,43): error TS6133: 'Sun' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(8,48): error TS6133: 'Hammer' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(9,3): error TS6133: 'Tractor' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(9,20): error TS6133: 'Pencil' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(9,36): error TS6133: 'Plus' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(14,10): error TS6133: 'generateTerrain' is declared but its value is never read.
src/pages/HyDroMaCenter.tsx(391,35): error TS2345: Argument of type 'TerrainData | null' is not assignable to parameter of type 'TerrainData'.
src/pages/Visualization3D.tsx(11,39): error TS6133: 'Suspense' is declared but its value is never read.
src/pages/Visualization3D.tsx(13,36): error TS6133: 'Text' is declared but its value is never read.
src/pages/Visualization3D.tsx(16,35): error TS6133: 'Info' is declared but its value is never read.
src/pages/Visualization3D.tsx(17,18): error TS6133: 'Play' is declared but its value is never read.
src/pages/Visualization3D.tsx(17,35): error TS6133: 'Maximize2' is declared but its value is never read.
src/pages/Visualization3D.tsx(18,37): error TS6133: 'EyeOff' is declared but its value is never read.
src/pages/Visualization3D.tsx(19,3): error TS6133: 'Download' is declared but its value is never read.
src/pages/Visualization3D.tsx(19,13): error TS6133: 'Share2' is declared but its value is never read.
src/pages/Visualization3D.tsx(20,3): error TS6133: 'Thermometer' is declared but its value is never read.
src/pages/Visualization3D.tsx(20,16): error TS6133: 'Sun' is declared but its value is never read.
src/pages/Visualization3D.tsx(20,21): error TS6133: 'Cloud' is declared but its value is never read.
src/pages/Visualization3D.tsx(20,28): error TS6133: 'Wind' is declared but its value is never read.
src/pages/Visualization3D.tsx(20,34): error TS6133: 'Zap' is declared but its value is never read.
src/pages/Visualization3D.tsx(21,38): error TS6133: 'PieChartIcon' is declared but its value is never read.
src/pages/Visualization3D.tsx(65,9): error TS6198: All destructured elements are unused.
src/pages/Visualization3D.tsx(246,19): error TS2322: Type '{ children: Element; geometry: BufferGeometry<NormalBufferAttributes, BufferGeometryEventMap>; }' is not assignable to type 'SVGLineElementAttributes<SVGLineElement>'.
src/pages/Visualization3D.tsx(302,10): error TS6133: 'error' is declared but its value is never read.
src/services/scientificChainApi.ts(23,3): error TS6133: 'onProgress' is declared but its value is never read.
src/test/smoke.test.tsx(1,10): error TS6133: 'render' is declared but its value is never read.
src/test/smoke.test.tsx(4,1): error TS2593: Cannot find name 'test'. Do you need to install type definitions for a test runner? Try `npm i --save-dev @types/jest` or `npm i --save-dev @types/mocha` and then add 'jest' or 'mocha' to the types field in your tsconfig.
src/test/smoke.test.tsx(5,3): error TS2304: Cannot find name 'expect'.
src/test/smoke.test.tsx(8,1): error TS2593: Cannot find name 'test'. Do you need to install type definitions for a test runner? Try `npm i --save-dev @types/jest` or `npm i --save-dev @types/mocha` and then add 'jest' or 'mocha' to the types field in your tsconfig.
src/test/smoke.test.tsx(12,3): error TS2304: Cannot find name 'expect'.
```
#### پیشنهاد رفع:
- فایل‌های `*.test.tsx` از tsconfig build خارج شوند + `import {test, expect} from 'vitest'`
- ایمپورت‌های بلااستفاده (TS6133) حذف شوند
- `<line geometry>` در Visualization3D → `<primitive object={new THREE.Line(...)}>`
