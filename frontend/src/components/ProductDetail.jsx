import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import productService from '../services/productService';
import { formatProduct } from '../utils/imageUtils';
import Footer from './Footer';
import ImageSlider from './common/ImageSlider';

const ProductDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
    const { addToCart, cartItems, isInCart, getCartCount, getItemQuantity, updateQuantity, removeFromCart } = useCart();
  const { addToWishlist, removeFromWishlist, isInWishlist, wishlistItems } = useWishlist();
  const { user, isAuthenticated } = useAuth();
  const [product, setProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [selectedSize, setSelectedSize] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [activeTab, setActiveTab] = useState('descriptions');

  // Fetch product details from backend
  useEffect(() => {
    const fetchProduct = async () => {
      if (!id) {
        setError('Product ID is missing');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        console.log('Fetching product with ID:', id);
        
        const response = await productService.getProductById(id);
        console.log('Product response:', response);
        
        // The response might be the product directly or wrapped in a data object
        const productData = response.product || response.data || response;
        
        // Format the product
        const formattedProduct = formatProduct(productData);
        console.log('Formatted product:', formattedProduct);
        
        setProduct(formattedProduct);
        
        // Set default selections
        if (productData.sizes && productData.sizes.length > 0) {
          setSelectedSize(productData.sizes[0].size || productData.sizes[0]);
        }
        if (productData.metal_type) {
          setSelectedColor(productData.metal_type);
        }
      } catch (err) {
        console.error('Error fetching product:', err);
        setError('Failed to load product details. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  // Helper functions
  const getImageUrl = (image) => {
    if (!image) return '/Images/default.png';
    if (typeof image === 'string') return image;
    if (image.url) return image.url;
    return '/Images/default.png';
  };

  const getProductImages = () => {
    if (!product) return [];
    if (product.images && Array.isArray(product.images)) {
      return product.images.map(img => getImageUrl(img));
    }
    if (product.image) {
      return [product.image];
    }
    return ['/Images/default.png'];
  };

  const images = getProductImages();

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-[#3E2F2A] mx-auto mb-4"></div>
          <p className="text-[#3E2F2A] text-lg">Loading product details...</p>
        </div>
      </div>
    );
  }

  // Show error state
  if (error || !product) {
    return (
      <div className="min-h-screen bg-[#F4E7D0] flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-[#3E2F2A] mb-4">Product Not Found</h2>
          <p className="text-gray-600 mb-6">{error || 'The product you are looking for does not exist.'}</p>
          <button
            onClick={() => navigate('/shop')}
            className="bg-[#3E2F2A] text-white px-6 py-3 hover:bg-opacity-90 transition-colors"
          >
            Back to Shop
          </button>
        </div>
      </div>
    );
  }

  const handleQuantityChange = (type) => {
    if (isInCart(product.id)) {
      // Control cart quantity when item is already in cart
      const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
      if (!item) return;
      
      if (type === 'increment') {
        updateQuantity(item.cartId, item.quantity + 1);
      } else if (type === 'decrement') {
        if (item.quantity > 1) {
          updateQuantity(item.cartId, item.quantity - 1);
        } else {
          removeFromCart(item.cartId);
        }
      }
    } else {
      // Control local state when item is not in cart
      if (type === 'increment') {
        setQuantity(prev => prev + 1);
      } else if (type === 'decrement' && quantity > 1) {
        setQuantity(prev => prev - 1);
      }
    }
  };

  const handleAddToCart = () => {
    if (!product) return;
    
    const productToAdd = {
      id: product.id,
      name: product.name,
      price: product._rawPrice || product.price,
      originalPrice: product._rawOldPrice || product.oldPrice,
      image: images[0],
      selectedColor: selectedColor,
      selectedSize: selectedSize,
      quantity: quantity
    };
    addToCart(productToAdd);
  };

  const handleWishlistToggle = () => {
    if (!product) return;
    
    const wishlistProduct = {
      id: product.id,
      name: product.name,
      price: product._rawPrice || product.price,
      originalPrice: product._rawOldPrice || product.oldPrice,
      image: images[0]
    };
    
    if (isInWishlist(product.id)) {
      removeFromWishlist(product.id);
    } else {
      addToWishlist(wishlistProduct);
    }
  };

  const handleBuyNow = () => {
    if (!product) return;
    
    // Add to cart if not already in cart
    if (!isInCart(product.id)) {
      const productToAdd = {
        id: product.id,
        name: product.name,
        price: product._rawPrice || product.price,
        originalPrice: product._rawOldPrice || product.oldPrice,
        image: images[0],
        selectedColor: selectedColor,
        selectedSize: selectedSize,
        quantity: quantity
      };
      addToCart(productToAdd);
    }
    
    // Navigate to cart page
    navigate('/cart');
  };

  return (
    <div className="min-h-screen bg-[#F4E7D0]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white px-[5%] py-5">
        <div className="max-w-[1400px] mx-auto flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3 cursor-pointer">
            <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Soara Logo" className="w-20 h-20 object-contain" />
          </Link>

          <nav className="hidden md:flex gap-11 uppercase text-[13px] tracking-wider font-light">
            <Link to="/rings" className="hover:text-yellow-500 transition-colors">RINGS</Link>
            <Link to="/earrings" className="hover:text-yellow-500 transition-colors">EARRINGS</Link>
            <Link to="/bracelets" className="hover:text-yellow-500 transition-colors">BRACELETS</Link>
            <Link to="/pendents" className="hover:text-yellow-500 transition-colors">PENDENTS</Link>
            <Link to="/necklaces" className="hover:text-yellow-500 transition-colors">NECKLACES</Link>
          </nav>

          <div className="flex gap-5 items-center">
            <button className="hover:text-yellow-500 transition-colors">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </button>
            <Link to="/wishlist" className="hover:text-yellow-500 transition-colors relative">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
              {wishlistItems.length > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {wishlistItems.length}
                </span>
              )}
            </Link>
            <button className="hover:text-yellow-500 transition-colors">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                <circle cx="12" cy="7" r="4"></circle>
              </svg>
            </button>
            <Link to="/cart" className="hover:text-yellow-500 transition-colors relative">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <path d="M16 10a4 4 0 0 1-8 0"></path>
              </svg>
              {getCartCount() > 0 && (
                <span className="absolute -top-2 -right-2 bg-yellow-500 text-[#3E2F2A] text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {getCartCount()}
                </span>
              )}
            </Link>
          </div>
        </div>
      </header>

      {/* Breadcrumb */}
      <div className="px-[5%] py-4 bg-[#F4E7D0]">
        <div className="max-w-[1400px] mx-auto flex items-center gap-2 text-sm">
          <Link to="/" className="text-gray-700 hover:text-gray-900">HOME</Link>
          <span className="text-gray-500">›</span>
          <Link to="/shop" className="text-gray-700 hover:text-gray-900">SHOP</Link>
          <span className="text-gray-500">›</span>
          <span className="text-gray-900 font-medium uppercase">{product.name}</span>
        </div>
      </div>

      {/* Product Detail Section */}
      <div className="px-[5%] py-12 bg-[#F4E7D0]">
        <div className="max-w-[1400px] mx-auto">
          <div className="grid grid-cols-2 gap-12 mb-16">
            {/* Left - Images */}
            <div>
              {/* Image Slider */}
              <div className="bg-white rounded-lg overflow-hidden mb-4">
                <ImageSlider 
                  images={product.images || [product.image].filter(Boolean)} 
                  productName={product.name}
                  className="w-full h-[500px]"
                />
              </div>
              
              {/* Image count and info */}
              {product.images && product.images.length > 1 && (
                <div className="text-center text-sm text-gray-600 mb-4">
                  <span className="bg-gray-100 px-3 py-1 rounded-full">
                    📷 {product.images.length} images
                  </span>
                </div>
              )}
            </div>

            {/* Right - Product Info */}
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-4">{product?.name || 'Product Name'}</h1>

              {product.brand && (
                <div className="mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <span className="text-base text-gray-700">Brand: <span className="font-semibold text-gray-900">{product.brand}</span></span>
                </div>
              )}

              <div className="flex items-center gap-2 mb-4">
                <div className="flex gap-0.5">
                  {[...Array(5)].map((_, i) => (
                    <svg key={i} className="w-4 h-4 fill-current text-yellow-400" viewBox="0 0 24 24">
                      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                    </svg>
                  ))}
                </div>
                <span className="text-sm text-gray-700">5.0 (26 Reviews)</span>
              </div>

              <div className="flex items-center gap-3 mb-6">
                <span className="text-3xl font-bold text-gray-900">
                  {product.price}
                </span>
                {product.oldPrice && (
                  <span className="text-xl text-gray-400 line-through">
                    {product.oldPrice}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 mb-4 text-sm text-gray-700">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <span>24 People are viewing this right now</span>
              </div>

              <div className="mb-6">
                <span className="text-sm text-gray-700">Only </span>
                <span className="text-sm font-semibold text-red-600">8 items</span>
                <span className="text-sm text-gray-700"> left in stock</span>
                <div className="w-full h-1 bg-gray-300 rounded-full mt-2">
                  <div className="w-[30%] h-full bg-red-600 rounded-full"></div>
                </div>
              </div>

              {/* Color/Diamond Shape Selection */}
              {product?.diamond_shape && (
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-sm font-medium text-gray-900">Diamond Shape:</span>
                    <span className="text-sm text-gray-700">{product.diamond_shape}</span>
                  </div>
                </div>
              )}

              {/* Size Selection */}
              {product?.available_sizes && product.available_sizes.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-900 mb-3">Size</label>
                  <select 
                    value={selectedSize}
                    onChange={(e) => setSelectedSize(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-400 bg-white text-gray-700 rounded focus:outline-none focus:border-gray-600"
                  >
                    {product.available_sizes.map((size) => (
                      <option key={size} value={size}>{size}</option>
                    ))}
                  </select>
                </div>
              )}              {/* Quantity */}
              <div className="mb-6">
                <div className="flex items-center gap-4">
                  <button 
                    onClick={() => handleQuantityChange('decrement')}
                    className="w-10 h-10 border border-gray-400 rounded flex items-center justify-center hover:bg-gray-100 transition-colors"
                  >
                    −
                  </button>
                  <span className="text-lg font-medium text-gray-900 w-12 text-center">
                    {isInCart(product.id) ? getItemQuantity(product.id) : quantity}
                  </span>
                  <button 
                    onClick={() => handleQuantityChange('increment')}
                    className="w-10 h-10 border border-gray-400 rounded flex items-center justify-center hover:bg-gray-100 transition-colors"
                  >
                    +
                  </button>
                  {isInCart(product.id) ? (
                    <button 
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white py-3 text-sm uppercase tracking-wider font-medium transition-colors rounded"
                    >
                      ADDED
                    </button>
                  ) : (
                    <button 
                      onClick={handleAddToCart}
                      className="flex-1 bg-[#3E2F2A] text-white py-3 text-sm uppercase tracking-wider font-medium hover:bg-[#2d2219] transition-colors rounded"
                    >
                      ADD TO CART
                    </button>
                  )}
                  <button 
                    onClick={handleWishlistToggle}
                    className={`w-12 h-12 border rounded flex items-center justify-center transition-colors ${
                      isInWishlist(product.id) 
                        ? 'bg-red-50 border-red-400 text-red-600 hover:bg-red-100' 
                        : 'border-gray-400 hover:bg-gray-100'
                    }`}
                  >
                    {isInWishlist(product.id) ? '♥' : '♡'}
                  </button>
                </div>
              </div>

              {/* Buy Now */}
              <button 
                onClick={handleBuyNow}
                className="w-full bg-white border-2 border-[#3E2F2A] text-[#3E2F2A] py-3 text-sm uppercase tracking-wider font-medium hover:bg-[#3E2F2A] hover:text-white transition-colors rounded mb-6"
              >
                BUY NOW
              </button>

              {/* Product Meta */}
              <div className="border-t border-gray-300 pt-6 space-y-2 text-sm">
                <div className="flex">
                  <span className="text-gray-700 w-24">SKU</span>
                  <span className="text-gray-900">{product.sku}</span>
                </div>
                <div className="flex">
                  <span className="text-gray-700 w-24">Categories</span>
                  <span className="text-gray-900">{product.categories}</span>
                </div>
              </div>

              {/* Features */}
              <div className="grid grid-cols-3 gap-4 mt-8 pt-8 border-t border-gray-300">
                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-2 flex items-center justify-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M20 7h-9"></path>
                      <path d="M14 17H5"></path>
                      <circle cx="17" cy="17" r="3"></circle>
                      <circle cx="7" cy="7" r="3"></circle>
                    </svg>
                  </div>
                  <h4 className="text-xs font-semibold text-gray-900 mb-1">Risk Free Shopping</h4>
                  <p className="text-xs text-gray-600">30 Day Returns</p>
                </div>

                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-2 flex items-center justify-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                  </div>
                  <h4 className="text-xs font-semibold text-gray-900 mb-1">Lifetime Warranty</h4>
                  <p className="text-xs text-gray-600">Complimentary Repairs</p>
                </div>

                <div className="text-center">
                  <div className="w-12 h-12 mx-auto mb-2 flex items-center justify-center">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <path d="M20 7h-9"></path>
                      <path d="M14 17H5"></path>
                      <circle cx="17" cy="17" r="3"></circle>
                      <circle cx="7" cy="7" r="3"></circle>
                    </svg>
                  </div>
                  <h4 className="text-xs font-semibold text-gray-900 mb-1">Free Shipping</h4>
                  <p className="text-xs text-gray-600">On Every Order</p>
                </div>
              </div>

              {/* Social Share */}
              <div className="flex items-center gap-6 mt-8 pt-6 border-t border-gray-300">
                <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="18" cy="5" r="3"></circle>
                    <circle cx="6" cy="12" r="3"></circle>
                    <circle cx="18" cy="19" r="3"></circle>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                  </svg>
                  COMPARE
                </button>
                <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    <polyline points="9 22 9 12 15 12 15 22"></polyline>
                  </svg>
                  CONTACT US
                </button>
                <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                  </svg>
                  SHIPPING INFO
                </button>
                <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="18" cy="5" r="3"></circle>
                    <circle cx="6" cy="12" r="3"></circle>
                    <circle cx="18" cy="19" r="3"></circle>
                    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                  </svg>
                  SHARE
                </button>
              </div>
            </div>
          </div>

          {/* Tabs Section */}
          <div className="bg-white rounded-lg overflow-hidden mb-12">
            <div className="flex border-b border-gray-300">
              <button 
                onClick={() => setActiveTab('descriptions')}
                className={`flex-1 py-4 text-sm uppercase tracking-wider font-medium transition-colors ${
                  activeTab === 'descriptions' ? 'bg-[#3E2F2A] text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                DESCRIPTIONS
              </button>
              <button 
                onClick={() => setActiveTab('shipping')}
                className={`flex-1 py-4 text-sm uppercase tracking-wider font-medium transition-colors ${
                  activeTab === 'shipping' ? 'bg-[#3E2F2A] text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                SHIPPING
              </button>
              <button 
                onClick={() => setActiveTab('packaging')}
                className={`flex-1 py-4 text-sm uppercase tracking-wider font-medium transition-colors ${
                  activeTab === 'packaging' ? 'bg-[#3E2F2A] text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                PACKAGING
              </button>
              <button 
                onClick={() => setActiveTab('returns')}
                className={`flex-1 py-4 text-sm uppercase tracking-wider font-medium transition-colors ${
                  activeTab === 'returns' ? 'bg-[#3E2F2A] text-white' : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                RETURNS & CANCELLATIONS
              </button>
            </div>
            
            <div className="p-8">
              {activeTab === 'descriptions' && (
                <div className="text-sm text-gray-700 leading-relaxed">
                  {product?.description || 'No description available for this product.'}
                </div>
              )}
              {activeTab === 'shipping' && (
                <div className="text-sm text-gray-700 leading-relaxed">
                  <p className="mb-3">Free worldwide shipping on all orders over ₹200</p>
                  <p>Delivers in 2-4 working days</p>
                </div>
              )}
              {activeTab === 'packaging' && (
                <div className="text-sm text-gray-700 leading-relaxed">
                  All our products are packaged in premium gift boxes with protective materials to ensure safe delivery.
                </div>
              )}
              {activeTab === 'returns' && (
                <div className="text-sm text-gray-700 leading-relaxed">
                  We offer 30-day returns for all items. Products must be in original condition with all tags attached.
                </div>
              )}
            </div>
          </div>

          {/* Reviews Section */}
          <div className="bg-white rounded-lg p-8 mb-12">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-2xl font-serif text-gray-900">Customer Reviews</h2>
              <button className="bg-[#3E2F2A] text-white px-6 py-2 text-xs uppercase tracking-wider font-medium hover:bg-[#2d2219] transition-colors rounded">
                WRITE A REVIEW
              </button>
            </div>
            
            {/* Reviews List */}
            {product.reviews && product.reviews.length > 0 ? (
              <div className="space-y-6">
                {product.reviews.map((review, index) => (
                  <div key={review.id || index} className="border-b border-gray-200 pb-6 last:border-0">
                    <div className="flex items-start gap-4">
                      <div className="w-12 h-12 rounded-full bg-[#3E2F2A] text-white flex items-center justify-center font-medium">
                        {review.customer_name ? review.customer_name.charAt(0).toUpperCase() : 'A'}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <div>
                            <h4 className="font-medium text-gray-900">{review.customer_name || 'Anonymous'}</h4>
                            <div className="flex items-center gap-2 mt-1">
                              <div className="flex">
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <span key={star} className={star <= (review.rating || 5) ? 'text-yellow-400' : 'text-gray-300'}>★</span>
                                ))}
                              </div>
                              <span className="text-xs text-gray-500">
                                {review.created_at ? new Date(review.created_at).toLocaleDateString() : 'Recently'}
                              </span>
                            </div>
                          </div>
                        </div>
                        {review.title && <h5 className="font-medium text-gray-900 mb-2">{review.title}</h5>}
                        <p className="text-gray-600">{review.comment || review.review_text}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 mb-4">No reviews yet. Be the first to review this product!</p>
                <button className="bg-[#3E2F2A] text-white px-6 py-2 text-xs uppercase tracking-wider font-medium hover:bg-[#2d2219] transition-colors rounded">
                  WRITE THE FIRST REVIEW
                </button>
              </div>
            )}
          </div>

          {/* Similar Products - Hidden until we have similar product data */}
          <div style={{display: 'none'}}>
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-serif text-gray-900">Similar Products</h2>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section className="bg-[#3E2F2A] px-[5%] py-12">
        <div className="max-w-[1400px] mx-auto grid grid-cols-4 gap-8">
          <div className="flex items-start gap-4 text-white">
            <div className="w-12 h-12 flex items-center justify-center">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M20 7h-9"></path>
                <path d="M14 17H5"></path>
                <circle cx="17" cy="17" r="3"></circle>
                <circle cx="7" cy="7" r="3"></circle>
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-1">Free Shipping</h4>
              <p className="text-xs text-gray-300">You'll love it or email orders</p>
            </div>
          </div>

          <div className="flex items-start gap-4 text-white">
            <div className="w-12 h-12 flex items-center justify-center">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-1">15 Days Returns</h4>
              <p className="text-xs text-gray-300">Within 15 days for an exchange</p>
            </div>
          </div>

          <div className="flex items-start gap-4 text-white">
            <div className="w-12 h-12 flex items-center justify-center">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                <line x1="12" y1="19" x2="12" y2="23"></line>
                <line x1="8" y1="23" x2="16" y2="23"></line>
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-1">Customer Support</h4>
              <p className="text-xs text-gray-300">24 hours a day, 7 days a week</p>
            </div>
          </div>

          <div className="flex items-start gap-4 text-white">
            <div className="w-12 h-12 flex items-center justify-center">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect>
                <line x1="1" y1="10" x2="23" y2="10"></line>
              </svg>
            </div>
            <div>
              <h4 className="text-sm font-semibold mb-1">Flexible Payment</h4>
              <p className="text-xs text-gray-300">Pay with multiple credit cards</p>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default ProductDetail;
