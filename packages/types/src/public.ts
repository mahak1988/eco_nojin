import { z } from 'zod';

export interface ProvenanceStamp {
  source: string;
  verified?: boolean;
  timestamp?: string;
  method?: string;
}

export interface PublicPageMeta {
  title: string;
  description: string;
  provenance: ProvenanceStamp[];
}

export interface ServiceStatus {
  id: string;
  name: string;
  status: 'operational' | 'degraded' | 'maintenance' | 'offline';
  latencyMs?: number;
  lastCheck: string;
  provenance: ProvenanceStamp;
}

export interface ServiceOverview {
  services: ServiceStatus[];
  summary: {
    total: number;
    operational: number;
    degraded: number;
    offline: number;
  };
  provenance: ProvenanceStamp;
}

export interface ScienceEvidence {
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

export interface Methodology {
  id: string;
  name: string;
  standard: 'FAO' | 'IPCC' | 'OGC' | 'ISO' | 'custom';
  version: string;
  description: string;
  complianceLevel: 'full' | 'partial' | 'reference';
  provenance: ProvenanceStamp;
}

export interface ValidationResult {
  id: string;
  modelId: string;
  metric: string;
  value: number;
  threshold: number;
  passed: boolean;
  provenance: ProvenanceStamp;
}

export interface UncertaintyQuantification {
  parameter: string;
  distribution: 'normal' | 'lognormal' | 'uniform' | 'triangular' | 'empirical';
  mean: number;
  stdDev?: number;
  min?: number;
  max?: number;
  confidenceInterval: [number, number];
  provenance: ProvenanceStamp;
}

export interface ReproducibilityRecord {
  runId: string;
  modelVersion: string;
  inputsHash: string;
  outputsHash: string;
  environment: Record<string, string>;
  timestamp: string;
  provenance: ProvenanceStamp;
}

export interface DataSource {
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

export interface EducationResource {
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

export interface Course {
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

export interface CourseModule {
  id: string;
  title: string;
  description: string;
  duration: string;
  resources: EducationResource[];
}

export interface VideoContent {
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

export interface GlossaryTerm {
  id: string;
  term: string;
  definition: Record<string, string>;
  category: string;
  relatedTerms: string[];
  provenance: ProvenanceStamp;
}

export interface Certification {
  id: string;
  name: string;
  description: string;
  requirements: string[];
  validityPeriod: string;
  issuer: string;
  provenance: ProvenanceStamp;
}

export interface Workshop {
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

export interface PolicyDocument {
  id: string;
  title: string;
  version: string;
  effectiveDate: string;
  content: string;
  diffFromPrevious?: string;
  languages: string[];
  provenance: ProvenanceStamp;
}

export interface ComponentDemo {
  id: string;
  name: string;
  description: string;
  type: 'hydroma-engine' | 'marketplace' | 'ecowallet' | 'mrv-dashboard' | 'satellite-view' | 'dispute-resolution' | 'land-profiler' | 'api-playground';
  status: 'live' | 'demo' | 'development';
  embedUrl?: string;
  documentationUrl?: string;
  provenance: ProvenanceStamp;
}

export interface ApiEndpoint {
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

export interface ApiParameter {
  name: string;
  in: 'query' | 'path' | 'header' | 'cookie';
  required: boolean;
  schema: Record<string, unknown>;
  description: string;
}

export interface ApiResponse {
  status: number;
  description: string;
  schema?: Record<string, unknown>;
}

export const ProvenanceStampSchema = z.object({
  source: z.string(),
  verified: z.boolean().optional(),
  timestamp: z.string().optional(),
  method: z.string().optional(),
});

export const ServiceStatusSchema = z.object({
  id: z.string(),
  name: z.string(),
  status: z.enum(['operational', 'degraded', 'maintenance', 'offline']),
  latencyMs: z.number().optional(),
  lastCheck: z.string(),
  provenance: ProvenanceStampSchema,
});

export const ServiceOverviewSchema = z.object({
  services: z.array(ServiceStatusSchema),
  summary: z.object({
    total: z.number(),
    operational: z.number(),
    degraded: z.number(),
    offline: z.number(),
  }),
  provenance: ProvenanceStampSchema,
});

export const ScienceEvidenceSchema = z.object({
  id: z.string(),
  title: z.string(),
  doi: z.string().optional(),
  authors: z.array(z.string()),
  year: z.number(),
  journal: z.string().optional(),
  summary: z.string(),
  verificationStatus: z.enum(['peer-reviewed', 'preprint', 'internal', 'validated']),
  provenance: ProvenanceStampSchema,
});

export const MethodologySchema = z.object({
  id: z.string(),
  name: z.string(),
  standard: z.enum(['FAO', 'IPCC', 'OGC', 'ISO', 'custom']),
  version: z.string(),
  description: z.string(),
  complianceLevel: z.enum(['full', 'partial', 'reference']),
  provenance: ProvenanceStampSchema,
});

export const ValidationResultSchema = z.object({
  id: z.string(),
  modelId: z.string(),
  metric: z.string(),
  value: z.number(),
  threshold: z.number(),
  passed: z.boolean(),
  provenance: ProvenanceStampSchema,
});

export const UncertaintyQuantificationSchema = z.object({
  parameter: z.string(),
  distribution: z.enum(['normal', 'lognormal', 'uniform', 'triangular', 'empirical']),
  mean: z.number(),
  stdDev: z.number().optional(),
  min: z.number().optional(),
  max: z.number().optional(),
  confidenceInterval: z.tuple([z.number(), z.number()]),
  provenance: ProvenanceStampSchema,
});

export const ReproducibilityRecordSchema = z.object({
  runId: z.string(),
  modelVersion: z.string(),
  inputsHash: z.string(),
  outputsHash: z.string(),
  environment: z.record(z.string()),
  timestamp: z.string(),
  provenance: ProvenanceStampSchema,
});

export const DataSourceSchema = z.object({
  id: z.string(),
  name: z.string(),
  provider: z.string(),
  type: z.enum(['satellite', 'weather', 'soil', 'hydrology', 'carbon', 'socioeconomic', 'other']),
  coverage: z.string(),
  resolution: z.string(),
  frequency: z.string(),
  license: z.string(),
  accessUrl: z.string().optional(),
  provenance: ProvenanceStampSchema,
});

export const EducationResourceSchema = z.object({
  id: z.string(),
  title: z.string(),
  type: z.enum(['article', 'video', 'course', 'glossary', 'workshop', 'certification']),
  language: z.string(),
  level: z.enum(['beginner', 'intermediate', 'advanced']),
  duration: z.string().optional(),
  description: z.string(),
  tags: z.array(z.string()),
  url: z.string().optional(),
  provenance: ProvenanceStampSchema,
});

export const CourseSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  language: z.string(),
  level: z.enum(['beginner', 'intermediate', 'advanced']),
  duration: z.string(),
  modules: z.array(z.object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    duration: z.string(),
    resources: z.array(EducationResourceSchema),
  })),
  certificationId: z.string().optional(),
  provenance: ProvenanceStampSchema,
});

export const VideoContentSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  duration: z.string(),
  language: z.string(),
  subtitles: z.array(z.string()),
  thumbnailUrl: z.string(),
  videoUrl: z.string(),
  transcript: z.string().optional(),
  provenance: ProvenanceStampSchema,
});

export const GlossaryTermSchema = z.object({
  id: z.string(),
  term: z.string(),
  definition: z.record(z.string()),
  category: z.string(),
  relatedTerms: z.array(z.string()),
  provenance: ProvenanceStampSchema,
});

export const CertificationSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  requirements: z.array(z.string()),
  validityPeriod: z.string(),
  issuer: z.string(),
  provenance: ProvenanceStampSchema,
});

export const WorkshopSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  date: z.string(),
  duration: z.string(),
  location: z.string(),
  language: z.string(),
  capacity: z.number(),
  registered: z.number(),
  topics: z.array(z.string()),
  provenance: ProvenanceStampSchema,
});

export const PolicyDocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  version: z.string(),
  effectiveDate: z.string(),
  content: z.string(),
  diffFromPrevious: z.string().optional(),
  languages: z.array(z.string()),
  provenance: ProvenanceStampSchema,
});

export const ComponentDemoSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  type: z.enum(['hydroma-engine', 'marketplace', 'ecowallet', 'mrv-dashboard', 'satellite-view', 'dispute-resolution', 'land-profiler', 'api-playground']),
  status: z.enum(['live', 'demo', 'development']),
  embedUrl: z.string().optional(),
  documentationUrl: z.string().optional(),
  provenance: ProvenanceStampSchema,
});

export const ApiEndpointSchema = z.object({
  path: z.string(),
  method: z.string(),
  summary: z.string(),
  description: z.string(),
  parameters: z.array(z.object({
    name: z.string(),
    in: z.enum(['query', 'path', 'header', 'cookie']),
    required: z.boolean(),
    schema: z.record(z.unknown()),
    description: z.string(),
  })),
  responses: z.array(z.object({
    status: z.number(),
    description: z.string(),
    schema: z.record(z.unknown()).optional(),
  })),
  authentication: z.boolean(),
  rateLimit: z.string().optional(),
  provenance: ProvenanceStampSchema,
});

export type {
  ProvenanceStamp,
  PublicPageMeta,
  ServiceStatus,
  ServiceOverview,
  ScienceEvidence,
  Methodology,
  ValidationResult,
  UncertaintyQuantification,
  ReproducibilityRecord,
  DataSource,
  EducationResource,
  Course,
  CourseModule,
  VideoContent,
  GlossaryTerm,
  Certification,
  Workshop,
  PolicyDocument,
  ComponentDemo,
  ApiEndpoint,
  ApiParameter,
  ApiResponse,
};