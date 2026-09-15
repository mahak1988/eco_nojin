/**
 * Content splitting helper for site.ts modularization.
 * Provides typed accessors to reduce direct reads from the 1900+ line site.ts.
 * 
 * Usage:
 *   import { getNav, getHero, getTrust } from '../content/contentHelpers';
 *   const nav = getNav(lang);
 */
import { content, type Lang, type SiteContent } from './site';

export type ContentAccessor<T> = (lang: Lang) => T;

export const getBrand: ContentAccessor<SiteContent['brand']> = (lang) => content[lang].brand;
export const getNav: ContentAccessor<SiteContent['nav']> = (lang) => content[lang].nav;
export const getMeta: ContentAccessor<SiteContent['meta']> = (lang) => content[lang].meta;
export const getHero: ContentAccessor<SiteContent['hero']> = (lang) => content[lang].hero;
export const getTrust: ContentAccessor<SiteContent['trust']> = (lang) => content[lang].trust;
export const getImpact: ContentAccessor<SiteContent['impact']> = (lang) => content[lang].impact;
export const getPlatform: ContentAccessor<SiteContent['platform']> = (lang) => content[lang].platform;
export const getStats: ContentAccessor<SiteContent['stats']> = (lang) => content[lang].stats;
export const getFaq: ContentAccessor<SiteContent['faq']> = (lang) => content[lang].faq;
export const getBlog: ContentAccessor<SiteContent['blog']> = (lang) => content[lang].blog;
export const getCarbon: ContentAccessor<SiteContent['carbon']> = (lang) => content[lang].carbon;
export const getRules: ContentAccessor<SiteContent['rules']> = (lang) => content[lang].rules;
export const getPrivacy: ContentAccessor<SiteContent['privacy']> = (lang) => content[lang].privacy;
export const getTerms: ContentAccessor<SiteContent['terms']> = (lang) => content[lang].terms;
export const getContact: ContentAccessor<SiteContent['contact']> = (lang) => content[lang].contact;
export const getAbout: ContentAccessor<SiteContent['about']> = (lang) => content[lang].about;
export const getWhy: ContentAccessor<SiteContent['why']> = (lang) => content[lang].why;
export const getCapabilities: ContentAccessor<SiteContent['capabilities']> = (lang) => content[lang].capabilities;
export const getChannels: ContentAccessor<SiteContent['channels']> = (lang) => content[lang].channels;
export const getScience: ContentAccessor<SiteContent['science']> = (lang) => content[lang].science;
export const getTransparency: ContentAccessor<SiteContent['transparency']> = (lang) => content[lang].transparency;
export const getNotFound: ContentAccessor<SiteContent['notFound']> = (lang) => content[lang].notFound;
export const getCta: ContentAccessor<SiteContent['cta']> = (lang) => content[lang].cta;
export const getFooter: ContentAccessor<SiteContent['footer']> = (lang) => content[lang].footer;
export const getCommon: ContentAccessor<SiteContent['common']> = (lang) => content[lang].common;

/** Get a specific nested value by path with type safety */
export function getPath<T extends Record<string, unknown>>(
  lang: Lang,
  ...path: (keyof SiteContent | number)[]
): T | undefined {
  let current: unknown = content[lang];
  for (const key of path) {
    if (current == null) return undefined;
    current = (current as Record<string, unknown>)[key as string];
  }
  return current as T | undefined;
}

/** Batch fetch multiple sections in a single call */
export function getSections<K extends keyof SiteContent>(
  lang: Lang,
  ...sections: K[]
): Pick<SiteContent, K> {
  const result = {} as Pick<SiteContent, K>;
  for (const key of sections) {
    result[key] = content[lang][key];
  }
  return result;
}
