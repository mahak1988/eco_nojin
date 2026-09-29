/**
 * Public surface of the design-system primitives.
 *
 * Exported through one barrel so a page imports `from '@/components/ui'` and the
 * internal file layout can change without touching 241 pages. Every component
 * here takes its labels as props: none of them carries translatable copy, which
 * is the constraint the 53 public pages violated with inline `{ fa, en }`
 * dictionaries.
 */
export { Accordion, type AccordionItem, type AccordionProps } from './Accordion';
export { Badge, type BadgeDensity, type BadgeProps, type BadgeTone } from './Badge';
export { Button } from './Button';
export { Card, type CardDensity, type CardProps } from './Card';
export { type Column, DataTable, type DataTableProps, type SortDirection } from './DataTable';
export { Input } from './Input';
export {
  Breadcrumb,
  type BreadcrumbProps,
  type Crumb,
  Pagination,
  type PaginationProps,
} from './Navigation';
export { Progress, type ProgressProps, type ProgressSize, type ProgressTone } from './Progress';
export { Select } from './Select';
export { Skeleton } from './Skeleton';
export { Stat } from './Stat';
export {
  type DataState,
  type StateLabels,
  StateSlot,
  type StateSlotProps,
} from './StateSlot';
export { Switch } from './Switch';
export { type TabDensity, type TabItem, TabPanel, Tabs, type TabsProps } from './Tabs';
export { Textarea } from './Textarea';
