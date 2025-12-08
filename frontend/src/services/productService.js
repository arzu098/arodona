import api from './api';

/**
 * Product Service
 * Handles all product-related API calls
 */

const productService = {
  /**
   * Get all products with filters
   * @param {Object} params - Query parameters (category, skip, limit, etc.)
   * @returns {Promise} Products data
   */
  getProducts: async (params = {}) => {
    try {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString ? `/api/products?${queryString}` : '/api/products';
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Get products error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get single product by ID or slug
   * @param {string} productId - Product ID or slug
   * @returns {Promise} Product data
   */
  getProductById: async (productId) => {
    try {
      const response = await api.get(`/api/products/${productId}`);
      return response.data;
    } catch (error) {
      console.error('Get product error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Search products
   * @param {string} query - Search query
   * @param {Object} filters - Additional filters
   * @returns {Promise} Search results
   */
  searchProducts: async (query, filters = {}) => {
    try {
      const params = { q: query, ...filters };
      const queryString = new URLSearchParams(params).toString();
      const response = await api.get(`/api/products/search?${queryString}`);
      return response.data;
    } catch (error) {
      console.error('Search products error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get product reviews
   * @param {string} productId - Product ID
   * @param {Object} params - Query parameters
   * @returns {Promise} Reviews data
   */
  getProductReviews: async (productId, params = {}) => {
    try {
      const queryString = new URLSearchParams(params).toString();
      const url = queryString 
        ? `/api/reviews/product/${productId}?${queryString}` 
        : `/api/reviews/product/${productId}`;
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      console.error('Get reviews error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Add product review
   * @param {string} productId - Product ID
   * @param {Object} reviewData - Review data (rating, comment, etc.)
   * @returns {Promise} Created review
   */
  addReview: async (productId, reviewData) => {
    try {
      const response = await api.post(`/api/reviews/product/${productId}`, reviewData);
      return response.data;
    } catch (error) {
      console.error('Add review error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get featured/trending products
   * @returns {Promise} Featured products
   */
  getFeaturedProducts: async () => {
    try {
      const response = await api.get('/api/products?featured=true&limit=10');
      return response.data;
    } catch (error) {
      console.error('Get featured products error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  },

  /**
   * Get products by category
   * @param {string} category - Category name or ID
   * @param {Object} params - Additional parameters
   * @returns {Promise} Products in category
   */
  getProductsByCategory: async (category, params = {}) => {
    try {
      // Normalize category to lowercase for API
      const normalizedCategory = category.toLowerCase();
      const queryParams = { 
        category: normalizedCategory,
        in_stock_only: true,  // Only show in-stock products
        ...params 
      };
      const queryString = new URLSearchParams(queryParams).toString();
      const response = await api.get(`/api/products?${queryString}`);
      return response.data;
    } catch (error) {
      console.error('Get category products error:', error);
      console.error('Error details:', error.response?.data);
      throw error;
    }
  }
};

export default productService;
