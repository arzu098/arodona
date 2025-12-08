import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute Component - Handles role-based access control
 * 
 * @param {React.ReactNode} children - The component to render if authorized
 * @param {string|string[]} roles - Required role(s) to access the route
 * @param {string} redirectTo - Where to redirect if not authorized (default: /login)
 * @param {boolean} requireAuth - Whether authentication is required (default: true)
 */
const ProtectedRoute = ({ 
  children, 
  roles = [], 
  redirectTo = '/login', 
  requireAuth = true 
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  // Show loading while auth state is being determined
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  // Redirect to login if authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // If specific roles are required, check if user has one of them
  if (roles.length > 0 && isAuthenticated) {
    const userRole = user?.role || 'customer'; // Default to customer
    const hasRequiredRole = Array.isArray(roles) 
      ? roles.includes(userRole)
      : roles === userRole;

    if (!hasRequiredRole) {
      // Redirect unauthorized users to appropriate dashboard or home
      const unauthorizedRedirect = user?.role === 'admin' ? '/admin/dashboard' :
                                   user?.role === 'vendor' ? '/vendor/dashboard' :
                                   '/customer/dashboard';
      return <Navigate to={unauthorizedRedirect} replace />;
    }
  }

  // Render the protected component
  return children;
};

export default ProtectedRoute;