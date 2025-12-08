import api from './api';

/**
 * Cart Service
 * Handles all cart-related API calls
 */

const cartService = {
  /**
   * Get user's cart
   * @returns {Promise} Cart data with items
   */
  getCart: async () => {
    try {
      const response = await api.get('/cart/');
      return response.data;
    } catch (error) {
      console.error('Get cart error:', error);
      throw error;
    }
  },

  /**
   * Add item to cart
   * @param {Object} itemData - Item data to add
   * @returns {Promise} Updated cart
   */
  addToCart: async (itemData) => {
    try {
      console.log('Adding to cart:', itemData);
      const response = await api.post('/cart/add', itemData);
      console.log('Cart response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Add to cart error:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      throw error;
    }
  },

  /**
   * Update item quantity in cart
   * @param {string} itemId - Cart item ID
   * @param {number} quantity - New quantity
   * @returns {Promise} Updated cart
   */
  updateQuantity: async (itemId, quantity) => {
    try {
      const response = await api.put(`/cart/items/${itemId}/quantity?quantity=${quantity}`);
      return response.data;
    } catch (error) {
      console.error('Update quantity error:', error);
      throw error;
    }
  },

  /**
   * Remove item from cart
   * @param {string} itemId - Cart item ID
   * @returns {Promise} Updated cart
   */
  removeFromCart: async (itemId) => {
    try {
      const response = await api.delete(`/cart/items/${itemId}`);
      return response.data;
    } catch (error) {
      console.error('Remove from cart error:', error);
      throw error;
    }
  },

  /**
   * Clear entire cart
   * @returns {Promise} Empty cart
   */
  clearCart: async () => {
    try {
      const response = await api.delete('/cart/clear');
      return response.data;
    } catch (error) {
      console.error('Clear cart error:', error);
      throw error;
    }
  },

  /**
   * Apply discount code
   * @param {string} code - Discount code
   * @returns {Promise} Updated cart with discount
   */
  applyDiscount: async (code) => {
    try {
      const response = await api.post('/cart/apply-discount', { code });
      return response.data;
    } catch (error) {
      console.error('Apply discount error:', error);
      throw error;
    }
  },

  /**
   * Remove discount from cart
   * @returns {Promise} Updated cart without discount
   */
  removeDiscount: async () => {
    try {
      const response = await api.delete('/cart/discount');
      return response.data;
    } catch (error) {
      console.error('Remove discount error:', error);
      throw error;
    }
  },

  /**
   * Get cart summary
   * @returns {Promise} Cart summary with totals
   */
  getCartSummary: async () => {
    try {
      const response = await api.get('/cart/summary');
      return response.data;
    } catch (error) {
      console.error('Get cart summary error:', error);
      throw error;
    }
  }
};

export default cartService;
