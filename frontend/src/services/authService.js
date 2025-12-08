import api, { updateLoginTime } from './api';

/**
 * Authentication Service
 * Handles all authentication-related API calls
 */

const authService = {
  /**
   * Login user with email and password
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} Login response with token and user data
   */
  login: async (email, password) => {
    try {
      const response = await api.post('/api/auth/login', {
        email,
        password
      });
      
      // Check if 2FA is required
      if (response.data.require_2fa) {
        return {
          require_2fa: true,
          temp_token: response.data.temp_token
        };
      }
      
      // Store token and user data
      if (response.data.access_token) {
        localStorage.setItem('accessToken', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Update login time to prevent immediate logout
        updateLoginTime();
      }
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  },

  /**
   * Register new user
   * @param {Object} userData - User registration data
   * @returns {Promise} Registration response
   */
  register: async (userData) => {
    try {
      const response = await api.post('/api/auth/register', userData);
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  },

  /**
   * Logout user
   * @returns {Promise} Logout response
   */
  logout: async () => {
    try {
      await api.post('/api/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Always clear local storage
      localStorage.removeItem('accessToken');
      localStorage.removeItem('user');
      localStorage.removeItem('userRole');
      localStorage.removeItem('userEmail');
    }
  },

  /**
   * Refresh access token
   * @returns {Promise} New access token
   */
  refreshToken: async () => {
    try {
      const response = await api.post('/api/auth/refresh');
      if (response.data.access_token) {
        localStorage.setItem('accessToken', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      console.error('Token refresh error:', error);
      throw error;
    }
  },

  /**
   * Request password reset
   * @param {string} email - User email
   * @returns {Promise} Password reset response
   */
  forgotPassword: async (email) => {
    try {
      const response = await api.post('/api/auth/password/forgot', {
        email
      });
      return response.data;
    } catch (error) {
      console.error('Forgot password error:', error);
      throw error;
    }
  },

  /**
   * Reset password with token
   * @param {string} token - Reset token
   * @param {string} newPassword - New password
   * @returns {Promise} Password reset response
   */
  resetPassword: async (token, newPassword) => {
    try {
      const response = await api.post('/api/auth/password/reset', {
        token,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      console.error('Reset password error:', error);
      throw error;
    }
  },

  /**
   * Setup 2FA
   * @returns {Promise} 2FA setup data with QR code
   */
  setup2FA: async () => {
    try {
      const response = await api.post('/api/auth/2fa/setup');
      return response.data;
    } catch (error) {
      console.error('2FA setup error:', error);
      throw error;
    }
  },

  /**
   * Verify 2FA code
   * @param {string} code - 2FA code
   * @returns {Promise} Verification response
   */
  verify2FA: async (code) => {
    try {
      const response = await api.post('/api/auth/2fa/verify', {
        code
      });
      return response.data;
    } catch (error) {
      console.error('2FA verification error:', error);
      throw error;
    }
  },

  /**
   * Get current user profile
   * @returns {Promise} User profile data
   */
  getCurrentUser: async () => {
    try {
      const response = await api.get('/api/profile/me');
      return response.data;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  },

  /**
   * Check if user is authenticated
   * @returns {boolean} Authentication status
   */
  isAuthenticated: () => {
    const token = localStorage.getItem('accessToken');
    return !!token;
  },

  /**
   * Get stored user data
   * @returns {Object|null} User data
   */
  getUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Get access token
   * @returns {string|null} Access token
   */
  getToken: () => {
    return localStorage.getItem('accessToken');
  },

  /**
   * Update stored user data
   * @param {Object} userData - Updated user data
   */
  updateStoredUser: (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
  },

  /**
   * Login delivery boy with email and password
   * @param {string} email - Delivery boy email
   * @param {string} password - Delivery boy password
   * @returns {Promise} Login response with token and user data
   */
  deliveryBoyLogin: async (email, password) => {
    try {
      const response = await api.post('/api/delivery/login', {
        email,
        password
      });

      // Store token and user data
      if (response.data.access_token) {
        localStorage.setItem('accessToken', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Set authorization header for future requests
        api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        
        // Update login time
        updateLoginTime();
      }

      return response.data;
    } catch (error) {
      console.error('Delivery boy login error:', error);
      throw error.response?.data || error;
    }
  }
};

export default authService;
