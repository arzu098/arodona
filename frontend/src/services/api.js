import axios from 'axios';

// Track last login time to prevent immediate logout
let lastLoginTime = 0;

// Create axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:5858', // Backend URL
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds timeout
});

// Function to update last login time (call this after successful login)
export const updateLoginTime = () => {
  lastLoginTime = Date.now();
};

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Log detailed error information for debugging
    console.group('🚨 API Error Details');
    console.error('Request URL:', error.config?.url);
    console.error('Request method:', error.config?.method?.toUpperCase());
    console.error('Request headers:', error.config?.headers);
    console.error('Response status:', error.response?.status);
    console.error('Response data:', error.response?.data);
    console.error('Response headers:', error.response?.headers);
    console.groupEnd();
    
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      
      // Handle specific status codes
      if (status === 401) {
        // Unauthorized - token is invalid or expired
        console.warn('Unauthorized request - token may be invalid or expired');
        
        // Only auto-logout if there was a token (meaning it's expired/invalid)
        // Don't logout if user is already on login/register page or has no token
        // Also don't logout if user just logged in (within 5 seconds)
        // Also don't logout if this is an initial auth check (profile/me request)
        const hadToken = error.config?.headers?.Authorization;
        const isAuthPage = window.location.pathname === '/login' || window.location.pathname === '/register';
        const justLoggedIn = (Date.now() - lastLoginTime) < 5000; // 5 second grace period
        const isProfileCheck = error.config?.url?.includes('/api/profile/me');
        
        if (hadToken && !isAuthPage && !justLoggedIn && !isProfileCheck) {
          // Clear authentication data
          localStorage.removeItem('accessToken');
          localStorage.removeItem('user');
          localStorage.removeItem('userEmail');
          localStorage.removeItem('userRole');
          
          // Redirect to login page with session expired message
          window.location.href = '/login?expired=true';
        }
      } else if (status === 403) {
        console.error('Access forbidden');
      } else if (status === 404) {
        console.error('Resource not found');
      } else if (status === 500) {
        console.error('Internal server error');
      }
      
      // Return detailed error message
      return Promise.reject({
        status,
        message: data?.detail || data?.message || 'An error occurred',
        data
      });
    } else if (error.request) {
      // Request was made but no response received
      return Promise.reject({
        message: 'No response from server. Please check your connection.',
        error
      });
    } else {
      // Something else happened
      return Promise.reject({
        message: error.message || 'An unexpected error occurred',
        error
      });
    }
  }
);

export default api;
