import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import { useAuth } from '../context/AuthContext';
import productService from '../services/productService';
import { formatProduct } from '../utils/imageUtils';
import Search from './Search';

const Shop = () => {
  const { addToCart, cartItems, isInCart, getCartCount, getItemQuantity, updateQuantity, removeFromCart } = useCart();
  const { addToWishlist, removeFromWishlist, isInWishlist, wishlistItems } = useWishlist();
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [sortBy, setSortBy] = useState('POPULARITY');
  const [priceRange, setPriceRange] = useState([0, 10000]);
  const [selectedSize, setSelectedSize] = useState(null);
  const [selectedDiamond, setSelectedDiamond] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [isPageTransitioning, setIsPageTransitioning] = useState(false);
  const [categories, setCategories] = useState([]);
  const productsPerPage = 12;

  // Fetch products from backend
  useEffect(() => {
    const fetchAllProducts = async () => {
      try {
        setIsLoading(true);
        // Fetch all products without limit to show everything in shop
        const response = await productService.getProducts({ limit: 100 });
        const backendProducts = response.products || response.items || [];
        
        console.log('Raw backend products:', backendProducts.slice(0, 3));
        
        // Transform backend products to frontend format
        const formattedProducts = backendProducts.map(formatProduct);
        console.log('Formatted products:', formattedProducts.slice(0, 3));
        setAllProducts(formattedProducts);
        setProducts(formattedProducts);
        
        // Extract unique categories from products
        const categoryMap = {};
        formattedProducts.forEach(product => {
          const category = product.category || 'Uncategorized';
          const normalizedCategory = category.toLowerCase();
          console.log(`Product: ${product.name}, Category: ${category}, Normalized: ${normalizedCategory}`);
          if (categoryMap[normalizedCategory]) {
            categoryMap[normalizedCategory]++;
          } else {
            categoryMap[normalizedCategory] = 1;
          }
        });
        
        // Convert to array format with proper capitalization
        const categoriesArray = Object.entries(categoryMap).map(([name, count]) => ({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          originalName: name,
          count
        }));
        
        console.log('Extracted categories:', categoriesArray);
        setCategories(categoriesArray);
      } catch (error) {
        console.error('Error fetching products:', error);
        setAllProducts([]);
        setProducts([]);
        setCategories([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAllProducts();
  }, []);

  // Filter and sort products whenever filters change
  useEffect(() => {
    let filtered = [...allProducts];

    // Filter by category
    if (selectedCategories.length > 0) {
      filtered = filtered.filter(product => {
        const productCategory = (product.category || 'Uncategorized').toLowerCase();
        return selectedCategories.some(selectedCat => 
          productCategory === selectedCat.toLowerCase()
        );
      });
    }

    // Filter by price range - use raw price values
    filtered = filtered.filter(product => {
      const price = product._rawPrice || product.price || 0;
      return price >= priceRange[0] && price <= priceRange[1];
    });

    // Filter by diamond shape
    if (selectedDiamond) {
      filtered = filtered.filter(product => 
        product.diamond_shape?.toLowerCase() === selectedDiamond.toLowerCase() ||
        product.name?.toLowerCase().includes(selectedDiamond.toLowerCase()) ||
        product.description?.toLowerCase().includes(selectedDiamond.toLowerCase())
      );
    }

    // Filter by size
    if (selectedSize) {
      filtered = filtered.filter(product => 
        product.size === selectedSize ||
        product.available_sizes?.includes(selectedSize)
      );
    }

    // Sort products
    switch (sortBy) {
      case 'PRICE_LOW':
        filtered.sort((a, b) => (a._rawPrice || a.price || 0) - (b._rawPrice || b.price || 0));
        break;
      case 'PRICE_HIGH':
        filtered.sort((a, b) => (b._rawPrice || b.price || 0) - (a._rawPrice || a.price || 0));
        break;
      case 'NEWEST':
        filtered.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
        break;
      case 'POPULARITY':
      default:
        // Sort by rating or keep original order
        filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        break;
    }

    setFilteredProducts(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  }, [selectedCategories, priceRange, sortBy, selectedDiamond, selectedSize, allProducts]);

  // Paginate products
  useEffect(() => {
    const startIndex = (currentPage - 1) * productsPerPage;
    const endIndex = startIndex + productsPerPage;
    setProducts(filteredProducts.slice(startIndex, endIndex));
  }, [currentPage, filteredProducts]);

  // Scroll to top with transition when page changes
  useEffect(() => {
    if (currentPage > 1 || isPageTransitioning) {
      // Smooth scroll to top of products section
      const productsSection = document.querySelector('main');
      if (productsSection) {
        productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      // Alternative: scroll to top of page
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [currentPage]);

  // Handle page change with transition
  const handlePageChange = (newPage) => {
    setIsPageTransitioning(true);
    
    // Add fade out effect
    setTimeout(() => {
      setCurrentPage(newPage);
      
      // Remove transition state after animation
      setTimeout(() => {
        setIsPageTransitioning(false);
      }, 300);
    }, 150);
  };

  // Calculate total pages
  const totalPages = Math.ceil(filteredProducts.length / productsPerPage);

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push('...');
        pages.push(currentPage - 1);
        pages.push(currentPage);
        pages.push(currentPage + 1);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  // Helper function to get numeric price value
  const getPrice = (product) => {
    return product._rawPrice || product.price || 0;
  };

  const getOriginalPrice = (product) => {
    return product._rawOldPrice || product.originalPrice || product._rawPrice || product.price || 0;
  };

  // Handle user icon click - redirect to dashboard if logged in
  const handleUserIconClick = () => {
    if (isAuthenticated && user) {
      switch (user.role) {
        case 'super_admin':
          navigate('/super-admin/dashboard');
          break;
        case 'admin':
          navigate('/admin/dashboard');
          break;
        case 'vendor':
          navigate('/vendor/dashboard');
          break;
        case 'customer':
          navigate('/customer/dashboard');
          break;
        default:
          navigate('/login');
      }
    } else {
      navigate('/login');
    }
  };

  const handleCategoryToggle = (categoryName) => {
    setSelectedCategories(prev => {
      if (prev.includes(categoryName)) {
        return prev.filter(cat => cat !== categoryName);
      } else {
        return [...prev, categoryName];
      }
    });
  };

  const diamonds = [
    { name: 'Round', count: 800 },
    { name: 'Princess', count: 450 },
    { name: 'Emerald', count: 530 },
    { name: 'Pear', count: 200 },
    { name: 'Cushion', count: 660 },
    { name: 'Oval', count: 900 },
  ];

  const sizes = [
    { size: 4.0, count: 1200 },
    { size: 4.5, count: 240 },
    { size: 5.0, count: 1775 },
    { size: 6.0, count: 1200 },
    { size: 6.5, count: 900 },
    { size: 7.0, count: 850 },
    { size: 7.5, count: 560 },
    { size: 8.0, count: 350 },
  ];

  return (
    <div className="min-h-screen bg-[#F4E7D0]">
      {/* Header */}
      <header className="bg-[#3E2F2A] text-white px-[5%] py-5">
        <div className="max-w-[1400px] mx-auto flex justify-between items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 cursor-pointer">
            <img src="/Images/1000017875-removebg-preview 9.jpg" alt="Soara Logo" className="w-20 h-20 object-contain" />
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex gap-11 uppercase text-[13px] tracking-wider font-light">
            <Link to="/rings" className="hover:text-yellow-500 transition-colors">RINGS</Link>
            <Link to="/earrings" className="hover:text-yellow-500 transition-colors">EARRINGS</Link>
            <Link to="/bracelets" className="hover:text-yellow-500 transition-colors">BRACELETS</Link>
            <Link to="/pendents" className="hover:text-yellow-500 transition-colors">PENDENTS</Link>
            <Link to="/necklaces" className="hover:text-yellow-500 transition-colors">NECKLACES</Link>
          </nav>

          {/* Icons */}
          <div className="flex gap-5 items-center relative">
            <button 
              onClick={() => setIsSearchOpen(!isSearchOpen)}
              className="hover:text-yellow-500 transition-colors"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="m21 21-4.35-4.35"></path>
              </svg>
            </button>
            <Search isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
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
            <button 
              onClick={handleUserIconClick}
              className="hover:text-yellow-500 transition-colors bg-transparent border-none cursor-pointer"
              aria-label={isAuthenticated ? "Go to Dashboard" : "Login"}
            >
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
          <span className="text-gray-900 font-medium">SHOP</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-[5%] py-8 bg-[#F4E7D0]">
        <div className="max-w-[1400px] mx-auto flex gap-8">
          {/* Sidebar Filters */}
          <aside className="w-[280px] flex-shrink-0">
            {/* Clear Filters Button */}
            {(selectedCategories.length > 0 || selectedDiamond || selectedSize || priceRange[1] < 10000) && (
              <button
                onClick={() => {
                  setSelectedCategories([]);
                  setSelectedDiamond(null);
                  setSelectedSize(null);
                  setPriceRange([0, 10000]);
                }}
                className="w-full mb-6 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                Clear All Filters
              </button>
            )}
            
            {/* Categories */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-base font-semibold text-gray-900">Categories</h3>
                <button className="text-gray-600">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                </button>
              </div>
              <div className="space-y-2.5">
                {categories.map((category) => (
                  <label key={category.name} className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        className="w-4 h-4 rounded border-gray-400" 
                        checked={selectedCategories.includes(category.name)}
                        onChange={() => handleCategoryToggle(category.name)}
                      />
                      <span className="text-sm text-gray-700 group-hover:text-gray-900">{category.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">({category.count})</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Ring by Diamond */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-base font-semibold text-gray-900">Ring by Diamond</h3>
                <button className="text-gray-600">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                </button>
              </div>
              <div className="space-y-2.5">
                {diamonds.map((diamond) => (
                  <label key={diamond.name} className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <input 
                        type="radio" 
                        name="diamond" 
                        className="w-4 h-4" 
                        checked={selectedDiamond === diamond.name}
                        onChange={() => setSelectedDiamond(selectedDiamond === diamond.name ? null : diamond.name)}
                      />
                      <span className="text-sm text-gray-700 group-hover:text-gray-900">{diamond.name}</span>
                    </div>
                    <span className="text-xs text-gray-500">({diamond.count})</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-base font-semibold text-gray-900">Price Range</h3>
                <button className="text-gray-600">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                </button>
              </div>
              <div className="space-y-4">
                <div className="text-sm text-gray-700">
                  Price: <span className="font-medium">₹{priceRange[0]} - ₹{priceRange[1]}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="10000" 
                  value={priceRange[1]}
                  onChange={(e) => setPriceRange([priceRange[0], parseInt(e.target.value)])}
                  className="w-full h-1 bg-gray-300 rounded-lg appearance-none cursor-pointer accent-[#3E2F2A]"
                />
              </div>
            </div>

            {/* Size */}
            <div className="mb-8">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-base font-semibold text-gray-900">Size</h3>
                <button className="text-gray-600">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="18 15 12 9 6 15"></polyline>
                  </svg>
                </button>
              </div>
              <div className="space-y-2.5">
                {sizes.map((size) => (
                  <label key={size.size} className="flex items-center justify-between cursor-pointer group">
                    <div className="flex items-center gap-2">
                      <input 
                        type="radio" 
                        name="size" 
                        className="w-4 h-4" 
                        checked={selectedSize === size.size}
                        onChange={() => setSelectedSize(selectedSize === size.size ? null : size.size)}
                      />
                      <span className="text-sm text-gray-700 group-hover:text-gray-900">{size.size}</span>
                    </div>
                    <span className="text-xs text-gray-500">({size.count})</span>
                  </label>
                ))}
              </div>
            </div>
          </aside>

          {/* Products Grid */}
          <main className="flex-1">
            {/* Toolbar */}
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-4">
                <button className="p-2 bg-[#3E2F2A] text-white rounded">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                  </svg>
                </button>
                <button className="p-2 text-gray-600 hover:text-gray-900">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="8" y1="6" x2="21" y2="6"></line>
                    <line x1="8" y1="12" x2="21" y2="12"></line>
                    <line x1="8" y1="18" x2="21" y2="18"></line>
                    <line x1="3" y1="6" x2="3.01" y2="6"></line>
                    <line x1="3" y1="12" x2="3.01" y2="12"></line>
                    <line x1="3" y1="18" x2="3.01" y2="18"></line>
                  </svg>
                </button>
                <span className="text-sm text-gray-700">
                  Showing {filteredProducts.length > 0 ? (currentPage - 1) * productsPerPage + 1 : 0}–{Math.min(currentPage * productsPerPage, filteredProducts.length)} of {filteredProducts.length} results
                </span>
              </div>

              <div className="flex items-center gap-4">
                <button className="px-4 py-2 text-sm bg-[#3E2F2A] text-white rounded hover:bg-[#2d2219] transition-colors flex items-center gap-2">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                  </svg>
                  FILTER
                </button>
                <select 
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-4 py-2 text-sm bg-transparent border border-gray-400 rounded text-gray-700 cursor-pointer outline-none"
                >
                  <option value="POPULARITY">SORT BY POPULARITY</option>
                  <option value="PRICE_LOW">PRICE: LOW TO HIGH</option>
                  <option value="PRICE_HIGH">PRICE: HIGH TO LOW</option>
                  <option value="NEWEST">NEWEST</option>
                </select>
              </div>
            </div>

            {/* Loading State */}
            {isLoading ? (
              <div className="flex justify-center items-center py-20">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#3E2F2A] mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading products...</p>
                </div>
              </div>
            ) : products.length === 0 ? (
              <div className="text-center py-20">
                <p className="text-gray-600 text-lg">No products found matching your criteria.</p>
              </div>
            ) : (
              <>
            {/* Products Grid/List */}
            <div className={`transition-all duration-300 ease-in-out ${
              isPageTransitioning 
                ? 'opacity-0 scale-95' 
                : 'opacity-100 scale-100'
            }`}>
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-3 gap-6">
                {products.map((product) => (
                  <div key={product.id} className="bg-white rounded-lg overflow-hidden hover:shadow-xl transition-all group relative">
                    <Link to={`/product/${product.id}`} className="block">
                      <div className="relative w-full h-[280px] flex items-center justify-center bg-white p-6">
                        <img src={product.image} alt={product.name} className="max-w-full max-h-full object-contain" />
                      </div>
                      <div className="px-4 py-4 text-center bg-white">
                        <h3 className="text-xs uppercase tracking-wider text-gray-800 mb-2 font-medium">{product.name}</h3>
                        {product.brand && (
                          <p className="text-xs text-gray-500 mb-2">Brand: {product.brand}</p>
                        )}
                        <div className="flex justify-center items-center gap-2 mb-2">
                          <span className="text-sm font-semibold text-gray-900">₹{getPrice(product).toFixed(2)}</span>
                          {getOriginalPrice(product) > getPrice(product) && (
                            <span className="text-sm text-gray-400 line-through">₹{getOriginalPrice(product).toFixed(2)}</span>
                          )}
                        </div>
                        <div className="flex justify-center gap-0.5">
                          {[...Array(5)].map((_, i) => (
                            <span key={i} className="text-yellow-500 text-xs">★</span>
                          ))}
                        </div>
                      </div>
                    </Link>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        const wishlistProduct = {
                          id: product.id,
                          name: product.name,
                          price: getPrice(product),
                          originalPrice: getOriginalPrice(product),
                          image: product.image
                        };
                        if (isInWishlist(product.id)) {
                          removeFromWishlist(product.id);
                        } else {
                          addToWishlist(wishlistProduct);
                        }
                      }}
                      className={`absolute top-3 left-3 border w-9 h-9 rounded-sm flex items-center justify-center transition-all ${
                        isInWishlist(product.id)
                          ? 'bg-red-50 border-red-300 text-red-600 hover:bg-red-100'
                          : 'bg-white border-gray-300 hover:bg-gray-100'
                      }`}
                    >
                      {isInWishlist(product.id) ? '♥' : '♡'}
                    </button>
                    {isInCart(product.id) ? (
                      <div className="mx-4 mb-4 w-[calc(100%-2rem)] flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white py-2.5 rounded transition-all">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
                            if (item && item.quantity > 1) {
                              updateQuantity(item.cartId, item.quantity - 1);
                            } else if (item) {
                              removeFromCart(item.cartId);
                            }
                          }}
                          className="text-xl font-bold hover:scale-110 transition-transform px-2"
                        >
                          −
                        </button>
                        <span className="text-xs font-semibold min-w-[20px] text-center uppercase tracking-wider">
                          {getItemQuantity(product.id)}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
                            if (item) {
                              updateQuantity(item.cartId, item.quantity + 1);
                            }
                          }}
                          className="text-xl font-bold hover:scale-110 transition-transform px-2"
                        >
                          +
                        </button>
                      </div>
                    ) : (
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          addToCart({
                            id: product.id,
                            name: product.name,
                            price: getPrice(product),
                            originalPrice: getOriginalPrice(product),
                            image: product.image,
                            quantity: 1
                          });
                        }}
                        className="mx-4 mb-4 w-[calc(100%-2rem)] bg-[#3E2F2A] hover:bg-[#2d2219] text-white py-2.5 text-xs uppercase tracking-wider font-medium transition-colors"
                      >
                        ADD TO CART
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-6">
                {products.map((product) => (
                  <div key={product.id} className="bg-white rounded-lg overflow-hidden hover:shadow-lg transition-all flex">
                    <Link to={`/product/${product.id}`} className="flex flex-1">
                      <div className="w-[180px] h-[200px] flex items-center justify-center bg-white p-6 flex-shrink-0">
                        <img src={product.image} alt={product.name} className="max-w-full max-h-full object-contain" />
                      </div>
                      <div className="flex-1 p-6 flex flex-col justify-between">
                        <div>
                          <h3 className="text-base font-medium text-gray-900 mb-2">{product.name}</h3>
                          {product.brand && (
                            <p className="text-sm text-gray-500 mb-2">Brand: {product.brand}</p>
                          )}
                          <div className="flex items-center gap-2 mb-3">
                            <span className="text-lg font-semibold text-gray-900">₹{getPrice(product).toFixed(2)}</span>
                            {getOriginalPrice(product) > getPrice(product) && (
                              <span className="text-sm text-gray-400 line-through">₹{getOriginalPrice(product).toFixed(2)}</span>
                            )}
                          </div>
                          <div className="flex gap-0.5 mb-3">
                            {[...Array(5)].map((_, i) => (
                              <span key={i} className="text-yellow-500 text-sm">★</span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </Link>
                    <div className="p-6 flex items-end">
                      <div className="flex items-center gap-3">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            const wishlistProduct = {
                              id: product.id,
                              name: product.name,
                              price: getPrice(product),
                              originalPrice: getOriginalPrice(product),
                              image: product.image
                            };
                            if (isInWishlist(product.id)) {
                              removeFromWishlist(product.id);
                            } else {
                              addToWishlist(wishlistProduct);
                            }
                          }}
                          className={`w-10 h-10 border rounded flex items-center justify-center transition-all ${
                            isInWishlist(product.id)
                              ? 'bg-red-50 border-red-300 text-red-600 hover:bg-red-100'
                              : 'border-gray-300 hover:bg-gray-100'
                          }`}
                        >
                          {isInWishlist(product.id) ? '♥' : '♡'}
                        </button>
                        <button className="w-10 h-10 border border-gray-300 rounded flex items-center justify-center hover:bg-gray-100 transition-all">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="16"></line>
                            <line x1="8" y1="12" x2="16" y2="12"></line>
                          </svg>
                        </button>
                        <button className="w-10 h-10 border border-gray-300 rounded flex items-center justify-center hover:bg-gray-100 transition-all">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                            <polyline points="22,6 12,13 2,6"></polyline>
                          </svg>
                        </button>
                        {isInCart(product.id) ? (
                          <div className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white py-2.5 rounded transition-all">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
                                if (item && item.quantity > 1) {
                                  updateQuantity(item.cartId, item.quantity - 1);
                                } else if (item) {
                                  removeFromCart(item.cartId);
                                }
                              }}
                              className="text-xl font-bold hover:scale-110 transition-transform px-2"
                            >
                              −
                            </button>
                            <span className="text-xs font-semibold min-w-[20px] text-center uppercase tracking-wider">
                              {getItemQuantity(product.id)}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                const item = cartItems.find(i => i.id === product.id || i.product_id === product.id);
                                if (item) {
                                  updateQuantity(item.cartId, item.quantity + 1);
                                }
                              }}
                              className="text-xl font-bold hover:scale-110 transition-transform px-2"
                            >
                              +
                            </button>
                          </div>
                        ) : (
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              addToCart({
                                id: product.id,
                                name: product.name,
                                price: getPrice(product),
                                originalPrice: getOriginalPrice(product),
                                image: product.image,
                                quantity: 1
                              });
                            }}
                            className="flex-1 bg-[#3E2F2A] hover:bg-[#2d2219] text-white py-2.5 text-xs uppercase tracking-wider font-medium transition-colors rounded"
                          >
                            ADD TO CART
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            </div>
            </>
            )}

            {/* Pagination */}
            {!isLoading && filteredProducts.length > 0 && (
              <div className="flex justify-center items-center gap-3 mt-10">
                <button 
                  onClick={() => handlePageChange(Math.max(currentPage - 1, 1))}
                  disabled={currentPage === 1}
                  className={`px-4 py-2 text-sm flex items-center gap-2 transition-colors ${
                    currentPage === 1 
                      ? 'text-gray-400 cursor-not-allowed' 
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="15 18 9 12 15 6"></polyline>
                  </svg>
                  PREV
                </button>
                
                {getPageNumbers().map((pageNum, index) => (
                  pageNum === '...' ? (
                    <span key={`ellipsis-${index}`} className="px-2 text-gray-500">...</span>
                  ) : (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`w-9 h-9 rounded text-sm font-medium transition-colors ${
                        currentPage === pageNum
                          ? 'bg-[#3E2F2A] text-white'
                          : 'text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {String(pageNum).padStart(2, '0')}
                    </button>
                  )
                ))}
                
                <button 
                  onClick={() => handlePageChange(Math.min(currentPage + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className={`px-4 py-2 text-sm flex items-center gap-2 transition-colors ${
                    currentPage === totalPages 
                      ? 'text-gray-400 cursor-not-allowed' 
                      : 'text-gray-700 hover:text-gray-900'
                  }`}
                >
                  NEXT
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </button>
              </div>
            )}
          </main>
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

      {/* Newsletter Section */}
      <section className="px-[5%] py-12 bg-[#F4E7D0]">
        <div className="max-w-[1400px] mx-auto text-center">
          <h2 className="text-3xl font-serif text-gray-900 mb-6">Start a Conversation</h2>
          <p className="text-sm text-gray-700 mb-8">Inside: hot drops, members-only deals, and so much more</p>
          
          <div className="flex justify-center items-center gap-2 max-w-[500px] mx-auto">
            <input 
              type="email" 
              placeholder="Email Address" 
              className="flex-1 px-5 py-3 border border-gray-400 bg-white text-sm text-gray-700 focus:outline-none focus:border-gray-600"
            />
            <button className="bg-[#3E2F2A] text-white px-6 py-3 text-xs font-medium hover:bg-[#2d2219] transition-colors uppercase tracking-wider">
              SIGN UP
            </button>
          </div>

          <div className="flex justify-between items-center mt-12 pt-8 border-t border-gray-400">
            <div>
              <h4 className="text-xs font-semibold text-gray-900 mb-2 uppercase">CONTACT US</h4>
              <p className="text-sm text-gray-700">(405) 555-0128</p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-900 mb-3 uppercase">SOCIAL NETWORKS</h4>
              <div className="flex gap-3 justify-center">
                <a href="#facebook" className="text-gray-700 hover:text-gray-900">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                  </svg>
                </a>
                <a href="#instagram" className="text-gray-700 hover:text-gray-900">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                  </svg>
                </a>
                <a href="#twitter" className="text-gray-700 hover:text-gray-900">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/>
                  </svg>
                </a>
                <a href="#youtube" className="text-gray-700 hover:text-gray-900">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#3E2F2A] px-[5%] py-8">
        <div className="max-w-[1400px] mx-auto">
          <div className="flex justify-center gap-8 mb-6 text-xs">
            <Link to="/rings" className="text-white hover:text-yellow-500 transition-colors uppercase tracking-wide">RINGS</Link>
            <Link to="/bracelets" className="text-white hover:text-yellow-500 transition-colors uppercase tracking-wide">BRACELETS</Link>
            <a href="#about" className="text-white hover:text-yellow-500 transition-colors uppercase tracking-wide">ABOUT US</a>
            <a href="#contact" className="text-white hover:text-yellow-500 transition-colors uppercase tracking-wide">CONTACT US</a>
            <a href="#terms" className="text-white hover:text-yellow-500 transition-colors uppercase tracking-wide">TERMS & CONDITIONS</a>
            <a href="#privacy" className="text-white hover:text-yellow-500 transition-colors uppercase tracking-wide">PRIVACY POLICY</a>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center gap-3 pt-5 border-t border-gray-600">
            <p className="text-xs text-gray-400">Copyright © 2025 Soara. All Rights Reserved.</p>
            <div className="flex gap-2 items-center">
              <div className="w-10 h-6 bg-[#EB001B] rounded flex items-center justify-center text-white text-xs font-bold">M</div>
              <div className="w-10 h-6 bg-[#1434CB] rounded flex items-center justify-center text-white text-xs font-bold">V</div>
              <div className="w-10 h-6 bg-[#00579F] rounded flex items-center justify-center text-white text-xs font-bold">AE</div>
              <div className="w-10 h-6 bg-[#FF5F00] rounded flex items-center justify-center text-white text-xs font-bold">DC</div>
              <div className="w-10 h-6 bg-[#1A1F71] rounded flex items-center justify-center text-white text-xs font-bold">DS</div>
              <div className="w-10 h-6 bg-[#EB001B] rounded flex items-center justify-center text-white text-xs font-bold">MC</div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Shop;
