import React, { createContext, useState, useContext, useEffect } from 'react';
import authService from '../services/authService';

// Create AuthContext
const AuthContext = createContext(null);

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// AuthProvider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize auth state on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Check if user is authenticated
  const checkAuth = async () => {
    try {
      const token = authService.getToken();
      const storedUser = authService.getUser();

      if (token && storedUser) {
        // First, set the stored user immediately to prevent redirect flash
        setUser(storedUser);
        setIsAuthenticated(true);
        
        // Then optionally verify token with backend in the background
        try {
          const currentUser = await authService.getCurrentUser();
          // Update with fresh user data from server
          setUser(currentUser);
          authService.updateStoredUser(currentUser);
        } catch (error) {
          // Token validation failed - only clear auth for 401 (unauthorized)
          if (error.status === 401) {
            console.error('Token expired or invalid:', error);
            clearAuth();
          } else {
            // For other errors (network, 500, etc.) - keep user logged in with cached data
            console.warn('Could not validate token, keeping user logged in with cached data:', error);
            // Keep the user authenticated with stored data
          }
        }
      } else {
        clearAuth();
      }
    } catch (error) {
      console.error('Auth check error:', error);
      // Don't clear auth on general errors - only clear if we're sure there's no valid session
      const token = authService.getToken();
      const storedUser = authService.getUser();
      
      if (!token || !storedUser) {
        clearAuth();
      } else {
        // Keep user logged in with cached data if token and user exist
        console.warn('Using cached authentication data due to error');
        setUser(storedUser);
        setIsAuthenticated(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Login function
  const login = async (email, password) => {
    try {
      setError(null);
      setIsLoading(true);

      const response = await authService.login(email, password);

      // Check if 2FA is required
      if (response.require_2fa) {
        return {
          success: true,
          require_2fa: true,
          temp_token: response.temp_token
        };
      }

      // Set user and authentication state
      setUser(response.user);
      setIsAuthenticated(true);

      return {
        success: true,
        user: response.user
      };
    } catch (error) {
      const errorMessage = error.message || 'Login failed. Please try again.';
      setError(errorMessage);
      console.error('Login error:', error);
      return {
        success: false,
        error: errorMessage
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setError(null);
      setIsLoading(true);

      const response = await authService.register(userData);

      return {
        success: true,
        message: response.message,
        user: response.user
      };
    } catch (error) {
      const errorMessage = error.message || 'Registration failed. Please try again.';
      setError(errorMessage);
      console.error('Registration error:', error);
      return {
        success: false,
        error: errorMessage
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Delivery Boy Login function
  const deliveryBoyLogin = async (email, password) => {
    try {
      setError(null);
      setIsLoading(true);

      const response = await authService.deliveryBoyLogin(email, password);

      // Set user and authentication state
      setUser(response.user);
      setIsAuthenticated(true);

      return {
        success: true,
        user: response.user
      };
    } catch (error) {
      const errorMessage = error.message || 'Delivery boy login failed. Please try again.';
      setError(errorMessage);
      console.error('Delivery boy login error:', error);
      return {
        success: false,
        error: errorMessage
      };
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
    }
  };

  // Clear authentication state
  const clearAuth = () => {
    setUser(null);
    setIsAuthenticated(false);
    setError(null);
    // Clear localStorage tokens
    localStorage.removeItem('accessToken');
    localStorage.removeItem('user');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userEmail');
  };

  // Update user profile
  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem('user', JSON.stringify(updatedUser));
  };

  // Role-based helpers
  const isAdmin = () => user?.role === 'admin';
  const isVendor = () => user?.role === 'vendor';
  const isCustomer = () => user?.role === 'customer' || !user?.role; // Default to customer
  const isDeliveryBoy = () => user?.role === 'delivery_boy';
  
  const hasRole = (role) => user?.role === role;
  
  const hasAnyRole = (roles) => roles.includes(user?.role);

  // Get dashboard route based on role
  const getDashboardRoute = () => {
    if (user?.role === 'super_admin') return '/super-admin/dashboard';
    if (isAdmin()) return '/admin/dashboard';
    if (isVendor()) return '/vendor/dashboard';
    if (isDeliveryBoy()) return '/delivery/dashboard';
    return '/customer/dashboard';
  };

  // Context value
  const value = {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    deliveryBoyLogin,
    register,
    logout,
    updateUser,
    checkAuth,
    clearAuth,
    isAdmin,
    isVendor,
    isCustomer,
    isDeliveryBoy,
    hasRole,
    hasAnyRole,
    getDashboardRoute
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
