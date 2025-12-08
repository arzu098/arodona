import api from './api';

/**
 * Orders Service
 * Handles all order-related API calls
 */

const ordersService = {
  /**
   * Get user's orders
   * @param {Object} params - Query parameters (skip, limit, status, etc.)
   * @returns {Promise} Orders data
   */
  getMyOrders: async (params = {}) => {
    try {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `/api/orders/?${queryString}` : '/api/orders/';
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Get orders error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get single order by ID
   * @param {string} orderId - Order ID
   * @returns {Promise} Order data
   */
  getOrderById: async (orderId) => {
    try {
      const response = await api.get(`/api/orders/${orderId}`);
      return response.data;
    } catch (error) {
      console.error('Get order error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Create new order
   * @param {Object} orderData - Order data
   * @returns {Promise} Created order
   */
  createOrder: async (orderData) => {
    try {
      const response = await api.post('/api/orders/', orderData);
      return response.data;
    } catch (error) {
      console.error('Create order error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Cancel order
   * @param {string} orderId - Order ID
   * @param {string} reason - Cancellation reason
   * @returns {Promise} Updated order
   */
  cancelOrder: async (orderId, reason) => {
    try {
      const response = await api.post(`/api/orders/${orderId}/cancel`, { reason });
      return response.data;
    } catch (error) {
      console.error('Cancel order error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Track order by order number
   * @param {string} orderNumber - Order tracking number
   * @returns {Promise} Order tracking data
   */
  trackOrder: async (orderNumber) => {
    try {
      const response = await api.get(`/api/orders/track/${orderNumber}`);
      return response.data;
    } catch (error) {
      console.error('Track order error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get order analytics
   * @returns {Promise} Order analytics data
   */
  getAnalytics: async () => {
    try {
      const response = await api.get('/api/orders/analytics');
      return response.data;
    } catch (error) {
      console.error('Get analytics error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Create return request
   * @param {string} orderId - Order ID
   * @param {Object} returnData - Return request data
   * @returns {Promise} Return request
   */
  createReturn: async (orderId, returnData) => {
    try {
      const response = await api.post(`/api/orders/${orderId}/returns`, returnData);
      return response.data;
    } catch (error) {
      console.error('Create return error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get user's return requests
   * @returns {Promise} Return requests
   */
  getMyReturns: async () => {
    try {
      const response = await api.get('/api/orders/returns/my-returns');
      return response.data;
    } catch (error) {
      console.error('Get returns error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  }
};

export default ordersService;
