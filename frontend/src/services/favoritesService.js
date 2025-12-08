import api from './api';

/**
 * Favorites/Wishlist Service
 * Handles all favorites-related API calls
 */

const favoritesService = {
  /**
   * Get user's favorites/wishlist
   * @param {number} skip - Number of items to skip
   * @param {number} limit - Number of items to return
   * @returns {Promise} Favorites data
   */
  getFavorites: async (skip = 0, limit = 100) => {
    try {
      const response = await api.get(`/api/favorites/?skip=${skip}&limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Get favorites error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Toggle favorite (add or remove)
   * @param {string} productIdOrSlug - Product ID or slug
   * @returns {Promise} Toggle result
   */
  toggleFavorite: async (productIdOrSlug) => {
    try {
      const response = await api.post('/api/favorites/toggle', {
        product: productIdOrSlug
      });
      return response.data;
    } catch (error) {
      console.error('Toggle favorite error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Check if product is favorited
   * @param {string} productIdOrSlug - Product ID or slug
   * @returns {Promise} Check result
   */
  checkFavorite: async (productIdOrSlug) => {
    try {
      const response = await api.get(`/api/favorites/check/${productIdOrSlug}`);
      return response.data;
    } catch (error) {
      console.error('Check favorite error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Remove favorite by ID
   * @param {string} favoriteId - Favorite ID
   * @returns {Promise} Remove result
   */
  removeFavorite: async (favoriteId) => {
    try {
      const response = await api.delete(`/api/favorites/${favoriteId}`);
      return response.data;
    } catch (error) {
      console.error('Remove favorite error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  }
};

export default favoritesService;
