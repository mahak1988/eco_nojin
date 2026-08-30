/**
 * ContentStudio Types
 * ====================
 * Type definitions for content management.
 *
 * @module features/content-studio/types
 */

/** Content status */
export type ContentStatus = 'published' | 'draft' | 'scheduled';

/** Content type */
export type ContentType = 'article' | 'video' | 'podcast' | 'guide';

/** Content item */
export interface ContentItem {
  id: string;
  title: string;
  type: ContentType;
  status: ContentStatus;
  author?: string;
  updated_at?: string;
  created_at?: string;
  language?: string;
  excerpt?: string;
}

/** Filter options */
export type ContentFilter = 'all' | ContentStatus;

/** Generate draft request */
export interface GenerateDraftRequest {
  topic: string;
  language: string;
}

/** Translate request */
export interface TranslateRequest {
  target_language: string;
}

/** Derived content data (memoized) */
export interface DerivedContentData {
  published: ContentItem[];
  drafts: ContentItem[];
  scheduled: ContentItem[];
  filtered: ContentItem[];
  searched: ContentItem[];
}
