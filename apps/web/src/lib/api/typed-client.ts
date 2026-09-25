import {
  type AnalyzeRequest,
  aiHealthApiV1AiHealthGet,
  type aiHealthApiV1AiHealthGetResponse,
  analyzeLandApiV1PlatformAnalyzePost,
  type analyzeLandApiV1PlatformAnalyzePostResponse,
  analyzeSatelliteApiV1SatelliteAnalyzePost,
  type analyzeSatelliteApiV1SatelliteAnalyzePostResponse,
  analyzeSoilApiV1SoilAnalyzePost,
  type analyzeSoilApiV1SoilAnalyzePostResponse,
  applyScenarioApiV1ScenariosApplyPost,
  type applyScenarioApiV1ScenariosApplyPostResponse,
  type ChatRequest,
  // AI endpoints
  chatApiV1AiChatPost,
  type chatApiV1AiChatPostResponse,
  compareScenariosApiV1ScenariosCompareFarmIdGet,
  type compareScenariosApiV1ScenariosCompareFarmIdGetResponse,
  cppStatusApiV1ModelsCppStatusGet,
  type cppStatusApiV1ModelsCppStatusGetResponse,
  type GenerateDraftApiV1AdminContentGenerateDraftPostParams,
  type GetHistoryApiV1AiHistoryGetParams,
  generateDraftApiV1AdminContentGenerateDraftPost,
  type generateDraftApiV1AdminContentGenerateDraftPostResponse,
  getHistoryApiV1AiHistoryGet,
  type getHistoryApiV1AiHistoryGetResponse,
  getScenarioImpactApiV1AnalyticsScenarioImpactGet,
  type getScenarioImpactApiV1AnalyticsScenarioImpactGetResponse,
  type IVRCallIn,
  type IVRDTMFIn,
  type IVRSMSIn,
  type IVRStartIn,
  ivrCallApiV1VoiceIvrCallPost,
  type ivrCallApiV1VoiceIvrCallPostResponse,
  ivrDtmfApiV1VoiceIvrDtmfPost,
  type ivrDtmfApiV1VoiceIvrDtmfPostResponse,
  ivrMenuPreviewApiV1VoiceIvrMenuLanguageGet,
  type ivrMenuPreviewApiV1VoiceIvrMenuLanguageGetResponse,
  ivrSmsApiV1VoiceIvrSmsPost,
  type ivrSmsApiV1VoiceIvrSmsPostResponse,
  ivrStartApiV1VoiceIvrStartPost,
  type ivrStartApiV1VoiceIvrStartPostResponse,
  listLandscapesApiV1PlatformLandscapesGet,
  type listLandscapesApiV1PlatformLandscapesGetResponse,
  listModelsApiV1HydromaModelsGet,
  type listModelsApiV1HydromaModelsGetResponse,
  listProductsApiV1MarketplaceProductsGet,
  type listProductsApiV1MarketplaceProductsGetResponse,
  marketplaceStatsApiV1MarketplaceStatsGet,
  type marketplaceStatsApiV1MarketplaceStatsGetResponse,
  platformHealthApiV1PlatformHealthGet,
  type platformHealthApiV1PlatformHealthGetResponse,
  platformStatsApiV1PlatformStatsGet,
  type platformStatsApiV1PlatformStatsGetResponse,
  realLandAnalysisApiV1SatelliteRealLandPost,
  type realLandAnalysisApiV1SatelliteRealLandPostResponse,
  type SatelliteAnalyzeRequest,
  type ServicesApiGatewayRoutersScenariosScenarioRequest,
  type SoilAnalysisRequest,
  speechToTextApiV1VoiceSttPost,
  streamChatApiV1AiStreamPost,
  type streamChatApiV1AiStreamPostResponse,
  textToSpeechApiV1AiVoiceTtsPost,
  type textToSpeechApiV1AiVoiceTtsPostResponse,
  textToSpeechApiV1VoiceTtsPost,
  voiceAskApiV1VoiceAskPost,
  voiceHealthApiV1VoiceHealthGet,
  voiceLanguagesApiV1VoiceLanguagesGet,
} from '@eco/api-client';

// Thin namespace over the Orval-generated client (@eco/api-client).
// Every function hits the real API gateway — no mock layer exists.
export const api = {
  platform: {
    health: () => platformHealthApiV1PlatformHealthGet(),
    stats: () => platformStatsApiV1PlatformStatsGet(),
    landscapes: () => listLandscapesApiV1PlatformLandscapesGet(),
  },
  hydroma: {
    models: () => listModelsApiV1HydromaModelsGet(),
    cppStatus: () => cppStatusApiV1ModelsCppStatusGet(),
  },
  marketplace: {
    products: () => listProductsApiV1MarketplaceProductsGet(),
    stats: () => marketplaceStatsApiV1MarketplaceStatsGet(),
  },
  ai: {
    // Chat
    chat: (request: ChatRequest) => chatApiV1AiChatPost(request),
    streamChat: (request: ChatRequest) => streamChatApiV1AiStreamPost(request),
    health: () => aiHealthApiV1AiHealthGet(),
    history: (params?: GetHistoryApiV1AiHistoryGetParams) => getHistoryApiV1AiHistoryGet(params),

    // Voice / TTS (OpenAI-compatible endpoints under /api/v1/ai/voice)
    tts: (request: ChatRequest) => textToSpeechApiV1AiVoiceTtsPost(request),
    voiceAsk: (request: { question: string; language?: 'en' | 'fa' | 'ar' }) =>
      voiceAskApiV1VoiceAskPost(request),
    voiceHealth: () => voiceHealthApiV1VoiceHealthGet(),
    voiceLanguages: () => voiceLanguagesApiV1VoiceLanguagesGet(),

    // Voice (IVR/STT/TTS under /api/v1/voice)
    ttsVoice: (request: { text: string; language?: 'en' | 'fa' | 'ar' }) =>
      textToSpeechApiV1VoiceTtsPost(request),
    sttVoice: (request: { audio_base64: string; language?: 'en' | 'fa' | 'ar' }) =>
      speechToTextApiV1VoiceSttPost(request),

    // Scenarios
    applyScenario: (request: ServicesApiGatewayRoutersScenariosScenarioRequest) =>
      applyScenarioApiV1ScenariosApplyPost(request),
    compareScenarios: (farmId: number) => compareScenariosApiV1ScenariosCompareFarmIdGet(farmId),
    scenarioImpact: () => getScenarioImpactApiV1AnalyticsScenarioImpactGet(),

    // Analysis
    analyzeLand: (request: AnalyzeRequest) => analyzeLandApiV1PlatformAnalyzePost(request),
    analyzeSoil: (request: SoilAnalysisRequest) => analyzeSoilApiV1SoilAnalyzePost(request),
    analyzeSatellite: (request: SatelliteAnalyzeRequest) =>
      analyzeSatelliteApiV1SatelliteAnalyzePost(request),
    realLandAnalysis: (request: SatelliteAnalyzeRequest) =>
      realLandAnalysisApiV1SatelliteRealLandPost(request),

    // Content generation
    generateDraft: (params: GenerateDraftApiV1AdminContentGenerateDraftPostParams) =>
      generateDraftApiV1AdminContentGenerateDraftPost(params),

    // IVR
    ivrStart: (request: {
      session_id: string;
      phone_number: string;
      language?: 'en' | 'fa' | 'ar';
    }) => ivrStartApiV1VoiceIvrStartPost(request),
    ivrDtmf: (request: { session_id: string; digit: string }) =>
      ivrDtmfApiV1VoiceIvrDtmfPost(request),
    ivrMenu: (language: 'en' | 'fa' | 'ar') => ivrMenuPreviewApiV1VoiceIvrMenuLanguageGet(language),
    ivrCall: (request: {
      phone_number: string;
      twiml?: string;
      menu_language?: 'en' | 'fa' | 'ar';
    }) => ivrCallApiV1VoiceIvrCallPost(request),
    ivrSms: (request: { to: string; body: string }) => ivrSmsApiV1VoiceIvrSmsPost(request),
  },
};

export type {
  AnalyzeRequest,
  aiHealthApiV1AiHealthGetResponse as AiHealth,
  analyzeLandApiV1PlatformAnalyzePostResponse as AnalyzeLandResponse,
  analyzeSatelliteApiV1SatelliteAnalyzePostResponse as AnalyzeSatelliteResponse,
  analyzeSoilApiV1SoilAnalyzePostResponse as AnalyzeSoilResponse,
  applyScenarioApiV1ScenariosApplyPostResponse as ApplyScenarioResponse,
  // AI types
  ChatRequest,
  chatApiV1AiChatPostResponse as AiChatResponse,
  compareScenariosApiV1ScenariosCompareFarmIdGetResponse as CompareScenariosResponse,
  cppStatusApiV1ModelsCppStatusGetResponse as CppStatus,
  GenerateDraftApiV1AdminContentGenerateDraftPostParams,
  GetHistoryApiV1AiHistoryGetParams,
  generateDraftApiV1AdminContentGenerateDraftPostResponse as GenerateDraftResponse,
  getHistoryApiV1AiHistoryGetResponse as AiHistory,
  getScenarioImpactApiV1AnalyticsScenarioImpactGetResponse as ScenarioImpact,
  IVRCallIn,
  IVRDTMFIn,
  IVRSMSIn,
  IVRStartIn,
  ivrCallApiV1VoiceIvrCallPostResponse as IVRCallResponse,
  ivrDtmfApiV1VoiceIvrDtmfPostResponse as IVRDTMFResponse,
  ivrMenuPreviewApiV1VoiceIvrMenuLanguageGetResponse as IVRMenuResponse,
  ivrSmsApiV1VoiceIvrSmsPostResponse as IVRSMSResponse,
  ivrStartApiV1VoiceIvrStartPostResponse as IVRStartResponse,
  listLandscapesApiV1PlatformLandscapesGetResponse as Landscapes,
  listModelsApiV1HydromaModelsGetResponse as HydromaModels,
  listProductsApiV1MarketplaceProductsGetResponse as MarketplaceProducts,
  marketplaceStatsApiV1MarketplaceStatsGetResponse as MarketplaceStats,
  platformHealthApiV1PlatformHealthGetResponse as PlatformHealth,
  platformStatsApiV1PlatformStatsGetResponse as PlatformStats,
  realLandAnalysisApiV1SatelliteRealLandPostResponse as RealLandAnalysisResponse,
  SatelliteAnalyzeRequest,
  SoilAnalysisRequest,
  streamChatApiV1AiStreamPostResponse as AiStreamChatResponse,
  textToSpeechApiV1AiVoiceTtsPostResponse as AiTtsResponse,
};
