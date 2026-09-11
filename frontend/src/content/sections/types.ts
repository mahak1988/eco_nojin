/**
 * Typed bilingual content model for the Eco Nojin website.
 * Single source of truth for all copy (fa / en); components only read from here.
 * Facts are limited to what the repository documents state (no invented numbers).
 */

export type Lang = 'fa' | 'en';

export type IconKey =
  | 'satellite'
  | 'droplets'
  | 'sprout'
  | 'mountain'
  | 'blocks'
  | 'store'
  | 'globe'
  | 'message'
  | 'sms'
  | 'bot'
  | 'mic'
  | 'soil'
  | 'climate'
  | 'chart'
  | 'book'
  | 'clipboard'
  | 'sync'
  | 'coins'
  | 'flask'
  | 'workflow'
  | 'server'
  | 'database'
  | 'route'
  | 'shield'
  | 'monitor';

export interface LegalSection {
  title: string;
  body: string[];
}

export interface LegalPageContent {
  kicker: string;
  title: string;
  lead: string;
  version: string;
  changelog: string[];
  updated: string;
  draftNote: string;
  sections: LegalSection[];
}

export interface BlogPost {
  title: string;
  date: string;
  category: string;
  excerpt: string;
  paragraphs: string[];
  sections?: { heading: string; paragraphs: string[] }[];
}

export interface FaqItem {
  cat: string;
  q: string;
  a: string;
}

export interface TimelineItem {
  id: string;
  title: string;
  desc: string;
  status: 'completed' | 'active' | 'planned';
}

export interface UseCase {
  problem: string;
  module: string;
  output: string;
}

export interface SiteContent {
  meta: { title: string; description: string };
  brand: { name: string; latin: string; tagline: string };
  nav: {
    home: string;
    platform: string;
    science: string;
    about: string;
    blog: string;
    langLabel: string;
  };
  hero: {
    kicker: string;
    title: string;
    titleAccent: string;
    subtitle: string;
    ctaPrimary: string;
    ctaSecondary: string;
    visualCaption: string;
    chips: { ndvi: string; era5: string; soc: string };
  };
  stats: { value: string; label: string }[];
  why: {
    kicker: string;
    title: string;
    items: { icon: IconKey; title: string; desc: string }[];
  };
  capabilities: {
    kicker: string;
    title: string;
    lead: string;
    items: { icon: IconKey; title: string; desc: string }[];
  };
  science: {
    kicker: string;
    title: string;
    lead: string;
    steps: { title: string; desc: string }[];
    modelsTitle: string;
    models: { name: string; desc: string; detail: string; slug: string }[];
    outputsTitle: string;
    outputsLead: string;
    outputs: string[];
    dataSourcesTitle: string;
    dataSources: { name: string; desc: string }[];
    more: string;
  };
  channels: {
    kicker: string;
    title: string;
    lead: string;
    items: { icon: IconKey; title: string; desc: string }[];
  };
  carbon: {
    kicker: string;
    title: string;
    lead: string;
    bullets: string[];
    cta: string;
  };
  platform: {
    kicker: string;
    title: string;
    lead: string;
    modules: { icon: IconKey; title: string; desc: string }[];
    useCasesTitle: string;
    useCasesLead: string;
    useCasesProblem: string;
    useCasesModule: string;
    useCasesOutput: string;
    useCases: UseCase[];
    stack: {
      title: string;
      lead: string;
      layers: { icon: IconKey; title: string; desc: string }[];
    };
    apiTitle: string;
    apiDesc: string;
  };
  about: {
    kicker: string;
    title: string;
    lead: string;
    paragraphs: string[];
    timelineTitle: string;
    timelineNote: string;
    timeline: TimelineItem[];
    inviteTitle: string;
    invite: string;
    contactTitle: string;
    contactPageLink: string;
    emailLabel: string;
    email: string;
    siteLabel: string;
    site: string;
    licenseLabel: string;
    license: string;
    legalEntityLabel: string;
    legalEntity: string;
    contributingTitle: string;
    contributingBody: string;
  };
  terms: LegalPageContent;
  rules: LegalPageContent;
  privacy: LegalPageContent;
  blog: {
    kicker: string;
    title: string;
    lead: string;
    note: string;
    posts: BlogPost[];
  };
  faq: {
    kicker: string;
    title: string;
    lead: string;
    categories: string[];
    items: FaqItem[];
  };
  contact: {
    kicker: string;
    title: string;
    lead: string;
    formTitle: string;
    formNote: string;
    nameLabel: string;
    emailLabel: string;
    roleLabel: string;
    roles: string[];
    messageLabel: string;
    sendButton: string;
    validationError: string;
    successTitle: string;
    successNote: string;
    errorTitle: string;
    errorFallback: string;
    faqLink: string;
    emailCardTitle: string;
    channelsTitle: string;
    channelsNote: string;
  };
  transparency: {
    kicker: string;
    title: string;
    lead: string;
    phasesTitle: string;
    phasesNote: string;
    phases: TimelineItem[];
    verificationTitle: string;
    verification: string[];
    commitmentsTitle: string;
    commitments: string[];
    reportsNote: string;
  };
  notFound: {
    title: string;
    lead: string;
    homeButton: string;
  };
  cta: { title: string; lead: string; button: string };
  footer: {
    desc: string;
    exploreTitle: string;
    contactTitle: string;
    legalTitle: string;
    legalLinks: { terms: string; rules: string; privacy: string };
    quickLinks: { faq: string; contact: string; transparency: string };
    legal: string;
  };
  common: { conceptual: string; learnMore: string };
  trust: {
    kicker: string;
    title: string;
    lead: string;
    items: { icon: IconKey; title: string; desc: string }[];
  };
}
