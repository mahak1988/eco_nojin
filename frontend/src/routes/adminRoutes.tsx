/** Admin routes — centralized admin panel with layout wrapper */

import type { ReactElement } from 'react';
import AdminLayout from '../components/admin/AdminLayout';
import AdminDashboard from '../pages/dashboard/admin/AdminDashboard';
import AdminUsersPage from '../pages/dashboard/admin/AdminUsersPage';
import AdminVendorsPage from '../pages/dashboard/admin/AdminVendorsPage';
import AdminMarketplacePage from '../pages/dashboard/admin/AdminMarketplacePage';
import AdminTransactionsPage from '../pages/dashboard/admin/AdminTransactionsPage';
import AdminSettingsPage from '../pages/dashboard/admin/AdminSettingsPage';

function AdminLayoutWrapper({ children }: { children: ReactElement }) {
  return <AdminLayout>{children}</AdminLayout>;
}

export const adminRoutes = [
  {
    path: '/dashboard/admin',
    element: (
      <AdminLayoutWrapper>
        <AdminDashboard />
      </AdminLayoutWrapper>
    ),
  },
  {
    path: '/dashboard/admin/users',
    element: (
      <AdminLayoutWrapper>
        <AdminUsersPage />
      </AdminLayoutWrapper>
    ),
  },
  {
    path: '/dashboard/admin/vendors',
    element: (
      <AdminLayoutWrapper>
        <AdminVendorsPage />
      </AdminLayoutWrapper>
    ),
  },
  {
    path: '/dashboard/admin/marketplace',
    element: (
      <AdminLayoutWrapper>
        <AdminMarketplacePage />
      </AdminLayoutWrapper>
    ),
  },
  {
    path: '/dashboard/admin/transactions',
    element: (
      <AdminLayoutWrapper>
        <AdminTransactionsPage />
      </AdminLayoutWrapper>
    ),
  },
  {
    path: '/dashboard/admin/settings',
    element: (
      <AdminLayoutWrapper>
        <AdminSettingsPage />
      </AdminLayoutWrapper>
    ),
  },
  {
    path: '/dashboard/admin/reports',
    element: (
      <AdminLayoutWrapper>
        <div className="px-4 py-10">
          <h1 className="text-2xl font-bold text-[var(--color-night-100)] mb-4">گزارش‌ها</h1>
          <p className="text-[var(--color-night-200)]/60">صفحه گزارش‌ها در حال توسعه است.</p>
        </div>
      </AdminLayoutWrapper>
    ),
  },
];