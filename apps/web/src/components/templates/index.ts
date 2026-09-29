import { type PageTemplate, TEMPLATE_BY_ID, type TemplateId } from '@/lib/design/page-templates';

import { CoverPage } from './CoverPage';
import { DashboardPage } from './DashboardPage';
import { DetailPage } from './DetailPage';
import { DiscoveryPage } from './DiscoveryPage';
import { FlowPage } from './FlowPage';
import { InstrumentPage } from './InstrumentPage';
import { LearningPage } from './LearningPage';
import { LedgerPage } from './LedgerPage';
import { LegalPage } from './LegalPage';
import { NarrativePage } from './NarrativePage';
import { ReportPage } from './ReportPage';
import { SystemPage } from './SystemPage';
import {
  TemplateFrame,
  type TemplateFrameProps,
  type TemplateLayout,
  type TemplatePageProps,
  TemplateRegion,
  type TemplateRegionNodes,
} from './TemplateFrame';

/**
 * The twelve archetypes, addressable by plan id.
 *
 * `ResourcePage` dispatches on `TemplateId`; the catalogue carries the id; the
 * generator writes the id into the page. Nothing else has to know the mapping,
 * and a thirteenth template is a compile error here rather than a route that
 * quietly renders with the wrong layout.
 */
export const PAGE_TEMPLATE_COMPONENTS: Readonly<
  Record<TemplateId, (props: never) => React.ReactNode>
> = {
  cover: CoverPage as (props: never) => React.ReactNode,
  narrative: NarrativePage as (props: never) => React.ReactNode,
  discovery: DiscoveryPage as (props: never) => React.ReactNode,
  detail: DetailPage as (props: never) => React.ReactNode,
  flow: FlowPage as (props: never) => React.ReactNode,
  dashboard: DashboardPage as (props: never) => React.ReactNode,
  instrument: InstrumentPage as (props: never) => React.ReactNode,
  ledger: LedgerPage as (props: never) => React.ReactNode,
  legal: LegalPage as (props: never) => React.ReactNode,
  report: ReportPage as (props: never) => React.ReactNode,
  system: SystemPage as (props: never) => React.ReactNode,
  learning: LearningPage as (props: never) => React.ReactNode,
};

/** The archetype definition for a plan id, for callers that need its metadata. */
export function templateDefinition(id: TemplateId): PageTemplate {
  return TEMPLATE_BY_ID[id];
}

export {
  CoverPage,
  DashboardPage,
  DetailPage,
  DiscoveryPage,
  FlowPage,
  InstrumentPage,
  LearningPage,
  LedgerPage,
  LegalPage,
  NarrativePage,
  ReportPage,
  SystemPage,
  TemplateFrame,
  type TemplateFrameProps,
  type TemplateLayout,
  type TemplatePageProps,
  TemplateRegion,
  type TemplateRegionNodes,
};
