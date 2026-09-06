import {
  Outlet,
  RouterProvider,
  createRootRoute,
  createRoute,
  createRouter,
} from '@tanstack/react-router';
import { KnowledgePage } from '@/features/knowledge/KnowledgePage';
import { HomePage } from '@/features/home/HomePage';
import { ModelsPage } from '@/features/models/ModelsPage';
import { NotFoundPage } from '@/features/system/NotFoundPage';
import { SiteLayout } from './SiteLayout';

const rootRoute = createRootRoute({
  component: () => <SiteLayout />,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <HomePage />,
});

const knowledgeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/knowledge',
  component: () => <KnowledgePage />,
});

const modelsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/models',
  component: () => <ModelsPage />,
});

const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: () => <NotFoundPage />,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  knowledgeRoute,
  modelsRoute,
  notFoundRoute,
]);

export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

export { Outlet };