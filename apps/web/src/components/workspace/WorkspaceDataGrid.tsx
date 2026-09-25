import {
  AdminDataGrid,
  type AdminGridColumn,
  type AdminSearchParams,
} from '@/components/admin/AdminDataGrid';

/**
 * Workspace tables reuse the existing console data grid rather than a second
 * implementation, so captions, keyboard sorting, live result counts, pagination
 * and the 320 pixel reflow behaviour stay identical across every gated surface.
 *
 * Only the names are re-exported; no behaviour is copied or weakened here.
 */
export const WorkspaceDataGrid = AdminDataGrid;
export type WorkspaceSearchParams = AdminSearchParams;
export type WorkspaceGridColumn<Row> = AdminGridColumn<Row>;
