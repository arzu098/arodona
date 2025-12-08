/**
 * Utility functions for handling product images
 */

const BASE_URL = 'http://localhost:5858';

/**
 * Convert relative image URLs to absolute URLs
 * @param {string} imageUrl - The image URL from backend
 * @returns {string} - Absolute URL
 */
export const getImageUrl = (imageUrl) => {
  if (!imageUrl) {
    return '/Images/default.png';
  }
  
  // If URL is relative (starts with / but not //)
  if (imageUrl.startsWith('/') && !imageUrl.startsWith('//')) {
    return `${BASE_URL}${imageUrl}`;
  }
  
  // If URL is already absolute
  return imageUrl;
};

/**
 * Get product image from product object
 * @param {Object} product - Product object from backend
 * @returns {string} - Image URL
 */
export const getProductImage = (product) => {
  if (product?.images && product.images.length > 0 && product.images[0]?.url) {
    return getImageUrl(product.images[0].url);
  }
  return '/Images/default.png';
};

/**
 * Transform backend product to frontend format
 * @param {Object} product - Product object from backend
 * @returns {Object} - Formatted product for frontend
 */
export const formatProduct = (product) => {
  const oldPrice = product.compare_at_price || product.original_price;
  return {
    id: product._id || product.id,
    name: product.name,
    price: `₹ ${product.price?.toLocaleString('en-IN')}`,
    oldPrice: oldPrice ? `₹ ${oldPrice?.toLocaleString('en-IN')}` : null,
    image: getProductImage(product),
    category: product.category,
    diamond_shape: product.diamond_shape,
    size: product.size,
    available_sizes: product.available_sizes,
    description: product.description,
    brand: product.brand,
    vendor_id: product.vendor_id,
    _rawPrice: product.price,
    _rawOldPrice: oldPrice
  };
};
