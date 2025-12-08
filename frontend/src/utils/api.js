// Utility function to get the correct API base URL
export const getApiBaseUrl = () => {
  return import.meta.env.VITE_API_URL || 'http://localhost:5858';
};

// Utility function to construct image URLs
export const getImageUrl = (imageUrl) => {
  if (!imageUrl) return null;
  
  const API_BASE_URL = getApiBaseUrl();
  
  // If it's already a full URL, return as is
  if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
    return imageUrl;
  }
  
  // If the URL starts with /uploads, prepend the backend URL
  if (imageUrl.startsWith('/uploads')) {
    return `${API_BASE_URL}${imageUrl}`;
  }
  
  // Handle legacy /static prefix - replace with /uploads
  if (imageUrl.startsWith('/static')) {
    return `${API_BASE_URL}${imageUrl.replace('/static', '/uploads')}`;
  }
  
  // If it's a relative path without prefix (legacy data), add /uploads
  if (imageUrl.startsWith('products/') || imageUrl.startsWith('uploads/')) {
    const cleanUrl = imageUrl.startsWith('uploads/') ? imageUrl.substring(8) : imageUrl;
    return `${API_BASE_URL}/uploads/${cleanUrl}`;
  }
  
  // Default: assume it needs /uploads/ prefix
  return `${API_BASE_URL}/uploads/${imageUrl}`;
};