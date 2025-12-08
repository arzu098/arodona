import api from './api';

/**
 * Vendor Service - All vendor-related API calls
 */

const vendorService = {
  /**
   * Apply to become a vendor
   * POST /api/vendors/apply
   */
  applyAsVendor: async (applicationData) => {
    const response = await api.post('/api/vendors/apply', applicationData);
    return response.data;
  },

  /**
   * Get current vendor's profile
   * GET /api/vendors/my-profile
   */
  getMyProfile: async () => {
    const response = await api.get('/api/vendors/my-profile');
    return response.data;
  },

  /**
   * Update current vendor's profile
   * PUT /api/vendors/my-profile
   */
  updateMyProfile: async (profileData) => {
    const response = await api.put('/api/vendors/my-profile', profileData);
    return response.data;
  },

  /**
   * Get current vendor's storefront
   * GET /api/vendors/my-storefront
   */
  getMyStorefront: async () => {
    const response = await api.get('/api/vendors/my-storefront');
    return response.data;
  },

  /**
   * Update current vendor's storefront
   * PUT /api/vendors/my-storefront
   */
  updateMyStorefront: async (storefrontData) => {
    const response = await api.put('/api/vendors/my-storefront', storefrontData);
    return response.data;
  },

  /**
   * Upload vendor document
   * POST /api/vendors/upload-document
   */
  uploadDocument: async (formData) => {
    const response = await api.post('/api/vendors/upload-document', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Get current vendor's analytics
   * GET /api/vendors/my-analytics
   */
  getMyAnalytics: async (params = {}) => {
    const response = await api.get('/api/vendors/my-analytics', { params });
    return response.data;
  },

  /**
   * Get current vendor's activities
   * GET /api/vendors/my-activities
   */
  getMyActivities: async (params = {}) => {
    const response = await api.get('/api/vendors/my-activities', { params });
    return response.data;
  },

  /**
   * Get current vendor's products
   * GET /api/products/my-products
   */
  getMyProducts: async (params = {}) => {
    const response = await api.get('/api/products/my-products', { params });
    return response.data;
  },

  /**
   * Get a specific product from current vendor
   * GET /api/products/my-products/{product_id}
   */
  getMyProduct: async (productId) => {
    const response = await api.get(`/api/products/my-products/${productId}`);
    return response.data;
  },

  /**
   * Update a product from current vendor
   * PUT /api/products/my-products/{product_id}
   */
  updateMyProduct: async (productId, productData) => {
    const response = await api.put(`/api/products/my-products/${productId}`, productData);
    return response.data;
  },

  /**
   * Partially update a product from current vendor
   * PATCH /api/products/my-products/{product_id}
   */
  patchMyProduct: async (productId, productData) => {
    const response = await api.patch(`/api/products/my-products/${productId}`, productData);
    return response.data;
  },

  /**
   * Delete a product from current vendor
   * DELETE /api/products/my-products/{product_id}
   */
  deleteMyProduct: async (productId) => {
    const response = await api.delete(`/api/products/my-products/${productId}`);
    return response.data;
  },

  /**
   * Get vendor dashboard data
   * GET /api/vendors/{vendor_id}/dashboard
   */
  getVendorDashboard: async (vendorId) => {
    const response = await api.get(`/api/vendors/${vendorId}/dashboard`);
    return response.data;
  },

  /**
   * Get vendor orders
   * GET /api/orders/vendor/orders
   */
  getVendorOrders: async (vendorId, params = {}) => {
    console.log('Getting vendor orders for vendor:', vendorId, 'with params:', params);
    const response = await api.get('/api/orders/vendor/orders', { params });
    console.log('Vendor orders API response:', response.data);
    return response.data;
  },

  /**
   * Get all vendors (admin/public)
   * GET /api/vendors
   */
  getAllVendors: async (params = {}) => {
    const response = await api.get('/api/vendors', { params });
    return response.data;
  },

  /**
   * Get specific vendor by ID
   * GET /api/vendors/{vendor_id}
   */
  getVendorById: async (vendorId) => {
    const response = await api.get(`/api/vendors/${vendorId}`);
    return response.data;
  },

  /**
   * Update vendor by ID (admin)
   * PUT /api/vendors/{vendor_id}
   */
  updateVendor: async (vendorId, vendorData) => {
    const response = await api.put(`/api/vendors/${vendorId}`, vendorData);
    return response.data;
  },

  /**
   * Delete vendor by ID (admin)
   * DELETE /api/vendors/{vendor_id}
   */
  deleteVendor: async (vendorId) => {
    const response = await api.delete(`/api/vendors/${vendorId}`);
    return response.data;
  },
};

export default vendorService;
