import { apiGet } from '@/lib/api/client';

interface ProvenanceStamp {
  source: string;
  verified?: boolean;
  timestamp?: string;
  method?: string;
}

interface ServiceStatus {
  id: string;
  name: string;
  status: 'operational' | 'degraded' | 'maintenance' | 'offline';
  latencyMs?: number;
  lastCheck: string;
  provenance: ProvenanceStamp;
}

interface ServiceOverview {
  services: ServiceStatus[];
  summary: {
    total: number;
    operational: number;
    degraded: number;
    offline: number;
  };
  provenance: ProvenanceStamp;
}

interface ScienceEvidence {
  id: string;
  title: string;
  doi?: string;
  authors: string[];
  year: number;
  journal?: string;
  summary: string;
  verificationStatus: 'peer-reviewed' | 'preprint' | 'internal' | 'validated';
  provenance: ProvenanceStamp;
}

interface Methodology {
  id: string;
  name: string;
  standard: 'FAO' | 'IPCC' | 'OGC' | 'ISO' | 'custom';
  version: string;
  description: string;
  complianceLevel: 'full' | 'partial' | 'reference';
  provenance: ProvenanceStamp;
}

interface ValidationResult {
  id: string;
  modelId: string;
  metric: string;
  value: number;
  threshold: number;
  passed: boolean;
  provenance: ProvenanceStamp;
}

interface UncertaintyQuantification {
  parameter: string;
  distribution: 'normal' | 'lognormal' | 'uniform' | 'triangular' | 'empirical';
  mean: number;
  stdDev?: number;
  min?: number;
  max?: number;
  confidenceInterval: [number, number];
  provenance: ProvenanceStamp;
}

interface ReproducibilityRecord {
  runId: string;
  modelVersion: string;
  inputsHash: string;
  outputsHash: string;
  environment: Record<string, string>;
  timestamp: string;
  provenance: ProvenanceStamp;
}

interface DataSource {
  id: string;
  name: string;
  provider: string;
  type: 'satellite' | 'weather' | 'soil' | 'hydrology' | 'carbon' | 'socioeconomic' | 'other';
  coverage: string;
  resolution: string;
  frequency: string;
  license: string;
  accessUrl?: string;
  provenance: ProvenanceStamp;
}

interface EducationResource {
  id: string;
  title: string;
  type: 'article' | 'video' | 'course' | 'glossary' | 'workshop' | 'certification';
  language: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  duration?: string;
  description: string;
  tags: string[];
  url?: string;
  provenance: ProvenanceStamp;
}

interface Course {
  id: string;
  title: string;
  description: string;
  language: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  duration: string;
  modules: CourseModule[];
  certificationId?: string;
  provenance: ProvenanceStamp;
}

interface CourseModule {
  id: string;
  title: string;
  description: string;
  duration: string;
  resources: EducationResource[];
}

interface VideoContent {
  id: string;
  title: string;
  description: string;
  duration: string;
  language: string;
  subtitles: string[];
  thumbnailUrl: string;
  videoUrl: string;
  transcript?: string;
  provenance: ProvenanceStamp;
}

interface GlossaryTerm {
  id: string;
  term: string;
  definition: Record<string, string>;
  category: string;
  relatedTerms: string[];
  provenance: ProvenanceStamp;
}

interface Certification {
  id: string;
  name: string;
  description: string;
  requirements: string[];
  validityPeriod: string;
  issuer: string;
  provenance: ProvenanceStamp;
}

interface Workshop {
  id: string;
  title: string;
  description: string;
  date: string;
  duration: string;
  location: string;
  language: string;
  capacity: number;
  registered: number;
  topics: string[];
  provenance: ProvenanceStamp;
}

interface PolicyDocument {
  id: string;
  title: string;
  version: string;
  effectiveDate: string;
  content: string;
  diffFromPrevious?: string;
  languages: string[];
  provenance: ProvenanceStamp;
}

interface ComponentDemo {
  id: string;
  name: string;
  description: string;
  type: 'hydroma-engine' | 'marketplace' | 'ecowallet' | 'mrv-dashboard' | 'satellite-view' | 'dispute-resolution' | 'land-profiler' | 'api-playground';
  status: 'live' | 'demo' | 'development';
  embedUrl?: string;
  documentationUrl?: string;
  provenance: ProvenanceStamp;
}

interface ApiEndpoint {
  path: string;
  method: string;
  summary: string;
  description: string;
  parameters: ApiParameter[];
  responses: ApiResponse[];
  authentication: boolean;
  rateLimit?: string;
  provenance: ProvenanceStamp;
}

interface ApiParameter {
  name: string;
  in: 'query' | 'path' | 'header' | 'cookie';
  required: boolean;
  schema: Record<string, unknown>;
  description: string;
}

interface ApiResponse {
  status: number;
  description: string;
  schema?: Record<string, unknown>;
}

const API_BASE =
  process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

export const publicApi = {
  services: {
    overview: (): Promise<{ ok: boolean; data: ServiceOverview; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ServiceOverview>('/api/v1/public/services/overview'),
    status: (serviceId: string): Promise<{ ok: boolean; data: ServiceOverview['services'][0]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ServiceOverview['services'][0]>(`/api/v1/public/services/${serviceId}/status`),
    list: (): Promise<{ ok: boolean; data: ServiceOverview['services']; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ServiceOverview['services']>('/api/v1/public/services'),
  },

  science: {
    evidenceBase: (): Promise<{ ok: boolean; data: ScienceEvidence[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ScienceEvidence[]>('/api/v1/public/science/evidence-base'),
    methodology: (): Promise<{ ok: boolean; data: Methodology[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<Methodology[]>('/api/v1/public/science/methodology'),
    validation: (modelId?: string): Promise<{ ok: boolean; data: ValidationResult[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ValidationResult[]>(modelId ? `/api/v1/public/science/validation?model_id=${modelId}` : '/api/v1/public/science/validation'),
    uncertainty: (): Promise<{ ok: boolean; data: UncertaintyQuantification[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<UncertaintyQuantification[]>('/api/v1/public/science/uncertainty'),
    reproducibility: (): Promise<{ ok: boolean; data: ReproducibilityRecord[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ReproducibilityRecord[]>('/api/v1/public/science/reproducibility'),
    dataSources: (): Promise<{ ok: boolean; data: DataSource[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<DataSource[]>('/api/v1/public/science/data-sources'),
  },

  education: {
    library: (params?: { language?: string; level?: string; type?: string }): Promise<{ ok: boolean; data: EducationResource[]; status: number } | { ok: false; error: string; status: number }> => {
      const search = new URLSearchParams();
      if (params?.language) search.set('language', params.language);
      if (params?.level) search.set('level', params.level);
      if (params?.type) search.set('type', params.type);
      return apiGet<EducationResource[]>(`/api/v1/public/education/library?${search.toString()}`);
    },
    courses: (language?: string): Promise<{ ok: boolean; data: Course[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<Course[]>(language ? `/api/v1/public/education/courses?language=${language}` : '/api/v1/public/education/courses'),
    video: (id: string): Promise<{ ok: boolean; data: VideoContent; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<VideoContent>(`/api/v1/public/education/video/${id}`),
    videos: (language?: string): Promise<{ ok: boolean; data: VideoContent[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<VideoContent[]>(language ? `/api/v1/public/education/videos?language=${language}` : '/api/v1/public/education/videos'),
    glossary: (params?: { language?: string; category?: string; search?: string }): Promise<{ ok: boolean; data: GlossaryTerm[]; status: number } | { ok: false; error: string; status: number }> => {
      const search = new URLSearchParams();
      if (params?.language) search.set('language', params.language);
      if (params?.category) search.set('category', params.category);
      if (params?.search) search.set('search', params.search);
      return apiGet<GlossaryTerm[]>(`/api/v1/public/education/glossary?${search.toString()}`);
    },
    certifications: (): Promise<{ ok: boolean; data: Certification[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<Certification[]>('/api/v1/public/education/certifications'),
    workshops: (params?: { upcoming?: boolean; language?: string }): Promise<{ ok: boolean; data: Workshop[]; status: number } | { ok: false; error: string; status: number }> => {
      const search = new URLSearchParams();
      if (params?.upcoming) search.set('upcoming', 'true');
      if (params?.language) search.set('language', params.language);
      return apiGet<Workshop[]>(`/api/v1/public/education/workshops?${search.toString()}`);
    },
  },

  policy: {
    terms: (version?: string): Promise<{ ok: boolean; data: PolicyDocument; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument>(version ? `/api/v1/public/policy/terms?version=${version}` : '/api/v1/public/policy/terms'),
    privacy: (): Promise<{ ok: boolean; data: PolicyDocument; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument>('/api/v1/public/policy/privacy'),
    cookies: (): Promise<{ ok: boolean; data: PolicyDocument; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument>('/api/v1/public/policy/cookies'),
    accessibility: (): Promise<{ ok: boolean; data: PolicyDocument; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument>('/api/v1/public/policy/accessibility'),
    licensing: (): Promise<{ ok: boolean; data: PolicyDocument; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument>('/api/v1/public/policy/licensing'),
    governance: (): Promise<{ ok: boolean; data: PolicyDocument; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument>('/api/v1/public/policy/governance'),
    versions: (documentId: string): Promise<{ ok: boolean; data: PolicyDocument[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<PolicyDocument[]>(`/api/v1/public/policy/${documentId}/versions`),
  },

  components: {
    hydromaEngine: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/hydroma-engine'),
    marketplace: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/marketplace'),
    ecowallet: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/ecowallet'),
    mrvDashboard: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/mrv-dashboard'),
    satelliteView: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/satellite-view'),
    disputeResolution: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/dispute-resolution'),
    landProfiler: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/land-profiler'),
    apiPlayground: (): Promise<{ ok: boolean; data: ComponentDemo; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo>('/api/v1/public/components/api-playground'),
    list: (): Promise<{ ok: boolean; data: ComponentDemo[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ComponentDemo[]>('/api/v1/public/components'),
  },

  api: {
    endpoints: (): Promise<{ ok: boolean; data: ApiEndpoint[]; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<ApiEndpoint[]>('/api/v1/public/api/endpoints'),
    schema: (): Promise<{ ok: boolean; data: Record<string, unknown>; status: number } | { ok: false; error: string; status: number }> =>
      apiGet<Record<string, unknown>>('/api/v1/public/api/schema'),
  },
};

export type {
  ServiceOverview,
  ScienceEvidence,
  Methodology,
  ValidationResult,
  UncertaintyQuantification,
  ReproducibilityRecord,
  DataSource,
  EducationResource,
  Course,
  VideoContent,
  GlossaryTerm,
  Certification,
  Workshop,
  PolicyDocument,
  ComponentDemo,
  ApiEndpoint,
};