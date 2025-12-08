import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import vendorService from '../../services/vendorService';
import api from '../../services/api';

const VendorAddProduct = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { id: productId } = useParams(); // Get product ID from URL for edit mode
  const isEditMode = Boolean(productId);
  
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEditMode);
  const [imageFiles, setImageFiles] = useState([]);
  const [imagePreviews, setImagePreviews] = useState([]);
  const [existingImages, setExistingImages] = useState([]); // For edit mode

  const [formData, setFormData] = useState({
    // Basic Information
    name: '',
    description: '',
    
    // Category & Classification
    category: '',
    subcategory: '',
    jewelry_type: '', // Jewelry type (ring, necklace, etc.)
    
    // Pricing
    price: '',
    original_price: '',
    discount_percentage: '',
    
    // Inventory
    stock: '',
    sku: '',
    
    // Jewelry Specific
    metal_type: '',
    stone_type: '',
    
    // Additional fields
    weight: '',
    dimensions: '',
    is_active: true
  });

  const [errors, setErrors] = useState({});

  // Category Options
  const categories = [
    'Rings',
    'Earrings',
    'Necklaces',
    'Bracelets',
    'Pendents',
    'Bangles',
    'Chains',
    'Anklets'
  ];

  // Subcategory Options
  const subcategories = [
    'Diamond',
    'Gold',
    'Rose Gold',
    'White Gold',
    'Platinum',
    'Silver',
    'Pearl',
    'Gemstone',
    'Fashion Jewelry'
  ];

  // Jewelry Types - matching backend enum values
  const jewelryTypes = [
    { value: 'ring', label: 'Ring' },
    { value: 'necklace', label: 'Necklace' },
    { value: 'earrings', label: 'Earrings' },
    { value: 'bracelet', label: 'Bracelet' },
    { value: 'pendant', label: 'Pendant' },
    { value: 'brooch', label: 'Brooch' },
    { value: 'watch', label: 'Watch' },
    { value: 'anklet', label: 'Anklet' },
    { value: 'chain', label: 'Chain' },
    { value: 'charm', label: 'Charm' },
    { value: 'cufflinks', label: 'Cufflinks' },
    { value: 'tiara', label: 'Tiara' },
    { value: 'other', label: 'Other' }
  ];

  // Metal Types - matching backend enum values
  const metalTypes = [
    { value: '14k_gold', label: '14K Gold' },
    { value: '18k_gold', label: '18K Gold' },
    { value: '22k_gold', label: '22K Gold' },
    { value: '24k_gold', label: '24K Gold' },
    { value: 'white_gold', label: 'White Gold' },
    { value: 'rose_gold', label: 'Rose Gold' },
    { value: 'silver', label: 'Silver' },
    { value: 'sterling_silver', label: 'Sterling Silver' },
    { value: 'platinum', label: 'Platinum' },
    { value: 'palladium', label: 'Palladium' },
    { value: 'titanium', label: 'Titanium' },
    { value: 'stainless_steel', label: 'Stainless Steel' },
    { value: 'copper', label: 'Copper' },
    { value: 'brass', label: 'Brass' },
    { value: 'other', label: 'Other' }
  ];

  // Stone Types - matching backend enum values
  const stoneTypes = [
    { value: 'diamond', label: 'Diamond' },
    { value: 'emerald', label: 'Emerald' },
    { value: 'ruby', label: 'Ruby' },
    { value: 'sapphire', label: 'Sapphire' },
    { value: 'pearl', label: 'Pearl' },
    { value: 'amethyst', label: 'Amethyst' },
    { value: 'aquamarine', label: 'Aquamarine' },
    { value: 'citrine', label: 'Citrine' },
    { value: 'garnet', label: 'Garnet' },
    { value: 'opal', label: 'Opal' },
    { value: 'peridot', label: 'Peridot' },
    { value: 'topaz', label: 'Topaz' },
    { value: 'turquoise', label: 'Turquoise' },
    { value: 'onyx', label: 'Onyx' },
    { value: 'jade', label: 'Jade' },
    { value: 'coral', label: 'Coral' },
    { value: 'moonstone', label: 'Moonstone' },
    { value: 'tanzanite', label: 'Tanzanite' },
    { value: 'cubic_zirconia', label: 'Cubic Zirconia' },
    { value: 'synthetic', label: 'Synthetic' },
    { value: 'other', label: 'Other' }
  ];

  // Helper function to normalize/map legacy values to new enum values
  const normalizeMetalType = (value) => {
    if (!value) return '';
    const lowerValue = value.toLowerCase();
    
    // Map legacy values to new enum values
    const metalMapping = {
      'gold': '18k_gold',
      'silver': 'sterling_silver',
      'white gold': 'white_gold',
      'rose gold': 'rose_gold',
      'platinum': 'platinum'
    };
    
    // If it's already a valid enum value, return as is
    if (metalTypes.some(m => m.value === lowerValue)) {
      return lowerValue;
    }
    
    // Try to map from legacy value
    return metalMapping[lowerValue] || value;
  };

  const normalizeStoneType = (value) => {
    if (!value) return '';
    const lowerValue = value.toLowerCase();
    
    // Map legacy values
    const stoneMapping = {
      'cz': 'cubic_zirconia',
      'cubic zirconia': 'cubic_zirconia'
    };
    
    // If it's already a valid enum value, return as is
    if (stoneTypes.some(s => s.value === lowerValue)) {
      return lowerValue;
    }
    
    // Try to map from legacy value
    return stoneMapping[lowerValue] || value;
  };

  // Helper function to get full image URL
  const getImageUrl = (image) => {
    if (!image) return null;
    
    let imageUrl = null;
    
    if (typeof image === 'string') {
      imageUrl = image;
    } else if (typeof image === 'object' && image.url) {
      imageUrl = image.url;
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

  // Fetch product data in edit mode
  useEffect(() => {
    if (isEditMode && productId) {
      fetchProductData();
    }
  }, [isEditMode, productId]);

  const fetchProductData = async () => {
    try {
      setInitialLoading(true);
      const product = await vendorService.getMyProduct(productId);
      console.log('Fetched product for edit:', product);
      console.log('Product images:', product.images);
      console.log('Product category:', product.category);
      console.log('Product subcategory:', product.subcategory);
      console.log('Product metal_type:', product.metal_type);
      console.log('Product stone_type:', product.stone_type);
      
      // Populate form data - ensure dropdown values match exactly
      setFormData({
        name: product.name || '',
        description: product.description || '',
        category: product.category || '',
        subcategory: product.subcategory || '',
        jewelry_type: product.jewelry_type || '',
        price: product.price || '',
        original_price: product.original_price || product.compare_at_price || '',
        discount_percentage: product.discount_percentage || '',
        stock: product.stock || product.stock_quantity || '',
        sku: product.sku || '',
        metal_type: normalizeMetalType(product.metal_type) || '',
        stone_type: normalizeStoneType(product.stone_type) || '',
        weight: product.weight?.value || product.weight || '',
        dimensions: product.dimensions?.length ? `${product.dimensions.length}mm x ${product.dimensions.width}mm` : (product.dimensions || ''),
        is_active: product.is_active !== undefined ? product.is_active : true
      });

      console.log('Form data set to:', {
        category: product.category,
        subcategory: product.subcategory,
        jewelry_type: product.jewelry_type,
        metal_type: product.metal_type,
        metal_type_normalized: normalizeMetalType(product.metal_type),
        stone_type: product.stone_type,
        stone_type_normalized: normalizeStoneType(product.stone_type)
      });

      // Handle existing images with better error handling
      if (product.images && product.images.length > 0) {
        console.log('Processing images...');
        const images = product.images.map((img, index) => {
          const url = getImageUrl(img);
          console.log(`Image ${index}:`, img, 'URL:', url);
          return {
            url: url,
            alt_text: typeof img === 'object' ? (img.alt_text || product.name) : product.name,
            is_primary: typeof img === 'object' ? (img.is_primary || index === 0) : (index === 0)
          };
        }).filter(img => img.url); // Filter out any null URLs
        
        console.log('Processed images:', images);
        setExistingImages(images);
        setImagePreviews(images.map(img => img.url));
      } else {
        console.log('No images found in product');
        setExistingImages([]);
        setImagePreviews([]);
      }
    } catch (error) {
      console.error('Error fetching product:', error);
      console.error('Error details:', error.response?.data);
      alert('Failed to load product data: ' + (error.response?.data?.detail || error.message));
      navigate('/vendor/products');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }

    // Auto-calculate discount percentage
    if (name === 'price' || name === 'original_price') {
      const price = name === 'price' ? parseFloat(value) : parseFloat(formData.price);
      const originalPrice = name === 'original_price' ? parseFloat(value) : parseFloat(formData.original_price);
      
      if (price && originalPrice && originalPrice > price) {
        const discount = ((originalPrice - price) / originalPrice * 100).toFixed(2);
        setFormData(prev => ({ ...prev, discount_percentage: discount }));
      }
    }
  };

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    
    if (imageFiles.length + files.length > 5) {
      alert('You can upload a maximum of 5 images');
      return;
    }

    setImageFiles(prev => [...prev, ...files]);

    // Create previews
    files.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreviews(prev => [...prev, reader.result]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index) => {
    // Check if this is an existing image or a newly uploaded one
    if (index < existingImages.length) {
      // Removing an existing image
      setExistingImages(prev => prev.filter((_, i) => i !== index));
    } else {
      // Removing a newly uploaded image
      const newIndex = index - existingImages.length;
      setImageFiles(prev => prev.filter((_, i) => i !== newIndex));
    }
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Product name is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!formData.category) {
      newErrors.category = 'Category is required';
    }

    if (!formData.price || parseFloat(formData.price) <= 0) {
      newErrors.price = 'Valid price is required';
    }

    if (!formData.stock || parseInt(formData.stock) < 0) {
      newErrors.stock = 'Valid stock quantity is required';
    }

    if (!formData.sku.trim()) {
      newErrors.sku = 'SKU is required';
    }

    // In add mode, at least one image is required
    // In edit mode, images are optional (existing images are kept)
    if (!isEditMode && imageFiles.length === 0) {
      newErrors.images = 'At least one product image is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      alert('Please fill in all required fields');
      return;
    }

    setLoading(true);

    try {
      if (isEditMode) {
        // Update existing product using vendor endpoint with form data
        const formDataToSend = new FormData();

        // Append all form fields
        Object.keys(formData).forEach(key => {
          if (formData[key] !== null && formData[key] !== '') {
            formDataToSend.append(key, formData[key]);
          }
        });

        // Append new images if any
        imageFiles.forEach((file, index) => {
          formDataToSend.append('images', file);
        });

        // If there are existing images to keep, send their URLs
        if (existingImages.length > 0) {
          formDataToSend.append('existing_images', JSON.stringify(existingImages.map(img => img.url)));
        }

        const response = await api.put(`/api/products/my-products/${productId}/form`, formDataToSend, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        alert('Product updated successfully!');
        navigate('/vendor/products');
      } else {
        // Create new product
        const formDataToSend = new FormData();

        // Debug: Log all form data being sent
        console.log('Form data being submitted:', formData);
        console.log('Image files count:', imageFiles.length);

        // Append all form fields
        Object.keys(formData).forEach(key => {
          if (formData[key] !== null && formData[key] !== '') {
            formDataToSend.append(key, formData[key]);
            console.log(`Adding field ${key}:`, formData[key]);
          } else {
            console.log(`Skipping empty field ${key}:`, formData[key]);
          }
        });

        // Append images
        imageFiles.forEach((file, index) => {
          formDataToSend.append('images', file);
          console.log(`Adding image ${index}:`, file.name);
        });

        // Debug: Log final form data entries
        console.log('Final FormData entries:');
        for (let pair of formDataToSend.entries()) {
          console.log(pair[0], typeof pair[1] === 'object' ? pair[1].name || pair[1] : pair[1]);
        }

        const response = await api.post('/api/products', formDataToSend, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        alert('Product added successfully!');
        navigate('/vendor/products');
      }
    } catch (error) {
      console.error('Error saving product:', error);
      console.error('Error response data:', error.response?.data);
      console.error('Error response status:', error.response?.status);
      console.error('Error response headers:', error.response?.headers);
      
      let errorMessage = `Failed to ${isEditMode ? 'update' : 'add'} product. `;
      
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Handle validation errors array
          const validationErrors = error.response.data.detail.map(err => 
            `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`
          ).join(', ');
          errorMessage += validationErrors;
        } else {
          // Handle single error message
          errorMessage += error.response.data.detail;
        }
      } else if (error.response?.status === 400) {
        errorMessage += 'Please check all required fields are filled correctly.';
      } else if (error.response?.status === 403) {
        errorMessage += 'You do not have permission to perform this action.';
      } else if (error.response?.status === 401) {
        errorMessage += 'Please log in again.';
      } else {
        errorMessage += 'Please try again.';
      }
      
      alert(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Vendor Logo" className="w-12 h-12 object-contain mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {isEditMode ? 'Edit Product' : 'Add New Product'}
                </h1>
                <p className="text-sm text-gray-600">
                  {isEditMode ? 'Update product details below' : 'Fill in the product details below'}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/vendor/products"
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300 transition-colors"
              >
                ← Back to Products
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

      {initialLoading ? (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-600">Loading product data...</p>
          </div>
        </div>
      ) : (
      <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Debug Info - Remove this in production */}
        {isEditMode && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-semibold text-blue-900 mb-2">Debug Info (Edit Mode)</h3>
            <div className="text-xs text-blue-800 space-y-1">
              <p><strong>Product ID:</strong> {productId}</p>
              <p><strong>Form Data Loaded:</strong> {formData.name ? 'Yes ✓' : 'No ✗'}</p>
              <p><strong>Category:</strong> "{formData.category}"</p>
              <p><strong>Subcategory:</strong> "{formData.subcategory}"</p>
              <p><strong>Jewelry Type:</strong> "{formData.jewelry_type}"</p>
              <p><strong>Metal Type:</strong> "{formData.metal_type}"</p>
              <p><strong>Stone Type:</strong> "{formData.stone_type}"</p>
              <p><strong>Images Loaded:</strong> {existingImages.length} existing, {imageFiles.length} new</p>
              <p><strong>Image Previews:</strong> {imagePreviews.length}</p>
            </div>
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Basic Information
            </h2>
            
            <div className="space-y-4">
              {/* Product Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Product Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., PURE 14K GOLD YELLOW BEE EARRING"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.name && (
                  <p className="text-red-500 text-xs mt-1">{errors.name}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Product title - This is the main name customers will see
                </p>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Detailed description of jewelry..."
                  rows="5"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.description ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.description && (
                  <p className="text-red-500 text-xs mt-1">{errors.description}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Helps SEO & customers - Provide detailed information about the jewelry
                </p>
              </div>
            </div>
          </div>

          {/* Category & Classification Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Category & Classification
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category <span className="text-red-500">*</span>
                </label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.category ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select Category</option>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                {errors.category && (
                  <p className="text-red-500 text-xs mt-1">{errors.category}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Product type (e.g., Earrings, Rings, Pendents)
                </p>
              </div>

              {/* Subcategory */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subcategory
                </label>
                <select
                  name="subcategory"
                  value={formData.subcategory}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Subcategory</option>
                  {subcategories.map(sub => (
                    <option key={sub} value={sub}>{sub}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Finer classification (e.g., "Diamond", "Rose Gold")
                </p>
              </div>

              {/* Jewelry Type */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Jewelry Type
                </label>
                <select
                  name="jewelry_type"
                  value={formData.jewelry_type}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Jewelry Type</option>
                  {jewelryTypes.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Specific jewelry classification (e.g., Ring, Necklace, Earrings)
                </p>
              </div>
            </div>
          </div>

          {/* Pricing Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Price & Discount
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Price */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Price (₹) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="price"
                  value={formData.price}
                  onChange={handleInputChange}
                  placeholder="200"
                  step="0.01"
                  min="0"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.price ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.price && (
                  <p className="text-red-500 text-xs mt-1">{errors.price}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Selling price
                </p>
              </div>

              {/* Original Price */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Original Price (₹)
                </label>
                <input
                  type="number"
                  name="original_price"
                  value={formData.original_price}
                  onChange={handleInputChange}
                  placeholder="250"
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Before discount
                </p>
              </div>

              {/* Discount Percentage */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Discount (%)
                </label>
                <input
                  type="number"
                  name="discount_percentage"
                  value={formData.discount_percentage}
                  onChange={handleInputChange}
                  placeholder="Auto-calculated"
                  step="0.01"
                  min="0"
                  max="100"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  readOnly
                />
                <p className="text-xs text-gray-500 mt-1">
                  Auto-calculated
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Purpose: Dynamic pricing - Set prices and discounts for your products
            </p>
          </div>

          {/* Stock & SKU Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Stock & SKU
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Stock */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Stock Quantity <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  name="stock"
                  value={formData.stock}
                  onChange={handleInputChange}
                  placeholder="10"
                  min="0"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.stock ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.stock && (
                  <p className="text-red-500 text-xs mt-1">{errors.stock}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Available quantity
                </p>
              </div>

              {/* SKU */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  SKU (Stock Keeping Unit) <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  name="sku"
                  value={formData.sku}
                  onChange={handleInputChange}
                  placeholder="EG_BEE_001"
                  className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.sku ? 'border-red-500' : 'border-gray-300'
                  }`}
                />
                {errors.sku && (
                  <p className="text-red-500 text-xs mt-1">{errors.sku}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Unique product identifier
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-4">
              Purpose: Inventory tracking - Manage your product inventory efficiently
            </p>
          </div>

          {/* Material Information Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Material Information
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Metal Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metal Type
                </label>
                <select
                  name="metal_type"
                  value={formData.metal_type}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Metal Type</option>
                  {metalTypes.map(metal => (
                    <option key={metal.value} value={metal.value}>{metal.label}</option>
                  ))}
                  {/* Show current value if it's not in the list (legacy data) */}
                  {formData.metal_type && !metalTypes.some(m => m.value === formData.metal_type) && (
                    <option value={formData.metal_type}>{formData.metal_type} (Legacy)</option>
                  )}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Material info (e.g., Gold, Silver)
                </p>
              </div>

              {/* Stone Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Stone Type
                </label>
                <select
                  name="stone_type"
                  value={formData.stone_type}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select Stone Type</option>
                  {stoneTypes.map(stone => (
                    <option key={stone.value} value={stone.value}>{stone.label}</option>
                  ))}
                  {/* Show current value if it's not in the list (legacy data) */}
                  {formData.stone_type && !stoneTypes.some(s => s.value === formData.stone_type) && (
                    <option value={formData.stone_type}>{formData.stone_type} (Legacy)</option>
                  )}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Purpose: Jewelry stone detail (e.g., Diamond, Ruby)
                </p>
              </div>

              {/* Weight */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Weight (grams)
                </label>
                <input
                  type="number"
                  name="weight"
                  value={formData.weight}
                  onChange={handleInputChange}
                  placeholder="5.5"
                  step="0.01"
                  min="0"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Product weight in grams
                </p>
              </div>

              {/* Dimensions */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dimensions
                </label>
                <input
                  type="text"
                  name="dimensions"
                  value={formData.dimensions}
                  onChange={handleInputChange}
                  placeholder="e.g., 10mm x 5mm"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Product dimensions
                </p>
              </div>
            </div>
          </div>

          {/* Image Upload Section */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Image Upload
            </h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Product Images <span className="text-red-500">*</span>
              </label>
              
              {/* Upload Button */}
              <div className="mb-4">
                <label className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Choose Images
                  <input
                    type="file"
                    multiple
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                  />
                </label>
                <span className="ml-3 text-sm text-gray-500">
                  Upload up to 5 images (JPG, PNG)
                </span>
              </div>

              {errors.images && (
                <p className="text-red-500 text-xs mb-2">{errors.images}</p>
              )}

              {/* Image Previews */}
              {imagePreviews.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {imagePreviews.map((preview, index) => {
                    const isExistingImage = index < existingImages.length;
                    const imageData = isExistingImage ? existingImages[index] : null;
                    
                    return (
                      <div key={`${isExistingImage ? 'existing' : 'new'}-${index}`} className="relative group">
                        <div className="relative w-full h-32 bg-gray-100 rounded-lg border-2 border-gray-300 overflow-hidden">
                          <img
                            src={preview}
                            alt={imageData?.alt_text || `Preview ${index + 1}`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              console.error('Image failed to load:', preview);
                              e.target.style.display = 'none';
                              const parent = e.target.parentElement;
                              if (parent && !parent.querySelector('.error-placeholder')) {
                                const errorDiv = document.createElement('div');
                                errorDiv.className = 'error-placeholder absolute inset-0 flex items-center justify-center bg-gray-200';
                                errorDiv.innerHTML = `
                                  <div class="text-center text-gray-500">
                                    <svg class="w-8 h-8 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <span class="text-xs">Failed to load</span>
                                  </div>
                                `;
                                parent.appendChild(errorDiv);
                              }
                            }}
                          />
                        </div>
                        <button
                          type="button"
                          onClick={() => removeImage(index)}
                          className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full p-1.5 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-700"
                          title="Remove image"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                        
                        {/* Badges */}
                        <div className="absolute bottom-1 left-1 flex gap-1">
                          {index === 0 && (
                            <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded shadow-sm font-medium">
                              Primary
                            </span>
                          )}
                        </div>
                        
                        {isExistingImage && (
                          <span className="absolute top-1 left-1 bg-green-600 text-white text-xs px-2 py-0.5 rounded shadow-sm font-medium">
                            Saved
                          </span>
                        )}
                        {!isExistingImage && (
                          <span className="absolute top-1 left-1 bg-orange-600 text-white text-xs px-2 py-0.5 rounded shadow-sm font-medium">
                            New
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              
              {/* No images message in edit mode */}
              {isEditMode && imagePreviews.length === 0 && !initialLoading && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                  <svg className="w-10 h-10 text-yellow-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-sm text-yellow-800 font-medium">No images found for this product</p>
                  <p className="text-xs text-yellow-700 mt-1">Upload new images below</p>
                </div>
              )}
              
              <p className="text-xs text-gray-500 mt-4">
                Purpose: Gallery view - Upload multiple images for a better customer experience. The first image will be the main product image.
              </p>
            </div>
          </div>

          {/* Product Status */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 border-b pb-3">
              Product Status
            </h2>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                name="is_active"
                checked={formData.is_active}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label className="ml-2 block text-sm text-gray-900">
                Make product active and visible to customers
              </label>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4">
            <Link
              to="/vendor/products"
              className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className={`px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {isEditMode ? 'Updating Product...' : 'Adding Product...'}
                </span>
              ) : (
                isEditMode ? 'Update Product' : 'Add Product'
              )}
            </button>
          </div>
        </form>
      </div>
      )}
    </div>
  );
};

export default VendorAddProduct;
