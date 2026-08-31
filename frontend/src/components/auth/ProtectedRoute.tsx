/**
 * ProtectedRoute - Authentication Guard
 * Supports both default and named imports for compatibility
 * Wraps protected routes with:
 *   - Authentication check
 *   - Role-based access (admin check)
 *   - SimulationPipelineProvider for data sharing
 */

import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { ReactNode } from 'react';
import { SimulationPipelineProvider } from '../../contexts/SimulationPipeline';

interface ProtectedRouteProps {
  children?: ReactNode;
  requiredRole?: string;
}

/**
 * Check if user is authenticated
 * Uses localStorage token as primary check
 */
export function useAuth(): { isAuthenticated: boolean; isAdmin: boolean; user: any } {
  const token = localStorage.getItem('access_token');
  const userStr = localStorage.getItem('user');

  let user = null;
  let isAdmin = false;

  try {
    if (userStr) {
      user = JSON.parse(userStr);
      isAdmin = user?.role === 'admin' || user?.is_admin === true;
    }
  } catch (e) {
    console.warn('[Auth] Failed to parse user data');
  }

  return {
    isAuthenticated: !!token,
    isAdmin,
    user,
  };
}

/**
 * ProtectedRoute component
 * Checks authentication and renders children with PipelineProvider
 */
function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const location = useLocation();
  const { isAuthenticated, isAdmin } = useAuth();

  // Check authentication
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (requiredRole === 'admin' && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  // Render with PipelineProvider
  return <SimulationPipelineProvider>{children || <Outlet />}</SimulationPipelineProvider>;
}

// Dual export: both default AND named
export { ProtectedRoute };
export default ProtectedRoute;
