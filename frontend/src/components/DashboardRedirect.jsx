import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * DashboardRedirect Component - Redirects users to their role-specific dashboard
 */
const DashboardRedirect = () => {
  const { user, getDashboardRoute } = useAuth();

  // Get the appropriate dashboard route based on user role
  const dashboardRoute = getDashboardRoute();

  return <Navigate to={dashboardRoute} replace />;
};

export default DashboardRedirect;