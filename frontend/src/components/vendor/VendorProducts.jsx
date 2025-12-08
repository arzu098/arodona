import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import vendorService from '../../services/vendorService';

const VendorProducts = () => {
  const { user, logout } = useAuth();
  const [products, setProducts] = useState([]);
  const [vendorProfile, setVendorProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, active, inactive
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // grid or list

  // Helper function to get image URL from various formats
  const getImageUrl = (image) => {
    if (!image) return null;
    
    let imageUrl = null;
    
    // If it's a string, use it directly
    if (typeof image === 'string') {
      imageUrl = image.trim();
    }
    // If it's an object with url property
    else if (typeof image === 'object' && image.url) {
      imageUrl = image.url.trim();
    }
    
    if (!imageUrl) return null;
    
    // If it's already a full URL, return as is
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      return imageUrl;
    }
    
    // If the URL starts with /uploads, prepend the backend URL
    if (imageUrl.startsWith('/uploads')) {
      return `http://localhost:5858${imageUrl}`;
    }
    
    // Handle legacy /static prefix - replace with /uploads
    if (imageUrl.startsWith('/static')) {
      return `http://localhost:5858${imageUrl.replace('/static', '/uploads')}`;
    }
    
    // If it's a relative path without prefix (legacy data), add /uploads
    if (imageUrl.startsWith('products/') || imageUrl.startsWith('uploads/')) {
      const cleanUrl = imageUrl.startsWith('uploads/') ? imageUrl.substring(8) : imageUrl;
      return `http://localhost:5858/uploads/${cleanUrl}`;
    }
    
    // Default: assume it needs /uploads/ prefix
    return `http://localhost:5858/uploads/${imageUrl}`;
  };

  useEffect(() => {
    fetchVendorData();
  }, []);

  const fetchVendorData = async () => {
    try {
      // Get vendor profile
      const vendor = await vendorService.getMyProfile();
      setVendorProfile(vendor);

      // Fetch products for this vendor using the my-products endpoint
      const productsData = await vendorService.getMyProducts();
      console.log('Products data received:', productsData);
      console.log('First product images:', productsData.products?.[0]?.images);
      setProducts(productsData.products || []);
    } catch (error) {
      console.error('Error fetching vendor data:', error);
    } finally {
      setLoading(false);
    }
  };  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    try {
      // Use vendorService for vendor-specific product deletion
      await vendorService.deleteMyProduct(productId);
      setProducts(products.filter(p => p.id !== productId));
      alert('Product deleted successfully');
    } catch (error) {
      console.error('Error deleting product:', error);
      alert('Failed to delete product');
    }
  };

  const handleToggleActive = async (productId, currentStatus) => {
    try {
      // Use vendorService for vendor-specific product updates
      await vendorService.patchMyProduct(productId, {
        is_active: !currentStatus
      });
      setProducts(products.map(p => 
        p.id === productId ? { ...p, is_active: !currentStatus } : p
      ));
    } catch (error) {
      console.error('Error toggling product status:', error);
      alert('Failed to update product status');
    }
  };

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = 
      filter === 'all' ? true :
      filter === 'active' ? product.is_active :
      !product.is_active;
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl">Loading products...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Vendor Logo" className="w-12 h-12 object-contain mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Product Management</h1>
                <p className="text-sm text-gray-600">{vendorProfile?.business_name}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/vendor/dashboard"
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 transition-colors"
              >
                ← Back to Dashboard
              </Link>
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Vendor Info Banner */}
        {vendorProfile && (
          <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg shadow-lg p-6 mb-6 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="bg-white rounded-full p-3">
                  <svg className="w-8 h-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-2xl font-bold">{vendorProfile.business_name}</h2>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-sm opacity-90">
                      {vendorProfile.contact_email}
                    </span>
                    {vendorProfile.business_type && (
                      <>
                        <span className="text-white opacity-50">•</span>
                        <span className="text-sm opacity-90 capitalize">
                          {vendorProfile.business_type}
                        </span>
                      </>
                    )}
                    {vendorProfile.contact_phone && (
                      <>
                        <span className="text-white opacity-50">•</span>
                        <span className="text-sm opacity-90">
                          {vendorProfile.contact_phone}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                  vendorProfile.status === 'active' 
                    ? 'bg-green-500 text-white' 
                    : vendorProfile.status === 'pending'
                    ? 'bg-yellow-500 text-white'
                    : 'bg-red-500 text-white'
                }`}>
                  <span className="w-2 h-2 rounded-full bg-white mr-2"></span>
                  {vendorProfile.status ? vendorProfile.status.charAt(0).toUpperCase() + vendorProfile.status.slice(1) : 'Unknown'}
                </div>
                {vendorProfile.approval_status && (
                  <div className="text-xs mt-2 opacity-90">
                    Approval: <span className="font-semibold capitalize">{vendorProfile.approval_status}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Total Products</p>
            <p className="text-2xl font-bold text-gray-900">{products.length}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Active</p>
            <p className="text-2xl font-bold text-green-600">{products.filter(p => p.is_active).length}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Inactive</p>
            <p className="text-2xl font-bold text-yellow-600">{products.filter(p => !p.is_active).length}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <p className="text-sm text-gray-600">Low Stock</p>
            <p className="text-2xl font-bold text-red-600">{products.filter(p => p.stock < 10).length}</p>
          </div>
        </div>

        {/* Actions Bar */}
        <div className="bg-white shadow rounded-lg p-4 md:p-6 mb-6">
          <div className="flex flex-col gap-4">
            {/* Search and Add Button Row */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search products by name..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <Link
                to="/vendor/products/add"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap text-center"
              >
                + Add Product
              </Link>
            </div>

            {/* Filters and View Toggle Row */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  All ({products.length})
                </button>
                <button
                  onClick={() => setFilter('active')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'active'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Active ({products.filter(p => p.is_active).length})
                </button>
                <button
                  onClick={() => setFilter('inactive')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'inactive'
                      ? 'bg-yellow-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Inactive ({products.filter(p => !p.is_active).length})
                </button>
              </div>

              {/* View Toggle */}
              <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1.5 rounded transition-colors ${
                    viewMode === 'grid'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="Grid View"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1.5 rounded transition-colors ${
                    viewMode === 'list'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="List View"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No products found</h3>
            <p className="text-gray-600 mb-4">
              {searchTerm
                ? 'Try adjusting your search terms'
                : 'Get started by adding your first product'}
            </p>
            {!searchTerm && (
              <Link
                to="/vendor/products/add"
                className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Add Your First Product
              </Link>
            )}
          </div>
        ) : viewMode === 'grid' ? (
          /* Grid View */
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
            {filteredProducts.map((product) => (
              <div key={product.id} className="bg-white shadow-md rounded-lg overflow-hidden hover:shadow-xl transition-shadow duration-300">
                {/* Product Image */}
                <div className="relative h-48 sm:h-56 bg-gray-200 group">
                  {product.images && product.images.length > 0 && getImageUrl(product.images[0]) ? (
                    <img
                      src={getImageUrl(product.images[0])}
                      alt={product.images[0]?.alt_text || product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        console.warn('Image failed to load:', getImageUrl(product.images[0]));
                        e.target.style.display = 'none';
                        const placeholder = e.target.parentElement.querySelector('.no-image-placeholder');
                        if (placeholder) {
                          placeholder.classList.remove('hidden');
                        }
                      }}
                    />
                  ) : null}
                  <div className={`no-image-placeholder w-full h-full flex items-center justify-center ${product.images && product.images.length > 0 && getImageUrl(product.images[0]) ? 'hidden' : ''}`}>
                    <svg className="h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div className="absolute top-2 right-2 flex gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium shadow-sm ${
                      product.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {product.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  {product.stock < 10 && product.stock > 0 && (
                    <div className="absolute top-2 left-2">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 shadow-sm">
                        Low Stock
                      </span>
                    </div>
                  )}
                  {product.stock === 0 && (
                    <div className="absolute top-2 left-2">
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 shadow-sm">
                        Out of Stock
                      </span>
                    </div>
                  )}
                </div>

                {/* Product Info */}
                <div className="p-4">
                  <div className="mb-3">
                    <h3 className="text-base font-semibold text-gray-900 mb-1 line-clamp-1" title={product.name}>
                      {product.name}
                    </h3>
                    
                    {/* Vendor Badge */}
                    {product.vendor_info && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {product.vendor_info.business_name}
                        </span>
                        {product.vendor_info.business_type && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 capitalize">
                            {product.vendor_info.business_type}
                          </span>
                        )}
                      </div>
                    )}
                    
                    <p className="text-gray-600 text-xs mb-2 line-clamp-2 min-h-[2.5rem]">
                      {product.description || 'No description available'}
                    </p>
                  </div>

                  {/* Product Metadata */}
                  <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                    {product.category && (
                      <div className="flex items-center text-gray-600">
                        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                        </svg>
                        <span className="truncate">{product.category}</span>
                      </div>
                    )}
                    {product.sku && (
                      <div className="flex items-center text-gray-600">
                        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                        </svg>
                        <span className="truncate">{product.sku}</span>
                      </div>
                    )}
                    {product.metal_type && (
                      <div className="flex items-center text-gray-600">
                        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="truncate capitalize">{product.metal_type}</span>
                      </div>
                    )}
                    {product.jewelry_type && (
                      <div className="flex items-center text-gray-600">
                        <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                        </svg>
                        <span className="truncate capitalize">{product.jewelry_type}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
                    <div>
                      <p className="text-xl font-bold text-gray-900">
                        ₹{product.price?.toLocaleString()}
                      </p>
                      {product.original_price && product.original_price > product.price && (
                        <div className="flex items-center gap-2">
                          <p className="text-xs text-gray-500 line-through">
                            ₹{product.original_price.toLocaleString()}
                          </p>
                          <span className="text-xs font-medium text-green-600">
                            {Math.round(((product.original_price - product.price) / product.original_price) * 100)}% OFF
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-600 mb-1">Stock</p>
                      <p className={`text-lg font-bold ${
                        product.stock > 10 ? 'text-green-600' :
                        product.stock > 0 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {product.stock || 0}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="grid grid-cols-2 gap-2">
                    <Link
                      to={`/vendor/products/edit/${product.id}`}
                      className="flex items-center justify-center bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 transition-colors text-xs font-medium"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit
                    </Link>
                    <button
                      onClick={() => handleToggleActive(product.id, product.is_active)}
                      className={`flex items-center justify-center px-3 py-2 rounded transition-colors text-xs font-medium ${
                        product.is_active
                          ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                          : 'bg-green-600 text-white hover:bg-green-700'
                      }`}
                    >
                      {product.is_active ? (
                        <>
                          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                          </svg>
                          Hide
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          Show
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleDeleteProduct(product.id)}
                      className="col-span-2 flex items-center justify-center bg-red-600 text-white px-3 py-2 rounded hover:bg-red-700 transition-colors text-xs font-medium"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete Product
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* List View */
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Product
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden md:table-cell">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden xl:table-cell">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stock
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden lg:table-cell">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredProducts.map((product) => (
                    <tr key={product.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-12 w-12 sm:h-16 sm:w-16">
                            {product.images && product.images.length > 0 && getImageUrl(product.images[0]) ? (
                              <img
                                src={getImageUrl(product.images[0])}
                                alt={product.images[0]?.alt_text || product.name}
                                className="h-12 w-12 sm:h-16 sm:w-16 rounded object-cover"
                                onError={(e) => {
                                  console.warn('Image failed to load:', getImageUrl(product.images[0]));
                                  e.target.style.display = 'none';
                                  const placeholder = e.target.parentElement.querySelector('.no-image-placeholder');
                                  if (placeholder) {
                                    placeholder.classList.remove('hidden');
                                  }
                                }}
                              />
                            ) : null}
                            <div className={`no-image-placeholder h-12 w-12 sm:h-16 sm:w-16 rounded bg-gray-200 flex items-center justify-center ${product.images && product.images.length > 0 && getImageUrl(product.images[0]) ? 'hidden' : ''}`}>
                              <svg className="h-6 w-6 sm:h-8 sm:w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                              {product.name}
                            </div>
                            {product.vendor_info && (
                              <div className="flex items-center gap-1 mt-1">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                  {product.vendor_info.business_name}
                                </span>
                              </div>
                            )}
                            {product.sku && (
                              <div className="text-xs text-gray-500 mt-1">
                                SKU: {product.sku}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap hidden md:table-cell">
                        <div className="text-sm text-gray-900">{product.category || 'N/A'}</div>
                        {product.metal_type && (
                          <div className="text-xs text-gray-500 capitalize">Metal: {product.metal_type}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap hidden xl:table-cell">
                        {product.jewelry_type ? (
                          <div className="flex flex-col">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 capitalize">
                              {product.jewelry_type}
                            </span>
                            {product.metal_purity && (
                              <span className="text-xs text-gray-500 mt-1">{product.metal_purity}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">₹{product.price?.toLocaleString()}</div>
                        {product.original_price && product.original_price > product.price && (
                          <div className="text-xs text-gray-500 line-through">
                            ₹{product.original_price.toLocaleString()}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          product.stock > 10 ? 'bg-green-100 text-green-800' :
                          product.stock > 0 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {product.stock || 0}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap hidden lg:table-cell">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          product.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {product.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <Link
                            to={`/vendor/products/edit/${product.id}`}
                            className="text-blue-600 hover:text-blue-900"
                            title="Edit"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </Link>
                          <button
                            onClick={() => handleToggleActive(product.id, product.is_active)}
                            className={product.is_active ? 'text-yellow-600 hover:text-yellow-900' : 'text-green-600 hover:text-green-900'}
                            title={product.is_active ? 'Deactivate' : 'Activate'}
                          >
                            {product.is_active ? (
                              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                              </svg>
                            ) : (
                              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            )}
                          </button>
                          <button
                            onClick={() => handleDeleteProduct(product.id)}
                            className="text-red-600 hover:text-red-900"
                            title="Delete"
                          >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VendorProducts;
